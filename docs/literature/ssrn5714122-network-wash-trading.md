# Network-Based Detection of Wash Trading (Polymarket)

- **SSRN:** [5714122](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5714122). The SSRN
  number comes from the authors' Substack post of 12 Nov 2025. The SSRN page itself was blocked,
  so its posting and revision dates were not checked.
- **Versions:** v. 6 Nov 2025 (80 pp, press copy at
  [gamblingharm.org](https://gamblingharm.org/wp-content/uploads/2025/11/Polymarket-Wash-Trading-Study.pdf))
  and v. 17 Jan 2026 (82 pp, press copy at
  [defirate.com](https://defirate.com/wp-content/uploads/2026/02/columbia-study-polymarket-wash-trading.pdf)).
  Both use the same data cutoff (12 Oct 2025) and report the same headline numbers.
  - The Jan version adds: a spillover-curve figure for Example 1, a footnote linking the
    spillover metric to normalised cut, an explicit "29.2% at θ = 0.9", a "Behavioral Markers"
    sub-heading, more acknowledgements, and wording fixes.
  - The Nov version says "Part I … converged in 12 iterations"; the Jan version corrects this to
    Part II.
- **Category:** market microstructure / fraud detection. 45 pp of main text, then appendices A
  (data collection), B (figures), C (proofs) and D (trade-graph examples).
- **Authors:** Allen Sirolly, Hongyao Ma, Yash Kanoria (Columbia Business School, DRO); Rajiv
  Sethi (Barnard College, Columbia; Santa Fe Institute).
- **Code/data:** neither is released. Comparator code is VW21's
  [repository](https://github.com/friedhelmvictor/lob-dex-wash-trading-paper). Contract addresses
  are in App. A, Table 11.
- **Read:** the full text of the Jan 2026 version (pypdf extraction), with the Nov 2025 version
  diffed on its key numbers and sections. Figures were read from captions only, so curves such as
  the weekly series and the sensitivity contours (Fig. 29) are known only through the text.
  Author commentary is from Sethi's Substack post.

## Question

How much of Polymarket's CLOB volume is wash trading? Wash trading is defined following the
CFTC and CME: trades that change no one's beneficial market position.

The paper also asks how to detect wash trading without ground truth, when wash traders:
- use many wallets;
- break closed cycles;
- get "intercepted" by outsiders;
- mix in real trades or hold small buffers to resolution.

Motivation:
- Volume drives homepage ranking.
- Volume is read as "crowd size".
- Volume serves as a platform-health metric.
- Volume can drive a possible airdrop. Polymarket confirmed a token and airdrop in Oct 2025.
- Polymarket has no KYC and, at the time of writing, no fees.

## Data

**Trades.** Every Polymarket CLOB trade from 2022-11-21 to 2025-10-12.
- Source: Polygonscan `accounts/` API transfer events for the module addresses: CTF_EXCHANGE
  `0x4bfb…982e`, NEG_RISK_CTF_EXCHANGE `0xc5d5…0f80a`, the NegRisk adapter, wrapped collateral,
  burn, the rewards contracts, USDC.e and CTF.
- Matching happens off-chain, so the book and its matching rules are not observed.
- Size: 67.7M trades (82.7M after splitting each trade into maker lines), 1.33M wallets, 102,532
  markets, 45,732 events, 29.0B shares, $15.5B dollar volume.
- The 2024 presidential-winner event alone is 3.7B shares ($2.0B).

**Trade representation.**
- Each taker fill is split line by line against each maker (Table 1).
- Price is the collateral amount divided by shares.
- Each line is typed buy/buy, buy/sell or sell/sell. Long means buying Yes or selling No.
- Non-Yes/No outcome labels (for example team names) are mapped to Yes/No arbitrarily.
- Timestamps are at block level. Order within a block comes from the transaction index.
- Splits, merges, redeems and NegRisk converts are excluded, because they have no counterparty.

**Volume convention.**
- In buy/buy and sell/sell trades, N Yes plus N No shares count as N shares and $N. This matches
  Polymarket's displayed volume.
- Share volume and dollar volume are kept separate. Polymarket labels share volume with "$".

**Metadata.**
- From the Gamma API: market and event names, start/end times and token ids.
- Gamma token ids, resolution prices and close times are "sometimes incorrect", so they were
  re-derived from `ConditionResolution` logs (signature `0xb44d84…5894`), decoded with the CTF ABI
  plus keccak, through a Chainstack RPC.
- Categories were labelled by GPT-4o-mini, because API category coverage is inconsistent.
- Public profiles supply display names and `created_at`. These were snapshot in Aug–Oct 2025, and
  about 96k wallets (7%) have none. Profiles are used only for auxiliary analysis.

**Other inputs.**
- Direct USDC transfers between wallets on Polygon, used for common-ownership evidence.
- Kalshi candlesticks, used for an open-interest comparison.

## Methods

**Anomaly descriptives.**
- New-wallet creation rate, with a jump from 2024-05-14.
- Display-name length histogram, with spikes at 10 and 17 characters.
- Share of buy/sell trades in share volume versus dollar volume.
- Share of buy/sell volume at p < $0.01.
- Volume-to-open-interest ratio, against Kalshi.
- Fraction of wallets with |PnL| < $1, and fraction trading ≥ 90% at p < 0.01 or p > 0.99.

**Part I: closure score x⁰.**
- Per wallet i and market m, P_{i,t} is the net long position and X = |P|. Position reversals are
  split into two trades.
- A *terminal contraction* is a contraction followed by an expansion, or the wallet's last trade
  in the market.
- A *closure* is a terminal contraction with X ≤ c·M, where M is the maximum |position| since the
  previous closure, and c = 0.005. In other words, a ≥ 99.5% drawdown.
- The score is x⁰_i = Σ_m s^m_i · 1{Q^m_i > 0}, where s^m_i is market m's share of i's total
  volume and Q^m_i is the number of closures. That is, x⁰ is the volume share of markets in which
  i ever closed.

**Part II: network propagation.**
- B is row-stochastic: b_ij is the fraction of i's share volume (all markets) traded with j, with
  b_ii = 0.
- Update: x^(k) = ½(x⁰ + B x^(k−1)), iterated to relative ℓ2 change < 1e-5. This is
  Friedkin–Johnsen with stubbornness ½.
- Prop. 1: the iteration converges to the unique solution of (I − ½B)x = ½x⁰.
- Prop. 2: the volume-weighted score vᵀx is conserved, so the iteration redistributes x⁰ across
  the network. The volume-weighted mean score is 0.747.
- It converged in 12 iterations.
- **Algorithm 1** flags a trade if min(x_i, x_j) ≥ θ.

**Part III (Algorithm 2): market-specific threshold.**
- r_im = min(x_i, max_{j ∈ N_m(i)} x_j).
- Relative spillover: Y_m(θ) = 1 − Σ v_ij 1{min(r_im, r_jm) ≥ θ} / Σ v_ij 1{max(r_im, r_jm) ≥ θ}.
  This is a normalised-cut sweep over pair volumes v_ij in market m.
- θ*_m = the smallest argmin of max(ζ, Y_m(θ)) over candidate θ ∈ {r_im} ∩ [θ_lo, θ_hi] with
  Y_m ≤ Ȳ. If no candidate qualifies, θ*_m = 1 and nothing is flagged.
- Parameters: θ_lo = 0.8, θ_hi = 0.99, Ȳ = 0.1, ζ = 0.001.
- θ_hi and Ȳ were chosen by eye, as the values that "give reasonable performance" on the example
  markets and the top-50 markets' trade-graph plots.

**Specialised pattern detectors.** These are mutually exclusive but do not cover everything.
- **Dyadic:**
  - Upper bound: 2 × Σ the reductions in the pairwise net position P_{ij}.
  - Refined: pairs that open and (almost) close against each other, with no time limit or within
    180 s.
- **Triangular:**
  - Motifs (i⇈j, j→k, k⇊i) or (i⇈j, k←i, j⇊k) under weak time compatibility.
  - Upper bound from an LP: maximise 3Σx_s subject to per-relation volume caps.
  - Refined: legs within 180 s of each other.
  - The largest markets are cut into 20 equal-volume parts to keep this tractable.
- **Chain:** wallets with exactly one distinct upstream and one distinct downstream counterparty;
  components of ≥ 3 wallets with trade-size coefficient of variation (CV) ≤ 0.1.
- **Cluster:** buy/sell subgraph of wallets with more than one counterparty in some direction;
  components of ≥ 4 wallets with trade-size CV ≤ 0.1.

**Validation without labels.**
- Overlap with the specialised detectors.
- Hand-built wallet clusters (Table 10). These were found from:
  - direct USDC transfer graphs;
  - display-name patterns;
  - similar volume, first-trade date and statistics;
  - crawling frequent counterparties.
- Behavioural profiles of high-score (x ≥ 0.9) versus low-score (x < 0.8) wallets: share of
  markets closed, median open-to-close time and median price change.
- Market-level generalised additive model (GAM, logit link) of wash share on:
  - buy/sell share;
  - average buy/sell price;
  - volume / max OI ("speculative ratio").
  This is restricted to markets with ≥ 10⁶ shares, 2.8% of markets.

**Comparison with VW21** (Victor & Weintraud 2021). Strongly connected components plus volume
matching within ±1% of the average trade size, run per market with a 1 h window. The
occurrence filter was dropped.

**Sensitivity.** Contours of total flagged share over (θ_lo, θ_hi, Ȳ, ζ) (Fig. 29), and the full
fixed-θ curve (Fig. 7).

## Findings

**Headline.**
- Algorithm 2 flags **24.2%** of all-time share volume. A fixed θ = 0.939 gives the same share.
- Algorithm 1 flags **18.0%** at θ = 0.99 and **29.2%** at θ = 0.9.
- **14%** of wallets have more than half their volume flagged. About 30% have some volume
  flagged.
- The intro reports these as "nearly 25% of volume" and "14% of the 1.26M wallets that ever
  traded".
- Under Algorithm 2, fewer than 10% of markets have any flagged volume.

**Over time** (weekly, Algorithm 2).
- Essentially none before Jun 2024 at θ ≥ 0.8. The rise starts in Jul 2024.
- Peak of about **60%** of weekly volume in Dec 2024.
- Elevated until late Apr 2025, then < 5% from Jun to late Sep 2025.
- About **20%** in the first week of Oct 2025.
- Dyadic trading dominated the detected patterns until Jan 2025, when cluster trading took over.
  Both faded in late Apr 2025, and dyadic trading resurged in late Sep 2025.

**By category** (all-time share volume).

| Category | Share flagged | Peak week |
| --- | ---: | --- |
| Sports | 45% | 90% (21 Oct 2024) |
| Elections | 17% | 95% (24 Mar 2025) |
| Politics | 12% | 60% (23 Dec 2024) |
| Crypto | 3% | 21% (6 Oct 2025) |

**Top-50 markets** (29.4% of share volume, 23.0% of dollar volume).
- Flagged shares are mostly either ≥ 0.9 or ≤ 0.1.
- Trump-win (1,568.7M shares), Harris-win and Trump-inaugurated get θ* = 1, so 0% flagged. No
  threshold met Ȳ.
- This contrasts with Chaos Labs' roughly one-third estimate for the presidential market.
- Nicolae Ciucă (Romania): 326.5M shares but $2.6M dollar volume, 98.5% flagged. About 60% of its
  volume is buy/sell, at an average price of $0.00147.
- Many 2025 NBA, Super Bowl and EPL long-shot futures are 77–97% flagged.

**Anomalies.**
- Over half of all wallets that had ever traded by early Jan 2025 first traded after
  5 Nov 2024. Open interest did not rise.
- The buy/sell share of share volume diverges from its dollar-volume share from Jan 2024, driven
  by buy/sell trades at p < $0.01.
- The volume/OI ratio rose sharply in 2024–25.

**Detected wash trading is concentrated** in buy/sell and sell/sell trades (which recycle
collateral), at extreme prices, and in markets with a high volume/OI ratio.
- Under 2% of weekly buy-only volume is flagged.
- The "exclude buy-only" series falls together with the wash series.

**Behaviour of high-score wallets** (x ≥ 0.9 versus x < 0.8). Price and timing are not inputs to
the score.

| Measure | High-score | Low-score |
| --- | ---: | ---: |
| Close positions in ≥ half of their markets | > 83% | 13% |
| Median open-to-close time < 1 min | 44% | 6% |
| Median open-to-close price change < $0.01 | > 96% | 35% |

**Specialised detectors** (share of total share volume).

| Pattern | Upper bound | Refined | Algorithm 2 recall |
| --- | --- | --- | ---: |
| Dyadic | 5.6B (19.3%) | no time limit: 4.23B (14.6%; $2.26B); ≤ 180 s: 2.16B (7.5%; $936M) | 64% |
| Triangular | 649M (2.2%) | ≤ 180 s: 100M (0.34%; $86.5M) | 12% |
| Chain | — | 306M (1.1%; $31.6M) | 85% |
| Cluster | — | 1.37B (4.74%; $67M) | 95% |
| Unclassified | — | — | 16% |

- Opened-and-drawn-down positions account for 21.5B shares (74.4%). Opened-and-closed positions
  account for 19.4B (66.8%).
- Table 9 gives the same recall columns at θ = 0.8, 0.9 and 0.99. For example, dyadic recall is
  90.3%, 73.6% and 53.2%.

**Clusters** (Table 10, 18 clusters).
- Almost all trade 85–99.9% of their volume within the cluster.
- Algorithm 2 flags most of that within-cluster volume, with two exceptions:
  - TwoTrade: 8.7%. Its hub-and-spoke triangles leave peripheral wallets with x⁰ = 0, so their
    scores fall to 0.8–0.9.
  - monasa: 0.0%. It keeps a buffer position of at least 3,000 shares.
- Selected clusters:

| Cluster | Wallets | Volume | Within-cluster flagged | Aggregate PnL |
| --- | ---: | --- | ---: | --- |
| Lander | 109,142 | 932.7M shares ($79.9M) | 93.3% | −$64,160 |
| TenChar | 43,011 | 188M shares ($1.0M) | 90.9% | −$9,873 |
| zhongxin | 492 | 517.1M shares | 99.8% | — |
| Fantasy | 514 | 109M | 94.4% | +$1,347 |

  - Fantasy wallets have a mean |PnL| of $17,134 each. They mask their activity with buffers,
    mixed-in real trades and hold-to-resolution offsets.
  - For TenChar, 99.8% of wallets have |PnL| < $4.
- **fengchu network:** 1,028 wallets, 792M shares ($407M), cumulative loss $511.31, 99.9% of
  within-cluster volume flagged.
  - It accounted for 27% of sports dollar volume (21% of shares) from 23 Oct to 25 Nov 2024, and
    70% of sports dollar volume in the week of 28 Oct 2024.
  - It was seeded with about $5k transfers to each of six children; fengchu itself was funded via
    Bybit/OKX.
- **81chain:** 12,036 wallets, of which 1,823 trade. 2.9M shares, −$666, 85.0% within-cluster,
  56.0% flagged. Capital passes through six non-trading wallets between consecutive traders.
- Clusters typically lose money in aggregate. The authors read this as support for
  Glosten–Milgrom, since outsiders intercept wash orders.

**Comparison with VW21.**
- Algorithm 2 catches 80.5% of VW21's flagged volume. VW21 catches 26.5% of Algorithm 2's.
- VW21 flags as little as 0.0–19.2% within several clusters (Fantasy 5.7%, Lander 0.0%).

**Sybil–maker pattern.**
- Example market (Fig. 47): 3,866 sybils buy at 0.996 and sell at 0.995 against 12 makers; 4.6% of
  that market's shares.
- This pattern is largely *not* flagged.
- Tick size drops to 0.001 when the price is < 0.04 or > 0.96 (since 20 Apr 2023).
- Self-trades (same wallet on both sides) have been blocked since 27 Apr 2023.

## Reusable definitions

- Closure: a terminal contraction with a ≥ 99.5% drawdown from the running maximum |position|.
- Volume-weighted closure score x⁰.
- Propagation x = ½(x⁰ + Bx), whose volume-weighted mean score is conserved.
- r_im and the relative spillover Y_m(θ), i.e. a sweep cut, for picking per-market thresholds.
- Trade-line representation with buy/buy, buy/sell and sell/sell types, and the
  no-double-counting volume convention.
- Dyadic pairwise-position reduction, triangular motifs and their LP bound, and chain and cluster
  rules (CV ≤ 0.1).
- "Speculative ratio" (volume / max OI).
- Buy-only volume share as a capital-efficiency control.
- Contract address table and per-transaction-type token-flow table (App. A).

## Stated limitations

- There is no ground truth, so results are estimates.
- Evasion goes undetected: buffers held to resolution (monasa), hub-and-spoke triangles, and
  sybil–maker trading.
- Buy-only wash schemes exist: buy with a colluder and hold to resolution in short markets, or
  transfer and merge.
- Algorithm 2 needs per-market separation, so wash trading inside mega-markets can go unflagged.
- Deploying the detector would cause adaptation.
- Future work:
  - other initialisations, such as dollar-days per share or counterparty `created_at` proximity
    (Fig. 27);
  - leave-one-out message passing;
  - a systematic choice of ρ (fixed at ½);
  - game-theoretically robust detection;
  - other markets.
- They suggest using open interest rather than volume as the health metric.

## Critical assessment

**Unclear definition of "wallet".** The paper does not say whether "wallet" means the proxy or
Safe address seen on-chain, or the EOA. Proxy versus EOA matters for USDC-transfer linkage.

**V1 contracts only.** Coverage is the V1-era CTF and NegRisk exchanges up to Oct 2025.

**Hand-tuned thresholds.** θ_hi and Ȳ were tuned by visual inspection of the same markets used to
showcase the results.
- Validation is circular to a degree: the clusters were found partly by crawling frequent
  counterparties, which is the same signal B encodes.
- Their recall is therefore not independent of the method.

**False positives untested.**
- There is no precision estimate and no labelled negatives.
- Legitimate market makers closing positions against other closers (for example arbitrage or
  liquidity-rewards farming between bots) could score high.
- The paper argues that the time series makes this unlikely, but does not test it.

**Volume-share concept is ambiguous.** Headline shares are computed on share volume. The dollar
share is much lower in cheap-share schemes: Lander is 932.7M shares but $79.9M, and the
Ciucă market has 98.5% of shares flagged on $2.6M of dollar volume.

**0% in the largest markets.** This is a design artefact: when no threshold separates well,
θ* = 1. It is not evidence of no wash trading, and it shows clearly against Chaos Labs' roughly
one-third.

**Inconsistencies.**
- 1.33M wallets in the data versus "14% of 1.26M wallets that ever traded".
- "14% flagged" in the intro means wallets with more than half their volume flagged.
- Prop. 1–2 refer to "Algorithm 2" but concern Algorithm 1's iteration.
- The Gamma-API paragraph is duplicated in App. A.
- The Glosten–Milgrom "support" rests on cluster PnL, and two clusters made gains.
- Sethi's blog says the algorithm converges "after three" iterations; the paper says 12.

**Look-ahead.** Scores use each wallet's full history to Oct 2025, so this is an ex-post
classifier, not a real-time one.

**Trust:**
- wash trading is large, peaked around Dec 2024 and is concentrated in sports and long shots:
  **high** (multiple independent signals, flagrant clusters);
- the exact 24.2% figure: **medium** (depends on parameters; detection is incomplete and
  unvalidated in both directions);
- category and top-50 numbers: **medium** (category labels from an LLM; θ* = 1 artefact);
- comparison with VW21: **medium** (VW21 was modified and run per market with a 1 h window);
- behavioural separation of high-score wallets: **high** (uses features that are not score
  inputs);
- cluster PnL and ownership evidence: **high** for the transfer-linked clusters, **medium** for
  those linked by name or statistics.

## Directions it opens

- **Reimplement Algorithms 1–2** on V1+V2 trades through 2026 and publish a per-trade wash flag
  with confidence. Compare share and dollar shares with the 24.2% here and the 13.8% used in
  2610.36639.
- **Proxy-to-EOA and funding-graph clustering** (USDC.e plus native-USDC transfers, CEX deposit
  addresses). This would give ground truth for precision and recall, and an "entity" table for
  every other study.
- **Evasion-robust scores:** dollar-days per share, `created_at` proximity, buffer-to-resolution
  detection, and the sybil–maker pattern at 0.001 ticks.
- **A streaming detector** from WebSocket fills, using a rolling B and an online fixed point, to
  power a "clean volume" leaderboard and homepage ranking.
- **Clean-volume metrics:** volume/OI, dollar versus share volume, and buy-only share. Then redo
  liquidity, price-discovery and calibration studies with and without wash-flagged trades.
- **Incentive event studies:** airdrop announcement (Oct 2025), liquidity and holding rewards, and
  the fee introduction, each followed by wash share.
- **Price impact of wash bursts:** whether volume spikes move prices or attract followers, and how
  this links to 24 h-volume ranking.
- **Correct metadata from chain logs** (`ConditionResolution`) rather than Gamma; quantify Gamma
  errors.
