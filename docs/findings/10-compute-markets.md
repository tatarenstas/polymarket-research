# 10 — Compute markets (GPU rental price): first look

Date: 2026-11-25. Status: first look, no backtest. Not investment advice.

## 1. What the category is

Polymarket's new Tech → Compute section lists ladders of binary markets on GPU rental
prices: "Will the average Ornn H100 rental price in December 2026 be above $X?", one market
per strike, for each month (Dec 2026, Jan/Feb/Mar/Jun/Sep/Dec 2027, Dec 2028) and each chip
(H100, B200, B300; a few A100, H200, RTX PRO 6000). The page turns the ladders into a forward
curve ("PIRP", Polymarket-implied rental price) and offers block quotes on request.

**Resolution (December 2026 H100 ladder):**
- arithmetic mean of the finalized daily settled values of the Ornn OCPI-H100 index dated in
  December 2026, rounded to the cent;
- a daily value is final once the next day's value is published; later revisions ignored;
- up to 7 days' wait for corrections of clearly erroneous data; fallback to another credible
  source, else 50-50.

**Underlying:** Ornn Compute Price Index (data.ornn.com), a daily GPU-hour rental index.
Ornn's site links an ICE Futures US spec sheet for Ornn compute futures; Polymarket's own markets imply no GPU compute futures has traded on a US exchange yet ("by Dec 31, 2026" at 7–8%, "by Mar 31, 2027" ~48%, "by Jun 30, 2027" ~70%). Public API (last 3 months, no auth):
- `GET https://data.ornn.com/api/public-index/gpu/{H100%20SXM|H200|B200|B300|A100%20SXM4}/index-history`
- `GET https://data.ornn.com/api/public-index/daily-index/all`

Older H100/B200 markets of a different design ("end of month", "hit by") have run since
May 2026 and resolved monthly.

## 2. The index (2026-08-26 → 11-24, 91 days)

| Chip | Last | Range | Daily SD | 20-day SD (random walk would be) | Monthly means Sep / Oct / Nov |
| --- | ---: | --- | ---: | --- | --- |
| H100 | 3.16 | 2.46–3.53 | 5.5% | 9.7% (24.4%) | 2.83 / 2.94 / 3.15 |
| H200 | 6.53 | 4.24–7.75 | 5.5% | 10.8% (24.6%) | 4.89 / 5.92 / 6.66 |
| B200 | 9.07 | 6.00–9.94 | 1.9% | 10.4% (8.3%) | 7.26 / 8.51 / 9.50 |
| B300 | 10.87 | 9.63–14.23 | 5.0% | — | 11.49 / 12.29 / 11.62 |
| A100 | 1.00 | 0.89–1.16 | 2.8% | — | 1.00 / 0.99 / 1.03 |

- **H100 and H200 are noisy around a slow level:** daily moves are large (5.5%) but mostly
  undo themselves; 20-day changes are 2.5x smaller than a random walk implies. A monthly
  average of ~31 such values is driven by the level, not by daily noise.
- **B200 trends** (variance ratio above 1): up 56% in three months.

## 3. Prices on 2026-11-25

H100 December 2026 (P(average > X), bid/ask): 2.80 → 0.75/0.76, 2.90 → 0.62/0.63,
3.00 → 0.52/0.53, 3.10 → 0.37/0.38, 3.20 → 0.31/0.32. Implied median ≈ $3.02, middle 50%
≈ $2.80–3.27, against a last value of 3.16, a November mean of 3.15 and a 14-day mean of
≈ 3.06. The curve slopes down: Jan 2027 2.98, Jun 2027 2.91, Dec 2027 2.67, Dec 2028 2.16.

A naive check (level = 14-day mean 3.06, lognormal SD ≈ 8% for the December average) gives
P(> 3.00) ≈ 0.60 and P(> 3.10) ≈ 0.44, a few points above the market. With three months of
history this is not evidence of mispricing; the market prices some decline (Blackwell ramp).

## 4. Liquidity rewards: the main reason to care

