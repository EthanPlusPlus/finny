# Recent Changes

Rolling log of meaningful changes. Keep last ~10 entries.

---

- **Debit order register shipped (2026-08-01)** — The slice aimed squarely at the moment in [[../problem|problem.md]]: a charge lands and the first reaction is alarm. Standing commitments are declared once (name, amount, day, account, category, variable flag) rather than logged per occurrence — the charge date is derived, so there is no monthly bookkeeping. Month-end clamping recorded as [[../decisions/004-debit-charge-dates-clamp-to-month-end|Decision 004]]: a 31st debit falls on the 28th in February rather than crashing or, worse, being silently dropped from the total. The month splits into already-gone vs still-to-come, with a next-7-days view. The lookup box answers "what was that charge?" against the register directly, with a 15% tolerance band for variable-amount orders. Debits can be paused rather than deleted, so a cancelled subscription keeps its history. 16 new tests (35 total), all stdlib.
- **Finny bootstrapped — TFSA slice shipped (2026-08-01)** — First slice of a personal money *management* layer (not a ledger). TFSA annual + lifetime cap tracking against the 2026/2027 SARS limits (annual raised R36 000 → R46 000 on 1 March 2026 — verified, not remembered), the deposit-then-buy two-step with an uninvested-cash flag, and prior-years seeding so lifetime is correct without back-entering history. Three founding decisions: stdlib-only (D001), integer cents (D002), deposit≠buy (D003). 19 stdlib `unittest` tests green. Runs on port 8090, tailnet-scoped.
