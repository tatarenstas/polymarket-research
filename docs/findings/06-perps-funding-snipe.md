# 06 — Perps funding snipe: hold ~40 s across the hourly settlement

**Script:** `research/perps_lp/funding_snipe_backtest.py`. Data comes from the public
Polymarket Perps REST API: hourly funding for all 90 markets over 30 days, plus 1-second
mark prices around every candidate hour. Cache: `data/perps/`.

**Status:** backtest plus one live check (see caveat 1). A 40-minute hold was charged the
full hour, so funding is a snapshot at settlement. A hold of seconds is not yet tested.
The strategy assumes that
a position open at the hourly settlement receives the *full* hourly rate, however short
the holding time. If Polymarket time-weights funding instead, each trade loses about the
maker fees (−2.5 bps).

## Rule

- **Side:** short when the hour's rate is positive (longs pay shorts), long when it is
  negative.
- **Timing:** enter at T−20 s and exit at T+20 s, where T is the settlement time.
- **Execution assumed:** post-only on both legs at the mark price, with maker fees of
  0.0125% per leg. A taker variant pays 0.04% per leg plus 2 bps of half-spread.
- **Which rate decides the trade:**
  - *Oracle:* the hour's final rate. It is the mean of 5-second premium samples over the
    hour, so it is almost fully determined seconds before T.
  - *Lagged:* the previous hour's rate, strictly known in advance.

## Results (30 days, 42 markets with signals)

| Variant | Trades | Funding, bps | Price move, mean / median / SD | Net (maker), mean / median | Win rate | Net (taker) |
| --- | ---: | ---: | --- | --- | ---: | ---: |
| Oracle, \|rate\| > 0.025%/h, all | 705 | +5.25 | +3.1 / 0.0 / 26 | **+5.8 / +1.5** | 65% | −3.7 |
| Oracle, excluding UNITREE | 592 | +4.50 | +1.1 / 0.0 / 17 | **+3.1 / +1.3** | 63% | −6.4 |
| **Oracle, \|rate\| > 0.05%/h** | 237 | +8.96 | +1.3 / 0.0 / 24 | **+7.7 / +5.6** | **76%** | −1.8 |
| Lagged, excluding UNITREE | 590 | +2.50 | −0.4 / −0.5 / 14 | −0.4 / −0.7 | 46% | −9.9 |
| Lagged, \|rate\| > 0.05%/h | 146 | +9.33 | −1.2 / −0.6 / 19 | **+5.6 / +4.7** | 75% | −3.9 |

**What the table shows:**
- **Price around settlement is noise with zero median.** There is no visible crowding
  against the funding side. Its SD (14–27 bps per trade) is several times the edge, so
  the edge only shows over many trades.
- **Taker execution always loses.** Maker execution is required.
- **The edge is concentrated in hours with high rates** (> 0.05%/h): about 8 trades per
  day across all markets.
- **The lagged rule fails when the rate flips sign** (86 trades paid funding, −4.2 bps
  each). In practice, decide on the live estimate in the last seconds, not on the
  previous hour.
- **Rough money:** oracle with |rate| > 0.05%/h at $5–10k per trade gives about $30–60
  per day before the caveats below. Daily P&L varies; some days are negative.

## Caveats, in order of importance

1. **Mechanism, partly verified (critical):** full-hour credit for a 40-second position.
   - *Live test 2026-11-13, NVDA-USD, long 0.2809, mark $168.23.* Opened 01:20:30 and
     closed 02:00:30 Kyiv time, so it held about 40 of the 60 minutes before the 00:00 UTC
     settlement. The account showed one payment of −$0.0005 at rate 0.0011%. A full hour
     comes to 0.2809 × 168.23 × 0.001096% = $0.00052, which rounds to $0.0005. Time-weighting
     40 minutes would give $0.00034, which rounds to $0.0003.
   - *Conclusion:* the payment is a snapshot of the position at T, not time-weighted.
   - *Second check (user-reported):* a position entered about 10 min before T also
     received the full hourly payment.
   - *Third check (2026-11-14, BTC-USD short 0.00877, entry $68,389):*
     - The position was held from 00:55 to 01:01 Kyiv time, across the 23:00 UTC
       settlement.
     - It received **+$0.0075**. The full hour at 0.00125% is 0.00877 × ~$68.1k × 0.0000125
       = $0.0075; time-weighting 5 minutes would give $0.0006.
     - Conclusion: a short position receives the full hour too.
   - *Still to check:* a minimum holding time of seconds. Repeat it
     with a short position entered about 30 s before T on a market with a positive rate.
2. **Fill risk:** post-only orders at exactly the right seconds may not fill, and a
   missed exit means holding longer.
3. **Capacity:** many signal markets are thin (UNITREE, NCLD and PRL have open interest of
   about $10–90k), so $10k positions would move them. XMR, ANT and SKHYNIX are larger.
4. **Prices:** the mark is not an executable price. The oracle rule needs the live
   funding estimate shortly before T, which the ticker exposes.
5. **Concentration:** 30 days only. UNITREE dominates the unfiltered result, so the
   table shows a version without it.

## Live scanner

`research/perps_lp/funding_scanner.py` (logic in `src/pmresearch/funding_scan.py`) is
read-only and places no orders. Every 15 s (every 3 s in the last 2 min) it reads the ticker
estimate of the current hour's rate for all markets. It prints:
- the receiving side;
- net bps after a maker or taker round trip;
- spread and depth within 10 bps.

It fires a SIGNAL when |rate| ≥ 0.05%/h within 120 s of settlement. Optional flag: `--notify`
(macOS notification).

It logs `signal` and `settled` events to `data/funding_scanner/`. A `settled` event
compares the last estimate before T with the paid rate.
