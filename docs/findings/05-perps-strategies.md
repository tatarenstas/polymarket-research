# 05 — Strategies on Polymarket Perps: fees, funding, rebates, rewards

Analysis summary, 2026-11-13. Sources: Polymarket Perps documentation (fees, funding, liquidity
rewards, referral, self-trade prevention, trading API), public APIs of Polymarket Perps,
Binance USDⓈ-M, Bybit, OKX and Hyperliquid, the paper test `research/perps_lp/run_paper.py`.
Related documents: `06-perps-funding-snipe.md`, `concepts/PERPS_LP_REWARDS_EXECUTION_PLAN.md`.
Not investment advice. All Polymarket program parameters may change.

## 1. Polymarket Perps mechanics (from the documentation)

**Fees by 30-day volume:**

| Volume ≥ | Taker | Maker |
| --- | ---: | ---: |
| $0 | 0.040% | 0.0125% |
| $1M | 0.037% | 0.010% |
| $5M | 0.035% | 0.008% |
| $25M | 0.030% | 0.005% |
| $100M | 0.027% | 0.002% |
| $500M | 0.025% | 0% |
| $1B | 0.020% | **−0.005%** (rebate) |

Some beta accounts have been temporarily moved to the top tier. Builder fee: up to 10 bps
on top.

**Funding:**
- The premium is sampled every 5 s and averaged over the hour; it is charged once an hour.
- Formula: `F_8h = scale·(mean_P + clamp(0.0001 − mean_P, ±0.0005))`,
  `FR_hour = clamp(F_8h/8, ±4%)`; scale = 1 for crypto, 0.5 for everything else.
- At zero premium the rate is **+0.00125%/h from longs to shorts** (~11% annualized). This
  is the structural reason why a short receives funding on average.

**Liquidity rewards:**
- Pool: $75,000 per day, split equally among active markets (90 → **~$833 per market**).
- Weights by distance from mid: ≤5 bps — 1.0; 5–10 — 0.25; 10–20 — 0.1. Counted up to $100k
  per level, per side, per market.
- Both sides are required: the snapshot is the harmonic mean of bid and ask.
- Threshold: ≥ 1% of the market's maker volume over 7 days.
- Formula: `raw = maker_score^0.35 · liquidity^0.65 · uptime`.

**Other:**
- Referral: 20% of referred users' fees, no discount for the referred user; you cannot refer yourself.
- STP blocks self-trades. Trades within one account group do not count toward
  rewards.

**Trading API:**
- post-only (`po`), GTC/IOC/FOK, `PATCH` to modify orders;
- auto-cancel (dead-man switch);
- up to 200 open orders per market;
- a "taker delay queue" for new orders: possibly a speed bump in favor of makers (not
  verified).

## 2. Live data (13.11.2026)

**BTC-USD:**
- spread 1 tick (~0.14 bps), depth ~$0.9M per side within 5 bps;
- open interest ~$12M, volume ~$13M per day;
- funding over 60 days: 7.9% annualized to shorts; 69% of hours at the base rate, 9.8% of hours
  negative.

**All 90 markets, funding over 16 days:**

| Category | Median, annualized |
| --- | ---: |
| Crypto | 6.2% |
| Stocks | 9.3% |
| Indices | 17.7% |

Individual markets: XMR ~100%, CRCL ~37%, SKHYNIX ~36%, ASML ~19%.

**Competition for rewards** (weighted liquidity within 20 bps): median $188k. Thin
markets — $4–40k (PRL, STRC, SOXL), giant ones — $1.5–3M (BTC, SP500, NAS100).

## 3. Strategy catalog

| # | Strategy | Income from | Estimate | Realism |
| --- | --- | --- | --- | --- |
| 1 | Spot + short perp (BTC/ETH) | funding | 5–8% annualized on capital at 2–3x; on stocks and indices 10–14% | Works: high |
| 2 | Cross-exchange funding arbitrage | rate difference | episodic | Borderline |
| 3 | Liquidity rewards with a hedge | pool of $833 per market per day | see §5 | Untested live |
| 4 | Maker rebates | payment to the maker | only at volume of $500M–1B per month | Rejected for small capital |
| 5 | Cashback and referrals | share of fees | lowers the fee of the hedge leg | Add-on |
| 6 | Volume farming | tiers, prizes | negative | Rejected |
| 7 | Entry across the hour boundary on a funding spike | a full hour of funding for ~40 s | see `06` | Borderline: mechanics not confirmed |

