---
record_type: canonical
id: "002"
title: Money is integer cents end to end
date: 2026-08-01
status: active
category: architecture
supersedes: []
superseded_by: []
---

# Decision 002 — Money is integer cents

## Status

Adopted 2026-08-01, in force from the first commit.

## Context

Binary floating point cannot represent most decimal fractions exactly.
`1234.55 * 100` evaluates to `123454.99999999999` in IEEE 754 doubles. Truncate
that and a cent disappears; accumulate it across enough records and a total
drifts.

In most applications that is cosmetic. Here it is not. Finny's central figure
is *cumulative contributions measured against a hard statutory cap*. SARS taxes
TFSA contributions above R500 000 at **40%**. A total that drifts upward can
trigger a penalty; a total that drifts downward can report room that does not
exist and invite the same penalty. The error compounds silently and is only
discovered at assessment.

## Decision

Money is stored, transported and computed as **integer cents** everywhere:
the SQLite column type is `INTEGER`, the JSON field names carry a `_cents`
suffix, and all arithmetic is integer arithmetic.

Floats are permitted at exactly one place: the display edge, when formatting a
figure for a human to read.

Parsing splits the input string on the decimal point and assembles cents from
the two halves as integers. It never multiplies a parsed float by 100:

```python
whole, _, frac = raw.partition(".")
frac = (frac + "00")[:2]
amount_cents = int(whole or "0") * 100 + int(frac)
```

The same rule applies in the browser — `toCents()` in the frontend parses by
string split, not `parseFloat(x) * 100`.

## Consequences

- Every amount crossing an API boundary is named `*_cents` so a bare `amount`
  is visibly suspicious in review.
- Division is the one operation that can still lose precision — the
  "deposit this much per month to max out" figure is derived, advisory, and
  rounded down with `int()`. Rounding down is deliberate: advice that
  under-shoots a statutory cap is safe, advice that over-shoots is not.
- A future currency with different minor units would need this revisited. Not a
  real prospect: this is a single-user ZAR tool.
- Tests assert exact cent values, including the `1234.55` case specifically, so
  a regression to float arithmetic fails immediately rather than drifting.
