# Prediction Market Accuracy: Crowd Wisdom or Informed Minority?

- **SSRN:** [6617059](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6617059).
  - Posted 20 Apr 2026, revised 25 Apr 2026. One listing gives 49 pp.
  - A later version, revised 25 Jun 2026, is listed at 78 pp.
  - Working paper, not peer-reviewed.
- **Authors:** Roberto Gómez-Cram, Yunhan Guo, Howard Kung (London Business School) and Theis
  Ingerslev Jensen (Yale SOM).
- **Related:** the same team's "Financial Prediction Markets: A New Measure of Earnings
  Expectations" (SSRN 5933475).
- **Code/data:** none released. A secondary source states that labels, code and category splits
  are unreleased.
- **Read: full text NOT obtained.** SSRN returned 403 to both the page and the PDF, and no
  author-hosted or seminar PDF was found. This note is assembled from secondary sources, each
  claim tagged:
  - **[Y]** Yale Insights article;
  - **[B]** SSRN blog "A Closer Look", 29 Jun 2026;
  - **[TB]** The Block, 26 Apr 2026;
  - **[BC]** Bitcoin.com News, 26 Apr 2026;
  - **[CXO]** CXO Advisory, 13 May 2026;
  - **[CR]** CRUCIAL Lab Substack;
  - **[AX]** arXiv 2605.02287 v2, a critical methods paper that describes GC in detail;
  - **[RQ]** GitHub replication `qaviinan/polymarket-minority`;
  - **[AK]** Akey et al. (SSRN 6443103), which summarises GC.
- Numbers may mix the April and June versions. Treat every figure as **unverified against the
  paper**.

## Question

Is Polymarket's accuracy produced by many diverse traders ("wisdom of crowds"), by insiders,
or by a small minority of persistently skilled traders? [Y, B, TB]

## Data

**Coverage.** The complete Polymarket transaction history, Jan 2023 – Dec 2025. [CR, TB, AX]
- Propositions created after early January 2023 and resolved by the end of December 2025
  [CXO].
- 1.72M accounts, 98,906 events, 210,322 markets, **$13.76B** volume [Y, BC, TB, AX].
- Accounts with at least 10 trades [CXO]. [AX] says the main classification uses accounts
  trading ≥10 *events*.

**Growth.** Monthly volume rose from $3.3M (Dec 2023) to $1.98B (Dec 2025); active accounts
from about 1,600 to 519,000+ [BC].

**Volume convention.**
- *Reviewer note:* $13.76B is very close to Qin & Yang's de-duplicated V1 USDC volume for
  2023–2025, which is $13.64B.
- That suggests GC use **USDC notional after removing the double-counted leg**.
- Akey's $67B is share volume over a longer window.

**Category mix.** Sports is 42.05% of markets and 35.37% of volume; Politics 7.52% / 35.85%;
Crypto 36.96% / 18.73% [AX]. It is unclear whether these are GC's figures or AX's own.

**Not available.** The source of trades (subgraph or RPC), direction construction, the
de-duplication method and the market-maker definition are unknown. [CXO] says market makers
are "liquidity providers using limit orders".

## Methods

**Sign-randomisation skill test** [Y, TB, AX].
- Each account's realised trade sequence (markets, timing, prices, sizes) is held fixed. Only
  buy versus sell is randomised, at the **event level** [AX], 10,000 times.
- The account's actual PnL is compared with this null distribution.

**Groups** [AX].

| Group | Rule |
| --- | --- |
| Skilled winners | p < 0.05 |
| Unskilled losers | p > 0.95 |
| Lucky winners | Positive PnL, not significant |
| Unlucky losers | Negative PnL, not significant |
| Market makers | Classified separately by liquidity provision |

**Circularity / persistence check** [Y].
- Split each trader's events at random into halves, classify on one half, and test on the
  other.
- This is compared with a mutual-fund analogue [BC], or with equity studies [AX].

**Information content.**
- Group-level net order flow (imbalance) as a predictor of next-period price changes and of
  final outcomes [TB, BC, AX].
- Pricing-error tests [AX].

