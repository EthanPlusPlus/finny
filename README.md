# finny

A management layer for money, not a transaction ledger. It answers "what is
due, what is left, and what have I not done yet" — it does not try to record
every purchase.

**Slice 1 (built): TFSA.** Contribution limits, and the deposit-then-buy two-step.

## Running it

```bash
python3 app.py --port 8090
```

Stdlib only — `http.server` + `sqlite3`. No venv, no dependencies, no build
step. Chosen deliberately: the host has no `python3-venv`, and for declarative
CRUD plus arithmetic the stdlib is sufficient and removes an entire class of
environment problem.

Data lives in `~/.finny.db` (SQLite, WAL). Override with `--db`.

## Tests

```bash
python3 -m unittest -v
```

19 tests, stdlib `unittest`, runs on a bare host.

## The two things this slice gets right

**A deposit is a contribution; a purchase is not.** Moving cash into the TFSA
counts against the annual and lifetime caps. Buying an instrument *inside* the
account is not a contribution — it moves money already contributed. Conflating
them double-counts a single deposit-then-buy cycle against the cap. `deposit`
and `buy` are separate event kinds and only deposits count toward limits.

**Money is integer cents end to end.** No floats anywhere except at the display
edge. `1234.55 * 100` is `123454.999...` in binary floating point; over enough
entries that drift becomes a wrong contribution total, and a wrong contribution
total against the R500 000 cap is a 40% penalty-tax problem.

## SARS limits (2026/2027 tax year)

| | |
|---|---|
| Annual | **R46 000** — raised from R36 000 with effect from 1 March 2026 |
| Lifetime | **R500 000** |
| Tax year | 1 March – end February |
| Unused annual allowance | **Forfeited.** Does not carry over. |
| Excess contributions | Taxed at **40%** |

The lifetime cap applies to *contributions*, not to growth — an account that
grows past R500 000 is fine.

Both limits are editable in Settings, so a future budget change needs no code
edit.

## Seeding prior years

Settings has "Contributed in earlier tax years". Put everything you contributed
before the deposits listed in the app there, and the lifetime figure is correct
without back-entering years of history. Note the caps are **per person, not per
account** — if you hold a TFSA at more than one provider, this figure must
include all of them.

## Not built yet

Deliberately deferred; slice 1 is TFSA only.

- Debit order register and calendar
- Monthly budget with rollover allocation
- Credit card payoff tracker
- Savings goals
- Reminders that reach you (currently in-app dashboard only, which means it
  only works if you open it)
