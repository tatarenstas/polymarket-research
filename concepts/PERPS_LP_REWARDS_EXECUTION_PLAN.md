# Execution plan: market making for liquidity rewards on Polymarket Perps with a hedge

Status: plan. Basis: the paper test `research/perps_lp/run_paper.py` (interim
results over 12 h) and live exchange data as of 2026-11-13. Numbers, strategy catalog and
profit estimates: `docs/findings/05-perps-strategies.md`. This is not investment advice.
Before starting, check each exchange's terms and availability in your jurisdiction.

## 1. Strategy in brief

```
income = liquidity rewards ($75k/day ÷ 90 markets ≈ $833 per market)
       + spread (bought at bid, sold at ask)
costs  = Polymarket maker fee 0.0125%
       + hedge on another exchange (fee + slippage)
       + adverse selection (price moves against you after the fill)
       ± funding difference between Polymarket and the hedge exchange
```

1. Limit orders (post-only) rest on Polymarket on both sides within 5 bps of the mid
   price. This gives the maximum weight in rewards.
2. When an order fills, the opposite position is opened on the hedge exchange, so price
   risk ≈ 0.
3. Positions on both exchanges grow when fills come mostly from one side. Quotes
   are shifted (skew) so that Polymarket fills bring the position back to zero. Then the hedge
   is closed.

## 2. Where to hedge (checked via public APIs on 13.11.2026)

| Polymarket asset | Best hedge | 24 h volume | Spread | Alternatives | Assessment |
| --- | --- | ---: | ---: | --- | --- |
| **ZEC** | Binance USDⓈ-M perp ZECUSDT | $2.1B | 0.1 bps | Bybit ($443M), Hyperliquid ($536M), OKX | Works: best |
| **SOXL** | Binance USDⓈ-M perp SOXLUSDT | $5.0B | 1.5 bps | Bybit ($930M), Hyperliquid xyz:SOXL ($300M), OKX | Works: excellent, 24/7 |
| **BTC** | any | billions | 0.01 bps | — | Works, but strong competition on Polymarket |
| **XMR** | Binance XMRUSDT | $119M | 0.2 bps | Hyperliquid ($92M), Bybit | Works |
| **PONS** | Binance PONSUSDT | $37M | 6.4 bps | Bybit ($16M), Hyperliquid ($4M), OKX | Caution: hedge is expensive (wide spread) |
| **ASML** | Binance ASMLUSDT | $3.3M | 3.1 bps | Hyperliquid xyz:ASML ($0.6M), OKX, Bybit | Caution: thin; or the stock at a broker during exchange hours |
| **STRC** | Binance STRCUSDT | $9.9M | 1.0 bps | Hyperliquid xyz:STRC, OKX | Caution: no fills on Polymarket |
| ANT | Binance/OKX "ANTHROPIC", Hyperliquid xyz:ANT ($38M) | — | — | — | check that it is the same underlying asset |

**Mandatory check before use.** Same ticker ≠ same asset. Compare the
index, price source, contract multiplier and settlement rules (especially for stocks and pre-IPO).
For stocks, a 24/7 perp on the hedge exchange and the perp on Polymarket may behave differently
when the stock exchange is closed.

**Funding on the hedge leg.** The hedge perp also pays or receives funding. Add the rate difference
to the calculation: rates on both venues are currently close to baseline, so the impact is small, but
it must be monitored.

## 3. Market selection

Criteria, all together:
1. Liquid 24/7 hedge: spread ≤ 2 bps, volume ≥ $50M per day.
2. Moderate competition on Polymarket: weighted liquidity within 20 bps ≤ ~$300k.
3. Enough fills to hold ≥ 1% of the market's maker volume over 7 days.
4. Price move after the fill (markout) over 10–60 s no worse than −5 bps on average.

First-wave candidates: **SOXL, ZEC**. Then XMR, ANT (after identity check),
ASML (only if the hedge is deep enough).

## 4. Capital (example for $9k)

| Item | Amount |
| --- | ---: |
| Polymarket margin (2 markets × position up to $5k at 3x, plus margin for quotes) | ~$4k |
| Hedge exchange margin (same positions at 3x) | ~$3.5k |
| Reserve for rebalancing between exchanges | ~$1.5k |

- Leverage 2–3x. Polymarket liquidation fee 0.5% of notional.
- Position limit per market: $5k. Global limit: $10k gross.

## 5. Bot architecture

