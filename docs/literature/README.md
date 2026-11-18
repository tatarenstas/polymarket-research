# Literature: Polymarket research map

There is one note per source. Each note covers the source's question, data, methods,
findings with numbers, reusable definitions, stated limits, a critical assessment with a
trust rating per finding, and the directions it opens. Each source was read on its own
terms, not through this repository's hypotheses.

The **Read** column records how much of the source the note is based on:
- **full** — the whole text;
- **partial** — some sections only;
- **abstract** — the abstract or secondary sources only. Every claim in these notes is
  tagged with where it came from.

## Index (27 sources)

### Data and datasets
| Source | Read | Note |
| --- | --- | --- |
| Qin & Yang, *Polymarket-v1 Database* (2606.04217 v2) | full | [note](2606.04217-polymarket-v1-database.md) |
| Young, *OpenMarket: synchronized Polymarket–Binance dataset* (2607.26245) | full | [note](2607.26245-openmarket-polymarket-binance.md) |

### Participants, profits and skill
| Source | Read | Note |
| --- | --- | --- |
| Akey, Grégoire, Harvie & Martineau, *Who Wins and Who Loses* (SSRN 6443103) | full (OSC PDF, 28 Aug 2026) | [note](ssrn6443103-who-wins-who-loses.md) |
| Gómez-Cram, Guo, Jensen & Kung, *Crowd Wisdom or Informed Minority?* (SSRN 6617059) | **abstract** / secondary | [note](ssrn6617059-crowd-wisdom-informed-minority.md) |
| Jia & Sun, *Beyond Profit Rankings: Smart Money* (2610.34754) | full | [note](2610.34754-beyond-profit-rankings-smart-money.md) |
| Nechepurenko, *Fill-side behavioral concentration* (2605.11640) | full v2, v1 partial | [note](2605.11640-fill-side-behavioral-concentration.md) |
| Pew Research, *The typical Polymarket user* (Jul 2026) | full | [note](pew-2026-07-typical-polymarket-user.md) |

