# 12 — Do Polymarket news-market shocks lead BTC?

Date: 2026-11-25. Status: tested, rejected at minute resolution. Not investment advice.

**Question:** when a Polymarket market on news (geopolitics, Fed/macro, politics, crypto
regulation) jumps, has Binance already priced it, or does BTC follow later?

**Script:** `research/pm_signal/news_shocks.py`. **Data:** V2 tape 2026-04 → 2026-11 (markets
listed ≥ 29 days before close), Binance BTCUSDT 1-minute closes.

**Shock:** the minute VWAP of one market moves ≥ 10 pp within 5 minutes with ≥ $10k traded,
starting from 5–95¢; one shock per event cluster per 2 hours; crypto price markets excluded.
**182 shocks**: 91 geopolitics (mostly US–Iran deal markets), 65 politics, 23 Fed/macro, 3 crypto.

**BTC |return| around shocks vs random minutes, bps (mean):**

| Window (minutes from the shock) | −60…−5 | −5…0 (the shock) | 0…5 | 5…30 | 30…120 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Random minutes | 25.1 | 7.6 | 7.6 | 17.1 | 32.4 |
| All shocks | 28.6 | **21.0** | 12.7 | 26.2 | 38.6 |
| Geopolitics | 32.2 | 25.5 | 14.1 | 31.6 | 36.5 |
| Politics | 27.3 | 13.8 | 9.7 | 22.0 | 38.2 |
| Fed / macro | 19.2 | 25.0 | 16.0 | 17.0 | 49.5 |

**Findings:**
1. **BTC moves in the same minutes as the Polymarket jump** (2.8x normal during the shock
   window). When the news matters for BTC, Binance reacts at the same time, not later.
2. **When BTC did not react during the jump (57 shocks, |move| < 5 bps), it did not react
   later either:** next 5 minutes 6.3 vs 6.0 bps for comparable quiet random minutes, next
   30 minutes 16.4 vs 15.1. A Polymarket jump that Binance ignores is news that doesn't move BTC.
3. **What remains is BTC's own post-news momentum,** visible on Binance without Polymarket:
   continuing BTC's move from the shock window earns +3.1 bps over the next 5 minutes (t 2.3)
   and +6.1 bps over 5–30 minutes (t 2.2). That is below a 10 bps taker round trip and at best
   break-even for a maker.
4. The largest shocks are scheduled events (FOMC at 18:00 UTC), where every venue sees the
   news simultaneously.

**Limits:** minute bars (a sub-minute lead would be invisible but is unusable without
low-latency infrastructure anyway); tape covers only markets listed ≥ 29 days before close,
so fast news markets are under-represented; BTC only, not oil, equities or FX, where
geopolitical markets might matter more.

**Verdict:** rejected for BTC. Polymarket news markets reprice at the same time as Binance,
not before it.
