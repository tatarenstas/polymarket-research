"""Do sharp probability moves in Polymarket news markets lead BTC on Binance?

Universe: V2 tape (2026-04 → 2026-11) markets in news categories that can move crypto
(Iran / geopolitics / Middle East / Strait of Hormuz / Israel / Ukraine peace, Fed / FOMC /
economy / economic policy, oil / commodities, Trump / politics, crypto non-price markets).
Crypto price markets (Bitcoin, Ethereum, "up or down", "above", "reach", "dip", "price")
are excluded because they follow BTC by construction.

Shock: in one market, the minute VWAP moves >= --jump (default 0.10) within 5 minutes,
with >= --min-usd traded in those minutes, starting from a price in [0.05, 0.95]. One shock
per event cluster (NegRisk group or market) per 2 hours; the shock time t0 is the end of
the 5-minute window (the first minute when the move is complete).

Event study on Binance BTCUSDT 1-minute closes around t0:
  * |return| in windows before and after t0, against the same windows at random times;
  * whether BTC's post-shock move continues the move BTC already made in the shock window.

Usage: uv run python research/pm_signal/news_shocks.py
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics as st
import time
from pathlib import Path

import duckdb
import requests

CATS = ("Iran", "Iran Regime", "Strait of Hormuz", "Geopolitics", "Middle East", "Israel", "Ukraine Peace Deal",
        "Economy", "Economic Policy", "fomc", "Fed", "Oil", "Commodities", "Trump", "Trump Presidency", "Politics",
        "Crypto")
PRICE_WORDS = ("up-or-down", "above", "reach", "dip", "price", "hit", "between", "updown")
WINDOWS = {"pre60_5": (-60, -5), "shock_5_0": (-5, 0), "post0_5": (0, 5), "post5_30": (5, 30), "post30_120": (30, 120)}
KLINES = "https://fapi.binance.com/fapi/v1/klines"


def btc_closes(t0: int, t1: int, cache: Path) -> dict[int, float]:
    if cache.exists():
        return {int(k): v for k, v in json.loads(cache.read_text()).items()}
    s = requests.Session()
    s.headers["User-Agent"] = "curl/8.7.1"
    out, cur = {}, t0 * 1000
    while cur < t1 * 1000:
        k = s.get(KLINES, params={"symbol": "BTCUSDT", "interval": "1m", "startTime": cur, "limit": 1500},
                  timeout=30).json()
        if not k:
            break
        for row in k:
            out[row[0] // 1000 + 60] = float(row[4])  # close, keyed by minute END
        cur = k[-1][0] + 60_000
        time.sleep(0.05)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(out))
    return out


def shocks(jump: float, min_usd: float) -> list[dict]:
    con = duckdb.connect()
    cats = ",".join(f"'{c}'" for c in CATS)
    excl = " and ".join(f"slug not like '%{w}%'" for w in PRICE_WORDS)
    rows = con.execute(f"""
    with t as (
      select cid, coalesce(nrm, cid) cl, category, slug, (ts // 60 + 1) * 60 as m, p, usdc
      from 'data/tape/v2/*.parquet'
      where category in ({cats}) and ({excl}) and p > 0 and p < 1
    ),
    b as (
      select cid, any_value(cl) cl, any_value(category) category, any_value(slug) slug, m,
             sum(p * usdc) / sum(usdc) vwap, sum(usdc) usd
      from t group by cid, m
    ),
    w as (
      select *, lag(vwap) over (partition by cid order by m) prev_vwap,
             lag(m) over (partition by cid order by m) prev_m
      from b
    ),
    j as (  -- compare each minute with the last price at least 5 minutes earlier
      select b1.cid, b1.cl, b1.category, b1.slug, b1.m, b1.vwap p1, b0.vwap p0,
             (select sum(usd) from b b2 where b2.cid = b1.cid and b2.m > b1.m - 300 and b2.m <= b1.m) usd5
      from b b1 asof join b b0 on b0.cid = b1.cid and b0.m <= b1.m - 300
      where b1.m - b0.m <= 900
    )
    select cid, cl, category, slug, m, p0, p1, usd5 from j
    where abs(p1 - p0) >= {jump} and usd5 >= {min_usd} and p0 between 0.05 and 0.95
    order by m
    """).fetchall()
    out, last = [], {}
    for cid, cl, cat, slug, m, p0, p1, usd in rows:
        if m - last.get(cl, -10**12) < 7200:
            continue
        last[cl] = m
        out.append({"cid": cid, "cat": cat, "slug": slug, "t0": int(m), "p0": p0, "p1": p1, "usd": usd})
    return out


def ret(px: dict[int, float], t: int, a: int, b: int) -> float | None:
    x, y = px.get(t + a * 60), px.get(t + b * 60)
    return None if x is None or y is None else math.log(y / x) * 1e4


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jump", type=float, default=0.10)
    ap.add_argument("--min-usd", type=float, default=10_000)
    args = ap.parse_args()
    ev = shocks(args.jump, args.min_usd)
    print(f"{len(ev)} shocks (|dp| >= {args.jump}, >= ${args.min_usd:,.0f} in 5 min)")
    t0, t1 = min(e["t0"] for e in ev) - 4 * 3600, max(e["t0"] for e in ev) + 4 * 3600
    px = btc_closes(t0, t1, Path("data/pm_signal/btc_1m_v2.json"))
    keys = sorted(px)
    random.seed(1)
    base_t = [keys[random.randrange(200, len(keys) - 200)] // 60 * 60 for _ in range(20000)]

    def prof(times):
        res = {}
        for name, (a, b) in WINDOWS.items():
            v = [abs(r) for t in times if (r := ret(px, t, a, b)) is not None]
            res[name] = (st.mean(v), st.median(v), len(v)) if v else (float("nan"),) * 3
        return res

    base = prof(base_t)
    print(f"\nBTC |return| in bps around shocks vs random minutes (mean / median):")
    print(f"{'group':<14}{'n':>5}" + "".join(f"{k:>18}" for k in WINDOWS))
    groups = {"all": ev}
    for e in ev:
        g = ("geopol" if e["cat"] in CATS[:7] else "macro" if e["cat"] in CATS[7:11] else
             "commod" if e["cat"] in CATS[11:13] else "politics" if e["cat"] in CATS[13:16] else "crypto")
        groups.setdefault(g, []).append(e)
    print(f"{'random':<14}{len(base_t):>5}" + "".join(f"{base[k][0]:>9.1f}/{base[k][1]:<8.1f}" for k in WINDOWS))
    for g, es in groups.items():
        r = prof([e["t0"] for e in es])
        print(f"{g:<14}{len(es):>5}" + "".join(f"{r[k][0]:>9.1f}/{r[k][1]:<8.1f}" for k in WINDOWS))

    # continuation: does BTC keep moving the way it moved during the shock window?
    print("\ncontinuation of BTC's own shock-window move (sign of [-5,0] applied to later windows):")
    for g, es in groups.items():
        line = []
        for name in ("post0_5", "post5_30", "post30_120"):
            a, b = WINDOWS[name]
            v = []
            for e in es:
                s0, r1 = ret(px, e["t0"], -5, 0), ret(px, e["t0"], a, b)
                if s0 and r1 is not None:
                    v.append(math.copysign(1, s0) * r1)
            if v:
                sd = st.pstdev(v) or 1e-9
                line.append(f"{name}: {st.mean(v):+6.1f} bps (t {st.mean(v) / sd * math.sqrt(len(v)):+.1f}, n {len(v)})")
        print(f"  {g:<10}" + " | ".join(line))
    Path("data/pm_signal/news_shocks.json").write_text(json.dumps(ev))
    print("\nlargest shocks:")
    for e in sorted(ev, key=lambda e: -e["usd"])[:15]:
        print(f"  {time.strftime('%Y-%m-%d %H:%M', time.gmtime(e['t0']))} {e['p0']:.2f}->{e['p1']:.2f} "
              f"${e['usd']:>9,.0f} pre {ret(px, e['t0'], -60, -5) or 0:+6.0f} shock {ret(px, e['t0'], -5, 0) or 0:+5.0f} "
              f"post5 {ret(px, e['t0'], 0, 5) or 0:+5.0f} post30 {ret(px, e['t0'], 5, 30) or 0:+5.0f}  {e['slug'][:55]}")


if __name__ == "__main__":
    main()
