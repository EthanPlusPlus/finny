# Constraints

Active limitations that materially affect design or system behaviour.

---

- **No third-party dependencies.** Stdlib only — [[../decisions/001-stdlib-only-no-dependencies|Decision 001]]. Adding one requires a decision record.
- **`http.server` is not hardened for hostile traffic.** Single-threaded-per-connection, no rate limiting, no CSRF protection, no auth. Acceptable only while access is tailnet-scoped and single-user. Public exposure requires revisiting [[../decisions/001-stdlib-only-no-dependencies|Decision 001]], not just putting auth in front.
- **No authentication.** Anyone on the tailnet can read and write the data. Fine for one user on a private tailnet; blocks any sharing.
- **The host has no `python3-venv`.** Installing it needs sudo. This constraint is what forced Decision 001, and it still applies to anything else built on this VM.
- **Root partition runs hot** — 87% at time of writing, already expanded 30GB → 40GB in June 2026. Avoid new Docker images for this project.
- **Not a systemd service yet.** The process does not survive a reboot.
- **Reminders are in-app only.** The dashboard shows what is outstanding, but nothing reaches the user unprompted. This is a known gap against the credit-card use case, where "remembering to check" is the failure being solved.