```
WS Polymarket (book, trades, own orders and fills)      WS hedge exchange (book, own fills)
            │                                                     │
            ▼                                                     ▼
       Market state ──► Quoting engine ──► Polymarket REST (post-only GTC, batch, modify)
            │                 ▲
            │                 │ inventory, skew
            ▼                 │
       Fill handler ──► Hedge engine ──► hedge exchange (IOC/limit; minimum size threshold)
            │
            ▼
   Risk manager (limits, margin on both exchanges, kill switch, auto-cancel)
            │
            ▼
   Log (all orders, fills, hedges, rewards) ──► daily reconciliation and report
```

**Polymarket Perps API (from the documentation):**
- `POST /trade/orders` with the `po` (post-only) flag and `tif=gtc`;
- `PATCH /trade/orders` to change the price without cancel/create;
- `DELETE /trade/orders/all` and **auto-cancel (dead-man switch)**: must be re-armed
  every few seconds so that orders are pulled automatically if the bot crashes;
- limit of 200 open orders per market;
- EIP-712 signature with a proxy key.
- **Important detail:** new orders may pass through a "taker delay queue". It looks like a
  speed bump for takers that gives the maker time to cancel an order. Check how exactly it
  works: it reduces adverse selection.

**Quoting logic:**
- price: mid ± 2–4 bps (within weight 1.0), on the market's tick grid;
- size: $2–5k per side;
- skew: at a position of +X% of the limit, shift both prices down by k·X bps (and vice versa);
- requote when mid moves > 1 bps or once every N seconds (respect the rate limit);
- quoting pause: sharp move (|Δmid| > 15 bps in 5 s), gap with the hedge exchange > 10 bps,
  data lag > 2 s.

**Hedge logic:**
- after each fill, hedge the net position if it is > the exchange's minimum lot;
- hedge with an IOC order on the hedge exchange; alternative: a limit hedge with a timeout;
- compare the actual hedge price with the mid at the moment of the Polymarket fill (slippage metric).

## 6. Rollout stages and promotion criteria

| Stage | What we do | Duration | Criterion to move on |
| --- | --- | --- | --- |
| 0. Legal and accounts | Check ToS and availability of Polymarket Perps and the hedge exchange; KYC; API keys **trading only, no withdrawal**, with IP whitelist; keys in macOS Keychain, not in code | 1–3 days | accounts and keys ready |
| 1. Longer paper test | 72+ h on SOXL, ZEC, XMR, ANT; **hedge with realistic latency** (hedge price = mid after 1–3 s + hedge exchange spread) | 3–4 days | net result > 0 on ≥ 2 markets with a conservative reward estimate |
| 2. Shadow mode | Bot runs on live data from both exchanges, computes which orders it would place, but does not send them; measure latency to both APIs | 2–3 days | latency to Polymarket and the hedge is stable; skew/pause logic works |
| 3. Micro-live | $200–500 per side, 1 market (SOXL or ZEC); real hedge; daily reconciliation | 7 days | **actually credited rewards** ≥ 50% of the estimate; net ≥ 0 |
| 4. Scaling | $2–5k per side, 2–3 markets | 2–4 weeks | stable net > 0 every week |
| 5. Rotation | Daily re-evaluation of markets by competition, reward per $ and markout | ongoing | — |

## 7. Risks and safeguards

| Risk | Safeguard |
| --- | --- |
| Adverse selection (informed takers) | wide offset in volatile moments, pause on sharp moves, daily markout monitoring |
| Hedge latency / one leg unhedged | position limit, IOC hedge, kill switch if the hedge exchange is unavailable |
| Liquidation of a leg | leverage ≤ 3x, margin alerts, rebalancing reserve |
| Bot crash | auto-cancel (dead-man switch) on Polymarket, watchdog process |
| `cancel_only` mode / maintenance | error handling → pull quotes, keep the hedge |
| Change to reward program rules | monitor docs/changelog; daily reconciliation of actual rewards |
| Different underlying assets under one ticker | manual check of specifications before launching each market |
| Key security | keys without withdrawal rights, IP whitelist, Keychain, no logging of secrets |
| Self-trading / multiple accounts | prohibited: one account, no wash trades |

## 8. Metrics (daily report)

- **Rewards:** actually credited vs. estimate; share of maker volume; uptime of both
  sides.
- **Trading:** fills; notional; spread PnL; fees; hedge cost; markout at 10, 60
  and 300 s.
- **Risk:** maximum position; margin usage on both exchanges; funding flow.
- **Net PnL** per market and overall; return on capital.

## 9. Open questions

1. How exactly the "taker delay queue" on Polymarket Perps works and whether it protects makers.
2. Whether orders modified via `PATCH` keep counting toward rewards without losing priority
   (impact on uptime).
3. Real reward share vs. estimate. The split between makers is not visible from the public book,
   so only micro-live will give the answer.
4. Whether the underlying assets and indices for ASML, SOXL, ANT are the same on Polymarket and the hedge exchanges.
