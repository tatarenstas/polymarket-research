# From Iran to Taylor Swift: Informed Trading in Prediction Markets

- **SSRN:** [6426778](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6426778), Columbia Law
  & Economics working paper, first posted around March 2026.
  - A second listing, [7259741](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7259741),
    appears to be a later version. Search snippets show 97 pp (6 Apr 2026) and 106 pp
    (Aug 2026), unverified.
  - Category: empirical law-and-finance plus legal and policy analysis.
- **Authors:** Joshua Mitts (Columbia Law School), Moran Ofir (University of Haifa).
- **Code/data:** the flagged wallet–market list is reportedly not released (per Nechepurenko,
  arXiv 2605.02287 and 2605.00493).
- **Read: NOT the full text.** SSRN blocked automated access behind a bot check, which was not
  bypassed, and no other hosted PDF was found. This note is assembled from:
  - **[HLS]** the authors' own summary on the Harvard Law School Forum on Corporate
    Governance (25 Mar 2026);
  - **[CLS]** a Columbia Law News interview with Mitts (5 Aug 2026);
  - **[ABS]** abstract fragments surfaced by search engines (SSRN/ResearchGate listings);
  - **[HEC]** the replication spec in Bock & Guenthoer, *Detecting Informed Trading Before
    Resolution* (HEC Paris MIF research paper, 1 Jun 2026), §4.4.1 and App. D.1, which
    reports the screen's weights "as specified in the original paper";
  - **[NEC]** descriptions in Nechepurenko, arXiv 2605.00493 and 2605.02287.

  Every claim below carries its source tag. Page counts, tables and the exact permutation
  design were not seen.

## Question

How widespread is trading on nonpublic information on Polymarket, what does it look like
on-chain, and how much does it earn? Can existing US insider-trading law reach it, and if
not, what should regulate it? [HLS, CLS]

## Data

- **Venue and period:** all Polymarket markets, Feb 2024 → Feb 2026 [HLS, CLS]. NEC says
  "2023 through early 2026", which is inconsistent.
- **Size:** "over 93,000 markets" [HLS, NEC]. The HLS summary also mentions "nearly 50,000
  wallets". That does not square with 210,718 flagged pairs and may count flagged wallets;
  treat it as unverified.
- **Unit:** the wallet–market pair, because an insider may be informed about one event only
  [ABS, HLS].
