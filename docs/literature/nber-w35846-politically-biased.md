# Are Prediction Markets Politically Biased?

- **Source:** [NBER Working Paper 35846](https://www.nber.org/papers/w35846), October 2026, JEL G13, G4, P0. Marked "preliminary"; to be revised after the 2026 midterms to add those elections and **Polymarket data**. 20 pp text, 9 tables, 1 appendix table (A1).
- **Author:** Eric Zitzewitz (Dartmouth College; CESifo; NBER). Discloses that he has traded on prediction markets but has no financial relationship with the venues. Pre-2007 data collected jointly with Andrew Leigh and Justin Wolfers.
- **Code/data:** none released. Venue data were supplied to the author for academic research.
- **Read:** full text of the PDF (33 pages, including all tables and Table A1), extracted with pypdf. Formulas came through garbled and were reconstructed from context.
- **Polymarket relevance:** indirect. **This version contains no Polymarket data.** Polymarket appears only in Table 1 (2024 volume), the background section and Table 2 ("to come"). The methods and the null result are the benchmark a Polymarket version will be judged against.

## Question

Does the unrepresentative trader population (younger, more male, more educated; disputed racial mix), together with large traders who might move prices on purpose, make prices of political prediction markets biased?
- **(a)** Are left-leaning or right-leaning candidates systematically overpriced in election markets?
- **(b)** Are female, non-white, Black, young or old candidates mispriced?
- **(c)** Are left-leaning or right-leaning outcomes mispriced in short-term polling-average markets?
- **(d)** Is there a favorite-longshot bias (FLB), and do the political and demographic results survive controlling for it?

## Data

**Venues and eras.** The paper uses the main US-facing market in each era:
- Wall Street curb betting, 1884–1940;
- London bookmakers, 1944–2001 (1880–1988 is used as "pre-IEM");
- IEM, 1992–2024 (winner-take-all only; vote-share contracts excluded);
- Intrade, 2002/03–2012 (trades; quotes 2007–12);
- PredictIt, 2014/16–2022 (trades; quotes 2019–22). Elections run only through 2022 because of the 2023–24 restrictions and 2025–26 low volume. Polling markets include 2025–26.
- Betfair, mid-2019 to mid-2023 (UK/Australia, seat-level races; trades and quotes);
- Kalshi, 2024–25 (trades and quotes).
- Polymarket 2024–25 is "to come".

**Scale (Table 1).** Notional political volume in October and November of presidential years, in thousands of US$:
- IEM: $39k in 1988 → $83k in 2024. Intrade peaked at $69.6M (2012). PredictIt reached $650M (2020).
- 2024: Kalshi **$1,386,483k**; Polymarket **$7,732,139k**; total $9.19B. Intrade/Kalshi/Polymarket counts include political markets only.

**Election sample.** General elections only. **9,642 observations, 216 election dates** (Table 3).
- The US is 60% of the sample, the UK 16%, Australia 13%, Canada 3.4%, Germany 2.4% and France 1.0%.
- Political orientation: US Republicans +1 and Democrats −1; independents are centrist (0), except Sanders (−1). European parties are coded by European Parliament alliance (left: Left/Greens/Social Democrats; right: Christian Democrat allies; FDP allies centrist). UK: Labour, Greens and SNP left; Conservatives and Reform right; Lib Dems centrist. Most other countries are not classified yet.

**Price construction.**
- The main price is the bid-ask midpoint where quotes exist and are narrow enough. Multi-outcome markets must have Σbid ≥ 0.8 and Σask ≤ 1.5. Otherwise the last trade is used.
- Multi-outcome midpoints are normalized to sum to 1: `p_i = b_i + (a_i − b_i)·(1 − Σb_j)/(Σa_j − Σb_j)`.
- **Horizons:** 1 day, 21 days ("3 weeks") and 120 days ("4 months") before the election, so a market can appear up to 3 times.
- The 3-week horizon is chosen because apparent manipulation attempts in 2012 (an Intrade Romney whale) and in 2024 (the Polymarket "French whale") happened then.

**Return.** Return to expiry in percentage points: payoff minus price.

**Demographics (Table 5).** Sex, race and age were gathered with Google Gemini acting as an RA.
- Mixed-race candidates take the first race listed.
- Age was available for about 80% of candidates, about half of them with an exact birthdate. Ranges were set to their midpoint.
- Spot checks found a couple of errors, for example confusing father and son of the same name.
- Sample: PredictIt and Kalshi US races where the contract names the candidate. Most general-election "Democratic/Republican" contracts are excluded. 3,126 observations, 112 election dates.

**Polling markets (Table 6).** PredictIt weekly bracket markets (7–10 bins) on RCP/538 polling averages, mostly settled at 11 AM ET on expiry.
- Late 2015 → early 2026, with a gap from mid-2022 to early 2025.
- **62,256 contract-days, 351 expiry weeks.** Each contract enters once per day of its life (typically 7 days).

## Methods

- **Political bias:** OLS of return to expiry on orientation (−1/0/+1), with election × horizon fixed effects. A positive coefficient means right-leaning candidates earn more, i.e. **left is overpriced**.
- **Standard errors** are clustered by **election date**. Clustering by election instead understates the SE by more than 2.75×. Clustering by quarter or year changes almost nothing.
- **Splits:** by venue, horizon, office (national leader, legislative control, seats, governor, other) and US/non-US.
- **Demographics:** the same regression on female, non-white, Black and age/10, with election × horizon fixed effects, so each candidate is compared with rivals in the same race.
- **Polling markets:** return on bin rank (−1 = most pro-Democratic outcome, +1 = most pro-Republican), with polling-average × day fixed effects and SEs clustered by expiry week.
  - Splits by presidency, election vs approval polling, Trump/non-Trump, source (RCP/538/other) and days to expiry.
  - Controls: price, bin number, extremeness.
- **FLB:** a Lattimore–Baker–Witte probability-weighting model. Misperceived probability `p(π) = απ^β / (απ^β + (1−π)^β)`, so log-odds(p) = ln α + β·log-odds(π).
  - A (multinomial, per Berg & Rietz 2019) logit of the outcome on log price, with election × horizon fixed effects, gives slope 1/β. **A slope > 1 means FLB**, i.e. prices too compressed: longshots overpriced, favorites underpriced.
  - Latent-variable reading (Zitzewitz 2026): traders overestimate the spread of future political shocks by that factor, analogous to overpriced option volatility.
- **Political and demographic bias controlling for FLB:** orientation and demographic terms are added to the logit. Coefficients are in percentage points and divided by 5 to approximate marginal effects.
- **Robustness (Table A1):**
  - SE clustering by election, quarter or year;
  - a −2..+2 extremeness coding;
  - trades instead of quotes;
  - the subsample with both trades and quotes, using each;
  - quotes only, or trades only;
  - tighter spreads;
  - equal weights per election, per date or per year.

## Findings

**Elections: no political bias (Table 3).**
- Full sample coefficient **0.03 (SE 2.66)**, n = 9,642, 216 dates. Mispricing of about ±5 pp is rejected at 95%.
- At 1 day: 0.76 (1.90). A left bias above about 4.5 pp and a right bias above about 3.0 pp are rejected.
- 3 weeks 0.74 (2.91); 4 months −3.63 (5.06).
- Commercial venues (n = 9,168, 150 dates): −0.43 (2.61).

**By venue (all horizons, SE in parentheses).**

| Venue | Coefficient | Note |
| --- | ---: | --- |
| Pre-IEM | 2.87 (12.47) | |
| IEM | 10.34 (8.42) | |
| Intrade | −5.53 (3.32) | |
| PredictIt | 2.07 (6.17) | |
| Betfair | −1.72 (1.19) | 4 months −2.38\* |
| Kalshi | 4.72 (3.85) | **1 day 6.11\*\* (2.50)**, n = 835, only 16 dates |

The author warns that SEs for single venues are biased down because there are few, unequal clusters.

**By office and country (Table 4).** Non-US −1.42 (1.30), the opposite sign to the US 0.84 (4.39). Non-US national leader −6.82\* (3.86). The non-US negatives are driven by Labor beating expectations in Australia 2022 and NSW 2023. There is no evidence that higher offices carry a larger hedging premium (the prediction being that left securities hedge against right-win equity rallies), but power is low.

**Robustness (Table A1).** Coefficients range from −1.66 to 3.75, and the largest |t| is 0.6.
- Equal-weighting elections gives 1.25; equal-weighting dates −1.17; equal-weighting years 3.75 (6.04).
- The subsample with both trades and quotes is about 1.5 pp more pro-left than the full sample; this is attributed to the cycles that were excluded.

**Demographics (Table 5).** Univariate estimates show female and non-white candidates overpriced by about 1 pp, and a candidate 9 years younger overpriced by about 1 pp. The largest |t| is about 0.85, so nothing is significant.
- Coefficients: female −0.95 (3.84); non-white −0.85 (4.02); Black −0.69 (4.17); age/10 1.17 (1.40).
- With all controls: female −5.17 (4.54).

**Polling markets: small, significant left overpricing (Table 6).**
- **Baseline 1.41\*\*\* (0.53)**; the 95% CI for overpricing is 0.3–2.5 pp. The most-left bin is overpriced by about 1.4 pp and the most-right bin underpriced by the same amount.

| Subsample | Coefficient (SE) |
| --- | ---: |
| Obama | 0.85 (1.44) |
| Trump I | 1.58\*\* (0.72) |
| Biden | 1.48\* (0.81) |
| Trump II | 0.95 (1.99) |
| Election polling | 1.21 (0.80) |
| Approval / favorability | 1.46\*\* (0.59) |
| Involves Trump | 1.47\*\* |
| No Trump | 1.32\* |
| RCP | 1.54\*\* |
| 538 | 1.09\*\* |
| ≤ 7 days to expiry | 1.14\*\*\* (0.41) |
| 29+ days | 2.76 (1.91) |
| With price, bin and extremeness controls | 1.44\*\*\* (0.51) |

**FLB (Table 7).** Full-sample slope **1.40\*\*\* (0.10)**, n = 8,778, 193 dates.

| Venue / horizon | Slope |
| --- | ---: |
| 1 day (all) | 1.48\*\*\* |
| 3 weeks (all) | 1.50\*\*\* |
| 4 months (all) | 1.15 (n.s.) |
| Intrade | 1.62\*\*\* (1 day 2.00\*\*\*) |
| PredictIt | 1.39\* |
| Betfair | 1.47\*\* |
| IEM | 1.00 |
| Kalshi | 1.44 (0.34), n.s., 13 dates |
| Pre-IEM at 4 months | 4.55\*\* |

The pattern does not match Page and Clemen (2013), who found a larger long-horizon FLB on Intrade.

**Political bias controlling for FLB (Table 8).** All 0.62 (2.54).
- Intrade −7.65\*\* (right overpriced).
- IEM: 3 weeks 8.20\*, 4 months 10.01\*\*.
- **Kalshi 1 day 9.56\*\*\* (2.71)**, i.e. left overpriced on Kalshi in 2024–25.
- The author treats these as marginal given the few clusters.

**Demographics controlling for FLB (Table 9).** With all controls, female is −10.76\*\* (5.35), i.e. **female candidates overpriced**. This is 1 significant coefficient out of 18, and it is collinear with age and longshot status. The ln(price) slope is 1.13–1.20.

**Conclusion.** Election markets show no systematic political or demographic bias, but do show FLB. Polling markets show a 1.4 pp left overpricing, too small to detect even in the 145-year election sample. The Kalshi sample is too small to confirm FLB.

## Reusable definitions

- Return to expiry = payoff − price (pp). A positive coefficient on a −1/0/+1 orientation score means left is overpriced.
- **Cluster by election date** (not by election). Correlated outcomes across races on the same day are the true unit of sample size.
- A spread-aware normalized multi-outcome midpoint, with eligibility filters Σbid ≥ 0.8 and Σask ≤ 1.5.
- Fixed horizons: 1 day, 21 days and 120 days before resolution.
- A Lattimore–Baker–Witte / multinomial-logit FLB slope (> 1 = FLB), which also lets bias covariates be estimated net of FLB (coefficient/5 ≈ marginal pp).
- A bin-rank political orientation score for bracket (range) markets.

## Stated limitations (and future work)

- The version is preliminary. **Polymarket and the 2026 midterms will be added.** Party coding for most non-Anglo/European countries is pending, and the demographic sample will be expanded to general-election contracts.
- Venue-level SEs are likely too small (few, unequal clusters).
- Power to detect a hedging premium or a 1–2 pp election bias is limited, because the effective n is the number of election dates.
- PredictIt 2023–26 elections are excluded; the Kalshi sample is small (13–16 dates).
- LLM-collected demographics contain occasional errors.
- Manipulation cannot be tested experimentally at current liquidity levels.

## Critical assessment

- **Essentially one Kalshi cycle.** Its 16 dates are dominated by 5 Nov 2024. The significant Kalshi left overpricing (6.11\*\* and 9.56\*\*\* with the FLB control) equals "Trump/Republicans beat the prices in 2024". That is a single realised shock, the exact ex-post ambiguity the paper warns about in its own introduction. The same caveat will apply to Polymarket 2024.
- **Wide null.** ±5 pp is not a tight bound for elections. The headline "no bias" is a failure to reject, not evidence of zero bias; the polling result shows 1–1.5 pp biases exist and would be invisible here.
- **Selection.** The sample covers general elections only. Candidate-named contracts drive the demographic sample (mostly PredictIt), so the demographic sample is not the same population as the political sample.
- **Weighting is a choice.** Results with equal weights per year (3.75) and per date (−1.17) bracket zero but move by about 5 pp. The baseline over-weights recent, many-race cycles such as 2019 UK seats and 2022 Australia.
- **Quote-versus-trade mixing** across eras means the price definition is not constant over the sample, though the robustness check covers this.
- **Text inconsistencies:**
  - Table A1's note describes the polling-market specification (bin ranking, contract-days, polling-average × day fixed effects), but the rows are the election sample. A copy-paste error.
  - Table 8's note refers to "the fixed effects log regression in Table 5", which should be Table 7.
  - Two sections are numbered VI.
  - The 1992–2024 IEM range conflicts with the 1988 start described in the text.
  - Footnote formulas did not extract cleanly from the PDF.
- **No mechanism data.** There is no trader-level analysis, so it says nothing about whether marginal traders offset partisans; that is inferred from older IEM work.
- **Trust:**
  - no political bias in elections overall: **medium-high** (robust across many cuts, but CIs of about ±5 pp);
  - no demographic bias: **medium** (small, selected sample; one significant coefficient appears under FLB control);
  - 1.4 pp left overpricing in polling markets: **high** (351 clusters, stable across subsamples, PredictIt-specific);
  - FLB in election markets: **high** for Intrade, PredictIt and Betfair; **low** for Kalshi (13 dates);
  - Kalshi left overpricing: **low** (one cycle).

## Directions it opens

- **Run the paper's exact spec on Polymarket** before the author does. Use the full on-chain fill history for 2020–2026 political markets (both CTF Exchange eras), with:
  - CLOB midpoints from the order book where available, otherwise the last trade;
  - 1/21/120-day horizons;
  - orientation coding from market metadata (candidate/party via an LLM, as here);
  - clustering by election date.
  Report 2024 separately from 2022/2026 midterms and non-US elections. Polymarket has far more non-US races than Kalshi, which raises the number of date clusters.
- **Polling and approval bracket markets on Polymarket** (Trump approval, RCP/Silver Bulletin brackets, "Trump says X" counts): test for the 1.4 pp left overpricing at much higher volume. Polymarket's bracket ladders map directly onto bin rank.
- **Cross-venue FLB slope comparison** (Kalshi vs Polymarket vs PredictIt) on identical events, using matched contracts. Tests whether a crypto, offshore trader base changes the β misperception parameter.
- **Wallet-level partisan flow.** Classify wallets by net exposure across many political markets ("partisan" wallets that are consistently long one party) versus "marginal" wallets, and test the Forsythe et al. marginal-trader mechanism. Do partisan-wallet imbalances predict returns to expiry? Do marginal wallets absorb them, and how fast?
- **Whale/manipulation event study.** For identified large one-sided wallets (e.g. the 2024 French-whale cluster), measure the price impact and its decay at the 3-week horizon the paper singles out, compared with the hours-long reversion Rhode & Strumpf found in the IEM.
- **Hedging premium test.** Do left-leaning Polymarket contracts trade at a premium that co-moves with equity/crypto exposure? Polymarket traders hold crypto, so the hedging sign may differ from equities.
- **Data product:** a standing "political bias monitor" that computes return-to-expiry by orientation, by election date cluster, as markets resolve, with the normalized-midpoint definition.
