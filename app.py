#!/usr/bin/env python3
"""
finance-tracker — TFSA slice.

Stdlib only (http.server + sqlite3). No venv, no dependencies, no build step.

Money is stored as integer cents everywhere. Rands never touch a float except
at the display edge — a float rounding error in a contribution total is a 40%
penalty-tax problem, not a cosmetic one.

Run:  python3 app.py [--port 8090] [--db ~/.finny.db]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import datetime as dt
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "static")

# SARS limits. Annual limit rose R36 000 -> R46 000 with effect from
# 1 March 2026 (2026/2027 year of assessment). Both are overridable in
# settings so a future budget change does not require a code edit.
DEFAULT_ANNUAL_LIMIT_CENTS = 46_000_00
DEFAULT_LIFETIME_LIMIT_CENTS = 500_000_00

# The South African tax year runs 1 March -> end of February.
TAX_YEAR_START_MONTH = 3

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ── tax year helpers ─────────────────────────────────────────────────────────

def tax_year_start(d: dt.date) -> dt.date:
    """First day of the SA tax year containing d."""
    year = d.year if d.month >= TAX_YEAR_START_MONTH else d.year - 1
    return dt.date(year, TAX_YEAR_START_MONTH, 1)


def tax_year_end(d: dt.date) -> dt.date:
    """Last day (inclusive) of the SA tax year containing d."""
    start = tax_year_start(d)
    return dt.date(start.year + 1, TAX_YEAR_START_MONTH, 1) - dt.timedelta(days=1)


def tax_year_label(d: dt.date) -> str:
    start = tax_year_start(d)
    return f"{start.year}/{start.year + 1}"


# ── storage ──────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- A TFSA "contribution" for limit purposes is the DEPOSIT of cash into the
-- account. Buying an instrument inside the account is not a contribution --
-- it moves money you already contributed. Conflating the two is the single
-- easiest way to miscount against the annual cap, so they are separate kinds
-- and only 'deposit' rows count toward limits.
CREATE TABLE IF NOT EXISTS events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    kind         TEXT    NOT NULL CHECK (kind IN ('deposit', 'buy')),
    date         TEXT    NOT NULL,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    provider     TEXT    NOT NULL DEFAULT '',
    instrument   TEXT    NOT NULL DEFAULT '',
    note         TEXT    NOT NULL DEFAULT '',
    created_at   TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_date ON events(date);
"""

DEFAULT_SETTINGS = {
    "annual_limit_cents": str(DEFAULT_ANNUAL_LIMIT_CENTS),
    "lifetime_limit_cents": str(DEFAULT_LIFETIME_LIMIT_CENTS),
    # Total contributed in tax years BEFORE the earliest year you itemise here.
    # Lets you seed lifetime usage without back-entering years of deposits.
    "prior_years_contributed_cents": "0",
    "default_provider": "",
}


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    for k, v in DEFAULT_SETTINGS.items():
        conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
    conn.commit()
    return conn


def get_settings(conn: sqlite3.Connection) -> dict:
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    out = {r["key"]: r["value"] for r in rows}
    for k, v in DEFAULT_SETTINGS.items():
        out.setdefault(k, v)
    return out


# ── domain ───────────────────────────────────────────────────────────────────

def build_state(conn: sqlite3.Connection, today: dt.date | None = None) -> dict:
    today = today or dt.date.today()
    s = get_settings(conn)

    annual_limit = int(s["annual_limit_cents"])
    lifetime_limit = int(s["lifetime_limit_cents"])
    prior = int(s["prior_years_contributed_cents"])

    ty_start = tax_year_start(today)
    ty_end = tax_year_end(today)

    rows = conn.execute(
        "SELECT * FROM events ORDER BY date DESC, id DESC"
    ).fetchall()
    events = [dict(r) for r in rows]

    deposits = [e for e in events if e["kind"] == "deposit"]
    buys = [e for e in events if e["kind"] == "buy"]

    def in_current_year(e) -> bool:
        return ty_start.isoformat() <= e["date"] <= ty_end.isoformat()

    annual_used = sum(e["amount_cents"] for e in deposits if in_current_year(e))
    itemised_lifetime = sum(e["amount_cents"] for e in deposits)
    lifetime_used = itemised_lifetime + prior

    # Cash that reached the account but was never put to work. This is the
    # second half of the two-step: deposit, then buy. Money idling here is
    # the failure mode the tracker exists to make visible.
    deposited_total = itemised_lifetime
    bought_total = sum(e["amount_cents"] for e in buys)
    uninvested = deposited_total - bought_total

    annual_remaining = max(annual_limit - annual_used, 0)
    lifetime_remaining = max(lifetime_limit - lifetime_used, 0)
    # The binding constraint is whichever runs out first.
    room = min(annual_remaining, lifetime_remaining)

    days_left = (ty_end - today).days
    months_left = max(days_left, 0) / 30.44

    return {
        "today": today.isoformat(),
        "tax_year": {
            "label": tax_year_label(today),
            "start": ty_start.isoformat(),
            "end": ty_end.isoformat(),
            "days_left": days_left,
        },
        "annual": {
            "limit_cents": annual_limit,
            "used_cents": annual_used,
            "remaining_cents": annual_remaining,
            "over_cents": max(annual_used - annual_limit, 0),
            "pct": round(100 * annual_used / annual_limit, 1) if annual_limit else 0,
        },
        "lifetime": {
            "limit_cents": lifetime_limit,
            "used_cents": lifetime_used,
            "prior_years_cents": prior,
            "remaining_cents": lifetime_remaining,
            "over_cents": max(lifetime_used - lifetime_limit, 0),
            "pct": round(100 * lifetime_used / lifetime_limit, 1) if lifetime_limit else 0,
        },
        "room_cents": room,
        "binding": "lifetime" if lifetime_remaining < annual_remaining else "annual",
        "uninvested_cents": uninvested,
        "to_max_monthly_cents": int(room / months_left) if months_left >= 1 else room,
        "settings": s,
        "events": events,
    }