**News tests.** Order imbalance by group around FOMC announcements and earnings releases [Y,
CR, BC].

**Behaviour tests** [B]:
- speed of reaction to public news;
- trading against the favourite–longshot bias;
- eliminating law-of-one-price violations, which the SSRN abstract also mentions per a search
  summary.

**Insider heuristic** [AX, CR], separate from the skill test.
- Account created ≤7 days before the event.
- Trades only that event, with ≥$1,000 volume and ≥$1,000 realised profit.
- No trades after resolution.

**Case study.** "Maduro out by January 31, 2026?" (App. B, Table B.1) [AX].

## Findings

**Group sizes** [AX].

| Group | Accounts | Share |
| --- | ---: | ---: |
| Skilled winners | 54,477 | **3.14%** |
| Unskilled losers | 110,703 | 6.4% |
| Lucky winners | — | 29.0% |
| Unlucky losers | — | 61.4% |
| Market makers | — | 0.1% |

[Y, CXO, TB] report the same skilled share. [CR] instead says "over 2% of accounts made profits
that only 0.5% would be expected to make by chance", which possibly reflects another version
or threshold.

**Who gains** [Y, TB, BC].
- Skilled winners plus market makers are **under 3.5% of accounts and take more than 30% of
  gains**.
- Lucky winners take the remaining **69%** of gains.
- Unlucky and unskilled losers (about 67% of accounts) absorb all aggregate losses.

**Raw PnL is a poor guide to skill** [TB].
- Top earners overlap only **12%** with the skilled group.
- About 60% of lucky winners revert to losses in held-out events.

**Persistence.**
- 44% of skilled accounts in the training half stay skilled in the test half [Y, TB, BC, AX].
- Unskilled losers stay unskilled 51% of the time [BC].
- The mutual-fund comparison is about 10% [Y, BC].

**Skilled traders.** They trade on average 79 markets each [BC].

**Order flow.**
- Skilled order flow predicts next-period price changes and final outcomes "at statistically
  significant levels" [TB, BC].
- A 1-pp rise in skilled net buying goes with an **8 bp** higher probability of the correct
  final outcome [BC].
- Lucky winners' flow has no predictive power [BC].
- [CR] says only the skilled group's trades predicted future prices.

**News.** Only skilled traders shift their imbalance toward the FOMC or earnings surprise
within a narrow window [Y, BC, CR]. The window length is not reported in the sources.

**Insiders** [AX, TB, BC, CR].
- 1,950 accounts are flagged, just over 0.1% of accounts [CR]. Mean profit $15,012.92,
  median $2,758.29.
- Their imbalance predicts next-period price changes (t = 2.54) and outcomes (t = 8.65), but
  does not significantly reduce absolute pricing error [AX].
- Per dollar, they move prices about **7–12× more** than skilled traders [TB].
- They are "sporadic, small", too concentrated in isolated events to drive accuracy [Y, TB].

**Maduro case** [AX, TB, BC].
- Three accounts opened between 27 Dec and 3 Jan.

| Account | PnL |
| --- | ---: |
| 0x31a…b8ed9 | $409,882.03 |
| 0x6ba…a94c5 | $141,619.92 |
| 0xa72…febd4 | $74,982.34 |
| **Total** | **$626,484.29** |

- Press coverage reports "more than $630,000".
- All three are classified as **lucky winners**, because a single informed trade cannot pass
  the sign test [AX].
- The lead account's figure matches the roughly $409,881 in the CFTC v. Van Dyke complaint.
  This is a consistency check, not an identity claim [AX].

**Conclusion** [Y]: "The remaining majority does not produce accuracy; rather, it funds it."

**Corroboration from Akey et al.** [AK] summarises GC as finding a skilled minority that is
"not systematically in possession of inside information". Akey et al. stress liquidity
provision and selection more.

## Reusable definitions

- Event-level sign randomisation of an account's realised trades, 10,000 draws, giving
  per-account p-values.
- The four-way grouping plus market makers.
- The single-event insider heuristic: created ≤7 days before, one event only, ≥$1k volume and
  ≥$1k profit, dormant after resolution.
