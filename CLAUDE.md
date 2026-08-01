# Finny

A personal money **management** layer — not a transaction ledger. It answers
"what is due, what is left, and what have I not done yet." It deliberately does
not try to record every purchase.

Declarative by design: recurring commitments, balances, investments and goals
are declared once and updated occasionally. There is no bank feed and no
transaction import.

## Stack

Python **stdlib only** — `http.server` + `sqlite3`. No dependencies, no venv,
no build step. Chosen deliberately: the host has no `python3-venv`, and for
declarative CRUD plus arithmetic the stdlib is sufficient and removes an entire
class of environment problem. Do not add a dependency without a decision record.

Money is **integer cents** everywhere. Floats are permitted only at the display
edge. A rounding drift in a contribution total is a 40% penalty-tax problem,
not a cosmetic one.

## Run

```bash
python3 app.py --port 8090        # data in ~/.finny.db
python3 -m unittest -v            # tests, no install needed
```

## MCP

Always retrieve context via MCP before reasoning or planning.

To add the MCP server (run from this repo directory):

    claude mcp add context-server --transport http \
      http://ubuntu-server.tail58b10c.ts.net:8001/mcp

## Workflow

0. Session bootstrap runs on the first user message — no trigger needed
1. Retrieve context from MCP
2. Check docs/context/ — progress.md, recent-changes.md, constraints.md
3. Propose a plan — wait for approval before touching anything
4. Execute the approved plan
5. Update docs/context/ and any affected docs
6. Re-index: curl -X POST http://localhost:8000/index
7. Commit and push

## Domain rules that must not drift

- A **deposit** into a TFSA is a contribution and counts against the annual and
  lifetime caps. A **buy** inside the account is not — it moves money already
  contributed. Conflating them double-counts a deposit-then-buy cycle.
- The SA tax year runs **1 March to end February**.
- Unused annual TFSA allowance is **forfeited**, never carried over.
- TFSA caps are **per person, not per account**.
