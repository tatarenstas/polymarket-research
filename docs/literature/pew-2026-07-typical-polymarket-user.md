# What We Know About the Typical Polymarket User (Pew Research Center)

- **Source:** Pew Research Center short read, 22 Jul 2026,
  [link](https://www.pewresearch.org/short-reads/2026/07/22/what-we-know-about-the-typical-polymarket-user/).
  - Seed-event appendix:
    [PDF](https://www.pewresearch.org/wp-content/uploads/sites/20/2026/07/SR_26.07.22_prediction-market_appendix.pdf),
    1 page.
- **Author:** Kaitlyn Radde (computational social science assistant, Pew).
- **Related Pew work:** a short read on prediction-market volume (27 May 2026).
- **Methodology:** given in the article's "How did we do this?" box. No separate methodology
  page or topline is linked. Each chart offers a CSV download.
- **Read:** the full article (raw HTML) and the appendix. The chart CSVs were not downloaded;
  their values appear in the HTML.

## Question

How do ordinary Polymarket accounts trade over a recent six-week window? The article covers
frequency, trade size, net gains and losses, topic focus, and the heaviest traders.

## Data

**Source.** Polymarket's public **user activity API** (Data API `/activity`). It excludes the
newer Polymarket US platform. Kalshi offers no comparable data.

**Seed sample.**
- In early May 2026, Pew picked **10 high-volume events** across topics and pulled the
  **4,000 most recent trades** on each. Those trades came from **16,836 accounts**.
- The seed events, all dated Feb–Apr 2026:
  - US–Iran ceasefire;
  - Trump posts (6–12 Apr);
  - Bitcoin price in March;
  - Fed Chair confirmation;
  - PSG vs Liverpool;
  - Warriors vs Suns;
  - Purdue vs Arizona;
  - best AI model at end of April;
  - Elon Musk tweet count (27 Feb – 6 Mar);
  - crude oil (CL) by end of March.

**Panel.**
- Activity was collected **15 times** between 7 May and 19 Jun 2026. That gave
  **11,989 active wallets**, the analysis sample.
- The API returns the most recent 4,000 activities per account per call (offset pagination).
  **2%** of wallets hit that cap, so their activity is incomplete.

**Definitions.**
- A "user" or "trader" is an account. Pew notes that one person may run several.
- An account's "primary topic" is one that holds ≥75% of its trades.
- Topics come from Polymarket tags, e.g. basketball → sports. 1% of events fall in several
  categories and under 1% are uncategorized.
- Amounts are in USDC.
- **Not defined:**
  - what a "trade" is (fill or order);
  - how "spent" and "net gain/loss" are computed (realized only, treatment of redemptions,
    open positions at 19 Jun);
  - whether "average" means mean or median.

## Methods

Descriptive statistics only: medians, shares in bins, and a breakdown by primary topic and
activity tier. There are no weights, no CIs and no tests.

## Findings

**Typical account.**
- The median account made **46 trades** on **10 active days** over 42 days.
- The "value of the average trade" was **$6.50**.
- The "average trader" spent a little over **$600**, with a **net loss under $2**.

**Distribution of trade counts.**

| Trades over 6 weeks | Share of accounts |
| --- | ---: |
| <10 | 24% |
| 10–99 | 39% |
| 100–999 | 27% |
| ≥1,000 | 11% |

**Net outcome over the six weeks.**

| Net outcome | Share of accounts |
| --- | ---: |
| Lost >$1,000 | 9% |
| Lost $100–1,000 | 15% |
| Lost <$100 | 32% |
| Made <$100 | 26% |
| Made $100–1,000 | 11% |
| Made >$1,000 | 7% |

So 58% are within ±$100. Implied: 56% net losers and 44% net winners.

**Topic focus.**
- The median account puts about three-quarters of its trades on one topic. 24% trade a single
  topic only.
- Sports, politics and crypto make up nearly all volume (no number given).

**By primary topic.**

| Topic | Median trades | Active days | Average trade size |
| --- | ---: | ---: | ---: |
| Sports | 69 | 12 | ≈ $9 |
| Crypto | 59 | 5 | < $4 |
| Politics | 13 | 7 | ≈ $6 |

The window overlapped the NBA Finals, the World Cup and the Stanley Cup.

**Heavy traders (≥1,000 trades, 11% of accounts).**
- They traded on 39 of 42 days "on average", versus 10 of 42 for the median account.
- The typical heavy trader **lost about $140**.
- **33% lost more than $1,000**, versus **27%** who made more than $1,000.
- Their average trade was about $6.

## Reusable definitions

- Seed-event wallet sampling through the activity API, with repeated pulls to work around the
  4,000-item pagination cap.
- Primary topic: ≥75% of an account's trades.
- Tag → broad category nesting.

## Stated limitations (and future work)

- Accounts are not people.
- The activity API excludes Polymarket US.
- 2% of wallets hit the pagination cap, so their trades are missing.
- Kalshi data is unavailable.
- No future work is stated.

## Critical assessment

**Sampling bias.**
- Accounts enter through recent trades on 10 high-volume events, so selection favours
  frequent and active traders (length-biased).
- The seed events tilt toward sports, crypto ranges and "mention/count" markets.
- "Typical user" therefore means the typical account active on popular markets in spring 2026,
  not the typical wallet. Compare Akey et al.: median lifetime of 28 trades across all wallets.

**Ambiguous statistics.**
- The topic chart reports **medians** but the text says "an average of 69 trades".
- "Average trader spent $600", "value of the average trade $6.50" and the median of 46 trades
  are not mutually consistent unless they mix means and medians: $600 / 46 ≈ $13 per trade.
- PnL construction is undocumented. Over six weeks, unresolved positions and redemption timing
  can dominate small net figures such as "lost under $2".

**API limits.**
- The Data API activity feed mixes TRADE, SPLIT, MERGE, REDEEM and REWARD records. It is
  unclear which ones count as trades or in PnL.
- The 4,000-item cap is per call. 15 pulls over six weeks may still miss the activity of
  high-frequency bots.

**Useful as.** An independent, recent (2026) behavioural snapshot. Small trade sizes ($4–$9)
fit the 2026 shift toward high-frequency short-dated crypto and sports markets.

**Trust.**

| Claim | Trust | Reason |
| --- | --- | --- |
| Activity distribution (24 / 39 / 27 / 11%) | **Medium-high** | Simple counts, but on a selected sample |
| Small typical net outcomes (58% within ±$100) | **Medium** | PnL undefined; six-week window |
| Heavy traders lose more often (33% vs 27% beyond ±$1k) | **Medium** | Small subgroup, about 1,300 accounts |
| Topic differences | **Medium** | Median/average wording is inconsistent |
| Trade-size figures | **Low-medium** | Mean or median, fill or order, not specified |

## Directions it opens

- **A population-level "typical user" panel from on-chain fills** (V1+V2) instead of API
  snowball sampling. Weight by wallet, by volume and by activity tier, and show how
  seed-sampling biases each statistic (replicate Pew's design within the full data).
- **Rolling six-week cohort dashboards:** trade counts, active days, trade size, and realised
  plus marked PnL by topic and tier, with a documented PnL definition (fills plus
  redemptions).
- **Polymarket US versus offshore comparison**, once US data becomes accessible.
- **Heavy-trader study:** do accounts with ≥1,000 trades in six weeks look like bots
  (inter-trade times, 5-min crypto markets)? Is their loss rate driven by fees or rebates
  after 2026?
- **Data API audit:** caps, activity types, and consistency with on-chain fills, for every
  product that relies on `/activity`.
