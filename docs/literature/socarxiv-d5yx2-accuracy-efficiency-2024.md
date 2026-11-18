# Prediction Markets? The Accuracy and Efficiency of Political Prediction Markets in the 2024 Presidential Election

- **Source:** SocArXiv [d5yx2](https://osf.io/preprints/socarxiv/d5yx2), DOI 10.31235/osf.io/d5yx2. RePEc lists v1 as [osf/socarx/d5yx2_v1](https://ideas.repec.org/p/osf/socarx/d5yx2_v1.html).
- **Versions and titles:**
  - OSF v1 (1 Dec 2025), v2 (8 Dec), v3 (9 Dec): "...The Accuracy and Efficiency of $2.4 Billion in the 2024 Presidential Election".
  - **OSF v5 (10 Jun 2026)**, retitled "...of Political Prediction Markets in the 2024 Presidential Election". The paper's own changelog calls this "Version 4 (June 2026)" and describes it as "a dramatic update"; OSF numbering differs. This is the current version.
  - v5 is about 39 pp of text plus a supplemental appendix A–J (80 PDF pages in all).
- **Authors:** Joshua D. Clinton (Vanderbilt, Political Science, Winkelried Chair); TzuFeng Huang (Vanderbilt, PhD student).
- **Code/data:** "fully reproducible by documented scripts", but no repository URL is given. The appendix names output CSVs such as `numbers_cohort_composition.csv`.
- **Read:** **the full text of v5** (pypdf, all pages; lines holding only figure-axis numbers were dropped). For **v1** only the abstract and spot sections were read, enough to document how the conclusions changed. Figures are images, so their captions and the numbers in the text were used.

## Question

Did 2024 US political prediction markets (IEM, PredictIt, Kalshi, Polymarket) aggregate information **accurately** (the favoured outcome happens), with good **calibration** (price ≈ resolution frequency), and **efficiently** (identical contracts priced alike across venues, daily changes unpredictable, coherent Trump/Harris moves, no cross-venue arbitrage)? The question is set against media reliance on prices and the "French whale" episode.

## Data

**Window.** 1 Sep → 4 Nov 2024 ("final nine weeks"). v1 used the final 5 weeks from 1 Oct.

**Sample.** Markets traded at least once in the window with an observed outcome. Non-election contracts must resolve by 20 Jan 2025.
- **2,170 scored contracts** (excluding IEM): Kalshi 550, Polymarket 1,587, PredictIt 33. IEM's 4 contracts are context only.
- **Types:** winner 610, margin 413, other 434, speech 713 (speech is entirely Polymarket and makes up 44.9% of its book).
- v1 had more than 2,500 markets, with 1,956 on Polymarket.

**Exclusions.**
- 542 Polymarket speech contracts that only traded on or after their event, so they cannot be scored.
- 15 non-speech "X-before-election" Polymarket contracts (about $86M volume) whose outcome was settled mid-campaign.
- 24 Polymarket multi-outcome markets in the eve cross-section (34 in the daily panel). The paper says it cannot split them into clean binaries; the grouped "Which party wins" market is one of them.
- 55 Kalshi contracts removed by a snapshot-validity guard. With them included, accuracy would be 96.5%, against 88.5% for Kalshi Election-Day-or-later contracts.
- PredictIt coverage is limited by its 90-day API window: 7 events and 33 contracts, 26 of them in two multi-outcome fields. Three economically identical Harris-wins contracts are each counted.

**Prices.**
- **Polymarket:** CLOB API daily close, the end-of-day bid-ask midpoint, or the last trade if the spread exceeds $0.10. v1 instead used on-chain fill ratios (`takerAmountFilled / makerAmountFilled`) with outcomes matched by regex on the title.
- **Kalshi:** last trade of the day; no value on days without trades.
- **PredictIt:** EST-based daily close (4–5 h behind UTC).
- One side (YES) per binary.

**Snapshot.** Scored at min(4 Nov, resolution date − 1):
- 1,108 contracts are scored at the 4 Nov close;
- 1,062 earlier-resolving contracts are scored the day before their own event (945 Polymarket, 117 Kalshi).

**Resolutions.** Official binary resolutions from each venue's API (v1 used hand coding).

**Volume** (no longer summed across venues):
- Kalshi: about 320M contracts on the 550 markets (about $320M settlement notional), of which 171.7M were in presidential winner-take-all contracts and 22.0M in popular-vote margin, 1 Oct–4 Nov.
- Polymarket: about $6.0B platform-reported lifetime volume on the 1,587 markets. The paper notes this overstates turnover because of minting and burning (Tsang & Yang).
- PredictIt: $5.9M in yes-side premium. IEM: about $37k.
- Fees: Polymarket 0, Kalshi ≈ 0.07·P(1−P), PredictIt 10% of profit plus 5% on withdrawal.

## Methods

- **Accuracy:** beat a coin flip, i.e. strict log-skill > 0, where `A_log = 1 − LogLoss/LogLoss_0.5`. Brier skill `1 − (p−y)²/0.25` is used as a check.
  - Wilson 95% CIs treat contracts as independent; the authors flag them as "descriptive".
  - Splits by venue, type, and eve-price band (lopsided < 0.2 or > 0.8; lean; competitive 0.4–0.6).
  - Accuracy over time by first-close band. A **balanced cohort** of 281 winner/margin markets active from 1 Sep to Election Day controls for listing composition. Accuracy is also given at 1 week, 2 weeks, 30 days and 60 days out.
- **Calibration:** a decile reliability diagram with Wilson CIs, n-weighted ECE, mean bias, and Brier reliability.
- **Cross-venue co-movement:** correlations of daily closing levels and of 1- to 7-day changes for the most similar national winner contracts, and for Kalshi vs Polymarket popular-vote-margin brackets (n = 28 days for 3–4%).
- **Random walk:** per-contract `ΔP_t = ρ·ΔP_{t−1} + ε` for contracts with ≥ 10 daily observations (1,046 markets, speech excluded), counting the share with ρ insignificant, negative or positive. Small-T downward bias −(1+3ρ)/T is noted.
- **Common daily shocks:** pooled first differences `ΔP_it = α + ι_t + γ_i + ε` for 11 Trump-side and 12 Harris-side national contracts, one day dummy at a time, with a 3×3 cross-tab of significant signs. Appendix H uses a lagged-level variant (with a Nickell-bias caveat).
- **Arbitrage:** the cheapest daily close of Trump plus the cheapest daily close of Harris across Kalshi and Polymarket, after fees, compared with $1.

## Findings

**Accuracy on the eve.** **86.4% beat a coin flip [84.9, 87.7]**, n = 2,170.

| Split | Share beating a coin flip [95% CI] |
| --- | --- |
| Kalshi | 89.8% [87.0, 92.1] |
| Polymarket | 85.3% [83.4, 86.9] |
| PredictIt | 81.8% [65.6, 91.4] |
| Winner | 93.4% |
| Margin | 87.9% |
| Other | 92.9% |
| Speech | 75.5% |
| **Lopsided** (n = 1,434) | **96.2%** |
| Lean (n = 486) | 73.3% |
| **Competitive** (n = 250) | **55.2% [49.0, 61.2]** |

- 28 markets (1.3%) have log-skill below −2.
- **Composition explains the venue gaps.**
  - Polymarket's lower rate comes from speech contracts. Across margin and other contracts the venues are about equal: margin 87.8 / 87.6 / 93.8%; other 92.5 / 93.1%.
  - Polymarket's lead in winner contracts (97.5% vs Kalshi 88.8%) reflects listings: **88% of Polymarket winner contracts were lopsided, against 58% on Kalshi**.
  - PredictIt winner contracts score 68.8% because three equivalent Harris contracts closed near $0.52 and lost.
- **v1 had said** 93% PredictIt, 78% Kalshi, 67% Polymarket. Those numbers were superseded after the snapshot rule, data source and resolutions were changed.

**Over time.** 77% of winner/margin contracts opened lopsided. The apparent late-campaign decline in pooled accuracy is compositional: the median market first traded on 8 Oct, competitive markets on 18 Oct, lean on 24 Oct.
- In the balanced cohort, lopsided log-skill is 0.92 before 7 Oct and 0.93 after. The full sample falls from 0.90 to 0.83 over the same date.
- National presidential markets (App. F) do "not necessarily converge" in accuracy over time.

**Calibration (Fig. 2).** **ECE 0.032; mean price exceeds the resolution rate by 0.028; Brier reliability 0.0022 out of a total Brier of 0.096.**
- Well calibrated above $0.60. For example, 128 contracts in $0.80–0.90 had a mean price of 0.847 and 85.2% resolved YES.
- **Mild longshot bias below $0.60:** the $0.10–0.20 bin has mean price 0.149 but only 7.1% resolved YES; the $0.30–0.40 bin had 21.8% resolve YES.
- The lowest decile holds 880 markets (41%): 33% winner, 31% other, 25% margin, 11% speech.

**Cross-venue co-movement (1 Oct–4 Nov, Trump winner contracts).**
- Level correlations are about **0.81–0.94** (the abstract says 0.77–0.96).
- Daily-change correlations: **Polymarket–Kalshi 0.63** (Harris 0.72); with PredictIt about 0.1–0.3.
  - Dropping 3 Nov (the Selzer Iowa poll; Kalshi Trump −7¢) raises Kalshi–PredictIt from 0.12 to 0.50 and Polymarket–PredictIt from 0.27 to 0.40. Polymarket–Kalshi is unchanged.
- 7-day change correlations: Polymarket–Kalshi 0.91, PredictIt–Kalshi 0.77, PredictIt–Polymarket 0.74.
- Trump led on Kalshi every day except 5–7 Oct and 3 Nov (tied on 8 and 10 Oct). PredictIt had Harris leading at the start and end. The IEM popular-vote market favoured Harris throughout, but Trump won the popular vote by 1.5 pts.
- **3–4% popular-vote margin, Kalshi vs Polymarket:** levels r = 0.87 (Dem) and 0.76 (GOP); daily changes 0.37 and 0.27. Dem vs GOP brackets within a venue: r = −0.84 (Polymarket) and −0.83 (Kalshi); across venues −0.81 and −0.87. Alignment is weaker for tail brackets.

**Random walk (Table 4).** Columns: n, mean ρ, insignificant, negative, positive.

| Type | n | Mean ρ | Insignificant | Negative | Positive |
| --- | ---: | ---: | ---: | ---: | ---: |
| Winner | 479 | −0.161 | **76.2%** | **21.8%** | 2.0% |
| Margin | 331 | −0.110 | 77.9% | 19.0% | 3.0% |
| Other | 236 | −0.142 | 73.2% | 21.3% | 5.5% |

- Speech contracts have a median life of 3 days (IQR 2–4).
- **v1 had claimed** that 58.3% of 182 national presidential markets had significantly negative autocorrelation. That claim was reversed.

**Common daily shocks (Table 5, first differences, 65 days).**
- Daily Trump and Harris shocks correlate at −0.876.
- 9 days with both sides significant, **all opposite-signed**; 12 days with one side only; 44 days with neither; **0 days with both moving the same way**. About 3 significant days per candidate are expected by chance.
- **The common day factor explains R² 0.265 (Trump) and 0.249 (Harris)**; contract fixed effects add 0.003. So about 3/4 of daily moves are idiosyncratic.
- Lagged-level variant: 25 and 23 significant days; 13 days with both sides significant, all opposite (4 + 9).

**Arbitrage (Fig. 7).** The cheapest Trump plus the cheapest Harris across Kalshi and Polymarket, net of fees, was **below $1 on "nearly every day"** from 1 Sep to 4 Nov. The gap **grew in the last two weeks**, peaked just before the election, and converged to zero as votes were counted. **No daily magnitudes are reported in the text.**

## Reusable definitions

- **Hybrid snapshot** min(event/Election Eve, resolution − 1), with a **snapshot-validity guard**: there must be a close exactly on the snapshot date, and the snapshot must precede any "by [date]" deadline in the title. This prevents scoring post-event prices, and matters for venues with administrative resolution dates.
- Log-skill `1 − LL/LL_0.5` and Brier skill `1 − Brier/0.25`. The share above 0 is identical under both.
- Eve-price bands (lopsided, lean, competitive) and a **balanced-cohort** control for listing composition.
- The 4-way type taxonomy: winner / margin / other / speech (mention).
- Calibration triplet: ECE, mean bias, Brier reliability.
- Pooled first-difference day shocks with a sign-coherence cross-tab for complementary outcomes.
- Cross-venue complementary-sum arbitrage after fees.

## Stated limitations (and future work)

- Contracts are not independent, so the CIs are descriptive.
- Market-level data cannot reveal mechanisms (behavioural bias, hedging, manipulation, thin trading).
- Results cannot be generalised to the rapidly changing post-2024 markets.
- Pre-resolution accuracy conflates mispricing with real changes in politics.
- PredictIt coverage is incomplete because of the API's 90-day window.
- Polymarket multi-outcome markets are excluded. Daily-close definitions differ across venues, as do the time zones (PredictIt).
- A broader follow-up study is in progress.

## Critical assessment

- **Large version drift.** v1's headline (Polymarket 67% accurate, strongly mean-reverting, "inefficient") is overturned in v5 (85% accurate, mostly random walks, "broadly efficient"). The v1 errors came from on-chain price reconstruction (fill ratios plus title regex), hand-coded resolutions and a snapshot rule that favoured Kalshi. This is a cautionary tale for anyone rebuilding Polymarket prices from fills without careful token-to-outcome mapping. Cite v5 only.
- **"Arbitrage on nearly every day" is not shown to be executable.**
  - Daily closes are not synchronous: Polymarket's is an end-of-day midpoint, Kalshi's the last trade, possibly hours earlier.
  - Buying requires asks, not mids or last trades.
  - The Kalshi contract is "Trump *or another Republican*"; the Polymarket one is "Donald Trump".
  - US and offshore access restrictions largely prevent one entity from holding both legs.
  - Kalshi settles weeks later, so capital is locked up and carries counterparty risk.
  - **The size of the gap is never reported.** At most the evidence supports "cross-venue price divergence", not riskless profit.
- **Accuracy is dominated by composition**, which the authors acknowledge and handle well (bands, the balanced cohort). The 55% in the competitive band [49, 61] is the informative number, and it is not distinguishable from 50% at the margin.
- **Calibration** is computed on correlated contracts at a single snapshot. The 2024 macro outcome (a Republican sweep) moved many correlated contracts the same way, so the longshot pattern and the +0.028 bias may partly be one shared shock. The contracts are not independent draws.
- **Daily-close noise.** A close equal to the midpoint, or the last trade if the spread exceeds $0.10, in thin markets inflates measured idiosyncratic moves and negative ρ through bid-ask bounce. That is consistent with roughly 20% of contracts showing negative ρ and with the R² of about 0.25 for common shocks. The noise looks like it comes from how prices are measured rather than from how information is processed.
- **Internal inconsistencies:**
  - the Table 2 caption says "2,225 analyzed contracts" against 2,170 in the text; the Figure 1 changelog also says 2,225;
  - the changelog's table and figure numbers (Table 2/3, Figure 5) do not match the current numbering (Tables 4/5, Figure 7);
  - the version label "4" differs from OSF v5;
  - cross-venue correlation ranges differ between the abstract (0.77–0.96) and the text (0.81–0.94);
  - v5 drops the "which party wins" grouped market as multi-outcome but keeps the candidate sub-markets of the same NegRisk event, an unclear distinction.
- **Selection:** 542 Polymarket speech contracts with no pre-event price are excluded. This is reasonable, but speech accuracy is measured only on contracts that traded before their event.
- **Trust:**
  - overall accuracy 86% with composition effects: **high**;
  - venue differences are compositional: **high**;
  - calibration with mild longshot bias: **medium-high** (correlated outcomes; one snapshot);
  - mostly random walks: **medium** (low power; daily closes);
  - coherent Trump/Harris day shocks: **medium-high**;
  - persistent cross-venue arbitrage: **low-medium** as an executable claim, **medium** as evidence of price divergence;
  - v1 numbers: **do not use**.

## Directions it opens

- **An executable cross-venue arbitrage study.** Use Polymarket order-book snapshots or WebSocket history (best ask plus depth) aligned to the second with Kalshi books. Measure fillable size below $1 after fees, gas, settlement lag and the cost of capital. Separate "price divergence" from "executable arbitrage".
- **Reproduce the calibration with on-chain trade-derived prices** (VWAP over a fixed pre-snapshot window, both exchange eras) to check sensitivity to the CLOB "daily close" definition. Extend to all political markets for 2020–2026, clustering by event or date to get honest CIs.
- **Correct token→outcome mapping as infrastructure.** v1's failure shows the value of a canonical market/condition/token/outcome table built from on-chain `ConditionPreparation`, `TokenRegistered` and NegRisk adapter events plus Gamma metadata, with resolution taken from the UMA/CTF `ConditionResolution` payouts rather than title regex.
- **Speech/mention market microstructure:** the 75.5% accuracy, the short lives and the many contracts priced only at or after their event make this a distinct product class. Study intra-event price paths (live during the speech), the timing of resolution sources, and possible insiders (transcript feeds).
- **Bid-ask bounce versus overreaction:** re-estimate ρ on mid-quote and on trade-signed series, with bootstrap correction for small T, to settle whether the negative-ρ minority is real.
- **A listing-composition-adjusted accuracy dashboard:** platform accuracy reported by price band and type, with balanced cohorts, so that headline "X% accurate" claims (including Polymarket's own) can be read correctly.
- **NegRisk multi-outcome scoring:** a multinomial log score for grouped markets (which this paper drops), using sum-to-one-normalised sub-market prices.
