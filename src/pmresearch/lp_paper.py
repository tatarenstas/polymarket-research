"""Paper market-making against the live Polymarket Perps feed, to estimate liquidity rewards.

No orders are sent. A virtual maker quotes both sides around mid; public trades decide
virtual fills; the rewards formula from the docs is applied to our virtual quotes vs the
visible book. Everything here is pure logic so it can be unit-tested; the I/O runner is
in research/perps_lp/run_paper.py.

Rewards (docs.polymarket.com/perps/liquidity-rewards):
  tier weights by distance from mid: <=5bps 1.0, <=10bps 0.25, <=20bps 0.10; cap $100k
  per tier per side per maker; snapshot = harmonic mean of bid and ask scores;
  maker_score = log(1 + min(share,25%)/1%) / log(26), eligible only if share >= 1%;
  raw = maker_score^0.35 * liquidity^0.65 * uptime.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

TIERS = ((5.0, 1.0), (10.0, 0.25), (20.0, 0.10))  # (max distance bps, weight)
TIER_CAP = 100_000.0
MAKER_FEE = 0.000125  # base tier


def tier_weight(dist_bps: float) -> float:
    for limit, w in TIERS:
        if dist_bps <= limit + 1e-9:
            return w
    return 0.0


def side_score(levels: list[tuple[float, float]], mid: float, cap: bool = True) -> float:
    """Weighted resting notional within 20 bps. levels = [(price, qty)]."""
    per_tier = [0.0, 0.0, 0.0]
    for p, q in levels:
        d = abs(p - mid) / mid * 1e4
        for i, (limit, _) in enumerate(TIERS):
            if d <= limit + 1e-9:
                per_tier[i] += p * q
                break
    return sum((min(n, TIER_CAP) if cap else n) * w for n, (_, w) in zip(per_tier, TIERS))


def harmonic(a: float, b: float) -> float:
    return 2 * a * b / (a + b) if a > 0 and b > 0 else 0.0


def maker_score(share: float) -> float:
    if share < 0.01:
        return 0.0
    return math.log(1 + min(share, 0.25) / 0.01) / math.log(26)


@dataclass
class Fill:
    ts: int
    side: int  # +1 we bought (our bid hit), -1 we sold
    price: float
    qty: float
    mid: float
    markouts: dict = field(default_factory=dict)  # horizon_s -> mid


@dataclass
class VirtualMaker:
    """One quoting policy on one market.

    hedged: inventory is flattened right after each fill at mid +/- hedge_bps (external venue).
    through_only: conservative fill model (trade must print strictly through our price).
    """

    name: str
    size_usd: float = 5_000.0
    offset_bps: float = 3.0
    requote_s: float = 2.0
    max_inv_usd: float = 5_000.0
    hedged: bool = False
    hedge_bps: float = 5.0
    through_only: bool = False

    bid: float | None = None
    ask: float | None = None
    bid_left: float = 0.0  # base qty
    ask_left: float = 0.0
    last_quote_ts: int = -10**15
    pos: float = 0.0
    cash: float = 0.0
    fees: float = 0.0
    hedge_cost: float = 0.0
    fills: list[Fill] = field(default_factory=list)
    maker_notional: float = 0.0

    def inventory_usd(self, mid: float) -> float:
        return self.pos * mid

    def requote(self, ts: int, mid: float) -> None:
        if (ts - self.last_quote_ts) < self.requote_s * 1000:
            return
        self.last_quote_ts = ts
        inv = self.inventory_usd(mid)
        q = self.offset_bps / 1e4
        self.bid = mid * (1 - q) if inv < self.max_inv_usd else None
        self.ask = mid * (1 + q) if inv > -self.max_inv_usd else None
        self.bid_left = self.size_usd / self.bid if self.bid else 0.0
        self.ask_left = self.size_usd / self.ask if self.ask else 0.0

    def on_trade(self, ts: int, taker_side: str, price: float, qty: float, mid: float) -> Fill | None:
        """A public taker trade; fill us if it reaches our resting price."""
        if taker_side == "long" and self.ask is not None and self.ask_left > 0:
            hit = price > self.ask if self.through_only else price >= self.ask
            if hit:
                return self._fill(ts, -1, self.ask, min(qty, self.ask_left), mid)
        if taker_side == "short" and self.bid is not None and self.bid_left > 0:
            hit = price < self.bid if self.through_only else price <= self.bid
            if hit:
                return self._fill(ts, +1, self.bid, min(qty, self.bid_left), mid)
        return None

    def _fill(self, ts: int, side: int, price: float, qty: float, mid: float) -> Fill:
        notional = price * qty
        self.pos += side * qty
        self.cash -= side * notional
        fee = notional * MAKER_FEE
        self.cash -= fee
        self.fees += fee
        self.maker_notional += notional
        if side > 0:
            self.bid_left -= qty
        else:
            self.ask_left -= qty
        f = Fill(ts, side, price, qty, mid)
        self.fills.append(f)
        if self.hedged:  # flatten on an external venue at mid, paying hedge_bps
            cost = abs(self.pos) * mid * self.hedge_bps / 1e4
            self.cash += self.pos * mid - cost
            self.hedge_cost += cost
            self.pos = 0.0
        return f

    def our_levels(self) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
        b = [(self.bid, self.bid_left)] if self.bid and self.bid_left > 0 else []
        a = [(self.ask, self.ask_left)] if self.ask and self.ask_left > 0 else []
        return b, a

    def pnl(self, mid: float) -> float:
        return self.cash + self.pos * mid


@dataclass
class RewardTracker:
    """Accumulates per-snapshot scores of us vs the visible competition."""

    snapshots: int = 0
    qualifying: int = 0
    ours_sum: float = 0.0
    comp_sum: float = 0.0

    def sample(self, maker: VirtualMaker, book_bids, book_asks, mid: float) -> None:
        ob, oa = maker.our_levels()
        ours = harmonic(side_score(ob, mid), side_score(oa, mid))
        comp = harmonic(side_score(book_bids, mid, cap=False), side_score(book_asks, mid, cap=False))
        self.snapshots += 1
        if ours > 0:
            self.qualifying += 1
            self.ours_sum += ours
        self.comp_sum += comp

    def estimates(self, pool_per_day: float, maker_share: float) -> dict:
        """Daily reward estimates.

        linear: pool * our liquidity share (ignores maker_score; upper-bound style).
        formula: docs formula for us; competitors treated as one maker with maker_score 1 and
                 uptime 1 (their true split is unobservable from the public book).
        """
        if self.snapshots == 0:
            return {}
        uptime = self.qualifying / self.snapshots
        ours_avg = self.ours_sum / self.qualifying if self.qualifying else 0.0
        comp_avg = self.comp_sum / self.snapshots
        linear = pool_per_day * self.ours_sum / (self.ours_sum + self.comp_sum) if self.ours_sum else 0.0
        ms = maker_score(maker_share)
        raw_us = (ms**0.35) * (ours_avg**0.65) * uptime
        raw_comp = comp_avg**0.65
        formula = pool_per_day * raw_us / (raw_us + raw_comp) if raw_us > 0 else 0.0
        return {
            "uptime": uptime,
            "our_liq_avg": ours_avg,
            "comp_liq_avg": comp_avg,
            "maker_share": maker_share,
            "maker_score": ms,
            "reward_linear_per_day": linear,
            "reward_formula_per_day": formula,
        }


@dataclass
class DelayedHedgeMaker(VirtualMaker):
    """Stage-1 model: Polymarket maker leg + realistic hedge on an external venue.

    * Polymarket position is NOT flattened instantly. After each fill a hedge check is
      scheduled at fill_time + hedge_delay_s; at that moment the net exposure
      (poly pos + hedge pos) is traded on the hedge venue as a taker at its then-current
      bid/ask, paying hedge_fee, if |net| * price exceeds hedge_threshold_usd.
    * Quotes are skewed against Polymarket inventory (skew_bps at max_inv_usd) so that
      later fills unwind it; the hedge unwinds through the same netting rule.
    * P&L marks each leg at its own venue mid, so cross-venue basis moves are included.
    All times are local receipt times in ms (one clock for both venues).
    """

    hedge_delay_s: float = 1.0
    hedge_fee: float = 0.0005
    hedge_threshold_usd: float = 0.0
    skew_bps: float = 3.0

    hpos: float = 0.0
    hcash: float = 0.0
    hedge_fees: float = 0.0
    hedge_slippage: float = 0.0  # vs hedge-venue mid at execution
    hedge_trades: int = 0
    funding: float = 0.0  # + received, - paid (both legs)
    due: list = field(default_factory=list)

    def requote(self, ts: int, mid: float) -> None:
        if (ts - self.last_quote_ts) < self.requote_s * 1000:
            return
        self.last_quote_ts = ts
        inv = self.inventory_usd(mid)
        frac = max(-1.0, min(1.0, inv / self.max_inv_usd)) if self.max_inv_usd else 0.0
        center = mid * (1 - self.skew_bps / 1e4 * frac)
        q = self.offset_bps / 1e4
        self.bid = center * (1 - q) if inv < self.max_inv_usd else None
        self.ask = center * (1 + q) if inv > -self.max_inv_usd else None
        self.bid_left = self.size_usd / self.bid if self.bid else 0.0
        self.ask_left = self.size_usd / self.ask if self.ask else 0.0

    def _fill(self, ts: int, side: int, price: float, qty: float, mid: float) -> Fill:
        f = super()._fill(ts, side, price, qty, mid)  # hedged=False on this class
        self.due.append(ts + int(self.hedge_delay_s * 1000))
        return f

    def on_hedge_quote(self, now: int, bid: float, ask: float) -> None:
        """Run hedge checks that are due, at the hedge venue's current top of book."""
        if not self.due or self.due[0] > now:
            return
        self.due = [d for d in self.due if d > now]
        net = self.pos + self.hpos
        hmid = (bid + ask) / 2
        if abs(net) * hmid <= self.hedge_threshold_usd or net == 0:
            return
        qty = -net  # trade to flatten
        px = ask if qty > 0 else bid
        notional = abs(qty) * px
        fee = notional * self.hedge_fee
        self.hpos += qty
        self.hcash -= qty * px + fee
        self.hedge_fees += fee
        self.hedge_slippage += abs(px - hmid) * abs(qty)
        self.hedge_trades += 1

    def apply_funding(self, venue: str, rate: float, mark: float) -> None:
        """Positive rate: longs pay shorts (both venues use this convention)."""
        pos = self.pos if venue == "poly" else self.hpos
        self.funding += -pos * mark * rate

    def pnl2(self, mid: float, hmid: float | None) -> float:
        h = self.hpos * hmid if (hmid and self.hpos) else 0.0
        return self.cash + self.hcash + self.pos * mid + h + self.funding
