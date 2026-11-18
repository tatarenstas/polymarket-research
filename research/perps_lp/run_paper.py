"""Live paper test of Polymarket Perps liquidity rewards. Read-only: no orders are sent.

For each market, four virtual makers quote $SIZE per side at OFFSET bps from mid:
  {unhedged, hedged} x {touch fills (optimistic), through fills (conservative)}
Public WebSocket trades decide virtual fills; the public book is the competition for the
rewards score. Every minute a summary line per (market, maker) is appended to
data/lp_paper/<run>/summary.jsonl; fills and raw trades are logged too.

Usage: uv run python research/perps_lp/run_paper.py --hours 6
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
import urllib.request
from pathlib import Path

import websockets

from pmresearch.lp_paper import RewardTracker, VirtualMaker

WS = "wss://ws.perpetuals.polymarket.com/v1/ws"
REST = "https://api.perpetuals.polymarket.com/v1/info"
MARKETS = {28: "ASML-USD", 32: "ZEC-USD", 69: "PONS-USD", 89: "SOXL-USD", 38: "STRC-USD", 6: "BTC-USD"}
DAILY_BUDGET = 75_000.0
SAMPLE_S = 5
SUMMARY_S = 60
MARKOUTS = (10, 60, 300)


class Market:
    def __init__(self, iid: int, sym: str, size: float, offset: float, max_inv: float, hedge_bps: float):
        self.iid, self.sym = iid, sym
        self.bids: list[tuple[float, float]] = []
        self.asks: list[tuple[float, float]] = []
        self.mid: float | None = None
        self.traded_notional = 0.0
        self.makers = {}
        for hedged in (False, True):
            for through in (False, True):
                name = f"{'hedged' if hedged else 'unhedged'}-{'through' if through else 'touch'}"
                self.makers[name] = VirtualMaker(name, size_usd=size, offset_bps=offset, max_inv_usd=max_inv,
                                                 hedged=hedged, hedge_bps=hedge_bps, through_only=through)
        self.rewards = {n: RewardTracker() for n in self.makers}
        self.pending = []  # (fill, maker_name) awaiting markouts
        self.markout_bps = {n: {h: [] for h in MARKOUTS} for n in self.makers}

    def on_book(self, ts: int, data: dict) -> None:
        self.bids = [(float(p), float(q)) for p, q in data.get("b", [])]
        self.asks = [(float(p), float(q)) for p, q in data.get("a", [])]
        if not self.bids or not self.asks:
            return
        self.mid = (self.bids[0][0] + self.asks[0][0]) / 2
        for m in self.makers.values():
            m.requote(ts, self.mid)
        keep = []
        for f, name in self.pending:
            for h in MARKOUTS:
                if h not in f.markouts and ts >= f.ts + h * 1000:
                    f.markouts[h] = self.mid
                    self.markout_bps[name][h].append(f.side * (self.mid - f.price) / f.price * 1e4)
            if len(f.markouts) < len(MARKOUTS):
                keep.append((f, name))
        self.pending = keep

    def on_trade(self, t: dict, fills_log) -> None:
        p, q = float(t["p"]), float(t["qty"])
        self.traded_notional += p * q
        if self.mid is None:
            return
        for name, m in self.makers.items():
            f = m.on_trade(int(t["ts"]), t["side"], p, q, self.mid)
            if f:
                self.pending.append((f, name))
                fills_log.write(json.dumps({"sym": self.sym, "maker": name, "ts": f.ts, "side": f.side,
                                            "price": f.price, "qty": f.qty, "mid": f.mid}) + "\n")

    def sample(self) -> None:
        if self.mid is None:
            return
        for name, m in self.makers.items():
            self.rewards[name].sample(m, self.bids, self.asks, self.mid)

    def summary(self, elapsed_h: float, pool: float) -> list[dict]:
        out = []
        days = max(elapsed_h / 24, 1e-9)
        for name, m in self.makers.items():
            share = m.maker_notional / self.traded_notional if self.traded_notional else 0.0
            est = self.rewards[name].estimates(pool, share)
            pnl = m.pnl(self.mid) if self.mid else 0.0
            mk = {f"markout_{h}s_bps": (sum(v) / len(v) if v else None) for h, v in self.markout_bps[name].items()}
            out.append({
                "sym": self.sym, "maker": name, "elapsed_h": round(elapsed_h, 3),
                "fills": len(m.fills), "maker_notional": m.maker_notional, "market_notional": self.traded_notional,
                "pos_usd": m.pos * (self.mid or 0), "trading_pnl": pnl, "fees": m.fees, "hedge_cost": m.hedge_cost,
                "trading_pnl_per_day": pnl / days, **est, **mk,
                "net_per_day_linear": est.get("reward_linear_per_day", 0) + pnl / days,
                "net_per_day_formula": est.get("reward_formula_per_day", 0) + pnl / days,
            })
        return out


def active_markets() -> int:
    with urllib.request.urlopen(f"{REST}/instruments", timeout=20) as r:
        j = json.load(r)
    rows = j["data"] if isinstance(j, dict) else j
    return sum(1 for i in rows if not i.get("close_only"))


async def run(args) -> None:
    out = Path("data/lp_paper") / time.strftime("%Y%m%d_%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    pool = DAILY_BUDGET / active_markets()
    (out / "config.json").write_text(json.dumps({**vars(args), "markets": MARKETS, "pool_per_market_day": pool}, indent=1))
    markets = {i: Market(i, s, args.size, args.offset, args.max_inv, args.hedge_bps) for i, s in MARKETS.items()}
    fills_log = open(out / "fills.jsonl", "a")
    trades_log = open(out / "trades.jsonl", "a")
    summ_log = open(out / "summary.jsonl", "a")
    t0 = time.time()
    end = t0 + args.hours * 3600
    last_sample = last_summary = 0.0
    print(f"run dir {out}; pool/market/day ${pool:.0f}", flush=True)
    chs = [f"book::{i}" for i in MARKETS] + [f"trades::{i}" for i in MARKETS]
    while time.time() < end:
        try:
            async with websockets.connect(WS, max_size=2**24, ping_interval=20) as ws:
                await ws.send(json.dumps({"id": 1, "req": "sub", "chs": chs}))
                while time.time() < end:
                    msg = json.loads(await asyncio.wait_for(ws.recv(), 60))
                    ch = msg.get("ch", "")
                    if "::" not in ch:
                        continue
                    kind, iid = ch.split("::")
                    mkt = markets.get(int(iid))
                    if mkt is None:
                        continue
                    if kind == "book":
                        mkt.on_book(int(msg.get("ts") or time.time() * 1000), msg["data"])
                    elif kind == "trades":
                        for t in msg["data"]:
                            trades_log.write(json.dumps({"sym": mkt.sym, **t}) + "\n")
                            mkt.on_trade(t, fills_log)
                    now = time.time()
                    if now - last_sample >= SAMPLE_S:
                        last_sample = now
                        for m in markets.values():
                            m.sample()
                    if now - last_summary >= SUMMARY_S:
                        last_summary = now
                        eh = (now - t0) / 3600
                        for m in markets.values():
                            for row in m.summary(eh, pool):
                                summ_log.write(json.dumps({"t": int(now), **row}) + "\n")
                        for f in (fills_log, trades_log, summ_log):
                            f.flush()
        except Exception as e:  # reconnect on any network error
            print(f"{time.strftime('%H:%M:%S')} reconnect after {type(e).__name__}: {e}", flush=True)
            await asyncio.sleep(5)
    print("done", out, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=6)
    ap.add_argument("--size", type=float, default=5_000, help="USD per side")
    ap.add_argument("--offset", type=float, default=3, help="bps from mid")
    ap.add_argument("--max-inv", type=float, default=5_000, help="USD inventory limit (unhedged)")
    ap.add_argument("--hedge-bps", type=float, default=5, help="external hedge cost incl. slippage")
    asyncio.run(run(ap.parse_args()))
