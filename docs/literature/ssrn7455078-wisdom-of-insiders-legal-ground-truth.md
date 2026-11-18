# The Wisdom of Insiders: Legal Ground Truth and the Detection of Informed Trading in Decentralized Prediction Markets

- **SSRN:** [7455078](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7455078), posted
  13 Sep 2026. A September 2026 version of a June 2026 thesis.
  - Keywords: prediction markets, adverse selection, surveillance, weak supervision,
    Polymarket.
  - Category: applied machine learning and market surveillance, with a law-and-economics
    framing.
- **Author:** Nicolas Lanker, PPLE College, University of Amsterdam (a thesis).
- **Code/data:** none found. No GitHub or thesis-repository link was located.
- **Read: NOT the full text.** SSRN blocked automated access behind a bot check, which was not
  bypassed. This note uses:
  - **[ABS]** the abstract, via search-engine snippets of the SSRN listing;
  - **[MLQ]** the abstract and metadata reproduced in a Substack post (mlquants, 4 Oct 2026),
    whose own commentary is kept separate.

  Sample periods, the number of positive labels, PU-learning details, feature importances,
  hyperparameters, the candidate list, tables and limitations were not seen.

## Question

Purely statistical screens cannot tell an insider from an unusually skilled trader. Can
labels taken from **legal outcomes** (indictments, CFTC enforcement, documented cases) train
a detector that uses only **pre-resolution** features? What does that detector reveal about
how insiders trade and where unconfirmed candidates sit? [ABS]

## Data

All from [ABS] and [MLQ].

| Set | Size |
| --- | --- |
| Baseline | > 20M deduplicated Polymarket trades across **28,767 resolved markets** |
| Detection | **889,569 trades** in **93 geopolitical and military markets** |
| Scoring | **254,528 wallet–market pairs** |

- **Positive labels:** from criminal indictments, CFTC enforcement actions and documented
  case studies. The abstract describes one charged case, a US Army Special Forces
  servicemember, contributing **four wallet–market observations**. The total number of
  labelled insiders is not seen.
- **Features (pre-resolution):** average entry price, capital deployed, trade count and share
  of market volume.
- "Deduplicated" suggests double-counted fills were handled. The procedure is not seen.

## Methods

- **Positive–unlabelled (PU), weakly supervised Random Forest** on the four features. It is
  anchored conceptually in Kyle (1985) and Glosten–Milgrom (1985) adverse selection [ABS].
- **Leave-one-wallet-out cross-validation**: each labelled wallet is held out in turn [ABS].
- **Descriptive comparison** of insiders' entry prices with those of comparable traders
  [ABS].
- **Scoring** of unlabelled pairs to produce a ranked candidate list, then examination of
  which kinds of market the candidates fall in [ABS].

## Findings

- **Detection:** mean AUC-ROC **0.946** under leave-one-wallet-out cross-validation [ABS].
- **Most informative fold:** all four held-out observations of the charged servicemember's
  wallet rank above all **80 contemporaneous non-insider observations**. That places the
  wallet in the **top 3%** by predicted probability, without the model having trained on it
  [ABS/MLQ].
- **Entry price:** confirmed insiders pay a **median 46¢** per outcome token, against **77¢**
  for comparable traders [ABS].
- **Candidates:** unconfirmed high-score candidates concentrate in markets where the relevant
  information is **legally restricted** [ABS].
- **Conclusion:** "prediction market accuracy and market integrity are separable, and often
  competing, objectives" [ABS].

## Reusable definitions

- "Legal ground truth": positives taken from indictments and enforcement actions.
- The PU-learning framing, in which unlabelled is not the same as clean.
- A four-feature pre-resolution vector (average entry price, capital, trade count, volume
  share).
- Leave-one-wallet-out validation.
- Restricted-information market categories (geopolitical and military).

## Stated limitations

Not seen. The paper's premise is that statistics alone cannot separate insiders from skilled
traders [ABS].

[MLQ] commentary, not the paper, adds that a low entry price may reflect access or better
reading of public signals, and that fills show what and when but not the information
source.

## Critical assessment

These points rest on the abstract only.

- **Very few positives.** The publicly charged Polymarket cases number in the single digits.
  A mean AUC over a handful of held-out wallets has very wide uncertainty, and "4 above 80"
  is a small comparison.
- **The labels are biased by how cases come to light.** Cases become public largely because
  someone bought a cheap outcome that then won and attracted press attention. A detector
  trained on them learns "cheap entry in geopolitical markets", which matches the 46¢ vs 77¢
  result.
  - The PU assumption that positives are labelled at random is violated. Precision on the
    unlabelled pool is not identified.
- **Contemporaneous controls are easy negatives.** If controls are drawn from the same market
  after the news, they enter at high prices. Separating them by entry price is close to
  trivial, and the "comparable traders" definition is critical.
- **A real strength:** the features are pre-resolution, so unlike profit-based screens the
  detector could in principle run in real time.
- **The candidate list is unvalidated.** "Concentrated in legally restricted markets" partly
  reflects the 93-market detection universe.
- **Trust:**
  - AUC 0.946: **low–medium** (tiny positive set; control construction unseen);
  - insiders enter at lower prices (46¢ vs 77¢): **medium** (plausible and mechanically
    expected; small n);
  - legal-label approach as a validation anchor: **medium–high** as a design idea, **low** as
    evidence of real-world precision;
  - accuracy and integrity in conflict: **medium** (a conceptual conclusion consistent with
    other work).

## Directions it opens

- Build an open labelled set: every publicly charged or enforcement-documented Polymarket
  wallet–market pair, with the source document and a public-news timestamp, for training
  and benchmarking detectors.
- Train the detector on the full V1+V2 fill history across all categories. Use controls
  matched on entry time **before** public news, rather than contemporaneous controls.
- Add microstructure features (taker aggressiveness, order-book depth consumed,
  time-to-first-news, wallet age, funding source) and test what they add beyond entry
  price.
- Deploy a real-time scorer on the WebSocket trade feed and measure lead time against
  public-news onsets, with false-alarm rates per category.
- Calibrate PU class priors from enforcement base rates so that scores become probabilities
  usable for platform surveillance.
