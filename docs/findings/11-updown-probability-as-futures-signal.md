# 11 — Polymarket Up/Down probability as a Binance futures signal

Date: 2026-11-25. Status: tested, rejected. Not investment advice.

**Idea:** treat the Polymarket "BTC Up or Down" probability as correct; when it crosses a
threshold during a 5m / 15m / 1h window, open a BTCUSDT perp in that direction and hold it
to the window end.

**Script:** `research/pm_signal/updown_futures.py` (public Gamma, CLOB `prices-history`,
Binance 1-minute klines). **Sample:** 2,852 resolved windows, 2026-11-18 → 11-25 (7 days).
First signal per window; entry at the open of the next full minute; exit at the window end.

| Window | Threshold | Trades | PM probability | PM side won | Futures hit rate | Mean, bps | t | Net, taker 10 bps | Net, maker 4 bps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5m | 0.6 | 1,986 | 71.4% | 72.6% | 49.6% | +0.48 | 1.2 | −9.5 | −3.5 |
| 5m | 0.8 | 1,485 | 88.7% | 90.2% | 48.8% | +0.38 | 1.0 | −9.6 | −3.6 |
| 15m | 0.6 | 671 | 66.9% | 66.0% | 47.4% | −2.39 | −1.8 | −12.4 | −6.4 |
| 15m | 0.8 | 618 | 85.7% | 85.6% | 42.7% | −2.70 | −2.2 | −12.7 | −6.7 |
| 1h | 0.6 | 167 | 64.1% | 65.9% | 52.1% | −1.32 | −0.2 | −11.3 | −5.3 |
| 1h | 0.8 | 166 | 82.9% | 80.1% | 42.2% | −1.18 | −0.2 | −11.2 | −5.2 |

(0.7 and 0.9 thresholds are in the script output and look the same.)

**Findings:**
1. **The probabilities are well calibrated.** When Polymarket says 89%, the side wins 90%.
2. **They still do not predict the futures move.** After the signal the futures position is
   right only 42–52% of the time and earns ≈ 0 bps before fees (15m is slightly negative,
   t ≈ −2). After fees every variant loses 4–13 bps per trade.
3. **Why:** the window resolves on the Chainlink TWAP versus the start price. A high
   probability means BTC has *already* moved and part of the TWAP is *already* fixed; it
   answers "will the window close up", not "will the price rise from here". The remaining
   move from the signal to the window end is close to a coin flip. Polymarket also follows
   Binance with a lag (literature: ~347 ms, `docs/literature/2607.26245...`), so its
   probability carries no information that the Binance price does not already have.

**Verdict:** rejected. A calibrated probability for an outcome that is partly realized is not
a forecast of future returns.