- **Filters:**
  - **buy side only**, and pairs with < $500 bought are excluded [HLS, HEC];
  - per HEC, markets with < 3 eligible wallets are dropped (it is unclear whether this is
    original or the replicator's choice).
- **Timing anchor:** in the HEC replication, late buying is the share of USD bought in the
  final 48 h before the market's **last recorded trade**, because `end_date` is unreliable
  for NegRisk markets. Whether the original uses 48 h and the same anchor is not confirmed.
- **Identity:** pseudonymous wallets. No entity clustering is reported.

## Methods

- **Composite screen** with five signals [HLS, CLS, HEC]. The weights are as reported by
  HEC:

  | Signal | Definition | Weight |
  | --- | --- | ---: |
  | Cross-sectional bet z | (USD bought − market mean) / market SD | 25 |
  | Within-wallet bet z | Against the wallet's own mean and SD across its markets | 20 |
  | Profit z | Realised PnL standardised within the market | 30 |
  | Late-buy fraction | Share bought in the final 48 h | 15 |
  | Directional concentration | One-sidedness; the original defines it qualitatively, HEC uses \|buy_share − 0.5\|·2 | 10 |

  - Score: `25·z_cross + 20·z_within + 30·z_profit + 15·late + 10·dir`, an unbounded linear
    combination.
  - **Flag** ("Layer 2" gate): z_cross > 2 or z_within > 2. The composite ranks pairs inside
    the gated set [HEC].
- **Null:** a permutation test of the flagged win rate against chance [ABS, HLS]. What is
  permuted and how many draws are used is unknown.
- **Case studies:** a narrative reconstruction of high-profile episodes [HLS, CLS].
- **Legal analysis:**
  - classical versus misappropriation theory;
  - securities versus commodities classification;
  - CFTC Rule 180.1 and CEA §6(c)(1);
  - wire fraud;
  - Kalshi (a CFTC-designated contract market) versus Polymarket's status;
  - H.R. 7004 [HLS].

## Findings

**Screen [ABS, HLS, CLS].**
- **210,718 flagged wallet–market pairs** [HLS]; "over 210,000" [ABS].
- Flagged pairs show positive realised profit in **69.9%** of resolved pairs, which beats
  the permutation null by "more than 60 standard deviations" (NEC quoting the paper).
- They hold the winning token in **75.0%** of pairs [ABS, later version].
- **About $143M** aggregate realised ("anomalous") profit [ABS, HLS], called a lower bound
  because of the buy-only design, the $500 floor and traders who deliberately stay small
  [HLS].
- **About $119M** more than execution prices implied [ABS, later version].

**Case studies [HLS].** Wallets are not named here.

- **Strike on Iran (28 Feb 2026, US–Israeli):** six newly created wallets earned about $1.2M
  buying Yes on "US strikes Iran by February 28?". One account traded 71 minutes before
  the news broke, at about 17% implied probability. [CLS] says about 70 minutes.
  - NEC dates "the canonical Iran-strike market" to Oct 2024, and also cites a 2026 US–Iran
    cluster. The secondary sources disagree on dates.
- **Maduro capture:** one account earned about $485k on a small stake, hours before the
  announcement. HEC cites a DOJ figure of $409k for the charged case, which may be a
  different measure or account.
- **Israel:** Israeli authorities indicted a civilian and a reservist for allegedly using
  classified wartime information to bet.
- **Other episodes:** Google Year-in-Search rankings, an OpenAI browser launch, and the
  timing of Taylor Swift's engagement announcement. The last involved no classified
  information [CLS].

**Legal conclusions [HLS].**
- Insider-trading doctrine depends on securities, and many event contracts may be
  commodities.
- Rule 180.1 is narrower than its securities analogue. Trading on lawfully obtained
  information without deception remains allowed, and the rule has never been tested in a
  contested prediction-market case. The CFTC issued an advisory in Feb 2026 and brought
  modest initial actions.
- Wire fraud requires the information to have commercial value to its source, which may
  fail for military or personal information.
- The difference in regulatory status between Kalshi and Polymarket gives informed traders
  a reason to use Polymarket.
- H.R. 7004 would cover federal officials only, and most of the cases fall outside it.

**Proposals [HLS, CLS].**
- Platform registration, surveillance and reporting duties for operators serving US persons.
- Contract-level rules for high-risk categories: government data releases, military
  operations and corporate material events.
- CFTC rulemaking that extends misappropriation-style liability to confidentiality duties
  owed to governments, employers and others.
- Heightened platform liability for failing to investigate repeat insider trading.
- Employer compliance policies.

The authors acknowledge the markets' information value, citing a Feb 2026 Federal Reserve
Board study of Kalshi macro markets [HLS].

## Reusable definitions

- The wallet–market pair as the unit of detection.
- The five-signal composite and its weights 25/20/30/15/10 (per HEC).
- The Layer-2 bet-size gate (z > 2).
- The $500 buy floor.
- The late-buy fraction anchored on the last trade.
- "Anomalous profit" (realised PnL of flagged pairs) versus excess over execution prices.

## Stated limitations

- The screen is statistical. There is no direct evidence of what any trader knew, and it
  does not show that information was obtained improperly [HLS, CLS].
- The authors see only partial portfolios [HLS].
- $143M is a lower bound: buy side only, < $500 excluded, small deliberate traders missed
  [HLS].
- Every risky contract type is hard to enumerate [HLS].
- Mitts says the scope of the problem "is open for debate" [CLS].

## Critical assessment

These points come from the method as described secondhand, not from the full text.

- **The win rate may be partly built in.** The sources disagree on how the flagged set is
  chosen.
  - The abstract speaks of joint anomalies in size, timing and **profitability**. If
    selection uses the composite, whose largest weight is profit z, computed from
    post-resolution PnL, then the 69.9% win rate is partly mechanical unless the null
    re-applies that selection.
  - HEC says the flag is the bet-size gate alone. In that case the win rate is not inflated
    by construction, but large late bets on near-certain favourites would also win about 70%
    of the time. That is why a baseline built from execution prices matters.
  - Either way, the "75% hold the winner" and "$119M above execution prices" figures are the
    more informative ones, and the design of the null is unknown.
- **Look-ahead.** Profit and the late-buy fraction (anchored on the last trade) are known only
  after resolution. The screen is a retrospective survey, not a detector, as NEC notes.
- **It flags whales.** HEC found that the bare z > 2 gate is dominated by high-volume wallets
  whose stakes are large for mechanical reasons. HEC had to keep only the top composite
  quartile.
- **Buy side only, pair level.** Sells, merges and NegRisk conversions are ignored. Sybil
  splitting across wallets defeats the bet-size z-scores.
- **Labels are uncalibrated.** There is no external ground truth for the 210k pairs. Skill,
  public-news speed and favourite-buying near resolution all score high.
- **No replication possible.** The pair list is not released.
- **Inconsistencies across secondary sources:** the period (2023 vs Feb 2024 start), the
  date of the Iran case, the Maduro profit figure, and the wallet count.
- **Trust:**
  - flagged-pair count and $143M: **medium** (stated consistently; definition-dependent);
  - "far beyond chance" (69.9%, > 60 SD): **low–medium** (possible mechanical selection;
    null unseen);
  - $119M excess over execution prices: **medium** (a better measure; method unseen);
  - case-study facts: **medium** (several are corroborated by public charges, but figures
    vary by source);
  - legal analysis: **medium–high** (a doctrinal argument consistent with other legal
    commentary).

## Directions it opens

- Re-implement the composite on full V1+V2 fills. Report the flagged win rate under a null
  that permutes outcomes **conditional on the gate and on buy prices**, so that selection on
  profit is cancelled out.
- Build an ex-ante variant using only pre-resolution inputs (size z, timing relative to the
  first news or price jump, directional concentration), with price-implied expected win
  rates as the baseline.
- Score sell-side and conversion-based informed trading, such as buying No through NegRisk
  conversions, which the buy-only screen misses.
- Aggregate wallets to entities (funding source, withdrawal destination, co-trading) before
  scoring, so that split positions cannot hide under the z thresholds.
- Map category risk: flag rate and excess profit by contract type (military, government
  data, corporate events, celebrity), in support of the paper's contract-level policy
  proposals.
- Publish a reproducible benchmark set of documented cases, with time-stamped public-news
  onsets, for comparing detectors (Mitts–Ofir, Liu, Della Vedova, Lanker, ex-ante screens).