| | Value |
| --- | --- |
| Ornn reward markets | 446 |
| Their pool | **≈ $60,300/day** (≈ 30% of the ≈ $205k/day total on 2026-11-14) |
| Central strikes of front months | $960/day per market, v = 4.5¢, min size 200 |
| Wing strikes | $40/day per market |
| $1k two-sided at the best bid/ask, mid 0.10–0.90, median | $6.9/day (all), $16–24/day (H100 Dec/Jan, B200 Dec, B300 Jan) |

Front-month central strikes are tight (1¢) with $100k+ depth, so a $1k quote gets only
~3–6% of a $960 pool, still $25–55/day. These are one snapshot's shares against the current
book, with fills and adverse selection excluded (same caveats as `09`).

**Why this may suit a maker better than the long tail in `09`:**
- one public, daily-published underlying with a known formula, so fair value for every
  strike can be computed from the index history;
- the uncertainty of a monthly average shrinks predictably during the month;
- all strikes and months move together, so inventory across a ladder can be netted.

**Risks:**
- informed flow at each daily index publication (~04:00–05:00 UTC): stale quotes get picked
  off; a bot should pull or re-price quotes around it;
- one index provider decides everything (errors, methodology changes, 50-50 fallback);
- correlated inventory across strikes: one index move hits the whole ladder;
- rewards this large are likely a launch subsidy and may shrink.

## 4a. Can the index be forecast?

**How it is built** (data.ornn.com/methodology, read 2026-11-25): a volume-weighted,
winsorized mean of *executed* on-demand rental prices per GPU type over a rolling one-hour
window, from an undisclosed network of contributor providers; no smoothing across windows;
published hourly to $0.001. Reserved and long-term contracts are excluded (Ornn publishes them
separately as a forward curve). The winsorization level is not public. Hourly values and
longer history are paid tiers; the public API gives daily values for 3 months.

**Simple statistical forecasts don't beat the last value** (mean absolute error, 2026-09 → 11):

| Chip | Next day: last / 7-day mean | Next 7-day avg: last / 7-day mean | Next 30-day avg: last / 7-day mean / trend |
| --- | --- | --- | --- |
| H100 | 4.7% / 5.2% | 5.5% / 4.1% | 7.8% / 7.4% / 9.2% |
| H200 | 4.9% / 6.7% | 6.5% / 5.7% | 9.5% / 10.4% / 6.1% |
| B200 | 1.1% / 3.5% | 3.5% / 5.2% | 9.8% / 11.7% / 11.1% |
| B300 | 3.2% / 6.0% | 6.3% / 6.9% | 5.5% / 4.5% / 9.2% |

A month ahead, every simple method misses by 5–10%, roughly the width of the market's own
middle-50% band. With 3 months of public data there is no evidence of a forecasting edge.

**What can be analyzed reliably:**
- **In-month arithmetic.** Once a month starts, the realized days are locked into the
  average: with 20 of 31 days known, only the last 11 can move it. Fair value of each strike
  tightens mechanically, and markets that lag the daily prints can be checked against it.
- **Consistency across the ladder and the curve.** P(above X) must fall as X rises, and
  adjacent months must be coherent; violations are pure pricing errors.

**Information others have and we don't:**
- hourly index values (paid tier) show the day's move before the daily settle;
- Ornn's reserved-capacity forward curve (and, once they trade, ICE compute futures);
- contributor identities are secret, so the index can't be replicated from public provider
  price lists (Lambda, RunPod, Vast.ai, etc.), only approximated; whether such proxies lead the
  index is untested.

**Conclusion:** directional bets on the index have no demonstrated edge. The useful angle is
pricing, not prediction: computing fair value inside the month and quoting around it for
rewards, while avoiding the daily publication where better-informed traders act.

## 5. Next steps (if pursued)

1. Collect the Ornn index daily and the compute books every minute from now on (the public
   API keeps only 3 months).
2. Fair-value model for a monthly-average strike: level estimate plus level drift, with the
   realized part of the month locked in.
3. Add 10–20 compute strikes to the prediction-market MM paper test (`09`, section 6), with
   quotes pulled around the index publication.
