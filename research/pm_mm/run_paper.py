"""Paper test: market making for liquidity rewards on Polymarket prediction markets.

Read-only: public REST + market WebSocket; no orders are sent anywhere. For each selected
market, several virtual makers (pmresearch.pm_mm_paper.PaperMaker) quote two-sided against
the live book; fills come from live trades with a queue model; rewards are sampled once a
minute with the official formula against the live competition (findings 09, section 5).

Selection: rewards >= --min-rate $/day, > --min-days to scheduled end, adjusted mid in
[0.10, 0.90], both best levels inside the reward spread v, at most 2 markets per event,
ranked by the snapshot reward per $ (pmresearch.pm_rewards.reward_estimate, join).

Output: data/pm_mm/paper/<UTC>/{config.json, fills.jsonl, samples.jsonl, status.log}
Usage: uv run python -u research/pm_mm/run_paper.py --hours 72 --markets 30 --capital 300
Report: uv run python research/pm_mm/report_paper.py
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import time
from pathlib import Path

import websockets

from pmresearch.pm_clob import WS_MARKET, books, days_left, reward_markets, session
from pmresearch.pm_mm_paper import ASK, BID, Book, PaperMaker, Params, to_yes_trade
from pmresearch.pm_rewards import adjusted_mid, reward_estimate

VARIANTS = {  # name: (back_cents, fill_model, latency_s)
    "join_q": (0.0, "queue", 1.0),
    "join_touch": (0.0, "touch", 1.0),
    "back1_q": (1.0, "queue", 1.0),
    "join_q_slow": (0.0, "queue", 5.0),
}


class Mkt:
    def __init__(self, m: dict, book: dict, capital: float):
        self.cid, self.question, self.event = m["condition_id"], m["question"], m.get("event_slug")
        self.yes, self.no = m["tokens"][0]["token_id"], m["tokens"][1]["token_id"]
        self.params = Params(float(m["rewards_max_spread"]), float(m["rewards_min_size"]), m["rate"],
                             float(book.get("tick_size") or 0.01))
        self.book = Book()
        self.book.snapshot(book.get("bids", []), book.get("asks", []))
        spread = (self.book.best_ask() or 1) - (self.book.best_bid() or 0)
        self.shares = round(capital / max(0.5, 1 - spread), 2)
        self.makers = {n: PaperMaker(n, self.shares, back_cents=b, fill_model=f, latency_s=lat)
                       for n, (b, f, lat) in VARIANTS.items()}
        self.trades = 0
        self.drift = 0

    def mid(self) -> float | None:
        bids, asks = self.book.levels()
        return adjusted_mid(bids, asks, self.params.min_size)

    def requote(self, now: float) -> None:
        for mk in self.makers.values():
            mk.on_book(self.book, self.params, now)

    def resync_caps(self, now: float) -> None:
        for mk in self.makers.values():
            for side in (BID, ASK):
                o = mk.orders[side]
                if o:
                    mk.on_level(side, o.price, self.book.size_at(side, o.price), now)


def select(s, args) -> list[Mkt]:
    mk = [m for m in reward_markets(s, args.min_rate) if m.get("tokens") and len(m["tokens"]) == 2]
    now = dt.datetime.now(dt.UTC)
    mk = [m for m in mk if (days_left(m.get("end_date"), now) or 0) > args.min_days]
    bk = books(s, [m["tokens"][0]["token_id"] for m in mk])
    cand = []
    for m in mk:
        b = bk.get(m["tokens"][0]["token_id"])
        if not b:
            continue
        v, ms = float(m["rewards_max_spread"]), float(m["rewards_min_size"])
        e = reward_estimate(b, m["rate"], v, ms, args.capital, float(b.get("tick_size") or 0.01))
        if not e or not 0.10 <= e["mid"] <= 0.90:
            continue
        if (e["mid"] - e["bid"]) * 100 >= v or (e["ask"] - e["mid"]) * 100 >= v:
            continue
        cand.append((e["reward_per_1k_day"], m, b))
    cand.sort(key=lambda x: -x[0])
    out, per_event = [], {}
    for _, m, b in cand:
        ev = m.get("event_slug") or m["condition_id"]
        if per_event.get(ev, 0) >= 2:
            continue
        per_event[ev] = per_event.get(ev, 0) + 1
        out.append(Mkt(m, b, args.capital))
        if len(out) >= args.markets:
            break
    return out


async def run(args) -> None:
    s = session()
    out = Path("data/pm_mm/paper") / time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out.mkdir(parents=True, exist_ok=True)
    mkts = select(s, args)
    by_token = {}
    for m in mkts:
        by_token[m.yes] = (m, True)
        by_token[m.no] = (m, False)
    (out / "config.json").write_text(json.dumps({
        **vars(args), "variants": VARIANTS,
        "markets": [{"cid": m.cid, "question": m.question, "event": m.event, "yes": m.yes, "no": m.no,
                     "rate": m.params.rate_per_day, "v": m.params.v_cents, "min_size": m.params.min_size,
                     "tick": m.params.tick, "shares": m.shares} for m in mkts]}, indent=1))
    fills = open(out / "fills.jsonl", "a")
    samples = open(out / "samples.jsonl", "a")
    status = open(out / "status.log", "a")

    def log(msg: str) -> None:
        line = f"{time.strftime('%m-%d %H:%M:%S')} {msg}"
        print(line, flush=True)
        status.write(line + "\n")
        status.flush()

    log(f"run dir {out}; {len(mkts)} markets, pool ${sum(m.params.rate_per_day for m in mkts):,.0f}/day, "
        f"${args.capital:.0f} two-sided per market")
    for m in mkts:
        log(f"  {m.params.rate_per_day:7.0f}/d v{m.params.v_cents} min{m.params.min_size:.0f} "
            f"tick{m.params.tick} sh{m.shares:.0f} mid {m.mid():.3f}  {m.question[:70]}")
    now = time.time()
    for m in mkts:
        m.requote(now)

    t_end = time.time() + args.hours * 3600

    def on_msg(e: dict, now: float) -> None:
        et = e.get("event_type")
        if et == "book":
            hit = by_token.get(e.get("asset_id"))
            if hit and hit[1]:
                m = hit[0]
                m.book.snapshot(e.get("bids", []), e.get("asks", []))
                m.resync_caps(now)
                m.requote(now)
        elif et == "price_change":
            touched = set()
            for c in e.get("price_changes", []):
                hit = by_token.get(c.get("asset_id"))
                if not hit or not hit[1]:
                    continue
                m = hit[0]
                side = BID if c["side"] == "BUY" else ASK
                p, sz = float(c["price"]), float(c["size"])
                m.book.set_level(side, p, sz)
                for mk in m.makers.values():
                    mk.on_level(side, p, sz, now)
                touched.add(m)
            for m in touched:
                m.requote(now)
        elif et == "last_trade_price":
            hit = by_token.get(e.get("asset_id"))
            if not hit:
                return
            m, is_yes = hit
            d, p = to_yes_trade(is_yes, e["side"], float(e["price"]))
            size = float(e["size"])
            m.trades += 1
            mid = m.mid()
            for mk in m.makers.values():
                for side, price, q in mk.on_trade(d, p, size):
                    fills.write(json.dumps({"t": now, "cid": m.cid, "maker": mk.name, "side": side, "price": price,
                                            "q": q, "mid": mid, "bb": m.book.best_bid(), "ba": m.book.best_ask(),
                                            "trade_p": p, "trade_q": size, "yes": mk.yes, "no": mk.no}) + "\n")
            m.requote(now)
        elif et == "tick_size_change":
            hit = by_token.get(e.get("asset_id"))
            if hit and hit[1]:
                hit[0].params.tick = float(e["new_tick_size"])

    async def ws_loop() -> None:
        ids = list(by_token)
        while time.time() < t_end:
            try:
                async with websockets.connect(WS_MARKET, max_size=None, ping_interval=None) as ws:
                    await ws.send(json.dumps({"assets_ids": ids, "type": "market"}))

                    async def ping():
                        while True:
                            await asyncio.sleep(10)
                            await ws.send("PING")
                    pt = asyncio.create_task(ping())
                    try:
                        while time.time() < t_end:
                            raw = await asyncio.wait_for(ws.recv(), timeout=60)
                            if raw == "PONG":
                                continue
                            msg = json.loads(raw)
                            now = time.time()
                            for e in msg if isinstance(msg, list) else [msg]:
                                on_msg(e, now)
                    finally:
                        pt.cancel()
            except Exception as ex:  # noqa: BLE001 - reconnect on any network error
                log(f"ws reconnect: {type(ex).__name__}: {str(ex)[:80]}")
                await asyncio.sleep(2)

    async def timers() -> None:
        last_sample = last_sync = last_rew = last_status = time.time()
        while time.time() < t_end:
            await asyncio.sleep(0.25)
            now = time.time()
            for m in mkts:
                for mk in m.makers.values():
                    mk.on_time(m.book, now)
            if now - last_sample >= 60:
                last_sample = now
                for m in mkts:
                    mid = m.mid()
                    row = {"t": round(now, 1), "cid": m.cid, "mid": mid, "bb": m.book.best_bid(), "ba": m.book.best_ask(),
                           "rate": m.params.rate_per_day, "mk": {}}
                    for mk in m.makers.values():
                        share, _ = mk.sample_reward(m.book, m.params)
                        ob, oa = mk.orders[BID], mk.orders[ASK]
                        row["mk"][mk.name] = [round(share, 5), round(mk.reward, 4),
                                              round(mk.pnl(mid), 4) if mid is not None else None,
                                              round(mk.yes, 2), round(mk.no, 2),
                                              ob.price if ob else None, oa.price if oa else None,
                                              round(mk.capital(), 2), mk.fills]
                    samples.write(json.dumps(row) + "\n")
                samples.flush()
                fills.flush()
            if now - last_sync >= 300:
                last_sync = now
                try:
                    bk = await asyncio.to_thread(books, s, [m.yes for m in mkts])
                    for m in mkts:
                        b = bk.get(m.yes)
                        if not b:
                            continue
                        old = (m.book.best_bid(), m.book.best_ask())
                        m.book.snapshot(b.get("bids", []), b.get("asks", []))
                        if old != (m.book.best_bid(), m.book.best_ask()):
                            m.drift += 1
                        m.resync_caps(now)
                        m.requote(now)
                except Exception as ex:  # noqa: BLE001
                    log(f"resync failed: {type(ex).__name__}")
            if now - last_rew >= 6 * 3600:
                last_rew = now
                try:
                    cur = {x["condition_id"]: x for x in await asyncio.to_thread(reward_markets, s, 1.0)}
                    for m in mkts:
                        x = cur.get(m.cid)
                        m.params.rate_per_day = x["rate"] if x else 0.0
                        if x:
                            m.params.v_cents = float(x["rewards_max_spread"])
                            m.params.min_size = float(x["rewards_min_size"])
                    log("reward params refreshed")
                except Exception as ex:  # noqa: BLE001
                    log(f"reward refresh failed: {type(ex).__name__}")
            if now - last_status >= args.status_s:
                last_status = now
                h = (now - t0) / 3600
                parts = []
                for n in VARIANTS:
                    rew = sum(m.makers[n].reward for m in mkts)
                    pnl = sum(m.makers[n].pnl(m.mid() or 0.5) for m in mkts)
                    nf = sum(m.makers[n].fills for m in mkts)
                    parts.append(f"{n}: rew {rew:.2f} pnl {pnl:+.2f} fills {nf}")
                log(f"{h:5.1f}h trades {sum(m.trades for m in mkts)} drift {sum(m.drift for m in mkts)} | " + " | ".join(parts))

    t0 = time.time()
    await asyncio.gather(ws_loop(), timers())
    log("done")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=72)
    ap.add_argument("--markets", type=int, default=30)
    ap.add_argument("--capital", type=float, default=300, help="USD per market, two-sided")
    ap.add_argument("--min-rate", type=float, default=20)
    ap.add_argument("--min-days", type=float, default=7)
    ap.add_argument("--status-s", type=float, default=1800)
    asyncio.run(run(ap.parse_args()))


if __name__ == "__main__":
    main()
