# 09 — Market making on Polymarket prediction markets with liquidity rewards

Date: 2026-11-14. Status: opportunity survey. A snapshot of rewards and competition plus a
historical estimate of adverse selection. No paper test yet. Not investment advice.

**Scripts:**
- `research/pm_mm/reward_scan.py` — snapshot of rewards versus competition;
- `research/pm_mm/maker_edge_v2.py` — maker income before rewards, V2 tape.

**Logic:** `src/pmresearch/pm_rewards.py`, tests `tests/test_pm_rewards.py`.

## 1. Mechanics (official documentation, read 2026-11-14)

**Liquidity rewards (`market-makers/liquidity-rewards`):**
- Each market has its own parameters: `rate_per_day`, `rewards_max_spread` v (¢) and
  `rewards_min_size` (shares).
- Order score: `S = ((v − s)/v)² `, where s is the distance in cents from mid. Mid is
  computed without levels smaller than min size.
- `Q_one` = YES bids + NO asks, `Q_two` = YES asks + NO bids.
  `Q_min = max(min(Q1,Q2), max(Q1,Q2)/3)` if mid is in [0.10, 0.90]. Outside this range
  `Q_min = min(Q1,Q2)`, so both sides are required.
- **Distribution:** the book is sampled once a minute (up to 1440 samples per day); share =
  our `Q_min` / sum of `Q_min` over all makers. Paid daily at 00:00 UTC, minimum $1.
- An order counts immediately; the exception is markets with a taker delay (sports after
  game start).

**Two-sided order without inventory:** bids on YES and on NO at the same time. Capital =
shares × (1 − spread).

**Fees (`trading/fees`):**
- Makers pay nothing.
- Takers pay `C·feeRate·p(1−p)`, where feeRate is 0.04–0.07; geopolitics is free.
- Maker rebate: 15–25% of taker fees (`programs/maker-rebates`).
- In the V2 tape the effective fee is ≈ 0.002% of volume, so we do not count rebates yet.

## 2. Reward pool now (2026-11-14 00:29 UTC)

**Total:** 11 096 markets with active rewards, **~$205k per day**. 1469 markets have
≥ $20 per day ($170k combined).

**Concentration:** the top 10 markets are 26% of the pool, the top 100 are 54%. The largest
pools are temporary, on fresh news: "FAA ground stop" — $48.8k per day for 1–2 days,
LoL Worlds — $29k.

**Parameters (typical):** v = 4.5¢ (6242 markets) or 6.5¢ (4056); min size 20 shares (7979
markets).

**Estimate:** what a $1000 two-sided order sitting at the best bid/ask earns against the
current book. This is an estimate of the reward share, not profit: fills and price moves
are not included.

| Sample | Markets | Median, $/day per $1k | p75 | p90 |
| --- | ---: | ---: | ---: | ---: |
| All (pool ≥ $20 per day) | 1463 | 7.4 | 18.6 | 36.5 |
| To close > 7 days | 1092 | 5.9 | 17.3 | 33.0 |
| > 7 days, mid 0.10–0.90 | 886 | 6.5 | 18.5 | 34.8 |
| < 2 days (news) | 214 | 11.4 | 26.4 | 61.0 |

**How to read this:**
- **A median of $6–7 per day per $1000 is ~0.6–0.7% of capital per day.** Many markets have
  a thin book within v, so even $1000 takes a large slice of the pool.
- **This is an upper bound.** One book snapshot. Other makers react. The share in any single
  market is capped by the pool ($100–300 per day).
- **Scales poorly:** a second $1000 in the same market earns less. It needs many markets
  at $200–1000 each.

## 3. How much a maker loses on fills (V2 tape, 2026-04 → 2026-10, before rewards)

27.8M trades, $5.8B of maker capital. Result per $ of capital, cluster t (cluster =
event).

**Overall: −0.32% to resolution**, not statistically different from zero.

**By trade price:**

| Price | To resolution | Price move over 1 h | Over 1 day | t |
| --- | ---: | ---: | ---: | ---: |
| 0–5¢ | +0.28% | +0.05% | +0.09% | 6.3 |
| 5–10¢ | +1.88% | +0.11% | +0.29% | 1.9 |
| 10–20¢ | −2.08% | +0.12% | +0.46% | −0.9 |
| 20–40¢ | −0.70% | **−0.81%** | −1.16% | −0.4 |
| 40–60¢ | −4.20% | **−1.19%** | −4.49% | −1.7 |
| 60–80¢ | −0.95% | **−1.19%** | −1.33% | −0.2 |
| 80–90¢ | +4.60% | −0.22% | +4.82% | 1.0 |
| 95–100¢ | +0.20% | −0.03% | +0.19% | 2.3 |

**By time to close:**

