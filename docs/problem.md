# The problem Finny solves

## The moment

A debit order lands. The notification says a few hundred rand left the account.
The first reaction is alarm — *what did I buy?* — followed a minute later by
the realisation that it was the Wi-Fi, on the same day it always goes off.

Nothing was wrong. The money was always going to leave. The only thing missing
was knowing it was coming.

## The root cause

The money is not the problem. Expenses are low — no car, no medical aid,
no insurance, with family covering a lot. There is genuine surplus most months.

The problem is **the absence of a picture**, and it produces two failures that
look opposite but share a cause:

**Fear of spending.** Money is available, but with nothing tracking it, any
discretionary purchase feels like it might be the one that breaks something.
So it does not happen. The surplus is not enjoyed, it is *avoided*.

**Drift into zero.** Whatever is not deliberately assigned quietly evaporates
by month end. Surplus that rolls over is not saved and not spent on anything
chosen — it is simply absorbed.

Both are symptoms of the same gap: **no structural home for money that has not
been assigned a job.**

## What Finny is

A **management layer**, not a ledger.

It does not want every transaction. It answers three questions:

1. **What is coming?** — so a legitimate debit is never a scare.
2. **What is left?** — so spending is a decision, not a gamble.
3. **What have I not done yet?** — the manual steps that are easy to half-finish.

That third one is the sharpest. Several money tasks here are multi-step and
stall in the middle:

- A TFSA contribution is *deposit cash*, then *buy the instrument*. Cash that
  arrives and is never invested is a silent failure — it looks done and is not.
- A credit card is *spend*, then *pay it off before the due date*. The card is
  currently unused out of fear of exactly this step being missed.
- A tax rebate is worth real money and is gated behind having tracking good
  enough to claim it confidently.

## Design consequences

- **Declarative, not ingested.** Commitments, balances and goals are declared
  once and updated occasionally. No bank feed, no CSV import, no categorisation
  UI. The cost of keeping it current has to stay near zero or it will be
  abandoned — and an abandoned tracker is worse than none, because it lies.
- **Surface the incomplete, not just the recorded.** The valuable state is what
  is *outstanding*: cash deposited but not invested, a statement not yet paid,
  surplus not yet assigned. A tool that only shows what happened misses the point.
- **Rollover must be a decision.** Surplus should force a choice — save it or
  spend it deliberately — rather than being allowed to quietly disappear.

## Non-goals

- Full transaction categorisation and net-worth reporting
- Anything requiring bank credentials or open-banking integration
- Multi-user, sharing, or advice
