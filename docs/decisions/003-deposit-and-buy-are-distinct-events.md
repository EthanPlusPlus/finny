---
record_type: canonical
id: "003"
title: A deposit is a contribution; a buy is not
date: 2026-08-01
status: active
category: domain
supersedes: []
superseded_by: []
---

# Decision 003 — Deposit and buy are distinct events

## Status

Adopted 2026-08-01, in force from the first commit.

## Context

Funding a tax-free share account is two steps, not one:

1. **Deposit** — move cash from a bank account into the TFSA.
2. **Buy** — use that cash to purchase an instrument inside the account.

Only step 1 is a *contribution* in SARS terms. Step 2 moves money that has
already been contributed; it does not consume any further allowance.

The naive model treats "I put R2 500 into my TFSA and bought Satrix with it" as
one R2 500 event. Any model that counts both steps against the cap records
R5 000 of contribution for R2 500 of actual funding. Against a R46 000 annual
limit that halves the apparent allowance; against the R500 000 lifetime cap it
produces a permanently wrong number.

The inverse error matters more. Step 2 is the one that gets forgotten — cash
lands in the share account and is never invested. It looks complete from the
outside because the money left the bank account. Sitting uninvested it earns
nothing and quietly wastes allowance that cannot be reclaimed, because unused
annual allowance is forfeited rather than carried forward.

## Decision

`deposit` and `buy` are separate event kinds on one `events` table,
distinguished by a `kind` column with a `CHECK` constraint.

- **Only `deposit` rows count toward the annual and lifetime caps.**
- **Uninvested cash** is `sum(deposits) - sum(buys)`, surfaced prominently in
  the UI as an outstanding action rather than buried in a report.
- A negative uninvested figure means purchases exceed deposits, which is not a
  legitimate state — it indicates a missing deposit record, and is flagged as
  such rather than clamped to zero.

The UI labels the tabs `1 · Deposit cash` and `2 · Buy shares` to make the
ordering part of the interface rather than something the user has to remember.

## Consequences

- The "what have I not finished" question from [[../problem|problem.md]] has a
  concrete answer for this slice: uninvested cash is a half-completed
  contribution, displayed as a flag.
- The same shape generalises to the other multi-step commitments — a credit
  card statement is *spend* then *pay off*, with the unpaid balance as the
  outstanding half. Later slices should reuse this two-event pattern rather
  than invent a per-domain one.
- Withdrawals are not modelled. They are rare, and in SA a withdrawal does
  **not** restore contribution room — the allowance stays consumed. Modelling
  them as negative deposits would be wrong for exactly that reason. If they are
  ever added they need a third kind that does not credit back against the caps.
