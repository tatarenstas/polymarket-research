# 02 — Realism probe: calibration atlas and wallet / informed-flow detection

**Status: exploratory probe, not a validated study.** The probe uses V1 cleaned layers
(`daily_aligned` + `daily_aligned_multi`) at revision `5aa1b9d5`, for 2024-01-01 →
2025-12-31, resolved markets only. That is 171.4M trades and 221,638 markets. The
scripts are in `research/probes/` (`realism_probe.py`, `realism_analysis.py`,
`realism_extra.py`), and the aggregates live in `data/probe/` (git-ignored, ~6 GB).

Conventions: `Y` = 1 if the `outcome_seq = 1` outcome won. A taker's per-share edge
to resolution is `D × (Y − p_event)`, and the maker gets the negative. ROI is
PnL / notional, marked to resolution, net of `fee_usdc` for takers.

## Data sanity

- `D` and `p_event` recomputed from `taker_direction`, `outcome_seq`, `price`:
  **0 mismatches** across 171M trades.
- Resolution labels inconsistent between the two legs: 921 of 1.63M market-days (0.06%).

## A. Calibration atlas

One observation per market (first day in the horizon with traded VWAP in 0.1–0.9 and ≥ $100):

| Horizon to close | Type | Markets | Mean price | Realised freq. | Gap | ±95% |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1–7 d | binary | 31,513 | 0.487 | 0.469 | −0.018 | 0.005 |
| 1–7 d | neg-risk | 17,887 | 0.314 | 0.301 | −0.013 | 0.006 |
| 7–30 d | binary | 15,133 | 0.456 | 0.433 | −0.023 | 0.007 |
| 7–30 d | neg-risk | 6,179 | 0.304 | 0.284 | −0.020 | 0.010 |
| 30 d+ | binary | 5,488 | 0.409 | 0.346 | **−0.063** | 0.011 |
| 30 d+ | neg-risk | 4,116 | 0.274 | 0.242 | −0.032 | 0.012 |

The 7 d+ gap by category: Sports −2.1, Politics −4.3, Crypto −4.4, Culture −5.6,
Finance −4.8, Sci-Tech −8.7 percentage points.

**Reading.** The reference ("Yes") side is systematically overpriced. The bias grows
with time to close and differs by category. This is a stable, measurable structure,
and exactly what a calibration atlas should map.

**Artefact to avoid.** The same-day (< 1 d) market-day table shows an apparent ±20 pp
S-curve. That is look-ahead: a daily VWAP on the resolution day mixes trades made
before and after the outcome became evident. The real atlas must use point-in-time
prices from the trade tape, never daily VWAP near resolution.

**Not yet shown.**
- The gap is measured at VWAP, not at an executable price (spread, depth).
- Capital is locked for weeks to months.
- Markets within one event are correlated, so the effective sample is smaller than
  the market count.
- No out-of-time test has been run yet, and the V2 era is untested.

## B. Wallet analytics

Discovery period: wallet-markets first entered 2024-01 → 2025-06. Test period:
2025-07 → 2025-12. Unit = (wallet, role, market) with ≥ $10 notional. Skill t-stat =
mean market ROI / s.e. over markets, for wallets with ≥ 20 markets.

- **Concentration.** The top 0.1% of taker wallets supply 42% of taker notional, the
  top 1% supply 69%, and the top 10% supply 90%.
- **Aggregate.** Takers lost money in both periods (−$10.5M, −$27.5M); makers gained
  (+$14.2M, +$26.6M).
- **Skill beyond chance.** 2,465 taker wallets have t > 3, against ~55 expected under
  a normal null. That is far beyond chance even allowing for fat tails.
- **Persistence out of sample (H2 2025).**

| Discovery group (takers) | Active in test | Pooled test ROI | Share of wallets positive |
| --- | ---: | ---: | ---: |
| t > 3 | 427 | **+3.06%** | **63.9%** |
| 0 < t ≤ 3 | 8,913 | +1.47% | 47.3% |
| t ≤ 0 | 13,046 | −0.74% | 38.3% |

  The effect holds for mid-price entries (0.15–0.85), not only for "sniping"
  near-certain outcomes.

### Insider-style single-trade signals (taker, directional, mid-price)

| Signal | n | Hit rate | Implied prob. | ROI |
| --- | ---: | ---: | ---: | ---: |
| Bet ≥ 10× wallet's own median | 104,542 | 0.412 | 0.448 | −2.5% |
| Bet 3–10× own median | 418,394 | 0.406 | 0.449 | −3.0% |
| Normal-size bet (< 3×) | 4,677,596 | 0.455 | 0.491 | −7.9% |
| Fresh wallet, first bet ≥ $10k | 3,339 | 0.390 (±0.017) | 0.443 | −2.0% |
| Fresh wallet, first bet $1k–10k | 24,123 | 0.410 | 0.453 | −7.9% |
| Fresh wallet, first bet ≥ $1k, < 1 day to close | 9,664 | 0.410 | 0.467 | −11.1% |

Hit rate counts every wallet once. ROI is weighted by notional, so a few large
winners can dominate it.

**Reading.** On average, "unusually large bet" and "new wallet with a big first bet"
carry **no** informed signal: hit rates sit below implied probability. Truly
informed trades, if present, are a tiny fraction hidden inside these classes. A rule
built on these features alone would produce mostly false alarms.

## Realism verdict

| Goal | Realism | Why |
| --- | --- | --- |
| Calibration atlas (research and product) | **High** | Large resolved sample, clean labels, stable bias structure by horizon and category |
| Calibration as a trading edge | **Medium–low, unproven** | Needs point-in-time executable prices, event clustering, out-of-time and V2 validation |
| Skilled / informed-wallet scoring (track record) | **High** | Strong excess of high-t wallets; persists out of sample |
| Copy-trading those wallets | **Unknown** | Edge measured at *their* fill price; the edge left after a follower's delay is not measured |
| Real-time "insider position / move" detection | **Low as a standalone rule** | No ground truth; generic anomaly classes are uninformative; base rate tiny |
| Informed-flow *candidate* alerts | **Medium** | Requires validated track record + abnormality vs own baseline + no preceding public news + validated lead-to-move |

## Next steps that decide the open questions

1. Build point-in-time price snapshots from the trade tape (price at t, outcome
   after). Redo calibration with event clustering and an out-of-time split, then
   replicate on V2.
2. Measure lead-to-move and follower decay for skilled wallets: the edge left when
   entering 1 min, 10 min and 1 h after their trade, at the then-current price.
3. Separate strategy types among skilled wallets (market makers, arbitrage between
   linked markets, resolution sniping, directional) before calling any of them
   "informed".
4. Add a timestamped public-news source to test "early versus reaction to news". Without
   it, informed flow cannot be told apart from fast reaction.
