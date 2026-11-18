"""Stage 1 paper test: Polymarket Perps maker for liquidity rewards + realistic Binance hedge.

Read-only on both venues (public WebSockets/REST); no orders are sent anywhere.
Per market, four virtual makers (DelayedHedgeMaker) differ in hedge delay, hedge netting
threshold and inventory skew. Hedge = taker on Binance USD-M perp at its live bid/ask
after the delay, paying --hedge-fee. Funding is applied on both legs (Polymarket hourly
from the ticker estimate just before settlement; Binance from the markPrice stream).

Usage: uv run python research/perps_lp/run_stage1.py --hours 72
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
import urllib.request
from pathlib import Path

import websockets

from pmresearch.lp_paper import DelayedHedgeMaker, RewardTracker

PM_WS = "wss://ws.perpetuals.polymarket.com/v1/ws"
PM_REST = "https://api.perpetuals.polymarket.com/v1/info"
BN_WS = "wss://fstream.binance.com/stream?streams="
# Polymarket instrument id -> (symbol, Binance symbol). Price parity checked 2026-11-13
# (ratio 0.9997-1.0004). ANT is excluded: Binance ANTHROPIC trades at a different scale.
MARKETS = {32: ("ZEC-USD", "zecusdt"), 78: ("XMR-USD", "xmrusdt"), 89: ("SOXL-USD", "soxlusdt"), 28: ("ASML-USD", "asmlusdt")}
VARIANTS = {  # name: (hedge_delay_s, hedge_threshold_usd, skew_bps)
    "d1_t0": (1.0, 0.0, 3.0),
    "d3_t0": (3.0, 0.0, 3.0),
    "d1_t1k": (1.0, 1000.0, 3.0),
    "d1_noskew": (1.0, 0.0, 0.0),
}
MARKOUTS = (10, 60, 300)


def now_ms() -> int:
    return int(time.time() * 1000)


class Market:
    def __init__(self, iid, sym, bsym, args):
        self.iid, self.sym, self.bsym = iid, sym, bsym
        self.bids, self.asks, self.mid = [], [], None
        self.hbid = self.hask = None
        self.traded = 0.0
        self.pm_rate = None
        self.pm_next = None
        self.bn = {}  # last markPrice msg
        self.makers = {
            n: DelayedHedgeMaker(n, size_usd=args.size, offset_bps=args.offset, max_inv_usd=args.max_inv,
                                 hedge_delay_s=d, hedge_threshold_usd=th, skew_bps=sk, hedge_fee=args.hedge_fee)
            for n, (d, th, sk) in VARIANTS.items()
        }
        self.rewards = {n: RewardTracker() for n in self.makers}
        self.pending = []
        self.mo = {n: {h: [] for h in MARKOUTS} for n in self.makers}

    @property
    def hmid(self):
        return (self.hbid + self.hask) / 2 if self.hbid and self.hask else None

    def on_book(self, data):
        self.bids = [(float(p), float(q)) for p, q in data.get("b", [])]
        self.asks = [(float(p), float(q)) for p, q in data.get("a", [])]
        if not self.bids or not self.asks:
            return
        self.mid = (self.bids[0][0] + self.asks[0][0]) / 2
        t = now_ms()
        for m in self.makers.values():
            m.requote(t, self.mid)
        keep = []
        for f, n in self.pending:
            for h in MARKOUTS:
                if h not in f.markouts and t >= f.ts + h * 1000:
                    f.markouts[h] = self.mid
                    self.mo[n][h].append(f.side * (self.mid - f.price) / f.price * 1e4)
            if len(f.markouts) < len(MARKOUTS):
                keep.append((f, n))
        self.pending = keep

    def on_trade(self, tr, log):
        p, q = float(tr["p"]), float(tr["qty"])
        self.traded += p * q
        if self.mid is None:
            return
        t = now_ms()
        for n, m in self.makers.items():
            f = m.on_trade(t, tr["side"], p, q, self.mid)
            if f:
                self.pending.append((f, n))
                log.write(json.dumps({"sym": self.sym, "maker": n, "ts": t, "side": f.side, "price": f.price,
                                      "qty": f.qty, "mid": f.mid, "hbid": self.hbid, "hask": self.hask}) + "\n")

    def on_hedge_book(self, bid, ask):
        self.hbid, self.hask = bid, ask
        t = now_ms()
        for m in self.makers.values():
            m.on_hedge_quote(t, bid, ask)

    def on_bn_mark(self, msg):
        prev = self.bn
        if prev and int(msg["T"]) > int(prev["T"]):  # a funding settlement passed
            for m in self.makers.values():
                m.apply_funding("hedge", float(prev["r"]), float(prev["p"]))
        self.bn = msg

    def on_pm_ticker(self, t):
        nxt = int(t["next_funding"])
        if self.pm_next and nxt > self.pm_next and self.pm_rate is not None and self.mid:
            for m in self.makers.values():
                m.apply_funding("poly", self.pm_rate, self.mid)
        self.pm_next, self.pm_rate = nxt, float(t["funding_rate"])

    def sample(self):
        if self.mid:
            for n, m in self.makers.items():
                self.rewards[n].sample(m, self.bids, self.asks, self.mid)

    def summary(self, eh, pool):
        days = max(eh / 24, 1e-9)
        out = []
        for n, m in self.makers.items():
            share = m.maker_notional / self.traded if self.traded else 0.0
            est = self.rewards[n].estimates(pool, share)
            pnl = m.pnl2(self.mid, self.hmid) if self.mid else 0.0
            out.append({
                "sym": self.sym, "maker": n, "elapsed_h": round(eh, 3), "fills": len(m.fills),
                "maker_notional": m.maker_notional, "market_notional": self.traded,
                "pos_usd": m.pos * (self.mid or 0), "hpos_usd": m.hpos * (self.hmid or 0),
                "net_exposure_usd": (m.pos + m.hpos) * (self.mid or 0),
                "pnl": pnl, "pnl_per_day": pnl / days, "maker_fees": m.fees, "hedge_fees": m.hedge_fees,
                "hedge_slippage": m.hedge_slippage, "hedge_trades": m.hedge_trades, "funding": m.funding,
                **est,
                **{f"mo{h}s_bps": (sum(v) / len(v) if v else None) for h, v in self.mo[n].items()},
                "net_lin_per_day": est.get("reward_linear_per_day", 0) + pnl / days,
                "net_frm_per_day": est.get("reward_formula_per_day", 0) + pnl / days,
            })
        return out


def rest(path):
    with urllib.request.urlopen(f"{PM_REST}/{path}", timeout=20) as r:
        j = json.load(r)
    return j["data"] if isinstance(j, dict) and "data" in j else j


async def pm_feed(mk, logs, stop):
    chs = [f"book::{i}" for i in mk] + [f"trades::{i}" for i in mk]
    while time.time() < stop:
        try:
            async with websockets.connect(PM_WS, max_size=2**24, ping_interval=20) as ws:
                await ws.send(json.dumps({"id": 1, "req": "sub", "chs": chs}))
                while time.time() < stop:
                    msg = json.loads(await asyncio.wait_for(ws.recv(), 60))
                    ch = msg.get("ch", "")
                    if "::" not in ch:
                        continue
                    kind, iid = ch.split("::")
                    m = mk.get(int(iid))
                    if not m:
                        continue
                    if kind == "book":
                        m.on_book(msg["data"])
                    else:
                        for tr in msg["data"]:
                            logs["trades"].write(json.dumps({"sym": m.sym, **tr}) + "\n")
                            m.on_trade(tr, logs["fills"])
        except Exception as e:
            print(f"{time.strftime('%H:%M:%S')} pm reconnect: {type(e).__name__}", flush=True)
            await asyncio.sleep(3)


async def bn_feed(mk, stop):
    by = {m.bsym.upper(): m for m in mk.values()}
    streams = "/".join(f"{m.bsym}@bookTicker/{m.bsym}@markPrice@1s" for m in mk.values())
    while time.time() < stop:
        try:
            async with websockets.connect(BN_WS + streams, max_size=2**24, ping_interval=20) as ws:
                while time.time() < stop:
                    d = json.loads(await asyncio.wait_for(ws.recv(), 60)).get("data", {})
                    m = by.get(d.get("s"))
                    if not m:
                        continue
                    if d.get("e") == "markPriceUpdate":
                        m.on_bn_mark(d)
                    elif "b" in d and "a" in d:  # bookTicker
                        m.on_hedge_book(float(d["b"]), float(d["a"]))
        except Exception as e:
            print(f"{time.strftime('%H:%M:%S')} binance reconnect: {type(e).__name__}", flush=True)
            await asyncio.sleep(3)


async def housekeeping(mk, logs, out, pool, t0, stop):
    last_sum = 0.0
    while time.time() < stop:
        await asyncio.sleep(5)
        for m in mk.values():
            m.sample()
        if time.time() - last_sum >= 60:
            last_sum = time.time()
            try:
                tick = {t["instrument_id"]: t for t in await asyncio.to_thread(rest, "tickers")}
                for i, m in mk.items():
                    if i in tick:
                        m.on_pm_ticker(tick[i])
            except Exception as e:
                print(f"ticker poll failed: {type(e).__name__}", flush=True)
            eh = (time.time() - t0) / 3600
            for m in mk.values():
                for row in m.summary(eh, pool):
                    logs["summary"].write(json.dumps({"t": int(time.time()), **row}) + "\n")
            for f in logs.values():
                f.flush()


async def main(args):
    out = Path("data/lp_stage1") / time.strftime("%Y%m%d_%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    pool = 75_000 / sum(1 for i in rest("instruments") if not i.get("close_only"))
    (out / "config.json").write_text(json.dumps({**vars(args), "markets": MARKETS, "variants": VARIANTS,
                                                 "pool_per_market_day": pool}, indent=1))
    mk = {i: Market(i, s, b, args) for i, (s, b) in MARKETS.items()}
    logs = {k: open(out / f"{k}.jsonl", "a") for k in ("fills", "trades", "summary")}
    t0 = time.time()
    stop = t0 + args.hours * 3600
    print(f"run dir {out}; pool/market/day ${pool:.0f}", flush=True)
    await asyncio.gather(pm_feed(mk, logs, stop), bn_feed(mk, stop), housekeeping(mk, logs, out, pool, t0, stop))
    print("done", out, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=72)
    ap.add_argument("--size", type=float, default=5_000)
    ap.add_argument("--offset", type=float, default=3)
    ap.add_argument("--max-inv", type=float, default=10_000)
    ap.add_argument("--hedge-fee", type=float, default=0.0005, help="Binance USD-M taker fee (verify your tier)")
    asyncio.run(main(ap.parse_args()))
