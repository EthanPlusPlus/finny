# Documentation Structure — Finny

Follows the Prismo-wide structure defined in `~/canon/prismo/docs/STRUCTURE.md`.

## Folders

- `context/` — live state: progress, recent changes, active constraints
- `decisions/` — why things were built the way they were; numbered `NNN-slug.md`
- `architecture/` — intended design of the system
- `runbooks/` — repeatable operational procedures
- `proposed-ideas/` — ideas with enough reasoning to track; numbered `NNN-slug.md`

## Key Files

- `problem.md` — the root problem this tool exists to solve; read this first
- `architecture/model.md` — how the system is put together
- `context/constraints.md` — active limitations that affect any future work
- `open-questions.md` — unresolved questions worth tracking across sessions

## Domain rules that must not drift

Recorded as decisions because getting them wrong has a financial consequence,
not just a code one:

- [[decisions/002-money-as-integer-cents|D002]] — money is integer cents; floats
  only at the display edge
- [[decisions/003-deposit-and-buy-are-distinct-events|D003]] — a deposit is a
  contribution, a buy inside the account is not
