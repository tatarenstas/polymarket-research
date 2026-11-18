"""Paper market maker for Polymarket prediction markets (CLOB), quoting for liquidity rewards.

Everything is in YES-token space. A two-sided quote is a YES bid at b plus a NO bid at 1 - a,
which the CLOB shows as a YES ask at a, so it needs no inventory. Fills on the YES bid add
YES shares; fills on the YES ask add NO shares. Matching YES + NO pairs merge into $1.

Live feed facts (checked 2026-11-18 on wss://ws-subscriptions-clob.polymarket.com/ws/market):
  * each match is published once, as `last_trade_price` on the taker's token. A NO-token
    trade (taker side, price q) is the YES-space trade (opposite side, 1 - q): `to_yes_trade`.
  * the YES book carries all resting liquidity (NO orders appear mirrored).

Fill models for our virtual orders (they are not in the real book):
  * "queue": placed behind the whole level at that price. Trades at our price consume the
    queue first; level shrinkage that is not a trade (cancels) caps the queue at the level
    size, applied 1 s after the change so the trade message and the book update can arrive
    in either order. A trade at a worse price than ours (trade-through) fills us fully.
  * "touch": any trade at our price fills us immediately (upper bound on fills).

Rewards follow pmresearch.pm_rewards: per sample, share = our Q_min / (our + competitors).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pmresearch.pm_rewards import adjusted_mid, competitor_qmin, qmin, score, side_q

BID, ASK = 1, -1
EPS = 1e-9


def to_yes_trade(is_yes_token: bool, side: str, price: float) -> tuple[int, float]:
    """Return (taker_dir, yes_price): taker_dir +1 = taker bought YES, -1 = sold YES."""
    d = 1 if side.upper() == "BUY" else -1
    return (d, price) if is_yes_token else (-d, round(1 - price, 6))


class Book:
    """YES-token order book: price -> size per side."""

    def __init__(self) -> None:
        self.bids: dict[float, float] = {}
        self.asks: dict[float, float] = {}

    def snapshot(self, bids, asks) -> None:
        self.bids = {round(float(o["price"]), 6): float(o["size"]) for o in bids if float(o["size"]) > 0}
        self.asks = {round(float(o["price"]), 6): float(o["size"]) for o in asks if float(o["size"]) > 0}

    def set_level(self, side: int, price: float, size: float) -> None:
        d = self.bids if side == BID else self.asks
        p = round(price, 6)
        if size > 0:
            d[p] = size
        else:
            d.pop(p, None)

    def size_at(self, side: int, price: float) -> float:
        return (self.bids if side == BID else self.asks).get(round(price, 6), 0.0)

    def best_bid(self) -> float | None:
        return max(self.bids) if self.bids else None

    def best_ask(self) -> float | None:
        return min(self.asks) if self.asks else None

    def levels(self):
        return sorted(self.bids.items(), reverse=True), sorted(self.asks.items())


@dataclass
class Params:
    v_cents: float
    min_size: float
    rate_per_day: float
    tick: float = 0.01


@dataclass
class Order:
    side: int
    price: float
    size: float
    queue: float
    placed: float
    cap: tuple[float, float] | None = None  # (level size, time of change) pending queue cap


@dataclass
class PaperMaker:
    name: str
    quote_shares: float
    back_cents: float = 0.0  # 0 = join the best level; 1 = one cent behind it
    fill_model: str = "queue"  # "queue" | "touch"
    latency_s: float = 1.0
    max_inv_shares: float | None = None  # |YES - NO| limit; default = quote_shares
    orders: dict = field(default_factory=lambda: {BID: None, ASK: None})
    pending: dict = field(default_factory=dict)  # side -> (price or None, due time)
    yes: float = 0.0
    no: float = 0.0
    cash: float = 0.0
    reward: float = 0.0
    fills: int = 0
    filled_shares: float = 0.0

    def __post_init__(self) -> None:
        if self.max_inv_shares is None:
            self.max_inv_shares = self.quote_shares

    # ---- quoting -------------------------------------------------------------------------
    def target(self, book: Book, p: Params) -> dict[int, float | None]:
        bids, asks = book.levels()
        mid = adjusted_mid(bids, asks, p.min_size)
        bb, ba = book.best_bid(), book.best_ask()
        out: dict[int, float | None] = {BID: None, ASK: None}
        if mid is None or bb is None or ba is None or ba <= bb:
            return out
        back = self.back_cents / 100
        net = self.yes - self.no
        b = _floor_tick(bb - back, p.tick)
        a = _ceil_tick(ba + back, p.tick)
        # quote a side only where it earns rewards (inside v) and inventory allows
        # never bid at/above the (size-adjusted) mid or offer at/below it: when small levels sit
        # past the mid, joining them would mean trading on the wrong side of fair value
        if 0 < b < mid - EPS and (mid - b) * 100 < p.v_cents - EPS and net < self.max_inv_shares - EPS:
            out[BID] = b
        if mid + EPS < a < 1 and (a - mid) * 100 < p.v_cents - EPS and -net < self.max_inv_shares - EPS:
            out[ASK] = a
        return out

    def on_book(self, book: Book, p: Params, now: float) -> None:
        """Schedule replacements when the target moved (after latency)."""
        tgt = self.target(book, p)
        for side in (BID, ASK):
            cur = self.orders[side]
            want = tgt[side]
            cur_p = cur.price if cur else None
            refill = cur is not None and cur.size < max(p.min_size, 0.5 * self.quote_shares) - EPS
            if (want is None and cur_p is None) or (want is not None and cur_p is not None
                                                    and abs(want - cur_p) < EPS and not refill):
                self.pending.pop(side, None)
                continue
            prev = self.pending.get(side)
            if prev is None or abs((prev[0] or -1) - (want or -1)) > EPS:
                self.pending[side] = (want, now + self.latency_s)

    def on_time(self, book: Book, now: float) -> None:
        for side, (price, due) in list(self.pending.items()):
            if now + EPS < due:
                continue
            del self.pending[side]
            if price is None:
                self.orders[side] = None
            else:
                self.orders[side] = Order(side, price, self.quote_shares, book.size_at(side, price), now)
        for o in self.orders.values():
            if o and o.cap and now - o.cap[1] >= 1.0:
                o.queue = min(o.queue, o.cap[0])
                o.cap = None

    def on_level(self, side: int, price: float, new_size: float, now: float) -> None:
        o = self.orders[side]
        if o and abs(o.price - price) < EPS and new_size < o.queue:
            o.cap = (new_size, now)

    # ---- fills ---------------------------------------------------------------------------
    def on_trade(self, taker_dir: int, price: float, size: float) -> list[tuple[int, float, float]]:
        """taker_dir +1 = taker bought YES (hits asks), -1 = taker sold YES (hits bids).
        Returns our fills as (side, price, shares)."""
        side = ASK if taker_dir == 1 else BID
        o = self.orders[side]
        if o is None or o.size <= EPS:
            return []
        through = price > o.price + EPS if side == ASK else price < o.price - EPS
        at = abs(price - o.price) < EPS
        if not (through or at):
            return []
        if through:
            # the volume that printed at a worse price would have hit us first
            q = min(o.size, size)
        elif self.fill_model == "touch":
            q = min(o.size, size)
        else:
            if o.queue >= size:
                o.queue -= size
                return []
            q = min(o.size, size - o.queue)
            o.queue = 0.0
        o.size -= q
        if side == BID:
            self.cash -= o.price * q
            self.yes += q
        else:
            self.cash -= (1 - o.price) * q
            self.no += q
        m = min(self.yes, self.no)
        if m > 0:
            self.yes -= m
            self.no -= m
            self.cash += m
        self.fills += 1
        self.filled_shares += q
        if o.size <= EPS:
            self.orders[side] = None
        return [(side, o.price, q)]

    # ---- accounting ----------------------------------------------------------------------
    def pnl(self, mid: float) -> float:
        return self.cash + self.yes * mid + self.no * (1 - mid)

    def capital(self) -> float:
        """Collateral locked in resting orders (USD)."""
        c = 0.0
        for o in self.orders.values():
            if o:
                c += o.size * (o.price if o.side == BID else 1 - o.price)
        return c

    def sample_reward(self, book: Book, p: Params, samples_per_day: float = 1440) -> tuple[float, float]:
        """Accrue one sample of rewards. Returns (share, reward added)."""
        bids, asks = book.levels()
        mid = adjusted_mid(bids, asks, p.min_size)
        if mid is None:
            return 0.0, 0.0
        q = {BID: 0.0, ASK: 0.0}
        for side, o in self.orders.items():
            if o and o.size >= p.min_size:
                q[side] = score(p.v_cents, abs(o.price - mid) * 100) * o.size
        ours = qmin(q[BID], q[ASK], mid)
        comp = competitor_qmin(side_q(bids, mid, p.v_cents, p.min_size), side_q(asks, mid, p.v_cents, p.min_size), mid)
        share = ours / (ours + comp) if ours > 0 else 0.0
        add = p.rate_per_day / samples_per_day * share
        self.reward += add
        return share, add


def _floor_tick(x: float, tick: float) -> float:
    k = round(x / tick)
    if k * tick > x + 1e-9:
        k -= 1
    return round(k * tick, 6)


def _ceil_tick(x: float, tick: float) -> float:
    k = round(x / tick)
    if k * tick < x - 1e-9:
        k += 1
    return round(k * tick, 6)
