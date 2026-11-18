"""Can every BTC perps fill on Polymarket be locked against Binance so that it covers all fees?

Records (read-only) for --minutes: Polymarket BTC-USD book top + public trades, and Binance
USD-M BTCUSDT bookTicker, all stamped with one local clock. Then measures:

1. Basis PM_mid vs BN_mid (bps): level, spread, time above fee thresholds.
2. "Locked-edge maker fills": for each Polymarket taker trade at price p, a resting maker
   order at p would have been filled; hedging immediately on Binance as taker after a
   latency L locks  edge = (p - BN_ask(t+L))/p  (we sold) or (BN_bid(t+L) - p)/p (we bought).
   Net = edge - PM maker fee - BN fee. Reports the share of PM volume whose net >= 0, i.e.
   the volume a maker could capture if it only quotes where a fill pays all fees.
3. Pure taker cross-venue arb: time share where PM_bid - BN_ask or BN_bid - PM_ask exceeds
   both taker fees.

Usage: uv run python research/perps_lp/btc_cross_venue_probe.py --minutes 25
"""

from __future__ import annotations

import argparse
import asyncio
import bisect
import json
import statistics as st
import time
from pathlib import Path

import websockets

PM_WS, BN_WS = "wss://ws.perpetuals.polymarket.com/v1/ws", "wss://fstream.binance.com/ws/btcusdt@bookTicker"
PM_MAKER, PM_TAKER = 0.000125, 0.0004
BN_TAKER, BN_MAKER = 0.0005, 0.0002  # Binance USD-M VIP0 (verify for your account)


def now():
    return time.time()


async def pm(rec, stop):
    while now() < stop:
        try:
            async with websockets.connect(PM_WS, max_size=2**24, ping_interval=20) as ws:
                await ws.send(json.dumps({"id": 1, "req": "sub", "chs": ["book::6", "trades::6"]}))
                while now() < stop:
                    m = json.loads(await asyncio.wait_for(ws.recv(), 30))
                    t = now()
                    if m.get("ch") == "book::6":
                        d = m["data"]
                        if d.get("b") and d.get("a"):
                            rec["pm_book"].append((t, float(d["b"][0][0]), float(d["a"][0][0])))
                    elif m.get("ch") == "trades::6":
                        for tr in m["data"]:
                            rec["pm_trades"].append((t, tr["side"], float(tr["p"]), float(tr["qty"])))
        except Exception as e:
            print("pm reconnect", type(e).__name__, flush=True)
            await asyncio.sleep(2)


async def bn(rec, stop):
    while now() < stop:
        try:
            async with websockets.connect(BN_WS, max_size=2**22, ping_interval=20) as ws:
                while now() < stop:
                    d = json.loads(await asyncio.wait_for(ws.recv(), 30))
                    rec["bn"].append((now(), float(d["b"]), float(d["a"])))
        except Exception as e:
            print("bn reconnect", type(e).__name__, flush=True)
            await asyncio.sleep(2)


def analyze(rec):
    bn = rec["bn"]
    bt = [x[0] for x in bn]

    def bn_at(t):
        i = bisect.bisect_right(bt, t) - 1
        return bn[i] if i >= 0 else None

    basis = []
    for t, b, a in rec["pm_book"]:
        q = bn_at(t)
        if q and t - q[0] < 2:
            basis.append(((b + a) / 2 - (q[1] + q[2]) / 2) / ((q[1] + q[2]) / 2) * 1e4)
    print(f"\nsamples: pm_book {len(rec['pm_book'])}, pm_trades {len(rec['pm_trades'])}, binance {len(bn)}")
    if basis:
        med = st.median(basis)
        print(f"basis PM_mid-BN_mid (bps): mean {st.mean(basis):+.2f} median {med:+.2f} sd {st.pstdev(basis):.2f} "
              f"p5 {sorted(basis)[len(basis)//20]:+.2f} p95 {sorted(basis)[len(basis)*19//20]:+.2f}")
        dm = [x - med for x in basis]
        for th in (2.5, 6.25, 9.0):
            print(f"   |basis - median| > {th} bps: {100*sum(abs(x) > th for x in dm)/len(dm):.2f}% of time")
    # pure taker arb
    arb = 0
    for t, b, a in rec["pm_book"]:
        q = bn_at(t)
        if q and t - q[0] < 2:
            if (b - q[2]) / q[2] > PM_TAKER + BN_TAKER or (q[1] - a) / a > PM_TAKER + BN_TAKER:
                arb += 1
    print(f"taker-taker cross arb (> {1e4*(PM_TAKER+BN_TAKER):.0f} bps) available: {100*arb/max(len(rec['pm_book']),1):.3f}% of book updates")
    # locked-edge maker fills
    vol = sum(p * q for _, _, p, q in rec["pm_trades"])
    print(f"PM BTC traded notional in window: ${vol:,.0f}")
    for lat in (0.2, 1.0, 3.0):
        for hedge_fee, hname in ((BN_TAKER, "BN taker"), (BN_MAKER, "BN maker*")):
            ok_vol = 0.0
            nets = []
            for t, side, p, q in rec["pm_trades"]:
                h = bn_at(t + lat)
                if not h or h[0] < t:
                    continue
                edge = (p - h[2]) / p if side == "long" else (h[1] - p) / p
                net = edge - PM_MAKER - hedge_fee
                nets.append(net)
                if net >= 0:
                    ok_vol += p * q
            if nets:
                pos = [x for x in nets if x >= 0]
                print(f"  latency {lat:>3}s, hedge {hname:9}: fills that lock >= all fees: {100*len(pos)/len(nets):5.2f}% of trades, "
                      f"{100*ok_vol/vol if vol else 0:5.2f}% of volume; avg net among them {1e4*st.mean(pos) if pos else 0:+.2f} bps; "
                      f"avg net all {1e4*st.mean(nets):+.2f} bps")
    print("  (*BN maker hedge assumes a passive fill at the touch, which is not guaranteed)")


async def main(minutes):
    rec = {"pm_book": [], "pm_trades": [], "bn": []}
    stop = now() + minutes * 60
    await asyncio.gather(pm(rec, stop), bn(rec, stop))
    out = Path("data/perps/btc_cross_venue_probe.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec))
    analyze(rec)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=25)
    asyncio.run(main(ap.parse_args().minutes))
