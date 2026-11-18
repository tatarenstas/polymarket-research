"""Backtest: hold a perps position for ~40 s across the hourly funding settlement.

Assumption under test (unverified, see docs/perps funding): every position open at the
end of the hourly window receives/pays the full hourly rate, regardless of how long it
was held. If Polymarket instead time-weights funding, this strategy earns ~nothing.

For every market and every hour with |rate| above a threshold:
  side   = short if rate > 0 (shorts receive), long if rate < 0
  entry  = mark price at T - pre_s, exit = mark price at T + post_s   (T = settlement)
  pnl    = side * (exit - entry)/entry + |rate| - fees
Two decision rules:
  oracle  — uses this hour's final rate (it is ~fully determined seconds before T,
            because it is the mean of 5-second premium samples over the hour)
  lagged  — uses the previous hour's rate only (strictly ex ante)
Fees: maker 0.0125% per side (both legs as post-only), taker 0.04% per side + half spread.

Data: public REST (/v1/info/funding, /v1/info/mark-history 1s). Cached under data/perps/.
Usage: uv run python research/perps_lp/funding_snipe_backtest.py --days 30
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import time
import urllib.parse
import urllib.request
from pathlib import Path

B = "https://api.perpetuals.polymarket.com/v1/info"
CACHE = Path("data/perps")
MAKER, TAKER = 0.000125, 0.0004


def get(path: str, **q):
    for a in range(5):
        try:
            with urllib.request.urlopen(f"{B}/{path}?" + urllib.parse.urlencode(q), timeout=30) as r:
                j = json.load(r)
            return j["data"] if isinstance(j, dict) and "data" in j else j
        except Exception:
            time.sleep(2 * (a + 1))
    return None


def funding_history(days: int) -> dict:
    f = CACHE / f"funding_{days}d.json"
    if f.exists():
        return json.loads(f.read_text())
    inst = get("instruments")
    now = int(time.time() * 1000)
    out = {}
    for i in inst:
        rates = {}
        for k in range((days + 3) // 4):
            page = get("funding", instrument_id=i["instrument_id"],
                       start_timestamp=now - (k + 1) * 4 * 86_400_000, end_timestamp=now - k * 4 * 86_400_000) or []
            for p in page:
                rates[int(p["timestamp"])] = float(p["funding_rate"])
            time.sleep(0.05)
        out[i["symbol"]] = {"id": i["instrument_id"], "category": i["category"], "rates": rates}
        print(f"  funding {i['symbol']}: {len(rates)} h", flush=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(out))
    return out


def mark_window(iid: int, t_ms: int, pre: int, post: int, cache: dict) -> dict | None:
    key = f"{iid}:{t_ms}"
    if key not in cache:
        rows = get("mark-history", instrument_id=iid, interval="1s",
                   start_timestamp=t_ms - (pre + 5) * 1000, end_timestamp=t_ms + (post + 5) * 1000)
        cache[key] = {int(ts): float(p) for ts, p in (rows or [])}
        time.sleep(0.05)
    return cache[key] or None


def price_at(series: dict, ts: int) -> float | None:
    """Last mark at or before ts (1 s grid)."""
    ks = [k for k in series if k <= ts]
    return series[max(ks)] if ks else None


def main(days: int, threshold: float, pre: int, post: int, half_spread_bps: float) -> None:
    hist = funding_history(days)
    cache_f = CACHE / "mark_windows.json"
    cache = json.loads(cache_f.read_text()) if cache_f.exists() else {}
    trades = []
    for sym, h in hist.items():
        ts_sorted = sorted(int(t) for t in h["rates"])
        rates = {int(t): r for t, r in h["rates"].items()}
        for idx, t in enumerate(ts_sorted):
            r = rates[t]
            prev = rates[ts_sorted[idx - 1]] if idx > 0 else None
            for rule, signal in (("oracle", r), ("lagged", prev)):
                if signal is None or abs(signal) <= threshold:
                    continue
                side = -1 if signal > 0 else 1  # short when longs pay
                settle = (t // 1000) * 1000  # settlement stamps are hh:00:00.0xx
                w = mark_window(h["id"], settle, pre, post, cache)
                if not w:
                    continue
                p0, p1 = price_at(w, settle - pre * 1000), price_at(w, settle + post * 1000)
                if not p0 or not p1:
                    continue
                price_ret = side * (p1 - p0) / p0
                funding = -side * r  # short (side -1) receives r when r > 0
                trades.append({"sym": sym, "cat": h["category"], "t": t, "rule": rule, "rate": r,
                               "price_ret": price_ret, "funding": funding,
                               "net_maker": price_ret + funding - 2 * MAKER,
                               "net_taker": price_ret + funding - 2 * TAKER - 2 * half_spread_bps / 1e4})
    cache_f.write_text(json.dumps(cache))

    def summarize(rows: list[dict], label: str) -> None:
        if not rows:
            print(f"{label}: no trades")
            return
        span_days = (max(r["t"] for r in rows) - min(r["t"] for r in rows)) / 86_400_000 or 1
        nm = [r["net_maker"] for r in rows]
        nt = [r["net_taker"] for r in rows]
        pr = [r["price_ret"] for r in rows]
        fd = [r["funding"] for r in rows]
        print(f"{label}: n={len(rows)}, markets={len({r['sym'] for r in rows})}, ~{len(rows)/span_days:.1f} trades/day")
        print(f"   funding mean {st.mean(fd)*1e4:+.2f} bps | price mean {st.mean(pr)*1e4:+.2f} bps "
              f"(sd {st.pstdev(pr)*1e4:.2f}) | net maker mean {st.mean(nm)*1e4:+.2f} bps, "
              f"win {sum(x > 0 for x in nm)/len(nm):.0%} | net taker mean {st.mean(nt)*1e4:+.2f} bps")
        per10k = sum(nm) * 10_000 / span_days
        print(f"   maker P&L per $10k notional per trade-slot: ~${per10k:,.0f}/day if every signal traded at $10k")

    print(f"\nthreshold |rate| > {threshold*100:.4f}%/h, window -{pre}s/+{post}s, days {days}")
    for rule in ("oracle", "lagged"):
        rows = [r for r in trades if r["rule"] == rule]
        summarize(rows, f"[{rule}] all")
        by = {}
        for r in rows:
            by.setdefault(r["sym"], []).append(r)
        top = sorted(by.items(), key=lambda kv: -len(kv[1]))[:8]
        for sym, rs in top:
            nm = [x["net_maker"] for x in rs]
            print(f"     {sym:14} n={len(rs):4}  rate {st.mean([abs(x['rate']) for x in rs])*1e4:5.2f} bps/h  "
                  f"price {st.mean([x['price_ret'] for x in rs])*1e4:+6.2f}  net maker {st.mean(nm)*1e4:+6.2f} bps  "
                  f"win {sum(x > 0 for x in nm)/len(nm):.0%}")
    out = CACHE / "funding_snipe_trades.json"
    out.write_text(json.dumps(trades))
    print(f"\ntrades saved to {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--threshold", type=float, default=0.00025, help="|hourly rate| to trade (0.025%% = maker fees)")
    ap.add_argument("--pre", type=int, default=20)
    ap.add_argument("--post", type=int, default=20)
    ap.add_argument("--half-spread-bps", type=float, default=2.0)
    a = ap.parse_args()
    main(a.days, a.threshold, a.pre, a.post, a.half_spread_bps)
