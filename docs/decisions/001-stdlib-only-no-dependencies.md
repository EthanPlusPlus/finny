---
record_type: canonical
id: "001"
title: Stdlib only — no dependencies, no venv, no build step
date: 2026-08-01
status: active
category: architecture
supersedes: []
superseded_by: []
---

# Decision 001 — Stdlib only

## Status

Adopted 2026-08-01, in force from the first commit.

## Context

The first slice was going to be FastAPI + uvicorn, matching `flight-planner`
and the rest of the house style. `python3 -m venv` failed: the VM has no
`python3.12-venv` package. Installing it needs sudo and a system change.

That was the trigger, not the reason. Three things made stdlib the better
answer rather than the fallback:

1. **The app is CRUD plus arithmetic.** Declarative records in, derived figures
   out. There is no async workload, no streaming, no auth, no ORM-shaped
   problem. FastAPI would have been carried, not used.
2. **The host is disk-constrained.** The root partition sat at 87% during the
   build, having already been expanded 30GB → 40GB in June for the same reason.
   A new Docker image or a venv full of wheels is real cost against a real limit.
3. **The project that cannot run its own tests is next door.** `context-server`
   has a suite whose "143 green" figure could not be reproduced during the
   2026-07-30 sweep — no pytest on the host, no pytest in the container, no CI.
   The cause is that its tests need an environment nobody can currently
   reconstruct. Depending on nothing makes that failure mode unreachable.

## Decision

Finny depends on the Python standard library only — `http.server`, `sqlite3`,
`json`, `datetime`. No third-party packages, no virtualenv, no build step, no
transpiler, no bundler. The frontend is one hand-written HTML file with inline
CSS and JS, served as a static asset.

Tests use stdlib `unittest` and run with `python3 -m unittest` on a bare host.

**Adding a dependency requires a new decision record** naming what it does that
the stdlib cannot, and what it costs to reconstruct the environment without it.

## Consequences

- Deployment is copying a directory and running one command. No image build,
  no lockfile, no dependency resolution, nothing to drift.
- The test suite runs anywhere Python 3 exists. It cannot become
  unreproducible the way its neighbour's did.
- Accepted cost: request parsing, routing and validation are hand-written.
  This is roughly 80 lines. It is bounded and it is the whole bill.
- Accepted cost: no automatic OpenAPI schema, no dependency-injected validation.
  For a single-user declarative app these are conveniences, not capabilities.
- `http.server` is explicitly not hardened for hostile traffic. Acceptable
  only while access is tailnet-scoped and single-user — see
  [[../context/constraints|constraints]]. Exposing Finny publicly requires
  revisiting this decision, not just adding auth in front of it.
