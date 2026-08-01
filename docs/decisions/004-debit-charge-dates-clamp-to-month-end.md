---
record_type: canonical
id: "004"
title: Debit charge dates clamp to month end
date: 2026-08-01
status: active
category: domain
supersedes: []
superseded_by: []
---

# Decision 004 — Debit charge dates clamp to month end

## Status

Adopted 2026-08-01 with the debit order slice.

## Context

A debit order is declared as a **day of the month**, because that is how the
bank and the user think about it: "the Wi-Fi goes off on the 1st."

Days 29, 30 and 31 do not exist in every month. A debit ordered for the 31st
has no 31st in April, June, September or November, and no 29th, 30th or 31st in
a non-leap February. `datetime.date(2026, 2, 31)` raises `ValueError`.

There are three possible behaviours and two of them are wrong:

- **Crash.** Constructing the date raises and the whole month view fails. Loud,
  at least, but the app is unusable in four months of the year.
- **Skip the charge.** Silently drop rows whose day does not exist this month.
  This is the dangerous one: the monthly committed total quietly understates by
  the amount of the missing debit, in exactly the months where it matters. The
  user would be told they have more room than they do.
- **Clamp to the last day of the month.** The charge still appears, on the last
  day the month has.

## Decision

`charge_date(day, year, month)` returns
`date(year, month, min(day, days_in_month(year, month)))`.

A debit ordered for the 31st falls on 30 September, 28 February in a common
year, and 29 February in a leap year.

This matches what banks actually do with month-end debit orders, and — more
importantly — it matches **what the user will see on the statement**. The
tracker's job is to make a real charge unsurprising; a model that disagrees
with the bank statement defeats the purpose.

A charge dated **today** counts as already gone, not still to come. The debit
that prompted this whole project went off the same morning it caused alarm; if
it showed as pending, the app would contradict the notification that made the
user open it.

## Consequences

- The monthly committed total is correct in every month, including February.
- Two debits ordered for the 30th and 31st collapse onto the same date in
  February. That is accurate rather than a bug — both really are charged that
  day.
- `days_in_month` is computed by stepping to the first of the next month and
  subtracting a day, which handles the December rollover and leap years without
  a lookup table or a `calendar` import.
- Tested explicitly for the 30-day, common-February, leap-February and December
  cases, plus a regression test asserting a 31st-of-the-month debit still
  appears in a February total.