# ── validation ───────────────────────────────────────────────────────────────

class BadRequest(Exception):
    pass


def parse_event(payload: dict) -> dict:
    kind = str(payload.get("kind", "")).strip()
    if kind not in ("deposit", "buy"):
        raise BadRequest("kind must be 'deposit' or 'buy'")

    date = str(payload.get("date", "")).strip()
    if not DATE_RE.match(date):
        raise BadRequest("date must be YYYY-MM-DD")
    try:
        dt.date.fromisoformat(date)
    except ValueError:
        raise BadRequest("date is not a real calendar date")

    raw = str(payload.get("amount", "")).strip().replace(",", "").replace(" ", "")
    if not raw:
        raise BadRequest("amount is required")
    try:
        # Parse via string to avoid binary-float drift on values like 1234.55
        whole, _, frac = raw.partition(".")
        frac = (frac + "00")[:2]
        amount_cents = int(whole or "0") * 100 + int(frac)
    except ValueError:
        raise BadRequest("amount must be a number")
    if amount_cents <= 0:
        raise BadRequest("amount must be greater than zero")

    return {
        "kind": kind,
        "date": date,
        "amount_cents": amount_cents,
        "provider": str(payload.get("provider", "")).strip()[:80],
        "instrument": str(payload.get("instrument", "")).strip()[:80],
        "note": str(payload.get("note", "")).strip()[:280],
        "created_at": dt.datetime.now().isoformat(timespec="seconds"),
    }


# ── http ─────────────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    server_version = "finance-tracker"
    conn: sqlite3.Connection = None  # set on the server instance

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} {fmt % args}", flush=True)

    # -- helpers

    def _json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        if length > 64 * 1024:
            raise BadRequest("payload too large")
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            raise BadRequest("body is not valid JSON")

    def _static(self, path: str):
        name = "index.html" if path in ("/", "") else path.lstrip("/")
        # Contain to STATIC; never serve outside it.
        full = os.path.normpath(os.path.join(STATIC, name))
        if not full.startswith(STATIC) or not os.path.isfile(full):
            self.send_error(404, "Not found")
            return
        ctype = {
            ".html": "text/html; charset=utf-8",
            ".js": "text/javascript",
            ".css": "text/css",
            ".svg": "image/svg+xml",
        }.get(os.path.splitext(full)[1], "application/octet-stream")
        with open(full, "rb") as fh:
            data = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    # -- routes

    def do_GET(self):
        route = urlparse(self.path).path
        if route == "/api/state":
            self._json(build_state(self.conn))
        elif route == "/api/health":
            self._json({"status": "ok"})
        else:
            self._static(route)

    def do_POST(self):
        route = urlparse(self.path).path
        try:
            if route == "/api/events":
                ev = parse_event(self._body())
                cur = self.conn.execute(
                    """INSERT INTO events
                       (kind, date, amount_cents, provider, instrument, note, created_at)
                       VALUES (:kind, :date, :amount_cents, :provider, :instrument, :note, :created_at)""",
                    ev,
                )
                self.conn.commit()
                self._json({"id": cur.lastrowid, "state": build_state(self.conn)}, 201)

            elif route == "/api/settings":
                payload = self._body()
                allowed = set(DEFAULT_SETTINGS)
                for key, val in payload.items():
                    if key not in allowed:
                        raise BadRequest(f"unknown setting: {key}")
                    if key.endswith("_cents"):
                        try:
                            val = str(int(val))
                        except (TypeError, ValueError):
                            raise BadRequest(f"{key} must be an integer number of cents")
                    self.conn.execute(
                        "INSERT INTO settings (key, value) VALUES (?, ?) "
                        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                        (key, str(val)),
                    )
                self.conn.commit()
                self._json({"state": build_state(self.conn)})
            else:
                self.send_error(404, "Not found")
        except BadRequest as exc:
            self._json({"error": str(exc)}, 400)

    def do_DELETE(self):
        route = urlparse(self.path).path
        m = re.match(r"^/api/events/(\d+)$", route)
        if not m:
            self.send_error(404, "Not found")
            return
        self.conn.execute("DELETE FROM events WHERE id = ?", (int(m.group(1)),))
        self.conn.commit()
        self._json({"state": build_state(self.conn)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8090)))
    ap.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
    ap.add_argument(
        "--db",
        default=os.environ.get("DB", os.path.expanduser("~/.finny.db")),
    )
    args = ap.parse_args()

    Handler.conn = connect(args.db)
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"finance-tracker on http://{args.host}:{args.port}  db={args.db}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped", flush=True)


if __name__ == "__main__":
    main()
