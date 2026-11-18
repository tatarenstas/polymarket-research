# The Price is (Almost) Right: A Calibration Analysis of Polymarket Pricing Data

- **Source:** Princeton University undergraduate senior thesis, [DataSpace record](https://theses-dissertations.princeton.edu/entities/publication/d5708372-5ea3-4252-b669-7f9cee07387c) (handle 88435/dsp01mw22v8973).
- **Dates:** issued 9 Apr 2026 (class of 2026); deposited 22 Jul 2026.
- **Author:** Aidan Walker. **Advisor:** Daniel Rigobon. Department of Operations Research & Financial Engineering; certificate in Optimization and Quantitative Decision Science.
- **Files:** `THESIS_FINAL.pdf` (4.05 MB) and an extracted-text bitstream, both **access-restricted** (`datacite.rights = restricted`; the DSpace API returns HTTP 401 for both).
- **Code/data:** unknown.
- **Read:** **abstract and repository metadata only.** The full text was not accessible, so this note is short and every claim below comes from the abstract. Methods details, tables, filters and robustness checks are unknown.

## Question

Polymarket says its prices are probabilities. Are they well calibrated, across market domains and time-to-resolution horizons? And how does inference change once the correlation between markets inside the same event is taken into account?

## Data

- **188,509 resolved binary Polymarket markets** and **1,875,570 daily price observations**, Nov 2022 → Dec 2025.
- The source (CLOB/Gamma API or on-chain), the daily-price definition, the liquidity filters, the domain taxonomy and the horizon bands are **not stated in the abstract**.

## Methods (from the abstract)

- Reliability diagrams.
- Brier score decomposition (presumably reliability, resolution and uncertainty) and the Brier Skill Score.
- Logistic recalibration: regress outcomes on the log-odds of price. A slope b > 1 means prices are compressed toward 0.5, i.e. underconfidence or favourite-longshot bias (FLB).
- All of the above by domain and by horizon.
- **Event-level clustered bootstrap** to handle correlated markets within multi-market events, presented as filling a gap in comparable recent work.

## Findings (from the abstract)

- **Overall Brier Skill Score 0.398.**
- **By domain:** from **0.264 in Sports** (worst) to **0.565 in Politics** (best). The other domains are not listed in the abstract.
- **Overall logistic recalibration slope b = 1.112:** broad underconfidence, so longshots are overpriced and favourites underpriced.
- **FLB appears in every domain and is worse at longer horizons.**
- **Clustered bootstrap CIs are much wider than naive ones.** The core miscalibration result holds, but **two horizon bands lose statistical significance** under clustering.
- The author concludes that domain- and horizon-specific recalibration could improve how raw prices are read.

## Reusable definitions

- Brier Skill Score against a climatology or base-rate reference. The reference is not specified in the abstract; it could be the base rate or 0.5.
- The logistic recalibration slope as a single summary of FLB (b > 1 means compressed prices).
- **Event-level clustered bootstrap**: resample events, not markets, so that negRisk/multi-outcome groups and ladders do not inflate the effective n.

## Stated limitations (and future work)

Not available from the abstract.

## Critical assessment

- The full text was not read, so methodological risks cannot be checked. The main ones to verify:
  - how the daily price was built, whether midpoint, last trade or Gamma `outcomePrices`, and whether stale prices in illiquid markets were filtered out;
  - whether the daily observations were pooled so that long-lived markets dominate the horizon analysis;
  - how "resolved binary" handles 50/50 or invalid resolutions and negRisk sub-markets;
  - which Brier Skill reference was used. Against a base rate in which most markets resolve No, a BSS of 0.398 means something different than against 0.5.
- **Coherence with other work:** b = 1.112 > 1 (prices too compressed) matches the FLB direction in Zitzewitz (NBER w35846; slope about 1.4 for election markets) and the mild longshot overpricing in Clinton & Huang (SocArXiv d5yx2). The size is smaller here, which fits a far broader, sports-heavy sample.
- The ranking of Politics as best and Sports as worst in BSS may partly reflect each domain's base rates and price distributions (many lopsided political long-shots) rather than information quality. The same compositional caution applies as in Clinton & Huang.
- **Trust** (from the abstract only):
  - overall skill (BSS ≈ 0.4): **medium**;
  - FLB/underconfidence (b ≈ 1.11), present in all domains: **medium** (consistent with the literature; method details unseen);
  - FLB worsens with horizon: **medium-low** (two bands lose significance under clustering);
  - domain ranking: **low-medium** (taxonomy and base rates unknown).

## Directions it opens

- **Replicate at full scale** with our own data: all resolved binaries in both exchange eras, prices from on-chain fills (VWAP over fixed windows) and from CLOB midpoints. Measure how sensitive calibration is to the price definition and to stale-price filters such as minimum volume or trades in the window.
- **A standard calibration report** with event-level clustered bootstrap CIs, broken down by domain × horizon × liquidity tier × maker share. Publish the recalibration curves (a, b per cell) as a live product: "recalibrated Polymarket probability".
- **Test the horizon effect causally** using ladders and repeated series (daily or weekly recurring markets), where the same question is priced at many horizons.
- **Link the FLB to who is on each side:** do wallet groups (high-frequency makers, whales, new accounts) systematically hold the overpriced longshot side? This turns a calibration finding into a microstructure explanation.
- **Ask for the full text** through Princeton (on-campus or request access) before relying on any detail beyond the abstract.
