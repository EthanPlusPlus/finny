#!/usr/bin/env python3
"""
Tests for the TFSA slice. Stdlib unittest — runs with `python3 -m unittest`
on a bare host, no venv and no install.

Run:  python3 -m unittest -v
"""

import datetime as dt
import os
import tempfile
import unittest

import app


class TaxYearBoundaries(unittest.TestCase):
    """SA tax year runs 1 March -> end February. Off-by-one here silently
    counts a contribution against the wrong year's cap."""

    def test_march_first_starts_new_year(self):
        d = dt.date(2026, 3, 1)
        self.assertEqual(app.tax_year_start(d), dt.date(2026, 3, 1))
        self.assertEqual(app.tax_year_end(d), dt.date(2027, 2, 28))
        self.assertEqual(app.tax_year_label(d), "2026/2027")

    def test_last_day_of_february_is_previous_year(self):
        d = dt.date(2027, 2, 28)
        self.assertEqual(app.tax_year_start(d), dt.date(2026, 3, 1))
        self.assertEqual(app.tax_year_label(d), "2026/2027")

    def test_january_belongs_to_previous_march(self):
        d = dt.date(2027, 1, 15)
        self.assertEqual(app.tax_year_start(d), dt.date(2026, 3, 1))

    def test_leap_year_end_is_29_february(self):
        # 2028 is a leap year; the tax year ending in it must land on the 29th.
        self.assertEqual(app.tax_year_end(dt.date(2027, 6, 1)), dt.date(2028, 2, 29))


class AmountParsing(unittest.TestCase):
    def parse(self, amount):
        return app.parse_event(
            {"kind": "deposit", "date": "2026-06-01", "amount": amount}
        )["amount_cents"]

    def test_whole_rands(self):
        self.assertEqual(self.parse("2500"), 250_000)

    def test_cents_are_exact(self):
        # The float trap: 1234.55 * 100 == 123454.99999... in binary float.
        self.assertEqual(self.parse("1234.55"), 123_455)

    def test_single_decimal_place_pads(self):
        self.assertEqual(self.parse("10.5"), 1_050)

    def test_separators_tolerated(self):
        self.assertEqual(self.parse("46 000.00"), 4_600_000)
        self.assertEqual(self.parse("46,000"), 4_600_000)

    def test_rejects_zero_and_negative(self):
        for bad in ("0", "-100"):
            with self.assertRaises(app.BadRequest):
                self.parse(bad)

    def test_rejects_bad_date(self):
        with self.assertRaises(app.BadRequest):
            app.parse_event({"kind": "deposit", "date": "2026-02-30", "amount": "1"})
        with self.assertRaises(app.BadRequest):
            app.parse_event({"kind": "deposit", "date": "01/06/2026", "amount": "1"})

    def test_rejects_unknown_kind(self):
        with self.assertRaises(app.BadRequest):
            app.parse_event({"kind": "withdrawal", "date": "2026-06-01", "amount": "1"})


class StateMath(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.conn = app.connect(self.path)

    def tearDown(self):
        self.conn.close()
        os.unlink(self.path)

    def add(self, kind, date, cents, instrument=""):
        self.conn.execute(
            """INSERT INTO events (kind, date, amount_cents, provider, instrument, note, created_at)
               VALUES (?, ?, ?, '', ?, '', '2026-01-01T00:00:00')""",
            (kind, date, cents, instrument),
        )
        self.conn.commit()

    def test_default_annual_limit_is_46k(self):
        s = app.build_state(self.conn, dt.date(2026, 8, 1))
        self.assertEqual(s["annual"]["limit_cents"], 4_600_000)
        self.assertEqual(s["lifetime"]["limit_cents"], 50_000_000)

    def test_only_deposits_count_toward_limits(self):
        """Buying inside the account is not a contribution. If buys counted,
        a single deposit-then-buy cycle would double-count against the cap."""
        self.add("deposit", "2026-06-01", 500_000)
        self.add("buy", "2026-06-02", 500_000, instrument="Satrix")
        s = app.build_state(self.conn, dt.date(2026, 8, 1))
        self.assertEqual(s["annual"]["used_cents"], 500_000)
        self.assertEqual(s["uninvested_cents"], 0)

    def test_uninvested_cash_is_deposits_minus_buys(self):
        self.add("deposit", "2026-06-01", 500_000)
        self.add("buy", "2026-06-02", 200_000)
        s = app.build_state(self.conn, dt.date(2026, 8, 1))
        self.assertEqual(s["uninvested_cents"], 300_000)

    def test_prior_year_deposit_excluded_from_annual_but_not_lifetime(self):
        self.add("deposit", "2026-02-01", 100_000)  # 2025/2026 tax year
        self.add("deposit", "2026-06-01", 300_000)  # 2026/2027 tax year
        s = app.build_state(self.conn, dt.date(2026, 8, 1))
        self.assertEqual(s["annual"]["used_cents"], 300_000)
        self.assertEqual(s["lifetime"]["used_cents"], 400_000)

    def test_prior_years_seed_counts_toward_lifetime_only(self):
        self.conn.execute(
            "UPDATE settings SET value=? WHERE key='prior_years_contributed_cents'",
            ("10000000",),  # R100 000
        )
        self.conn.commit()
        self.add("deposit", "2026-06-01", 300_000)
        s = app.build_state(self.conn, dt.date(2026, 8, 1))
        self.assertEqual(s["annual"]["used_cents"], 300_000)
        self.assertEqual(s["lifetime"]["used_cents"], 10_300_000)

    def test_room_is_the_binding_constraint(self):
        """With almost no lifetime room left, lifetime binds even though the
        annual allowance is untouched."""
        self.conn.execute(
            "UPDATE settings SET value=? WHERE key='prior_years_contributed_cents'",
            (str(49_900_000),),  # R499 000 of R500 000
        )
        self.conn.commit()
        s = app.build_state(self.conn, dt.date(2026, 8, 1))
        self.assertEqual(s["annual"]["remaining_cents"], 4_600_000)
        self.assertEqual(s["lifetime"]["remaining_cents"], 100_000)
        self.assertEqual(s["room_cents"], 100_000)
        self.assertEqual(s["binding"], "lifetime")

    def test_over_contribution_is_surfaced_not_clamped(self):
        self.add("deposit", "2026-06-01", 5_000_000)  # R50 000 > R46 000
        s = app.build_state(self.conn, dt.date(2026, 8, 1))
        self.assertEqual(s["annual"]["over_cents"], 400_000)
        self.assertEqual(s["annual"]["remaining_cents"], 0)
        self.assertEqual(s["room_cents"], 0)

    def test_unused_allowance_does_not_carry_over(self):
        """Deposit nothing in 2025/2026; the 2026/2027 allowance is still just
        the annual limit, never limit + forfeited room."""
        s = app.build_state(self.conn, dt.date(2026, 8, 1))
        self.assertEqual(s["annual"]["remaining_cents"], 4_600_000)


if __name__ == "__main__":
    unittest.main()
