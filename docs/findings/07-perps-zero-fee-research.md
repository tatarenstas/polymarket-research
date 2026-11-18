# 07 — Can the fee be guaranteed to "zero out" on every BTC-perp trade

Question: is there a method (a hedge or anything else) that **deterministically, on every trade** covers
the fee on Polymarket Perps, using BTC as the example. Date: 2026-11-13. Not investment advice.

## 1. Documentation: deterministic ways to reduce or offset the fee

| Mechanism | What the documentation / API says | Does it give a guaranteed zero to a small account |
| --- | --- | --- |
| Volume tiers | maker 0% from $500M over 30 days, rebate −0.005% from $1B | Rejected: needs hundreds of millions in volume |
| Beta tier | some beta accounts are temporarily on the top tier | only if your account is one of them (per your screenshot, no: taker 0.04%) |
| Fee override (`/v1/info/instruments`) | currently only ANT: taker 0.02%, maker 0.00625% (i.e. half) | Rejected: none on BTC; ANT is not zero |
| Builder codes | the builder fee is an **additional** charge; there is no share of the exchange fee; **builder and trader must be different accounts** | Rejected |
| Referral program | 20% of referees' fees; referring yourself is prohibited; the referee gets no discount | Rejected for your own trades |
| Account groups | can pool volume for the tier (opt-in) | Rejected without real large volume |
| Trading competitions | score = PnL × √(volume); prizes are irregular; wash, self- and multi-account trading disqualify | Rejected: not deterministic |
| Funding | hourly, from longs to shorts when premium ≈ 0 (+0.00125%/h) | Rejected: depends on holding time; the documentation does not say who receives the payment (holder at settlement or pro rata by time) |
| Liquidity rewards | a per-market pool for quoting within 20 bps | Rejected: accrued per day, not per trade; depend on competition |

## 2. Measurement: BTC on Polymarket vs Binance USDⓈ-M

Script: `research/perps_lp/btc_cross_venue_probe.py`. 30-minute recording: 9,559 Polymarket book
updates, 84 trades ($102k), 480k Binance updates.

| Metric | Result |
| --- | --- |
| Mid-price difference PM − BN | mean +0.17 bps, median +0.24, SD **0.46**, p5…p95 = −0.74…+0.76 bps |
| Time with deviation > 2.5 / 6.25 / 9 bps from the usual level | **0% / 0% / 0%** |
| Arbitrage with market orders on both venues (> 9 bps) | **0%** |
| Maker fills on PM with a hedge on BN that cover all fees | **0% of trades, 0% of volume** (latency 0.2, 1 or 3 s) |
| Average result of such a fill | taker hedge −7.1…−7.5 bps; maker hedge (not guaranteed) −4.1…−4.5 bps |

Fees combined: PM maker 1.25 bps + BN hedge 2–5 bps per leg. The Polymarket BTC price
deviates from Binance by tenths of a bp, so **"eating" the fee through the cross-venue
price difference is impossible**.

## 3. Conclusion

1. **Guaranteed coverage of the fee on every BTC trade is impossible for a small account.**
   There is no deterministic mechanism:
   - not in the documentation (no rebates on lower tiers, no fee share for builders,
     no self-referral);
   - not in the market (no price gap with Binance).
2. The fee can only be **minimized** and **covered statistically, on average**:
   - Post-only limit orders only: 0.025% per round trip instead of 0.08%;
   - funding on the short when holding 1–2 days or more (spot + short perp) — stable on
     average (`05`, §3);
   - liquidity rewards — summed per day, not per trade (stage 1 tests this);
   - funding for the full hour when holding across settlement — only during rate spikes
     and if the mechanics are confirmed (`06`).
3. **A hedge adds fees, it does not remove them.** It is needed against price risk, not to
   save on fees.