| To close | To resolution | Price move over 1 h | t |
| --- | ---: | ---: | ---: |
| < 1 day | −1.14% | −0.60% | −1.0 |
| 1–7 days | −0.85% | +0.05% | −1.0 |
| **7–30 days** | **+0.29%** | −0.03% | 1.4 |
| **> 30 days** | **+0.10%** | 0.00% | 0.8 |

**By category:** sports −0.71%, crypto −0.95% (t −2.0), politics −0.10%; macro +0.61%,
geopolitics +0.77%. The geopolitics and macro results rest on a few events.

**Conclusions:**
1. **A passive maker breaks roughly even on average before rewards.** So rewards
   (~0.6%/day in the snapshot) are almost pure income, if the losing spots are avoided.
2. **Where makers lose:** prices 20–80¢ (within an hour the price moves ~1% against the
   maker) and markets closing in < 7 days, especially news markets.
3. **Where it is safer:** markets with > 7 days to close. There the price move after a
   fill is ≈ 0.
4. **Tape limitation:** only markets created ≥ 29 days before close. 1–2 day news markets
   (with the largest pools) are barely represented here, and that is where adverse
   selection is strongest (see the H2 maker in `04`).

## 4. What is unknown and decides everything

1. **How much of our capital gets filled per day.** Losses ≈ fill share × ~1% (in the
   20–80¢ zone). If 50% of quotes fill per day, losses are ~0.5% per day — comparable to
   rewards.
2. **Stability of the share through the day.** The 00:29 UTC snapshot may be atypical: the
   book changes, makers come and go.
3. **Queue position.** Rewards do not depend on it, but fills do.
4. **Actual payouts.** Visible only on our own address after a micro-live run.

## 5. Next step

**Paper test for 48–72 h:**
- **Markets:** 20–40 with > 7 days to close, mid 0.10–0.90, the best reward estimate per
  $ and no news events.
- **Quotes:** a virtual two-sided order of $200–500 per market at the best bid/ask.
- **Rewards:** sample the book once a minute and compute the exact share by the formula,
  including our orders.
- **Fills:** from the WebSocket trade stream, with a queue — a fill only after the volume
  that stood ahead of us has traded through.
- **Risk:** inventory and per-market limits; price move after a fill at 1 min, 1 h and
  1 day; PnL at mid.
- **Success criterion:** rewards minus fill losses > 0 under a conservative queue model.

## 6. Paper test: started 2026-11-18 00:31 UTC (72 h)

**Code:**
- `research/pm_mm/run_paper.py` — launcher;
- `src/pmresearch/pm_mm_paper.py` — logic, tests `tests/test_pm_mm_paper.py`;
- `research/pm_mm/report_paper.py` — report.

**Data:** `data/pm_mm/paper/20261118T003053Z/`. Read-only: public REST and WebSocket,
no orders.

**Verified live on the market WebSocket:**
- each trade arrives once, as `last_trade_price` on the taker's token;
- a trade on NO (side, price q) is a trade on YES with the opposite side at price 1 − q;
- the YES and NO books are mirrors, so all liquidity is visible in the YES book.

**Market selection:**
- rewards ≥ $20 per day, > 7 days to close;
- mid in 0.10–0.90, both best levels within v;
- at most 2 markets per event;
- top 30 by reward estimate per $.

Total pool $3 989 per day. **Most selected markets are nearly empty:**
- Rotten Tomatoes, "what will Trump say at APEC", ECB, house prices;
- within v there are only tens of shares, so our $300 order would take 50–90% of the pool.

This is exactly what the test should check: whether rewards in the "long tail" really sit
uncollected.

**Quotes:** $300 per market, bids on YES and NO at the same time, no inventory.

**Four virtual makers per market:**

| Variant | Price | Fill model | Latency |
| --- | --- | --- | --- |
| `join_q` (main) | best bid/ask | queue | 1 s |
| `join_touch` | best bid/ask | any trade at our price (upper bound on fills) | 1 s |
| `back1_q` | 1¢ worse than the best level | queue | 1 s |
| `join_q_slow` | best bid/ask | queue | 5 s |

**Queue model:**
- We join the back of the level.
- Trades at our price first eat the queue ahead of us.
- Cancellations cap the queue at the level size, with a 1 s delay.
- A trade at a worse price (through us) fills us for its volume.

**Quoting rules:**
- do not quote a side outside v;
- do not place bid ≥ mid or ask ≤ mid;
- limit |YES − NO| = quote size.

**Rewards:** once a minute by the official formula against the live book.

**What is measured:**
- inventory PnL at mid;
- mid move after a fill at 1 min, 1 h, 1 day;
- **criterion:** rewards + inventory PnL > 0 for `join_q` and `join_q_slow`.

**Known limitations:**
- our virtual orders do not affect the book;
- in empty markets a real order of ours would itself become the best level and could
  attract takers;
- actual payouts and the true pool split are visible only in a micro-live run.
