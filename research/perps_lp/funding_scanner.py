"""Live funding scanner for Polymarket Perps (read-only, public API, places no orders).

Every --poll seconds it reads /v1/info/tickers (one request covers all markets) and prints
the markets with the largest |funding| for the current hour:
  rate %/h, side that receives it, time to settlement, OI, net bps after a maker / taker
  round trip, and for candidates the book spread and depth within 10 bps.

SIGNAL: |rate| >= --min-rate and settlement within --window seconds. Alerts once per market
and hour (terminal bell, plus a macOS notification with --notify).

Accuracy check: for every market with |rate| >= --track, the last estimate before
settlement is stored. ~30 s after settlement the realized rate is fetched from
/v1/info/funding and both are logged, so the log shows whether the ticker estimate
seconds before T predicts the paid rate.

Logs: data/funding_scanner/<YYYYMMDD>.jsonl (events: signal, settled).

Usage:
  uv run python research/perps_lp/funding_scanner.py                 # loop
  uv run python research/perps_lp/funding_scanner.py --once          # one table
  uv run python research/perps_lp/funding_scanner.py --min-rate 0.0005 --window 120 --notify
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from pmresearch.funding_scan import Row, book_metrics, is_signal, parse

B = "https://api.perpetuals.polymarket.com/v1/info"
LOG_DIR = Path("data/funding_scanner")


def get(path: str, **q):
    url = f"{B}/{path}" + ("?" + urllib.parse.urlencode(q) if q else "")
    for a in range(3):
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                j = json.load(r)
            return j["data"] if isinstance(j, dict) and "data" in j else j
        except Exception:
            time.sleep(1 + a)
    return None


def log(event: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_DIR / f"{dt.datetime.now():%Y%m%d}.jsonl", "a") as f:
        f.write(json.dumps(event) + "\n")


def notify(title: str, msg: str) -> None:
    try:
        subprocess.run(["osascript", "-e", f'display notification "{msg}" with title "{title}"'],
                       timeout=5, check=False, capture_output=True)
    except Exception:
        pass


def fmt_ttl(s: float) -> str:
    s = max(0, int(s))
    return f"{s // 60:02d}:{s % 60:02d}"


def print_table(rows: list[Row], books: dict, now_ms: int, args) -> None:
    ts = dt.datetime.now().strftime("%H:%M:%S")
    nxt = dt.datetime.fromtimestamp(rows[0].next_funding_ms / 1000).strftime("%H:%M") if rows else "?"
    print(f"\n{ts}  next settlement {nxt} (in {fmt_ttl(rows[0].ttl_s(now_ms)) if rows else '?'})  "
          f"signal: |rate| >= {args.min_rate*100:.3f}%/h within {args.window:.0f}s")
    print(f"{'symbol':<14}{'rate %/h':>10}{'side':>7}{'APR %':>9}{'OI $k':>9}{'net mkr':>9}{'net tkr':>9}"
          f"{'spread':>8}{'bid10 $k':>10}{'ask10 $k':>10}  status")
    for r in rows[: args.top]:
        bm = books.get(r.iid, {})
        status = "SIGNAL" if is_signal(r, now_ms, args.min_rate, args.window) else (
            "watch" if abs(r.rate) >= args.min_rate else "")
        print(f"{r.symbol:<14}{r.rate*100:>+10.4f}{r.side:>7}{abs(r.rate)*24*365*100:>9.0f}{r.oi_usd/1e3:>9.0f}"
              f"{r.net_maker_bps:>+9.2f}{r.net_taker_bps:>+9.2f}"
              + (f"{bm['spread_bps']:>8.1f}{bm['bid_depth_usd']/1e3:>10.1f}{bm['ask_depth_usd']/1e3:>10.1f}"
                 if bm else f"{'-':>8}{'-':>10}{'-':>10}") + f"  {status}")
    print("net = funding - round-trip fees, bps of notional, before price noise (SD ~15-25 bps over 40 s)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-rate", type=float, default=0.0005, help="signal threshold, fraction per hour")
    ap.add_argument("--track", type=float, default=0.00025, help="log estimate vs realized above this |rate|")
    ap.add_argument("--window", type=float, default=120, help="seconds before settlement that open the signal")
    ap.add_argument("--poll", type=float, default=15)
    ap.add_argument("--fast-poll", type=float, default=3, help="poll interval inside the window")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--books", type=int, default=6, help="fetch books for this many top markets")
    ap.add_argument("--notify", action="store_true")
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    inst = {i["instrument_id"]: i for i in (get("instruments") or [])}
    alerted: set[tuple[int, int]] = set()
    last_est: dict[tuple[int, int], dict] = {}  # (iid, T) -> last estimate before T
    last_print = 0.0
    while True:
        tick = get("tickers")
        now_ms = int(time.time() * 1000)
        if not tick:
            print("tickers request failed", file=sys.stderr, flush=True)
            time.sleep(args.poll)
            continue
        rows = parse(tick, inst, now_ms)
        in_window = bool(rows) and 0 < rows[0].ttl_s(now_ms) <= args.window

        for r in rows:
            if abs(r.rate) >= args.track and r.ttl_s(now_ms) > 0:
                last_est[(r.iid, r.next_funding_ms)] = {"symbol": r.symbol, "est": r.rate,
                                                        "est_ttl_s": round(r.ttl_s(now_ms), 1)}

        books = {}
        for r in rows[: args.books]:
            b = get("book", instrument_id=r.iid)
            if b:
                books[r.iid] = book_metrics(b)

        for r in rows:
            key = (r.iid, r.next_funding_ms)
            if is_signal(r, now_ms, args.min_rate, args.window) and key not in alerted:
                alerted.add(key)
                msg = (f"{r.symbol}: {r.side} {r.rate*100:+.4f}%/h, settles in {fmt_ttl(r.ttl_s(now_ms))}, "
                       f"net maker {r.net_maker_bps:+.1f} bps")
                print(f"\a*** SIGNAL {msg}", flush=True)
                log({"event": "signal", "t": now_ms, "symbol": r.symbol, "iid": r.iid, "rate": r.rate,
                     "side": r.side, "settle": r.next_funding_ms, "oi_usd": r.oi_usd,
                     "net_maker_bps": r.net_maker_bps, **books.get(r.iid, {})})
                if args.notify:
                    notify("Funding signal", msg)

        # realized vs estimate, ~30 s after each settlement
        for (iid, T), e in list(last_est.items()):
            if now_ms > T + 30_000:
                paid = get("funding", instrument_id=iid, start_timestamp=T - 60_000, end_timestamp=T + 60_000) or []
                realized = float(paid[0]["funding_rate"]) if paid else None
                log({"event": "settled", "settle": T, "iid": iid, **e, "realized": realized})
                if realized is not None:
                    print(f"settled {e['symbol']:<12} est {e['est']*100:+.4f}% ({e['est_ttl_s']:.0f}s before) "
                          f"-> paid {realized*100:+.4f}%", flush=True)
                del last_est[(iid, T)]

        if args.once or time.time() - last_print >= max(args.poll, 60) or in_window:
            print_table(rows, books, now_ms, args)
            sys.stdout.flush()
            last_print = time.time()
        if args.once:
            return
        time.sleep(args.fast_poll if in_window else args.poll)


if __name__ == "__main__":
    main()
