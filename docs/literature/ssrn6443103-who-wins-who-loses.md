# Who Wins and Who Loses in Prediction Markets? Evidence from Polymarket

- **SSRN:** [6443103](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6443103). SSRN blocked
  bots, so its posting and revision dates were not seen.
- **Version read:** draft dated **August 28, 2026**, hosted by the
  [OSC](https://www.osc.ca/sites/default/files/2026-10/research-grant-competition-2026-who-wins-and-who-loses-in-prediction-markets.pdf)
  (Ontario Securities Commission research grant). JEL G12, G14, G15, D47, D82.
  - 158-page PDF: main text with references runs to p. 41; tables to p. 56; then a roughly
    100-page Internet Appendix (A–L).
- **Authors:** Pat Akey (ESSEC, CEPR, ECGI), Vincent Grégoire (HEC Montréal), Nicolas Harvie
  and Charles Martineau (University of Toronto).
- **Data:** HF [`vgregoire/polymarket-users`](https://huggingface.co/datasets/vgregoire/polymarket-users),
  CC-BY-4.0, 3.12B rows, 119 GB. It holds trades, OHLCV bars, daily PnL panels in five
  variants, and 87 user features. No code repository is linked.
- **Read:** the full text of the OSC PDF, including the Internet Appendix. The A–L appendix
  tables were read selectively (G, H, J transition variants by heading and intro). Also read:
  the HF dataset card.

## Question

Who earns and who loses on Polymarket? How concentrated are profits, and what predicts them:
per-trade accuracy, liquidity provision, activity or specialisation? Is performance
persistent, and do the largest winners look like insiders?

## Data

**Sample.** 2022-11-11 → 2026-03-29. The sample stops before the all-market fees that began on
2026-03-30.
- 2,480,104 wallets ("users"), 588.3M reconciled trades, 614,883 markets with trades
  (729,133 in metadata), 255,427 events.
- **Volume $67.1B** under a "matched-notional" convention: one share = $1. This is share
  volume, not USDC notional.

**Sources.**
- Gamma API: metadata and tags.
- Goldsky Polymarket subgraph: `OrderFilled` events with tx hash, maker/taker, asset ids,
  amounts and fee.
- CLOB "simplified markets": the winner flag.
- Data API: used for PnL validation only.
- The Data API's per-market trade endpoint is capped, so it is incomplete.

**Reconciliation (App. A.1).**
- The exchange contract appears in the maker/taker fields. A matched trade emits one event
  per maker order plus a "taker-order" event (maker = taker user, taker = exchange).
- The real taker is recovered from that event. The taker-order event is then dropped and the
  taker field rewritten.
- Direct fills against an "off-exchange operator" are kept as is.
- A taker order hitting N makers gives N rows. A final check confirms no exchange address
  remains.

**Winner flag (A.2).**
- Primary source: CLOB simplified-markets flag, keeping only cases with exactly one winner.
- Fallback: `outcomePrices` when `umaResolutionStatus` is "resolved" or "settled", rounded
  to 2 decimals, with exactly one outcome equal to 1.
- The integer `outcome` field is **unreliable** and not used.

**Price normalisation.**
- Yes/No trades are mapped to Yes, using 1 − p for No trades. Other binaries map to outcome
  index 1.
- Only 39 of 729,133 markets have more than two outcomes. They are kept in PnL but dropped
  from calibration.

**PnL (A.3).**
- Each trade becomes token and USDC deltas for maker and taker. Cash starts at 0, and
  deposits and withdrawals are ignored.
- Holdings are aggregated daily and forward-filled.
- Resolution is a synthetic settlement the day after close, at $1 or $0. When the resolution
  price is missing, the last trade price is used.
- Open positions are marked at the last trade on or before the day, via a backward join.
- PnL = Σ position × price + cash.
- **Validation:** 1,000 stratified users (≥10 trades, last trade before the cutoff) showed a
  "perfect match" with the Polymarket Data API.
- **Not captured:** direct wallet-to-wallet token or USDC transfers, and gas.
- *Not discussed:* split, merge and NegRisk-convert events. See the critique.

**Categories (A.4).** Seven categories, assigned by an event-tag map, then the legacy category
field, then title rules, then manual overrides (249 events). 630 orphan markets are classified
from question text. 24 markets have trades but no metadata.

**Fees.** Most markets had no fees in the sample. Exceptions:
- crypto 1h/4h/daily/weekly, new markets from 2026-03-06;
- NCAA basketball and Serie A, from 2026-02-18;
- App. F cites a 1% taker fee on daily crypto Up/Down and NCAA.

About 15% of markets carry a fee.

**Category profile (Table 2).**

| Category | Markets | Share of volume | Share of trades | Users |
| --- | ---: | ---: | ---: | ---: |
| Sports | 321,231 | 37.9% | 16.2% | 1.57M |
| Politics | 29,926 | 31.5% | 9.4% | 1.57M |
| Crypto | 206,491 | 19.0% | 67.1% | 1.37M |
| Culture, Finance, Tech, Weather (combined) | — | <12% | — | — |

**User distribution (Table 1).**

| Statistic | Median | Mean | Other |
| --- | ---: | ---: | --- |
| Trades | 28 | 474 | — |
| Markets | 10 | 54 | — |
| Volume | $2,343 | $54,143 | p95 $97,793 |
| Share at extreme prices (<10¢ or >90¢) | 58.3% | 54.9% | — |
| Maker volume share | 0% | 17.9% | p75 39.5% |
| PnL | −$2 | $0 | p95 $251; range −$10.0M to +$22.0M |

## Methods

- **Concentration:** cumulative shares of gains among winners and of losses among losers,
  over the full sample and monthly.
- **Calibration:** realised Yes frequency by 10¢ price bin at 30, 14, 7 and 1 days before
  close, with 1,000-draw bootstrap bands. Also a lifetime-density figure and per-category
  calibration (App. B).
- **Value-weighted excess hit rate:** EHR_i = Σ q(o − p)/Σ q, with buy-side normalisation
  (a sale at p becomes a buy of the complement at 1 − p). Plotted across 200 PnL half-percentile
  bins.
- **Finite mixture model (App. C, adapting Crane–Crotty 2020):**
  - The input is α̂_i, the *equal-weighted* mean of (y − p), with s_i = √(mean p(1−p)/n_i).
    Users need ≥20 resolved trades.
  - Two normal components, N(µ_j, σ_j² + s_i²), unconstrained.
  - Fitted by ML from hundreds of starting points, with Sclove BIC, a 100-draw bootstrap, and a
    Self–Liang boundary LR test.
  - Fraction skilled = 1 − Σπ_jΦ(−µ_j/σ_j).
- **Probit of 1{PnL > 0}:** marginal effects at the mean, robust SEs.
  - Regressors: share at extreme prices, maker volume share, log trades, log volume, category
    HHI, counterparty HHI, and dummies for any trading in each category.
  - Samples: all users, >100 trades, >1,000 trades.
- **Group comparisons** (top 0.1%, next 0.9%, next 4%, bottom 95%): Welch t-tests and
  Mann-Whitney.
- **Performance analogues:** PnL-to-volatility √12·mean/sd of monthly ∆PnL (≥3 months, sd > $1)
  and its downside counterpart.
- **Persistence:**
  - 11-bucket monthly-∆PnL transition matrices at 1, 3 and 6 months, conditional on trading,
    with a "No Trade" column and exact binomial tests for P(>0) = 0.5.
  - Sharpe- and Sortino-analogue buckets from daily ∆PnL within the month (≥10 active days,
    √365).
- **Persistence regressions (Table 8):**
  - Probit of dropout (no trade at t+3), run per bucket.
  - OLS of growth in log committed capital (average end-of-day |position| × price).
  - Year-month FE, category dummies, SEs clustered by user.
- **Spread decomposition:** each taker fill is improved by the minimum half-spread (0.5¢, or
  0.05¢ on the fine-tick grid below 4¢ / above 96¢), with the offsetting change for the maker.
  This gives a lower bound on spread costs.
- **Maker-heavy versus taker-heavy user-months:** transition-matrix differences tested with
  pooled two-proportion z-tests.
- **Simulation benchmark (App. K):** 100k traders and 50k markets.
  - Heterogeneity in wealth, signal precision, overconfidence and maker propensity; a constant
    0.5¢ half-spread; wealth-dependent participation; exit below W_min.
  - Hand-tuned, not calibrated.
- **Robustness:**
  - Wash filter: counterparty HHI ≥ 0.5 for users with ≥100 trades.
  - Resolved markets only; no-fee markets only.
- **Top-100 descriptive analysis (App. L):** case comparison with prosecuted insiders.

## Findings

**Calibration.** Close to the 45° line already at 30 days, tightening toward 1 day. Tech,
Culture and Weather deviate even at 1 day. Shown in a figure only; no calibration error
numbers.

**Concentration.**
- 764,424 winners share $1.05B (Figure 3: 766,188 and $1.1B).
- Top 0.1% / 1% / 5% / 25% of winners take 51.2% / 76.5% / 91.4% / 99.2% of gains.
- Top 0.1% / 1% / 5% of losers bear 43.7% / 68.1% / 86.1% of losses.
- About 69% of users lose overall (30.8% are winners).
- The top-1% share of gains rose from about 40–50% before the 2024 election to about 80%,
  and stayed there.
- Share of winners by category: Crypto 42.4%, Politics 35.3%, Sports 31.3%, Weather 52.5%,
  Tech 50.1%.

**Accuracy gradient.**
- Mean EHR is about −0.15 to −0.18 across the loss tail and about +0.20 at the top. The
  overall mean is −0.021.
- PnL thresholds of −$100 / $0 / +$100 sit near percentiles 15 / 70 / 92.
- The mixture model finds two components:
  - π0 = 0.101, µ0 = −0.0288, σ0 = 0.1435;
  - π1 = 0.899, µ1 = −0.0017, σ1 = 0.0029.
- So 29.3% are "skilled" (positive true ability). The LR test p ≈ 0; adjusted BIC −5,103,865.

**Probit, all users (column 4).**
- Maker volume share: +33.1 pp per unit, or **+9.0 pp per SD**. Per SD it is 9.0 pp at
  >100 trades and 4.5 pp at >1,000 trades.
- Share at extreme prices: −0.1 pp (n.s.), but +12.8 / +12.6 pp at >1,000 trades.
- Log trades: −1.2 pp (−2.9 at >100 trades).
- Log volume: −2.3 pp (+2.0 to +4.4 among active users).
- Category HHI: −8.6 pp without category dummies, +5.5 pp with them.
- Counterparty HHI: −3.3 pp (−23.1 pp at >100 trades, −50.0 pp at >1,000 trades).
- Any trading in Crypto / Politics / Tech / Weather / Finance: +3.3 to +7.9 pp versus
  Sports-only. Crypto and Politics flip to −5.7 and −4.1 pp at >1,000 trades.
- Pseudo-R² ≤ 0.056.

**Groups (Table 5): top 0.1% versus bottom 95%.**

| Measure | Top 0.1% | Bottom 95% |
| --- | ---: | ---: |
| Maker share | 47.3% | 17.1% |
| Share at extreme prices | 28.2% | 56.4% |
| Average trades | 150,623 | 223 |
| Median PnL-to-volatility | 1.73 | −1.15 |
| Mean EHR | 0.098 | −0.027 |

The top 0.1% have mean monthly PnL of $54,586 and mean maximum drawdown of $35,216.

**Persistence (Table 6, 1 month).**
- Non-participation after a loss bucket is 34–45%; after the >$50k bucket it is 16.8%.
- Conditional on trading, extreme buckets are volatile. Of the >$50k bucket, 33.4% stay and
  18.2% fall to <−$50k. Of the <−$50k bucket, 18.8% jump to >$50k.
- P(next month > 0) is 39–45% from loss buckets and up to 60.2% / 61.3% from the top two
  buckets. The (100, 1k] bucket is 50.0% (p = 0.98).
- The breakeven bucket stays put 89.3% of the time.
- At 3 months every bucket differs from 50%.
- Overall, 44% stop trading after a month, and up to 66% after six months, including 55% of
  the best performers.

**Sharpe-analogue persistence (Table 7, 1 month).** P(>0) runs from 28.0% (bucket < −10) to
65.3% (bucket > 10).

**Dropout regressions (Table 8, t+3).**
- Log trades lowers dropout: −0.094 in the worst bucket, −0.055 in the best.
- Log volume raises it: +0.085 and +0.088.
- Committed capital lowers it in all 11 buckets.
- Effects are symmetric for winners and losers.
- Log committed capital mean-reverts (−0.15 to −0.33; −0.50 at breakeven).

**Spread decomposition (Table 9).**
- The minimum spread accounts for 190.9% of the losses of the bottom 0–20% of losers (the text
  says 195.8%), 59.6% at 40–60%, and 0.9% for the top 0.1% of losers.
- Removing it flips **18.5% of losers** to non-negative PnL.
- The top 0.1% of winners are net spread earners (−3.2%).
- By category, for the smallest losers: Politics 169.2% (104.1% at 40–60), Culture 118.9%,
  Sports 97.9%, Crypto 39.1%, Tech 52.3%.

**Maker-heavy versus taker-heavy months.** 1.19M maker-heavy versus 6.33M taker-heavy
user-months.
- ∆P(>0) is mostly +7 to +18 pp. In Sharpe-analogue buckets it is +6.6 to +11 pp.
- ∆No-trade is mostly negative (−9.7 pp for [−50k, −10k); −8.6 pp for >50k).
- Diagonal persistence is similar in both groups.

**Simulation (Table K42).**

| Scenario | Top-1% gains | Top-5% gains | Bottom-1% losses | Bottom-5% losses |
| --- | ---: | ---: | ---: | ---: |
| Baseline (wealth and luck only) | 30.2% | 58.2% | — | — |
| All three channels | 76.0% | 89.4% | 28.3% | 55.1% |
| Empirical | 76.5% | — | 68.1% | 86.1% |

The loss tail is not reproduced.

**Top 100 winners.**
- They hold 27.7% of winners' gains.
- 42 of them trade fewer than 100 markets, or their top 5 markets give >70% of gross positive
  PnL. Of these concentrated accounts' gains, the text says Sports 81%, the 2024 election 15%
  and other 4%.
- Prosecuted insiders rank 115th ($0.93M; the Google employee, CFTC v. Spagnuolo) and 307th
  ($0.41M; the US soldier, CFTC v. Van Dyke). Together they hold about 0.13% of winners'
  profits.

**Wash filter (App. D).**
- 7,241 wallets flagged at HHI ≥ 0.5 (1.5% of 482,092 screened), touching 3.1% of volume.
- At HHI 0.9: 0.5% of wallets and 2.0% of volume. At 0.3: 4.3% and 5.1%.
- Sports has the most (4.6%), Politics 2.1%.
- Results are unchanged after the filter (top shares 51.4 / 76.7 / 91.5%).
- Counterparty HHI strengthens to −34.3 / −82.2 pp.

**Resolved-only and no-fee subsets.** Near-identical results. Share at extreme prices turns
mildly positive in the resolved-only sample.

## Reusable definitions

- `OrderFilled` → end-user trade reconciliation: the exchange-as-taker leg is dropped and the
  taker recovered from it.
- Winner-flag precedence: simplified-markets flag → outcomePrices if resolved or settled.
  Never the integer `outcome` field.
- Trade-only PnL with a synthetic settlement at close + 1 day and a backward mark to last trade.
- EHR, which equals resolved PnL per share traded (see the critique).
- Matched-notional volume (shares).
- The minimum-tick spread counterfactual.
- Maker-heavy and taker-heavy user-months.
- Counterparty HHI ≥ 0.5 as a wash flag, at ≥100 trades.
- Dollar-PnL transition buckets.
- Committed capital.
- The Crane–Crotty mixture adapted to (y − p).

## Stated limitations (and future work)

- A wallet is not a person: some people run several wallets.
- No off-platform activity is observed (Kalshi legs, hedges).
- No deposits or withdrawals, so no returns. Hence the PnL-ratio "analogues".
- Direct token transfers are not captured.
- The absence of a benchmark model and short histories prevent firm skill claims.
- Persistence may be selection.
- Insider analysis cannot prove absence.

Future work:
- longer panels to separate survivors from dropouts;
- identification strategies for skill versus selection;
- whether prices move other asset prices;
- behavioural drivers of low maker activity.

## Critical assessment

**EHR is nearly mechanical, not independent evidence of skill.**
- With buy-side normalisation, Σ_k q_k(o_k − p_k) over a user's trades in resolved markets
  *equals* that user's resolved PnL.
- So EHR is resolved PnL divided by share volume, and Figure 4's gradient across PnL
  percentiles is largely by construction.
- The authors caution against a skill reading but still present it as forecasting evidence.

**The mixture model is fragile.**
- s_i treats trades as independent, but trades in the same market share one outcome. That
  understates noise and inflates apparent dispersion.
- The "29.3% skilled" comes almost entirely from component 1 (µ1 = −0.0017, σ1 = 0.0029)
  having 28% of its mass above zero. That is about 0.3¢ of edge, so economically trivial.
- The test also uses an equal-weighted α̂, while the main text uses value-weighted EHR.

**Top-100 attribution contradicts the paper's own table.**
- From Table L44 (each winner's PnL assigned to their "top category"): 40 winners trade fewer
  than 100 markets. Their PnL is about $118.6M with Politics as top category versus $34.4M
  Sports.
- Across all 100 winners: Politics $140.6M (38 users), Sports $140.8M (56), Crypto $9.6M.
- That is hard to square with "81% sports / 15% election" for the 42 concentrated traders.
- The #1 winner ($22.0M, 14 markets, Politics) alone is about 7.6% of top-100 PnL.
- The "insiders would need to know voting intentions of tens of millions" argument is
  rhetorical, not a test.

**PnL coverage gaps.**
- Accounting is trade-only. Complete sets via split or merge net out correctly at resolution.
- NegRisk *convert* operations (No → Yes on other outcomes) and transfers do not, so PnL in
  NegRisk events may be distorted.
- The "perfect match" with the Data API shows consistency with Polymarket's own accounting,
  not independent correctness.
- Unresolved positions are marked to stale last trades. The resolved-only check mitigates this.

**Internal inconsistencies.**
- 764,424 / $1.05B (text) versus 766,188 / $1.1B (Figure 3).
- 195.8% / 59.8% (text) versus 190.9% / 59.6% (Table 9).
- The HF card says the no-fee variants "predate the Q4 2024 fee introduction", while the paper
  dates fees to 2026.
- The volume convention (shares) makes "$67B" not comparable with USDC-notional figures
  (Qin & Yang: $28.6B de-duplicated USDC to Apr 2026).

**Maker share.** On-chain "maker" means the resting order, so it is mechanically linked to
earning the spread. The probit is descriptive, as the authors say.

**Trust.**

| Claim | Trust | Reason |
| --- | --- | --- |
| Gain/loss concentration and ~69% losers | **High** | Robust to wash, resolved and no-fee checks |
| Maker share predicts profit; spread lower bound | **High** | Large effect, consistent everywhere |
| Calibration "close on aggregate" | **Medium** | Figure only, pooled across categories |
| EHR gradient as skill | **Low** | Mechanical identity |
| 29.3% skilled | **Low** | Independence assumption, tiny edges |
| Modest persistence, selection by dropout | **Medium-high** | Large n, but monthly MTM PnL is noisy |
| "Insiders unlikely" for the top 100 | **Low-medium** | Its own table contradicts the category breakdown; argument-based |
| Wash-robustness | **Medium** | The HHI rule is conservative (3.1% vs Sirolly 25%) |

## Directions it opens

- **Ingest `vgregoire/polymarket-users`** (`trades`, `user_pnl_summary`, `pnl_daily*`,
  `ohlcv_*`) and reconcile row by row with our own fill table: trade count, volume in shares
  versus USDC, maker/taker labels, winners.
- **Full position accounting** with split, merge, convert, redeem and transfers. Re-estimate
  concentration, NegRisk-event PnL, and how far trade-only PnL errs.
- **Skill tests that respect market clustering:** event-level bootstrap or sign
  randomisation, and price-adjusted nulls. Compare with GC's sign-randomisation and this
  paper's mixture model on the same wallets.
- **Wallet → entity clustering** (funding graph, proxy/Safe → EOA) to revisit concentration
  and the "a user is a wallet" bias.
- **Maker-PnL decomposition** into spread capture, adverse selection (markout at 1m, 1h, 1d),
  rebates and fees. Link to maker concentration over time and V2.
- **Persistence on survivor-adjusted panels** (inverse-probability weighting for dropout) and
  at the event level rather than by calendar month.
- **Insider screening products:** new-wallet, single-event, pre-news conviction flags. Validate
  against the CFTC cases ranked 115 and 307, and against GC's heuristic.
- **Retail-harm dashboard:** loss distributions by category, price region and maker share,
  plus counterfactual "limit-order instead of market-order" savings per user.
