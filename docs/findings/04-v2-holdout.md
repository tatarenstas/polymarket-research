# 04 — V2 holdout of H2 (longshot bias), 2026-04 → 2026-10

The rules were fixed on V1 (see `03-strategy-backtests.md`) and run unchanged on the V2
contract era. These data were never used to choose parameters. Script:
`research/backtest/h2_v2_holdout.py`; tape builder: `research/backtest/build_tape_v2.py`;
output: `data/h2_v2.log`.

**Universe.**
- V2 revision `d1a73f36`: markets listed ≥ 29 days before their scheduled close, with a
  scheduled close on or before 2026-11-01.
- The selection uses the scheduled close date, which is known in advance. It does not
  use resolution status, so it avoids keeping only markets that already resolved early
  (mostly "Yes" outcomes).
- 46.7K markets, of which 33.0K are resolved.
- Unresolved markets cluster among September–October closes: metadata lag, plus events
  still running, such as the Brazil election and the Fed meetings. Through August
  ≥ 96% are resolved.
- The robust run therefore keeps only markets closing on or before 2026-08-31.
- V2 fees are negligible (effective ~0.001–0.02% of notional).

## H2 taker rule across three independent periods

Rule: buy the opposite side when the reference last traded at 5–30¢ with ≥ 30 days to
scheduled close. Daily snapshots, the next real fill on our side ≥ 60 s later, one
entry per market, hold to resolution.

| Period | Markets | Win rate | Mean return / trade | Event-cluster mean | Cluster t | Hold (days) | Median fill |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| V1 train (2024 → 2025-06) | 5,071 | 88.2% | +3.8% | +5.7% | 6.6 | 106 | ~$5 |
| V1 test (2025-H2) | 6,022 | 88.2% | +1.7% | +2.1% | 2.5 | 48 | ~$4 |
| **V2 holdout, close ≤ 2026-08-31** | **3,375** | **87.6%** | **+3.9%** | **+5.8%** | **2.3** | **38** | **$1.5** |
| V2 holdout, all closes ≤ 2026-11-01 | 4,945 | 87.0% | +3.2% | +5.0% | 2.4 | 44 | $1.5 |

V2 by entry band (all closes): 5–10¢ **94.3% win, +5.8%**; 10–20¢ 86.2%, +1.1%;
20–30¢ 76.5%, +1.9%.

**Mirror check.** Buying the reference itself at 1–20¢ in V2 (close ≤ Aug): 7.9% win,
**−36.6% per trade, t −7.0**. The longshot bias is strong and persists in the new
contract era.

## Maker variant does not hold up in V2

| Period | Maker capital | Win rate | Capital-weighted return | Event-cluster mean | Cluster t |
| --- | ---: | ---: | ---: | ---: | ---: |
| V1 test | $1.3B | 91.4% | +7.9% | −0.2% | −0.3 |
| V2, close ≤ Aug | $595M | 82.8% | +1.5% | −0.7% | −0.8 |
| V2, all | $642M | 82.8% | +1.1% | −2.2% | −3.1 |

Resting orders that sell longshots get filled exactly when someone buys them, and
those buyers are sometimes informed: the largest losses are ceasefire and leadership
markets. The typical event is break-even or negative for the passive seller. The
profit comes from a handful of large events, which is not a robust edge.

## Correction: most of the measured edge comes from off-market fills

The entry proxy is "the next real taker fill on our side". Sometimes that fill sits far
from the last traded price: a stale state, a sudden repricing, or a tiny off-market
print. A real trader looking at the live book would not get such a price at size.
Split by |entry price − last price|, one entry per market:

| Period | ≤ 1¢ | 1–3¢ | 3–10¢ | > 10¢ |
| --- | ---: | ---: | ---: | ---: |
| V1 train | +3.6% | +2.1% | +3.7% | +12.6% |
| V1 test | +2.3% | +0.7% | −0.0% | +6.9% |
| V2 (close ≤ Aug) | +1.2% | +0.2% | +0.6% | **+22.3%** |

With a realistic guard (entry within 3¢ of the last price):

| Period | Markets | Win rate | Mean return | Cluster t |
| --- | ---: | ---: | ---: | ---: |
| V1 train | 4,615 | 88.9% | +3.3% | 6.9 |
| V1 test | 4,634 | 87.8% | +1.1% | 1.0 |
| V2 holdout | 2,490 | 88.0% | +0.65% | 1.3 |

**Revised verdict:** the longshot bias is real on the *buy* side. Buying Yes at 1–20¢
loses 12–37%. But a taker who sells it (buys No at the ask) at realistic prices earns
only ~0.5–1% per trade out of sample, and that is not statistically significant. The
bias is roughly the size of the spread. The earlier "+3–4%" is an artefact of the fill
proxy, so the table above supersedes the conclusion below.

## Conclusion (before the correction, kept for the record)

- **H2 as a taker rule passed all three periods, including a genuine out-of-era
  holdout.** It returns +2–4% per trade at a ~87–88% win rate over a 1–3 month hold.
  The 5–10¢ band is the strongest.
- **The binding constraint is capacity, not the edge.** The fills we copy are
  $1.5–5. Whether larger orders can be filled near those prices depends on order-book
  depth at the moment of entry. No historical source records that depth.
- The maker approach gets adversely selected and is **not supported**.

## Decision-relevant next step

Live order-book collector for the long-dated longshot universe. It should record the
ask depth on the opposite side at 5–30¢ reference prices, measure the executable
average price for $100 / $1k / $10k orders, and paper-trade the H2 rule forward with
size-aware fills and per-event exposure limits.