**Strategy 1 return depends on leverage:**
`return on capital = f · leverage / (leverage + 1)`, where f is funding on notional.
- The ceiling is funding itself, because the spot leg is paid in full.
- If you already hold BTC, the return on the extra margin = f · leverage, but the short neutralizes
  the price risk of your BTC.

**For trades under 30 seconds, only three things cover the fee:**
- the spread when scalping as a maker (on BTC the 0.14 bps spread is smaller than the 2.5 bps round-trip fee —
  does not work; on markets with a spread ≥ 4–5 bps — possible);
- liquidity rewards;
- entry across the hour boundary, only at a rate > 0.025%/h.

With market orders over 30 s the fee is practically impossible to cover: it needs a move of ~$57 on BTC.

## 4. Funding skew on XMR (13.11.2026)

**Rates:**

| | Polymarket XMR-USD | Other exchange |
| --- | ---: | ---: |
| Rate | 0.0769%/h (~674% annualized) | 0.01% per 8 h |
| Premium over index | +0.37% | — |
| Leverage, max | 5x | — |

Funding on Polymarket by period:

| Period | Mean rate, %/h | Annualized |
| --- | ---: | ---: |
| 24 h | 0.079 | ~690% |
| 72 h | 0.033 | ~285% |
| 16 days | 0.011 | ~100% |

**Setup:** short on Polymarket + long on another exchange. Net ≈ 0.077%/h ≈ 1.8% per day of
notional while the skew lasts.

**Calculation for $9k capital** (notional per leg = capital × leverage / 2; $/day):

| Leverage | Notional | Rate as 24 h | as 72 h | as 16 days |
| --- | ---: | ---: | ---: | ---: |
| 2x | $9 000 | 167 | 68 | 22 |
| 3x | $13 500 | 251 | 102 | 33 |
| 5x | $22 500 | 418 | 169 | 55 |

- **Risks:** the skew fades; the premium may grow further; liquidation of one leg (fee 0.5%);
  different indices on the exchanges.
- **Recommendation:** leverage ≤ 3x, reserve ~$1k. Exit when the rate stays
  < 0.005%/h for several hours in a row.
- **As of 13.11 11:06 UTC** the XMR rate had already flipped sign (−0.024%/h), so the skew
  is temporary.

## 5. Paper test of liquidity rewards (`run_paper.py`, 12.2 h of 24)

**Parameters:** $5k per side, offset 3 bps, requote every 2 s. The "hedged" variant is
an instant hedge at mid for 5 bps. $/day is an extrapolation.

| Market | Fills | Volume share | Rewards (linear / formula) | Trading PnL | Net (lin. / form.) | Price move after fill, bps: 10 s / 60 s / 300 s |
| --- | ---: | ---: | --- | ---: | --- | --- |
| SOXL | 29 | 43% | 79 / 156 | −6 | +73 / +150 | +3.1 / −6.0 / +0.8 |
| PONS | 58 | 47% | 103 / 182 | −38 | +65 / +144 | +1.2 / +2.1 / −1.5 |
| ASML | 17 | 38% | 69 / 145 | −31 | +39 / +114 | −1.8 / −3.0 / −2.2 |
| ZEC | 12 | 8% | 35 / 85 | −6 | +29 / +79 | −8.9 / −7.2 / +0.9 |
| STRC | 0 | 0% | 50 / 0 (1% threshold not met) | 0 | 0 | — |
| BTC | 81 | 2.6% | 5 / 21 | −110 | −105 / −90 | −1.9 / +1.7 / +1.3 |

**What the unhedged variant showed:** the result is driven by the price move of the position, ±$300–500 per day
(for example, PONS +$496, SOXL −$364, BTC −$371). Because of the position limit, the share of time
quoting on both sides drops to 40–60%. So the hedge is mandatory.

**Adjustment for a real hedge on Binance** (taker fee ~5 bps + half the Binance spread +
price move during the ~10 s before the hedge), $/day:

| Market | Net (lin. / form.) | Why |
| --- | --- | --- |
| **SOXL** | **+60 / +135** | cheap hedge (Binance $5B/day, spread 1.5 bps) |
| **ASML** | **+20 / +100** | Binance is thin (spread 3.1 bps) |
| ZEC | −80 / −30 | price manages to move against you before the hedge |
| PONS | −70 / +10 | expensive hedge (Binance spread 6.4 bps) |
| BTC | ≈ −100 | competition |

**Estimate for $9k** (SOXL + ASML at $5k per side, leverage 3x):

| Scenario | $/day | $/month |
| --- | ---: | ---: |
| Optimistic | ~230 | ~7 000 |
| **Realistic** | **~50–100** | **~1 500–3 000** |
| Pessimistic | ~0–20 | ~0–600 |

**Limitations:**
- the split of the pool among makers is not visible from the public book; competitors were counted as one
  maker;
- competition reacts to profitable markets;
- the test is short (12–29 fills per market);
- the "touch" and "through" variants gave identical results, so the fill model is imprecise.

## 6. Hedge exchanges and price parity (13.11.2026)

| Asset | Hedge | 24 h volume | Spread | Parity with Polymarket |
| --- | --- | ---: | ---: | --- |
| ZEC | Binance ZECUSDT (perp) | $2.1B | 0.1 bps | 1.0002 (OK) |
| SOXL | Binance SOXLUSDT (TRADIFI_PERPETUAL) | $5.0B | 1.5 bps | ≈1.000 (OK) |
| XMR | Binance XMRUSDT | $119M | 0.2 bps | 0.9997 (OK) |
| ASML | Binance ASMLUSDT (TRADIFI_PERPETUAL) | $3.3M | 3.1 bps | ≈1.000 (OK) |
| PONS | Binance PONSUSDT | $37M | 6.4 bps | not verified |
| ANT | Binance ANTHROPICUSDT | — | — | **1768 vs 1338 — different contract (Rejected)** |

Alternatives: Bybit, OKX, Hyperliquid (including HIP-3 `xyz:SOXL`, `xyz:ASML`, `xyz:STRC`).

## 7. Polymarket prediction markets (not Perps): taker and maker rebates

**Taker Rebates:**
- `wV = size × (1 − price) × category weight`; tiers from Bronze ($2k wV, 3%, $10 bonus) to
  Obsidian ($10M+, 50%, $25k).
- Taker fee `fee = C·feeRate·p(1−p)`, so **fee / wV = feeRate / weight** —
  independent of price:

| Category | Fee per $ of wV |
| --- | ---: |
| Economics, Culture, Weather, Other | 2.94% |
| Crypto | 3.04% |
| Politics, Finance, Tech, Mentions | 3.08% |
| Sports | 5.0% |

- Bonuses are only 0.1–0.5% of wV, so **climbing tiers for the bonuses loses money**:
  Bronze ≈ −$49, Silver ≈ −$540, Gold ≈ −$5.6k.

**Maker Rebates:**
- makers pay no fees;
- they receive 15–25% of taker fees in proportion to their fee_equivalent, i.e.
  ~0.5–0.7% of notional at p ≈ 0.5.

## 8. Status and next steps

- **24 h paper test** (`data/lp_paper/20261113_014811/`) is running.
- **Stage 1** (`research/perps_lp/run_stage1.py`, model `DelayedHedgeMaker`): stopped
  14.11 at 12:50 UTC after 24.8 h of 72. Summary in section 9.
- **Entry across the hour boundary:** waiting for the user's micro-test ($20 across the hour boundary) to
  confirm whether a full hour of funding is charged.
- **Next per the plan:** shadow mode → micro-launch at $200–500 per side → scaling.

## 9. Stage 1: summary (real hedge on Binance, 24.8 h of 72)

**Run:** `data/lp_stage1/20261113_140445/`, from 13.11 12:05 UTC (Friday) to 14.11 12:51 UTC
(Saturday). Stopped manually. Report: `research/perps_lp/report_stage1.py`.

**Parameters:**
- $5k per side, offset 3 bps, position limit $10k;
- hedge is a taker on Binance at live bid/ask, fee 5 bps, delay 1–3 s;
- funding on both legs;
- reward pool is an assumption: $75k per day split equally across all markets, $833 per market.

