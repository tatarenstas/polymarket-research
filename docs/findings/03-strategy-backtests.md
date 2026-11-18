# 03 — Strategy backtests H1–H5 (V1, 2024–2025)

Engine: `src/pmresearch/backtest/` (unit-tested execution model). Scripts:
`research/backtest/`. Raw outputs: `data/*.log` (git-ignored). Tape: V1 cleaned layers
at revision `5aa1b9d5`, resolved markets, 2024-01 → 2025-12: 171M trades,
221,071 markets with consistent labels.

**Protocol.**
- Signals use only information available at signal time: the last traded price and
  the scheduled close date. Checking 221k markets: 9% stop trading ≥ 7 days before
  `close_at` and 4% trade more than a day after it, so `close_at` is a pre-announced
  end date, not the actual resolution time.
- Entry is the next *real* taker fill on our side, 60 s or more after the signal. The
  entry fill's own fee is charged.
- **Train** = entries before 2025-07-01; **test** = H2 2025.
- t-statistics are clustered by event (a neg-risk group, or a single market).
- 168 grid cells were tested in the H1–H3 grid, so a train t > 3 is expected by
  chance in about 0.2 cells.

## Verdicts

| # | Hypothesis | Result | Verdict |
| --- | --- | --- | --- |
| H1 | Long-horizon mid-price "Yes" overpriced → buy No | Train +18–21% per trade in 0.5–0.6 bands; **test −9% to −1%** | **Rejected** (overfit) |
| H2 | Longshots overpriced → buy No when Yes trades at 5–30¢, ≥ 30 d to close | Taker, one entry per market: test **88% win, +1.7% per trade, cluster t 2.5**, ~48-day hold; median fill only **$4–5** | **Weakly confirmed; tiny capacity as a taker** |
| H2-maker | Same edge, earned by *resting* orders that sell the longshot | Test **91% win, +7.9% capital-weighted**, on $1.3B of fills in 6 months; but the event-level mean is **−0.2% (t −0.3)** | **Promising; concentrated in large events; fill probability unknown** |
| H3 | Buy near-certain favourites (0.95–0.99) near close | −3% to +3% per trade, no consistent sign | **Rejected** |
| H4 | Fade or follow sharp 60-min moves (≥ 5¢) | Both lose 3–12% at 1–24 h exits; train and test agree | **Rejected**: round-trip spread (~3–5%) exceeds any reversal |
| H5 | Copy wallets with a proven train record | Their own fills in test: **+6.4% (t 3.9)**. Copying at **+60 s: −3.2%**; +10 min: −6.6%; +1 h: −22% | **Rejected as copy-trading.** Skill is real but its value is gone within a minute |

### Mirror image that confirms the longshot bias

Buying the reference at 1–20¢ loses **10–60% per trade** on every horizon, in both
periods. The bias is real. The question is only who captures it, and at what cost.

## What this means

1. **Taker strategies on Polymarket must beat a ~3–5% round trip.** H4 shows that
   short-term taking is a losing game unless information arrives faster than the book
   reprices.
2. **The informed edge is fast.** Skilled wallets keep earning out of sample, but
   their edge decays within 60 seconds. A wallet-alert *product* is viable. Following
   alerts as a trading strategy is not.
3. **The persistent inefficiency is the longshot bias, and makers capture it best.**
   A maker who rests orders to sell overpriced longshots:
   - collects the bias and the spread instead of paying it;
   - is paid liquidity rewards on top (not included here);
   - has capacity measured in hundreds of $M per month market-wide, not $4 fills.

   The remaining unknowns:
   - **fill probability and queue position**, which need live order-book data;
   - **event concentration**: most profit comes from a few large events, and the
     average event is break-even;
   - **V2-era fees and behaviour**, which must be tested on 2026 data.

## Next steps

1. **V2 holdout (2026-04 → 2026-11)** for H2 taker and maker, including the V2 fee
   schedule.
2. **Live order-book collector**, so that maker fill probability, queue position and
   spread can be measured for longshot markets.
3. **Maker strategy simulator:** quote longshot No bids or Yes asks, apply
   per-event exposure limits, account for capital lock-up and rewards, and evaluate
   on live paper fills.
4. **Product track (independent):** a skilled-wallet leaderboard and real-time alerts,
   framed as information, not a copy-trading signal.

Caveats:
- The one-entry-per-market H2 variant was defined after seeing the daily-entry
  results, so its test numbers carry mild selection.
- No result here includes liquidity rewards, or gas and relayer costs.
- Nothing here is investment advice.
