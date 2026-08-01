# Recent Changes

Rolling log of meaningful changes. Keep last ~10 entries.

---

- **Finny bootstrapped — TFSA slice shipped (2026-08-01)** — First slice of a personal money *management* layer (not a ledger). TFSA annual + lifetime cap tracking against the 2026/2027 SARS limits (annual raised R36 000 → R46 000 on 1 March 2026 — verified, not remembered), the deposit-then-buy two-step with an uninvested-cash flag, and prior-years seeding so lifetime is correct without back-entering history. Three founding decisions: stdlib-only (D001), integer cents (D002), deposit≠buy (D003). 19 stdlib `unittest` tests green. Runs on port 8090, tailnet-scoped.