**Summary, base variant `d1_t0` (1 s delay, no netting, skew 3 bps), $/day:**

| Market | Fills | Reward share | Uptime | Rewards (lin. / form.) | Trading PnL | **Net (lin. / form.)** | Price move after fill 10 / 60 / 300 s, bps |
| --- | ---: | ---: | ---: | --- | ---: | --- | --- |
| **SOXL** | 54 | 37% | 1.00 | 81 / 158 | −50 | **+30 / +108** | −2.6 / −4.4 / −3.1 |
| ASML | 29 | 20% | 0.99 | 43 / 107 | −56 | −13 / +50 | −2.2 / −3.7 / −2.5 |
| XMR | 135 | 26% | 1.00 | 13 / 53 | −74 | −61 / −21 | −1.6 / −1.2 / −6.0 |
| ZEC | 27 | 27% | 0.44 | 11 / 36 | −39 | −28 / −2 | −6.1 / −11.2 / −7.2 |

**Key point: the US session produces the loss, while the night and weekend produce the rewards.**

Breakdown of SOXL and ASML by time (`d1_t0`, cumulative, $):

| Market | US session, Fri, 6.5 h | Rest, Fri + Sat, 18.3 h |
| --- | --- | --- |
| SOXL | 37 fills; PnL −37; rewards +17 / +37 | 17 fills; PnL −15; rewards +66 / +126 |
| ASML | 15 fills; PnL −27; rewards +4 / +29 | 14 fills; PnL −31 (almost all on Fri 21–24 UTC); rewards +41 / +81 |

- From Saturday 00:00 UTC (12.8 h) SOXL PnL changed by only −$4, ASML by +$0.5. Rewards over
  that time: SOXL +$46 / +$88, ASML +$27 / +$64. That is **≈ +80 / +160 $/day on SOXL and
  ≈ +50 / +120 on ASML on the weekend**.
- During the US session SOXL lost ~$137 per day in trading PnL, while rewards gave only 63 / 137.
  Result from −74 to 0.
- The price move after fills is negative on all markets (−2…−11 bps over 60 s). Our fills come
  mostly from informed takers.

**Variant comparison, trading PnL, $/day:**
- **Hedge delay:**
  - 3 s instead of 1 s costs ~$19 per day on SOXL;
  - on ASML and ZEC the difference ≈ 0;
  - on XMR 3 s is even better (−64 vs −74).
- **Hedge netting up to $1k** cuts the number of hedges threefold, but is worse on SOXL:
  −99 vs −50.
- **No skew** is about the same as with skew. The difference is within noise.

**Weekly estimate for SOXL.** In the run 65% of the time is weekend, whereas in a normal week it is
29%. So the run total is overstated. Recalculated for a week: 5 US sessions × 6.5 h, the rest
of the time at the night-and-weekend pace. This gives **≈ +40 $/day under the linear model and
≈ +120 under the formula**.

**This estimate is very rough:**
- it rests on **one** US session;
- the weekday night pace is taken from Saturday.

ASML under the same recalculation gives ≈ −13 / +60.

**Conclusions:**
1. **XMR and ZEC are rejected.** Loss under both reward models. On ZEC, in addition, the position limit
   turned quoting off 56% of the time.
2. **SOXL is the only candidate, positive under both models.** ASML only under the formula.
3. **The main improvement is to not quote or to widen the offset during the US session** (14:30–21:00 UTC,
   plus the first hours after the close). Check on this data: had SOXL not quoted during
   the US session, trading PnL would have been ≈ −15 instead of −52 over 24.8 h, and rewards under the linear
   model ≈ 66 instead of 83. But the impact on pool share (uptime, Q during the session) was not modeled.
4. **The twofold gap between reward models (lin. vs form.) and the pool assumption ($833 per
   market)** are the main unknowns. Only actual micro-live payouts will resolve them.
5. **Statistics are weak:** 54 / 29 fills, one US session, one weekend. The conclusions are a
   direction, not proof.

**What next, if continuing:**
- 3–5 weekdays on SOXL (and ASML) with a "pause during the US session" variant;
- then micro-live at $200–500 per side to see actual rewards.

