# Finny — architecture

Single authoritative description of how Finny is put together.

---

## Shape

```
static/index.html        one file — inline CSS + JS, no build step
        ↓ fetch
app.py                   http.server request handler + domain functions
        ↓ sqlite3
~/.finny.db              SQLite, WAL mode
```

One process, one file of application code, one database file. There is no
framework, no ORM, no bundler and no container
([[../decisions/001-stdlib-only-no-dependencies|Decision 001]]).

## Layers inside `app.py`

| Section | Responsibility |
|---|---|
| tax year helpers | Pure date arithmetic. `tax_year_start/end/label`. |
| storage | Schema, connection, settings defaults. |
| domain | `build_state()` — the single source of every derived figure. |
| validation | `parse_event()` — raises `BadRequest`, never trusts input. |
| http | `Handler` — routing, JSON, static files. |

**`build_state()` is the whole domain.** Every number the UI shows is computed
there and nowhere else. The frontend performs no financial arithmetic — it
formats and renders. That is deliberate: two implementations of the same rule
drift, and here a drifted rule is a penalty-tax number.

Pure functions are separated from I/O so the tests exercise the arithmetic
directly without a running server.

## Data model

One table, one row per event.

```
events(id, kind, date, amount_cents, provider, instrument, note, created_at)
       kind ∈ {deposit, buy}   -- CHECK constraint
```

`settings` is a key/value table holding the statutory limits and the
prior-years seed, so a budget change is a settings edit rather than a code
change.

Storing deposits and buys in one table with a `kind` discriminator, rather than
two tables, keeps "everything that happened, in order" a single query — and the
two-step pattern generalises to the later slices
([[../decisions/003-deposit-and-buy-are-distinct-events|Decision 003]]).

## Derived figures

Nothing derived is stored. Everything is recomputed per request from the event
log, which means the numbers cannot go stale relative to the events.

| Figure | Rule |
|---|---|
| annual used | Σ deposits within the current SA tax year |
| lifetime used | Σ all deposits + `prior_years_contributed_cents` |
| uninvested | Σ deposits − Σ buys |
| room | `min(annual remaining, lifetime remaining)` — the binding constraint |
| to-max monthly | room ÷ months remaining, rounded **down** |

Over-contribution is reported as a positive `over_cents`, never clamped away —
the situation that most needs surfacing must not be the one that is hidden.

## Boundaries

- **No money arithmetic in the browser.** `toCents()` exists only to send a
  correctly-typed value to the server.
- **No stored derived state.** No caching, no materialised totals.
- **Static file serving is path-contained** — resolved paths must stay under
  `static/`, verified by test and by a traversal check.

## Deployment

`python3 app.py --port 8090`. Reachable over the tailnet. Not a systemd service
yet, so it does not survive a reboot — see
[[../context/constraints|constraints]].
