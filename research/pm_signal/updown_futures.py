"""Does a Polymarket "BTC Up or Down" probability predict the Binance futures move?

Idea tested: when the Up probability of a 5m / 15m / 1h window crosses a threshold
(e.g. >= 0.7), open a BTCUSDT perp position in that direction and hold it to the window end.

Data (public, read-only):
  * Gamma events `btc-updown-{5m,15m,1h}-{start_ts}`: outcome and Up token id;
  * CLOB `prices-history` of the Up token (~1 point per minute);
  * Binance USD-M BTCUSDT 1-minute klines.
Entry is at the open of the first full minute after the signal (no look-ahead), exit at the
open of the minute when the window ends. Fees: taker 5 bps per side, maker 2 bps per side.
The market resolves on a Chainlink TWAP vs the start price; the trade earns the raw price
change from entry to window end.

Usage: uv run python research/pm_signal/updown_futures.py --days 7
Output: data/pm_signal/updown_<UTC>.json and printed tables.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics as st
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

GAMMA = "https://gamma-api.polymarket.com/events"
HIST = "https://clob.polymarket.com/prices-history"
KLINES = "https://fapi.binance.com/fapi/v1/klines"
WINDOWS = {"5m": 300, "15m": 900, "1h": 3600}
THRESHOLDS = (0.6, 0.7, 0.8, 0.9)
FEES_BPS = {"taker": 10.0, "maker": 4.0}  # round trip


def sess() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = "curl/8.7.1"
    return s


def fetch_market(s, w: str, start: int):
    step = WINDOWS[w]
    for a in range(3):
        try:
            j = s.get(GAMMA, params={"slug": f"btc-updown-{w}-{start}"}, timeout=20).json()
            if not j:
                return None
            m = j[0]["markets"][0]
            if not m.get("closed"):
                return None
            outcome = json.loads(m["outcomePrices"])
            up_won = float(outcome[0]) > 0.5
            tok = json.loads(m["clobTokenIds"])[0]
            h = s.get(HIST, params={"market": tok, "startTs": start, "endTs": start + step, "fidelity": 1},
                      timeout=20).json().get("history", [])
            return {"w": w, "start": start, "up_won": up_won, "hist": [(x["t"], x["p"]) for x in h]}
        except Exception:  # noqa: BLE001 - retry on network errors
            time.sleep(1 + a)
    return None


def klines(s, t0: int, t1: int) -> dict[int, float]:
    """minute start (s) -> open price."""
    out, cur = {}, t0 * 1000
    while cur < t1 * 1000:
        k = s.get(KLINES, params={"symbol": "BTCUSDT", "interval": "1m", "startTime": cur, "limit": 1500},
                  timeout=30).json()
        if not k:
            break
        for row in k:
            out[row[0] // 1000] = float(row[1])
        cur = k[-1][0] + 60_000
    return out


def evaluate(mk: list[dict], px: dict[int, float], thr: float) -> dict:
    rets, hits, cal = [], 0, []
    for m in mk:
        step = WINDOWS[m["w"]]
        end = m["start"] + step
        for t, p in m["hist"]:
            if t <= m["start"] or t >= end - 60:
                continue
            d = 1 if p >= thr else -1 if p <= 1 - thr else 0
            if not d:
                continue
            entry_min = (t // 60 + 1) * 60
            if entry_min >= end or entry_min not in px or end not in px:
                break
            r = d * (px[end] / px[entry_min] - 1) * 1e4
            rets.append(r)
            hits += r > 0
            cal.append((max(p, 1 - p), (m["up_won"] if d == 1 else not m["up_won"])))
            break  # first signal per window only
    if not rets:
        return {"n": 0}
    sd = st.pstdev(rets) or 1e-9
    return {
        "n": len(rets), "mean_bps": st.mean(rets), "t": st.mean(rets) / sd * math.sqrt(len(rets)),
        "hit": hits / len(rets), "median_bps": st.median(rets),
        "net_taker": st.mean(rets) - FEES_BPS["taker"], "net_maker": st.mean(rets) - FEES_BPS["maker"],
        "pm_prob": st.mean(c[0] for c in cal), "pm_won": st.mean(c[1] for c in cal),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=float, default=7)
    args = ap.parse_args()
    s = sess()
    now = int(time.time())
    t0 = now - int(args.days * 86400)
    jobs = []
    for w, step in WINDOWS.items():
        jobs += [(w, t) for t in range((t0 // step + 1) * step, now - step, step)]
    print(f"fetching {len(jobs)} markets ...", flush=True)
    with ThreadPoolExecutor(8) as ex:
        mk = [m for m in ex.map(lambda j: fetch_market(sess(), *j), jobs) if m and m["hist"]]
    px = klines(s, t0 - 3600, now + 60)
    out = Path("data/pm_signal") / f"updown_{time.strftime('%Y%m%dT%H%M', time.gmtime())}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"markets": mk}))
    print(f"{len(mk)} markets with history, {len(px)} Binance minutes; saved {out}\n")
    print(f"{'window':<6}{'thr':>5}{'n':>6}{'PM prob':>9}{'PM won':>8}{'hit':>7}{'mean bps':>10}{'t':>6}"
          f"{'median':>8}{'net taker':>11}{'net maker':>11}")
    for w in WINDOWS:
        sub = [m for m in mk if m["w"] == w]
        for thr in THRESHOLDS:
            r = evaluate(sub, px, thr)
            if not r["n"]:
                continue
            print(f"{w:<6}{thr:>5.1f}{r['n']:>6}{r['pm_prob']:>9.1%}{r['pm_won']:>8.1%}{r['hit']:>7.1%}"
                  f"{r['mean_bps']:>+10.2f}{r['t']:>6.1f}{r['median_bps']:>+8.2f}{r['net_taker']:>+11.2f}{r['net_maker']:>+11.2f}")


if __name__ == "__main__":
    main()