### Informed and insider trading
| Source | Read | Note |
| --- | --- | --- |
| Mitts & Ofir, *From Iran to Taylor Swift* (SSRN 6426778) | **partial** (authors' summaries and a replication) | [note](ssrn6426778-from-iran-to-taylor-swift.md) |
| Liu, *Wisdom of the Insider?* (SSRN 6678718) | **abstract** / secondary | [note](ssrn6678718-wisdom-of-the-insider.md) |
| Lanker, *Legal Ground Truth and Detection of Informed Trading* (SSRN 7455078) | **abstract** | [note](ssrn7455078-wisdom-of-insiders-legal-ground-truth.md) |

### Microstructure, liquidity, manipulation and wash trading
| Source | Read | Note |
| --- | --- | --- |
| Dubach, *Anatomy of a Decentralized Prediction Market* (2604.24366) | full | [note](2604.24366-anatomy-order-book-microstructure.md) |
| Tsang & Yang, *Anatomy of a Blockchain Prediction Market: 2024 election* (2603.03136 v3) | full | [note](2603.03136-anatomy-2024-election.md) |
| IMDEA/Lund, *Opening Wide, Moving Fast: opening spreads* (2026) | full | [note](imdea-2026-opening-spreads.md) |
| Sirolly, Ma, Kanoria & Sethi, *Network-Based Detection of Wash Trading* (SSRN 5714122) | full (Jan 2026 version) | [note](ssrn5714122-network-wash-trading.md) |
| Dai, Jia & Yu, *Settlement Manipulation in Prediction Markets* (2606.31675) | full | [note](2606.31675-settlement-manipulation.md) |
| Ibrahim & Zaki, *Price Dislocations, News Citations, Epistemic Leverage* (2609.06005) | full | [note](2609.06005-dislocations-news-leverage.md) |

### Pricing, calibration and accuracy
| Source | Read | Note |
| --- | --- | --- |
| Cardozo & Rivero-Wildemauwe, *Favorite–Longshot Bias on Polymarket* (2609.12878) | full | [note](2609.12878-favorite-longshot-bias.md) |
| Fan, Sun & Zhao, *Whether Is Not When* (2610.36639) | full | [note](2610.36639-whether-is-not-when.md) |
| Clinton & Huang, *Accuracy and Efficiency of $2.4B in the 2024 Election* (SocArXiv d5yx2 v5) | full v5 | [note](socarxiv-d5yx2-accuracy-efficiency-2024.md) |
| Zitzewitz, *Are Prediction Markets Politically Biased?* (NBER w35846) | full | [note](nber-w35846-politically-biased.md) |
| Tsang & Yang, *Price discovery around 2024 political shocks* (2603.03152 v4) | full | [note](2603.03152-political-shocks-price-discovery.md) |
| Cutting et al., *Betting Markets vs Polling* (2507.08921) | full | [note](2507.08921-betting-markets-vs-polling.md) |
| Walker, *The Price is (Almost) Right* (Princeton thesis, 2026) | **abstract** (restricted) | [note](princeton-thesis-calibration.md) |

### Arbitrage and coherence
| Source | Read | Note |
| --- | --- | --- |
| Saguillo et al., *Unravelling the Probabilistic Forest* (2508.03474) | full | [note](2508.03474-arbitrage-probabilistic-forest.md) |
| Gebele, Mutzel & Matthes, *Executable Arbitrage in NegRisk markets* (2608.00666) | full | [note](2608.00666-executable-arbitrage-negrisk.md) |
| Cheng, Yang & Zou, *Arbitrage in Polymarket NBA markets* (2605.00864) | full | [note](2605.00864-nba-arbitrage.md) |

### Resolution and oracle
| Source | Read | Note |
| --- | --- | --- |
| Wen, Zhou & Huang, *LLMs and UMA dispute arbitration* (2604.15674) | full | [note](2604.15674-llm-uma-dispute-arbitration.md) |

**Version drift.** Several sources changed their headline results between versions:
- Clinton & Huang v1 → v5;
- Tsang & Yang 2603.03136 v2 → v3, and 2603.03152 v2 → v4;
- Nechepurenko v1 → v2;
- Dubach v1 → v2.

Always cite the version.

## Datasets and code referenced

| Resource | What | Source |
| --- | --- | --- |
| HF `TimeSeventeen/Polymarket-v1`, `-v2` | V1/V2 fills, CTF lifecycle, `p_event`/`D` (**in our catalog**) | 2606.04217 |
| HF `vgregoire/polymarket-users` v1.3 | 588M de-duplicated trades, wallet daily PnL panels, bars | SSRN 6443103 |
| HF `SII-WANGZJ/Polymarket_data` (Wang et al. 2026) | 568.6M trades, 734,790 markets, through 2026-03-31 | IMDEA, 2608.00666, HEC thesis |
| HF `vpcapitano/polymarket-genesis-liquidity`; github.com/vpercap-rg/polymarket-genesis-liquidity | Dome order books, 2025-10-14 → 2026-04-28 (the service is discontinued) | IMDEA |
| github.com/gregyoung14/openmarket (v0.5.2); HF `gregyoung14/openmarket-btc-polymarket`, `-models` | Polymarket BTC 15-min markets + Binance ticks, 727M rows | 2607.26245 |
| github.com/philippdubach/polymarket-microstructure (Zenodo 10.5281/zenodo.19811426) | Panel parquets and code; the WebSocket archive is available on request | 2604.24366 |
| github.com/hazemibrahim97/epistemic-leverage-replication | News-citation gold labels and the pre-registered grid | 2609.06005 |
| github.com/ForesightFlow/event-linked-perps | Fill-cohort code | 2605.11640 |
| pmxt Orderbook Archive v2 | L2 order books (only from April 2026) | 2608.00666, 2605.11640 |
| Goldsky subgraphs | Conversions, splits, merges | 2608.00666 |
| HEC thesis, Bock & Guenthoer (2026), vernimmen.com/ftp/mif2026_rp_bock_guenthoer.pdf | The most detailed open specification of the insider screens; compares them on 5 documented cases | Mitts–Ofir, Liu |

## Cross-paper facts

### Data and accounting

1. **Raw `OrderFilled` double-counts every match.**
   - Each match emits one row per maker order, plus a taker-side row whose `taker` is
     the exchange contract (`0x4bfb41d5…`, `0xc5d563a3…`).
   - The initiator of the match is the fill where the exchange contract is the taker.
     This equals `OrdersMatched.takerOrderMaker` and agrees with the price-change sign
     97.9% of the time.
   - Dropping these rows halves volume. The V1 "relayer filter" is actually this
     de-duplication.
   - Sources: 2603.03136, 2603.03152, SSRN 6443103 (App. A.1), 2606.04217, 2604.24366.
2. **Naive volume overstates turnover.** Naive volume = exchange volume + mint/burn
   volume, and turnover is a median 3.08× smaller across election markets. Volume
   conventions differ by source: USDC (Qin), shares (Akey's $67B), or the taker's shares
   (Polymarket's display). Sources: 2603.03136, SSRN 6443103.
3. **Inferring trade direction without the chain fails.**
   - The tick rule gets 49.8% of trades right and bulk volume classification 50.5% on V1
     (2606.04217).
   - Direction inferred from the public feed matches the chain in about 60% of buckets,
     and that comparison is itself contaminated by fact 1 (2604.24366).
   - Use the on-chain initiator rule.
4. **Metadata is unreliable.**
   - The integer `outcome` field, `end_date` for NegRisk markets, and some Gamma token
     IDs and close times are wrong.
   - Re-derive resolutions from `ConditionResolution` logs, or use the CLOB simplified
     winner flag.
   - Sources: SSRN 5714122, SSRN 6443103, the HEC thesis.
5. **Fees and regimes vary by market and date.**
   - Taker fees reached crypto first, then sports from 2026-02-18, then Fee Structure V2
     on 2026-03-30.
   - The CLOB V2 contract cutover was around 2026-04-28.
   - 5- and 15-minute crypto markets settle on Chainlink Data Streams.
   - Sources disagree on the dates, so use the per-market `taker_base_fee` and
     `fee_usdc` fields.
6. **Single-condition YES/NO "arbitrage" is an artefact.** The YES and NO books are
   exact mirrors: 308M WebSocket messages showed only 20 glitches. Real arbitrage is the
   NegRisk Σ-condition, where the NO side converts immediately and the YES side waits for
   settlement.
   - Polled REST snapshots miss short gaps and inflate their duration. Use WebSocket data
     with both exchange and ingestion timestamps.
   - Sources: 2608.00666, 2605.00864.

### Wash trading and entities

7. **Wash-trading estimates vary hugely by method and unit:**

   | Measure | Estimate | Source |
   | --- | --- | --- |
   | Network score | 24.2% of share volume (peak ~60% in Dec 2024; Sports 45%) | SSRN 5714122 |
   | Network-filtered shares | 13.8% | 2610.36639 |
   | Counterparty HHI ≥ 0.5 | 3.1–3.9% of dollars | SSRN 6443103, 2609.12878 |
   | Self-counterparty | ~1% median | 2604.24366 |

8. **Wallets are not people.**
   - Sybil clusters linked by withdrawal or funding address exist (Liu; Sirolly found
     a cluster of 109k wallets).
   - Clustering must exclude bridges, routers and exchanges.
   - Per-wallet z-scores are defeated by splitting positions across wallets.

### Participants

9. **Profits are extremely concentrated, and they go to liquidity providers.**
   - The top 1% take 76.5% (SSRN 6443103), 80% (2610.36639) and 89.2% in 2026
     (2610.34754).
   - About 69% of wallets lose.
   - Maker share is the strongest predictor of profit: +9 pp per SD (SSRN 6443103).
     Timing-skilled accounts are 62% maker (2610.36639).
   - The top 1% of makers supply 84% of maker volume (2606.04217).
10. **Skill estimates diverge by method:** 3.14% of accounts (random flips; SSRN 6617059),
    29.3% (mixture model, ≈0.3¢ edge; SSRN 6443103), and 7–10% for timing skill
    (2610.36639). Persistence is modest, and trades in the same market share one outcome,
    so tests must cluster by market.
11. **Copy trading is costly.** Followers pay about +1¢ per share more than the source,
    and only 1.45–9.8% of signals fill (2610.34754). Insiders enter far below later
    traders: 46¢ vs 77¢ (SSRN 7455078).
12. **Insider screens mostly select on the outcome.** They use realised profit or
    winning (Mitts–Ofir, Liu), so they are retrospective. Only Lanker's uses
    pre-resolution features, and its labels are tiny and biased. No public labelled
    benchmark exists.

### Pricing

13. **The favorite–longshot bias is broad and the market is slightly compressed toward
    0.5:**
    - recalibration slope 1.11 on Polymarket (Princeton thesis);
    - slope 1.40 in historical election markets (NBER w35846);
    - interior errors of −5.9 pp at 35¢ and +7.3 pp at 60¢ (2609.12878).

    Results swing by aggregation unit and cutoff (2609.12878), and listing mix drives
    headline accuracy (SocArXiv v5: 86.4% overall, 55.2% for competitive contracts).
14. **Prices know *whether* far better than *when*.** Deadline distance dominates prices
    (2610.36639).
15. **Minting lets heavy one-sided flow clear without moving price.** 66% of Trump YES
    supply at the Biden withdrawal was newly minted (2603.03152).
16. **Execution costs and price-impact benchmarks:**

    | Measure | Value | Source |
    | --- | --- | --- |
    | Opening spread | 3¢ (sports) to 21¢ | IMDEA |
    | First-minute taker cost | 12–16¢/share outside sports | IMDEA |
    | 91.9% of spreads | one tick (BTC 15-min markets) | 2607.26245 |
    | Cost to move 5pp | ~$22k median | 2609.06005 |
    | Kyle's λ, Trump YES | 0.587 → 0.022 log-odds per $1M | 2603.03136 |
    | Permanent share of price impact | ~45% | 2606.04217 |

17. **Short-horizon markets are a separate world.**
    - BTC 15-minute quotes follow Binance after a median of about 347 ms.
    - A 43-feature model does not beat the Polymarket mid out of sample (2607.26245).
    - Binance order flow in the final 10 seconds rose about 50% after the 5-minute
      contract launched, which suggests settlement manipulation (2606.31675).

### Arbitrage and resolution

18. **Arbitrage dollar figures depend on the definition:** $39.6M (VWAP-based, 2508.03474)
    vs $0.29M (mechanism-linked, 2608.00666) on the same window. Profit per conversion
    fell from about $1 to $0.08 between 2024 and 2026.
19. **Resolution disputes are measurable.**
    - Gamma `umaResolutionStatuses` flags 558 disputed markets.
    - LLMs match about 89% of post-dispute outcomes but cannot predict which markets will
      be disputed (2604.15674).
    - On-chain UMA events are needed to tell DVM votes from re-proposals.

## Research map: topics and open directions

Each line is a candidate workstream. The notes give the details.

### A. Data foundation
- **Canonical fill table** for V1, NegRisk and V2:
  - drop exchange-as-taker rows and take the initiator from them;
  - label each fill as mint, merge or transfer;
  - fold NO into the YES axis;
  - use exact block times.

  [2603.03136, 2606.04217, 2604.24366, 2605.11640]
- **Position and PnL reconstruction** from fills plus split, merge, convert, redeem and
  transfer events, so that returns are realised rather than mark-to-model. [2609.12878,
  SSRN 6443103, 2610.34754]
- **Resolution table** from on-chain `ConditionResolution` and UMA events, with dispute
  flags. [SSRN 5714122, 2604.15674]
- **Fee and regime calendar** checked against per-market fee fields. [SSRN 6443103,
  2606.04217]
- **Wash-trading library on one dataset:** network score, HHI, self-trades, flip pairs.
  [SSRN 5714122, 2604.24366]
- **Entity resolution:** proxy/Safe → EOA, the funding and withdrawal graph, with
  exclusions for bridges and exchanges. [SSRN 6678718, SSRN 5714122]
- **Live WebSocket capture** of order books, `price_change` and trades, with exchange
  and ingestion timestamps. [2604.24366, 2608.00666, 2607.26245]
- **Reconcile external datasets** with our catalog: `polymarket-users`,
  `SII-WANGZJ/Polymarket_data`, OpenMarket.

### B. Market quality and microstructure
- **Spreads normalised to ticks**, plus opening-phase spread and cost dynamics. [2604.24366,
  IMDEA]
- **Turnover-corrected volume and Kyle's λ** by market age. [2603.03136]
- **Natural experiments:**
  - the V1→V2 cutover;
  - fee roll-outs within markets (difference-in-differences with pre-trend checks).

  [2606.04217, 2604.24366]
- **Maker concentration over time**, and the effect of liquidity rewards. [2604.24366,
  2606.04217]
- **Short-horizon crypto markets:**
  - latency to Binance and Chainlink;
  - settlement-window manipulation monitors, with placebos.

  [2607.26245, 2606.31675]

### C. Pricing, calibration and information
- **Calibration library** weighted by trade, dollar, market, event and time sample, with
  horizon surfaces, cluster-robust inference, and slope and intercept. [2609.12878,
  Princeton, SocArXiv d5yx2]
- **Accuracy reporting** with balanced cohorts: competitive vs lopsided contracts, and
  contract type. [SocArXiv d5yx2]
- **Deadline ladders:** isotonic event-date distributions, whether/when scoring, implied
  dates. [2610.36639]
- **Partisan and demographic bias tests** on Polymarket political markets. [NBER w35846]
- **Shock event studies:** who supplies the response, and minting versus price impact.
  [2603.03152]
- **Cross-venue lead–lag** with Kalshi, sportsbooks and Binance, using synchronised
  books. [SocArXiv d5yx2, 2607.26245]

### D. Participants
- **Profit decomposition:** maker vs taker, tick-spread rents, persistence, dropout.
  [SSRN 6443103, SSRN 6617059]
- **Skill tests:** random-flip null, mixture models, dependence-aware FDR, clustering by
  market. [SSRN 6617059, 2610.34754, 2610.36639]
- **Smart-money identification** with an honest copy-trading simulation (slippage, fill
  rate). [2610.34754]
- **Informed-trading screens** on pre-resolution features only, benchmarked against
  outcome-based screens and documented cases. [SSRN 7455078, SSRN 6426778, SSRN 6678718]
- **Behaviour of the typical user:** activity, trade size, PnL distribution. [Pew]

### E. Arbitrage and coherence
- **Quote-level NegRisk Σ monitor:** the NO side converts now, the YES side waits for
  settlement. Track duration and depth, and discount for capital lock-up. [2608.00666]
- **Combinatorial and ladder coherence** (strike and bracket ladders, moneyline vs
  spread), measured at executable depth. [2508.03474, 2605.00864, 2610.36639]
- **Strict classification of realised arbitrage:** atomic vs inventory-based. [2508.03474,
  2608.00666]

### F. Information ecosystem and resolution
- **News ↔ market linkage**, and calibration of cited vs uncited markets. [2609.06005]
- **UMA dispute dataset:** dispute prediction and the economics of voters. [2604.15674]

### G. Products
- **Dashboards:** live calibration, overround, ladder and market quality. [2609.12878,
  2610.36639, 2604.24366]
- **Alerts:** coherence and dislocation feeds, and informed-flow candidates using
  pre-resolution features. [2608.00666, 2609.06005, SSRN 7455078]
- **Public panels:** corrected volume, microstructure and participant cohorts.
  [2603.03136, 2605.11640]