- Persistence on a random split of events into halves.

## Stated limitations (and future work)

Known from secondary sources only:
- Accounts are anonymous, and one person may run many.
- The sign test cannot detect one-shot informed traders, which is why there is a separate
  heuristic [AX].
- Accuracy depends on skilled traders continuing to participate and on there being enough
  counterparties.
- Hedging demand could drive prices away from probabilities. A follow-up paper on hedging
  capacity is announced [B].

## Critical assessment

**Full text unread.** Every number here is second-hand, and sources disagree:
- 3.14% at p < 0.05 [AX] versus ">2% vs 0.5% expected by chance" [CR];
- $626k versus ">$630k" for the Maduro case.

**Multiple testing.** If p-values were uniform under the null, about 5% of classified accounts
would land at p < 0.05 by chance.
- 3.14% is of *all* 1.72M accounts. Back-calculated, 54,477 / 0.0314 ≈ 1.73M. But
  classification applies only to accounts with ≥10 events, so the share among *classified*
  accounts is higher.
- Whether the count exceeds the false-discovery expectation cannot be checked without the
  paper.
- [RQ] reproduces 484 / 11,465 = 4.2% after Benjamini–Hochberg on one month of 2024 data, with
  539 expected by chance before correction.

**Price-adjusted null.**
- [RQ] says most "skilled" wallets buy favourites at ≥90¢, and only 8 wallets beat a
  price-adjusted null.
- *Caveat:* [RQ]'s statistic is a win/loss sign test, which may not be GC's PnL-based
  randomisation. Under PnL-weighted sign flips, a fair favourite-buyer is centred at zero. So
  this critique may not transfer.
- Still, conditioning on realised outcomes and flipping at the event level makes the null
  "direction independent of outcome". Its power and size depend on clustering by event.

**Insider heuristic.**
- It is an upper bound on lifecycle-matching accounts, not an insider count. Sybil farms and
  viral-event newcomers fit the same pattern [AX].
- Its precision has not been validated.

**"Accuracy comes from the minority."** This rests on order-flow predictability. Without the
specifications (horizon, controls for price level and maker flow), it cannot be judged. A
related paper (2610.36639) finds group order flow adds nothing beyond price for event timing.

**Selection.** Resolved-by-Dec-2025 markets created after Jan 2023 exclude long-dated markets
and any V2 trading.

**Trust.**

| Claim | Trust | Reason |
| --- | --- | --- |
| Small skilled minority (~3%) | **Medium** | Consistent across sources; null and FDR handling unseen |
| Minority + makers take >30% of gains | **Medium** | Widely reported; definitions unseen |
| 44% persistence | **Medium** | Split-sample is sound; the mutual-fund comparison is apples-to-oranges |
| Skilled flow predicts outcomes | **Low-medium** | Specification unseen |
| Insiders are small and sporadic | **Medium** | Heuristic upper bound, but the magnitudes are plausible and agree with Akey |
| Maduro accounts | **High** | Specific on-chain figures matching the CFTC filing |

## Directions it opens

**Re-implement the sign-randomisation test on our own fills.**
- PnL-weighted flips at the event level, plus a price-adjusted null.
- Benjamini–Hochberg and Storey FDR, plus the Barras et al. skilled-share estimator.
- Compare the resulting labels with Akey's mixture model, 2610.36639's sign flips and RQ's
  results. Publish a wallet-skill table with uncertainty.

**Order-flow information tests.** Group-level imbalance versus future mid (from the WebSocket
book) and outcomes, controlling for price, maker flow and horizon. Split maker versus taker
skill.

**News-reaction tests around scheduled events.** FOMC, CPI and earnings markets, measuring
latency from the release timestamp to the first skilled fill. This needs exchange timestamps
and the live feed.

**Insider-screen product.** The ≤7-day, single-event, conviction heuristic plus funding-graph
links. Validate against CFTC cases (Van Dyke, Spagnuolo), and measure false positives on viral
events.

**Version tracking.** Obtain the June 78-page version and update this note. Its full text is
the main gap.
