# 08 — Strategy map: what works, what doesn't, what is untested

Summary as of 2026-11-14. Compiled from `03`–`07`, `concepts/` and `docs/literature/README.md`,
plus results of tests that were still running. Numbers are backtests or paper tests; no strategy
has been tested with real money yet. Not investment advice.

**How to read the verdicts:**
- Works: mechanism confirmed, expected return positive;
- Borderline: possible profit, but there is an unknown that decides everything;
- Rejected: rejected by the data;
- Untested: not tested.

## 1. Polymarket prediction markets

| Strategy | What the data showed | Verdict |
| --- | --- | --- |
| H2: buy No against longshots (taker) | **The bias is real:** buying Yes at 1–20¢ loses 12–37%. But selling the longshot at realistic prices gives only +0.65% (V2) with t = 1.3, and the median trade is $1.5–5 | Rejected: effect ≈ spread, trade size negligible |
| H2-maker: sell longshots with limit orders | Orders fill when an informed participant buys. Mean across events −0.7…−2.2% | Rejected |
| H1 (mid prices), H3 (favorites near close), H4 (sharp moves) | Train and test contradict each other or are both negative. Round-trip spread of 3–5% exceeds any effect | Rejected |
| H5: copy strong wallets | Their trades return +6.4% (t 3.9), but a copy after 60 s returns −3.2% | Rejected as trading, works as a product |
| NegRisk arbitrage (Σ prices ≠ 1) | Per the literature: $0.29M of real arbitrage over the whole period; profit per conversion fell from $1 to $0.08 | Rejected for a small player (needs speed) |
| Farming taker-rebate tiers | Fee ≈ 3% of wV, while bonuses are only 0.1–0.5% | Rejected |
| **Market making with liquidity rewards on prediction markets** | Per the literature, profit goes to makers: maker share is the strongest predictor of PnL (+9 pp per SD); the top 1% of makers account for 84% of maker volume. We only tested selling longshots, not general MM | Untested: **the main gap**; a 72 h paper test started on 18.11 (`09`, section 6) |
| Cross-venue sports hedge (Polymarket vs betting exchanges) | Concept in `concepts/CROSS_VENUE_SPORTS_HEDGING.md`; no data collected | Untested |
| 5/15-min crypto markets vs Binance | Polymarket prices follow Binance with a ~347 ms lag; a 43-feature model does not beat the market price | Rejected without low-latency infrastructure |

## 2. Polymarket Perps

| Strategy | What the data showed | Return (estimate) | Verdict |
| --- | --- | --- | --- |
| **Spot + short perp (cash-and-carry)** | Base rate +0.00125%/h from longs to shorts. BTC: 7.9% annualized to shorts over 60 days, 9.8% of hours negative | ~5–6% annualized on capital at 3x (BTC); higher on indices and equities, but with 24/7 divergence risk | Works: reliable but modest |
| **Funding snipe (entry seconds before :00)** | The **full hour is accrued based on the position at :00** — verified with three of your trades (40 min, 10 min, 6 min). Backtest: at \|rate\| > 0.05%/h ~8 trades per day, +7.7 bps on average, 76% profitable | ~$30/day at $5k per trade; limited by the depth of small markets | Borderline; mechanics confirmed; untested: holds of seconds, limit-order execution and rate-estimate accuracy |
| **Cross-venue funding arbitrage on spikes** (short PM + long Binance) | XMR 13.11: 0.077%/h vs 0.01%/8 h on another venue; the spike faded in ~2 days | $68–169/day on $9k while the spike lasts | Borderline: episodic; needs a scanner that compares venue rates |
| Liquidity rewards with a Binance hedge | 24 h, perfect hedge: SOXL +42 / +119, PONS +31 / +109, ASML +6 / +69 $/day. **Stage 1, real hedge, 24.8 h (Fri + Sat):** SOXL +30 / +108, ASML −13 / +50, XMR −61 / −21, ZEC −28 / −2. The loss comes from the US session, while the weekend is almost pure rewards | SOXL positive in both models; weekly estimate ≈ +40 / +120 (rough, one US session) | Borderline; only a micro-live test (actual rewards) will decide |
| Zero fee on every trade (BTC, hedge) | PM vs Binance price difference: SD 0.46 bps; 0% of trades cover fees | — | Rejected: proven impossible |
| Scalping up to 30 s | Round-trip fee with limit orders 2.5 bps vs BTC spread 0.14 bps | — | Rejected on BTC |
| Maker rebates, volume farming | Rebate only from $1B of volume over 30 days | — | Rejected |

## 3. Information products (fallback path)

| Product | Basis | Feasibility |
| --- | --- | --- |
| Calibration atlas (longshot bias by horizon and category) | Large sample, stable structure | high |
| Strong-wallet ranking and alerts | Skill persists out of sample (t 3.9) | high as information |
| Perps funding / spike scanner | Already written (`research/perps_lp/funding_scanner.py`) | high |
| Best-odds monitor (sports) | Concept ready | medium |

## 4. Key points

1. **We have not found a "money machine" yet.** Most ideas were rejected by the data: all taker
   strategies on prediction markets and zero fees on perps.
2. **What remains shares a common source of return:** payments that Polymarket or the crowd
   shifts to the patient side. That is funding to shorts, rewards to makers and the overpayment for
   longshots. The one who earns is the one who **supplies liquidity or holds the unpopular side**, not
   the one who guesses direction.
3. **Priorities by "probability of success / effort":**
   1. **Funding snipe + spike arbitrage.** Mechanics confirmed, the tool exists (scanner).
      Next: collect 3–5 days of scanner data (signal count, estimate accuracy), one
      test with a ~30 s hold, then 5–10 manual trades at $100–500.
   2. **Cash-and-carry** as a base layer for idle capital: low risk, ~5–6% annualized.
   3. **Liquidity rewards on Perps.** SOXL only, and only after a micro-live test that
      shows actual rewards.
   4. **Investigate MM on prediction markets with rewards.** This is the largest untested
      opportunity: the literature says profits there concentrate among makers.
4. **Products (atlas, wallets, scanner)** are feasible regardless of trading, but earning
   from them requires traffic.
