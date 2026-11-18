# Opening Wide, Moving Fast: Polymarket Spread Dynamics

- **Source:** IMDEA Networks repository,
  [hdl 20.500.12761/2065](https://hdl.handle.net/20.500.12761/2065)
  ([PDF](https://dspace.networks.imdea.org/bitstream/handle/20.500.12761/2065/Polymarket_Initial_Liquidity-3.pdf?sequence=1)).
  - The record is dated 2026-09; type and venue are not stated. The layout is LNCS-style
    (21 pp including appendix tables).
  - The Polymarket documentation it cites was accessed 17–18 May 2026.
  - No arXiv version was found.
- **Authors:** Carl Jörnell and Vicente Perez (Lund University; equal contribution); Oriol
  Saguillo (IMDEA Networks; a co-author of arXiv 2508.03474).
- **Released:**
  - order-book snapshot dataset: HF `vpcapitano/polymarket-genesis-liquidity`;
  - code: github.com/vpercap-rg/polymarket-genesis-liquidity.
- **Read:** full text, including the appendix tables (Tables 8–9) and the figures, whose
  plotted values are printed in the text layer.

## Question

Every Polymarket contract opens with an empty book: no inherited orders, no designated market
maker and no opening auction. The paper asks what it costs to trade in a market's first 24 hours
(the "genesis window") and how that cost differs across eight event categories:
- **RQ1:** how wide quoted spreads start and how fast they narrow;
- **RQ2:** the realised taker cost (effective half-spread) over time;
- **RQ3:** how that cost splits into a realised half-spread kept by the maker and price impact.

The claimed central result is a **dissociation**: the category ranking by opening cost differs
from the ranking by post-trade price impact.

## Data

**Trades.** The Wang et al. (Shanghai Innovation Institute) open dataset, HF
`SII-WANGZJ/Polymarket_data`, rebuilt from Polygon.
- `quant.parquet`: 568,590,741 normalised peer-to-peer trades, 21 Nov 2022 – 31 Mar 2026, each
  with timestamp, price, quantity, wallets and market id. All trades are expressed from the YES
  token's perspective.
- `markets.parquet`: 734,790 markets.

**Books.** Snapshots from the Dome API, a third-party service.
- Each record has best bid, best ask, depth per visible level, midpoint and timestamp.
- A record is written only when the book changes, and the last state is carried forward.
- Coverage: 14 Oct 2025 – 28 Apr 2026, after which the service was discontinued.

**Categories.** Gamma API tags mapped to 8 classes: monetary policy, economy, geopolitics,
politics, elections, sports, crypto, other.
- Mapping uses rules, then LLM review of borderline cases, then a manual audit, following the
  resolving event rather than the title.
- Recurring crypto up/down contracts (5m/15m/1h) and mention or tweet-count markets are
  excluded as "mechanical".

**Window.** 17 Oct 2025 – 29 Mar 2026.
- The end date is one day before Fee Structure V2 (30 Mar 2026) and about a month before the
  CLOB v2 migration.
- Within the window, fees applied only to the excluded short crypto markets and to sports
  markets opened after 18 Feb 2026, with rebates of 20% (crypto) and 25% (other categories).

**Eligibility.**
- The first executed trade falls in the window; T₀ is defined as that first trade.
- At least one Dome state in [T₀, T₀ + 24 h].
- Lifetime volume ≥ 5,000 USDC.
- These filters take 497,506 contracts down to **162,342**. Neg-risk outcomes count as separate
  contracts.

**Type A subset.** More than 10 trades in the first 3 h and at least 1% of the market's volume
traded within the first 24 h.

**Reporting.** Medians only. Cells with fewer than 30 markets are suppressed. No significance
tests.

## Methods

- **Quoted spread** at T₀ and at 6, 12, 18 and 24 h (Dome state carried forward).
- **Opening-book shape at T₀:**
  - spread;
  - size at the best ask;
  - "extreme ask": the share of top-10 ask depth priced ≥ 0.90;
  - "stub": the share of markets with best ask ≥ 0.85 and best bid ≤ 0.15.
- **First-trade execution ratio:** the first trade's price relative to the posted best quote.
  - 1.00 means it hit the book; below 0.85 means substantially inside the spread.
  - The formula is not written out, and the figure calls it the "extraction ratio".
- **Effective half-spread** paid by takers relative to the prevailing midpoint, in 9 time
  buckets (<1m, 1–6m, 6–15m, 15–30m, 30–60m, 1–3h, 3–6h, 6–12h, 12–24h).
- **Huang–Stoll decomposition:**
  - realised half-spread uses the midpoint τ = 1 h later; price impact is the mid move;
  - R/E = realised ÷ effective;
  - computed for trades in the first 6 minutes, Type A markets only;
  - trades are signed with the Lee–Ready quote rule (above mid = buy), dropping at-mid trades.
- **Category medians** of each component are computed independently. The paper notes that they
  need not sum, and R/E is a ratio of medians.

## Findings

**RQ1: opening spread (median, ¢) at the first trade, Table 2.**

| Category | n (full) | full | n (Type A) | Type A |
| --- | ---: | ---: | ---: | ---: |
| Monetary policy | 111 | 13.0 | 56 | 7.0 |
| Economy | 201 | 21.0 | 108 | 10.5 |
| Geopolitics | 1,403 | 10.0 | 1,133 | 7.0 |
| Politics | 605 | 8.0 | 516 | 7.0 |
| Elections | 771 | 13.0 | 437 | 10.0 |
| Sports | 25,357 | 3.0 | 19,309 | 3.0 |
| Crypto | 565 | 19.0 | 404 | 15.0 |
| Other | 1,801 | 14.0 | 1,195 | 11.0 |

**Compression (full sample, Table 3/Fig. 1, ¢ at T₀ → 6h → 24h).**

| Category | n | T₀ | 6h | 24h | Fall |
| --- | ---: | ---: | ---: | ---: | ---: |
| Monetary policy | 196 | 13 | 8 | 5 | 62% |
| Economy | 332 | 21 | 8 | 4 | 81% |
| Geopolitics | 2,152 | 10 | 4 | 2 | 80% |
| Politics | 821 | 8 | 3 | 2 | 75% |
| Elections | 1,090 | 13 | 7 | 3.6 | 72% |
| Sports | 46,131 | 3 | 3 | 3 | 0% |
| Crypto | 880 | 19 | 7 | 3 | 84% |
| Other | 2,690 | 14 | 6 | 3.9 | 72% |

- In the Type A subset every non-sports category reaches a median of about 2¢ by 24 h. The
  Type A sports median falls 3 → 2¢ (−33%).
- Scheduled-event categories (elections, monetary policy) tighten most slowly.

**Opening-book shape (Table 4).**
- Median spread at T₀: 0.05 for sports versus 0.30–0.36 for non-sports.
- Top-ask size: 171 contracts for sports versus 32–73 elsewhere.
- Extreme-ask share: 23.9% for sports versus 67.6% to 91.9% elsewhere; crypto is highest and
  politics is 88.3%.
- Stub-book share: 5.1% for sports versus 9.9%–20.3% elsewhere.

**First trade.**
- The median execution ratio is 1.00 in every category.
- The share at the book is 75.7% (crypto) to 83.0% (elections).
- 15.6%–23.2% of first trades execute well inside the spread (ratio below 0.85).

**RQ2: effective half-spread (¢, full sample, Table 9).**
- Under 1 minute: 12–16¢ for non-sports (geopolitics 16.0, monetary policy 14.5, economy 12.0)
  versus 1.5 for sports.
- 1–6 minutes: roughly halved (3.15–6.5).
- 30–60 minutes: within 2× of sports.
- From 1–3 h on: converged at about 0.5–2¢. Sports holds at about 1¢ throughout.
- A few buckets are non-monotone (economy 6.25 at 15–30 m), which the authors attribute to
  fewer than 50 markets in those cells.

**RQ3: decomposition (τ = 1 h, first 6 minutes, Type A, Table 6, ¢).**

| Category | n | Effective | Realised | Impact | R/E | % positive realised |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Monetary policy | 34 | 5.00 | 0.73 | 4.30 | 0.15 | 55.9 |
| Economy | 221 | 3.50 | 3.00 | 2.00 | 0.86 | 82.4 |
| Geopolitics | 1,864 | 12.00 | 3.00 | 5.00 | 0.25 | 67.7 |
| Politics | 1,021 | 10.00 | 3.50 | 4.00 | 0.35 | 67.6 |
| Elections | 981 | 5.00 | 1.45 | 3.50 | 0.29 | 67.4 |
| Sports | 48,908 | 1.00 | 1.00 | 0.00 | 1.00 | 67.1 |
| Crypto | 677 | 6.50 | 3.50 | 1.50 | 0.54 | 67.7 |
| Other | 2,045 | 7.50 | 2.50 | 3.50 | 0.33 | 68.4 |

- **Realised-spread distribution (Table 7):**
  - 16%–38% of trades have a negative realised half-spread (economy 15.8%, monetary policy
    38.2%);
  - P25 is negative everywhere except economy.
- **At-mid trades dropped:** 2.79%–4.75% (sports: 465,776 of 10,962,722).
- **The dissociation:**
  - Sports (cheap) and economy (wide open) both have high R/E.
  - Geopolitics, politics, elections and other have low R/E at differing cost levels.
  - Interpretation offered: sports has external reference prices from bookmakers and betting
    exchanges; economy events are scheduled public releases.
- **Prediction:** maker rebates under the post-sample fee regime should compress opening
  spreads and raise R/E.

## Reusable definitions

- **Genesis window and T₀:** the first on-chain trade, not the creation time.
- **Type A activity screen:** more than 10 trades in 3 h and at least 1% of volume in 24 h.
- **Opening-book descriptors:** extreme-ask share (≥ 0.90 among the top 10 levels) and stub
  book (ask ≥ 0.85 and bid ≤ 0.15).
- **First-trade execution ratio.**
- **Effective, realised and impact half-spreads** at τ = 1 h; R/E as the maker-retained share.
- **Event-based 8-category taxonomy,** with recurring and mechanical formats excluded.

## Stated limitations

- Descriptive only; no causal channel is identified (informed trading, inventory, maker
  competition, platform incentives).
- No significance tests.
- Quoted spreads are composite: liquidity rewards (`max_incentive_spread`,
  `min_incentive_size` per market) are not separated out.
- Trade direction is inferred.
- The τ = 1 h midpoint absorbs unrelated news, so R/E describes post-trade midpoint behaviour
  rather than clean informed trading.
- "Other" is a residual mixture, and monetary policy rests on 34 markets.
- Future work: rerun on the post-Fee-V2 platform to see whether the dissociation survives.

## Critical assessment

**The dissociation depends on which cost measure is ranked.**
- It compares full-sample *quoted* opening spreads (RQ1) with a Type A, first-6-minute
  decomposition (RQ3).
- Within Table 6 itself, the effective half-spread and R/E line up fairly well. Economy is
  cheap there (3.5¢, below geopolitics at 12 and politics at 10) and also has high R/E.
- Our own Spearman calculation on the 8 category medians:
  - Table 6 effective half-spread vs impact share (1 − R/E): ρ ≈ 0.50 (p ≈ 0.20);
  - full-sample opening spread vs impact share: ρ ≈ −0.05;
  - Type A opening spread vs impact share: ρ ≈ −0.07.
- Because the claim rests on 8 points with no tests, it is weak.

**R/E is a ratio of medians, not a median ratio.** Components do not add up: economy has
effective 3.5, realised 3.0 and impact 2.0. Crypto has realised 3.5 greater than impact 1.5,
yet R/E is 0.54.

**Unexplained sample sizes.**
- 162,342 contracts are said to be eligible, but category n is about 31k (Table 2) or about
  54k (Table 3).
- The excluded mechanical formats are never counted.
- The n for the same "T₀" quantity differs between Tables 2, 3 and 4.

**"Opening spread" is inconsistent.** Tables 2 and 3 give non-sports at T₀ as 8–21¢. Table 4
gives 0.30–0.36 (30–36¢), and the text says "thirty-plus cents". Two different definitions of
the T₀ book (the first Dome state versus the state at the first trade) are likely but not
stated.

**Look-ahead selection.** The ≥ 5,000 USDC lifetime-volume filter conditions on the future.
Type A conditions on the first 3–24 h of activity, which is part of the outcome being measured.

**Timing alignment.**
- On-chain block times are matched to Dome change-events, and the latency of that matching is
  not reported.
- A snapshot that already reflects the trade's own fill would bias the quote-rule sign and the
  effective spread.
- Dome's "no record means unchanged" assumption is not validated against an independent feed.

**Unmodelled confounds.**
- Liquidity-reward parameters are observable via the API but not used.
- Sports markets are heavily template-listed, often market-maker-seeded at creation, and
  dominate the sample (about 85% of n).

**Trust:**
- category differences in opening quoted spread and fast compression: **high** (large n,
  medians, Type A robustness);
- sports at the tick floor with deep books: **high**;
- effective-cost collapse within the first hour: **medium–high** (depends on quote/trade
  alignment);
- R/E levels by category: **medium–low** (ratio of medians, inferred signs, τ = 1 h noise,
  small n for monetary policy and economy);
- "dissociation" as a general property: **low–medium** (it depends on the cost metric and
  sample chosen).

## Directions it opens

- **Rebuild with clean inputs.** Use the archived WebSocket book (`book` and `price_change`
  events) with exchange timestamps instead of Dome. Use the on-chain taker side (exchange-as-
  taker rule) instead of the quote rule. Compute per-trade R/E with bootstrapped CIs per
  category.
- **Creation-to-first-trade latency.** Combine Gamma `createdAt`/`acceptingOrdersTimestamp`
  with the first on-chain fill, and test whether creator or market-maker seeding explains
  sports' tight opening.
- **Liquidity rewards as a treatment.** Use per-market `max_incentive_spread`,
  `min_incentive_size` and reward pool to test their effect on opening spread and convergence
  speed.
- **Fee regime natural experiment.** Run a difference-in-differences on opening spreads and R/E
  around the category fee roll-outs (crypto, sports from 18 Feb 2026, Fee V2 on 30 Mar 2026)
  and the CLOB v2 migration.
- **First-maker identity.** Who supplies the T₀ liquidity (wallets), what they earn on the
  opening spread net of adverse selection, and how concentrated opening-liquidity provision is.
- **Live product.** A "new-market cost" alert showing the predicted time to reach about 2¢ by
  category, plus an opening-book "stub" detector for takers.
- **Coverage.** Extend to recurring crypto up/down markets (where price discovery is external,
  as for sports) and to neg-risk siblings sharing one event (staggered T₀).
