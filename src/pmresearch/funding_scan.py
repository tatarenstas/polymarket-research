"""Pure logic for the Polymarket Perps funding scanner (no I/O).

Funding settles hourly to whoever holds a position at the settlement instant (live-checked
2026-11-13/14, see docs/findings/06). The ticker exposes the running estimate of the
current hour's rate, so a short (rate > 0) or long (rate < 0) opened just before
settlement collects |rate| x notional. One round trip costs 2 x fee.
"""

from __future__ import annotations

from dataclasses import dataclass

MAKER_FEE, TAKER_FEE = 0.000125, 0.0004


def fees_for(instrument: dict, now_ms: int) -> tuple[float, float]:
    """(maker, taker) base-tier fee rate, honouring an active fee_override."""
    fo = instrument.get("fee_override")
    if fo and fo.get("tiers"):
        start, end = fo.get("start_time") or 0, fo.get("end_time")
        if start <= now_ms and (end is None or now_ms < end):
            t = fo["tiers"][0]
            return float(t["maker_fee_rate"]), float(t["taker_fee_rate"])
    return MAKER_FEE, TAKER_FEE


@dataclass
class Row:
    iid: int
    symbol: str
    rate: float  # current-hour estimate, fraction per hour; > 0 means longs pay shorts
    next_funding_ms: int
    mark: float
    oi_usd: float
    maker_fee: float = MAKER_FEE
    taker_fee: float = TAKER_FEE

    @property
    def side(self) -> str:
        """Side that RECEIVES funding."""
        return "SHORT" if self.rate > 0 else "LONG"

    def ttl_s(self, now_ms: int) -> float:
        return (self.next_funding_ms - now_ms) / 1000

    @property
    def net_maker_bps(self) -> float:
        """Funding minus a post-only round trip, bps of notional (before price noise)."""
        return (abs(self.rate) - 2 * self.maker_fee) * 1e4

    @property
    def net_taker_bps(self) -> float:
        """Funding minus a taker round trip, bps (before spread and price noise)."""
        return (abs(self.rate) - 2 * self.taker_fee) * 1e4


def parse(tickers: list[dict], instruments: dict[int, dict], now_ms: int) -> list[Row]:
    rows = []
    for t in tickers:
        inst = instruments.get(t["instrument_id"], {})
        if inst.get("close_only"):
            continue
        mk, tk = fees_for(inst, now_ms)
        mark = float(t["mark_price"])
        rows.append(Row(t["instrument_id"], t["symbol"], float(t["funding_rate"]), int(t["next_funding"]),
                        mark, float(t["open_interest"]) * mark, mk, tk))
    return sorted(rows, key=lambda r: -abs(r.rate))


def is_signal(row: Row, now_ms: int, min_rate: float, window_s: float) -> bool:
    return abs(row.rate) >= min_rate and 0 < row.ttl_s(now_ms) <= window_s


def book_metrics(book: dict, band_bps: float = 10.0) -> dict:
    """Spread and USD depth within band_bps of mid on each side of an /info/book reply."""
    bids = [(float(p), float(q)) for p, q in book.get("bids", [])]
    asks = [(float(p), float(q)) for p, q in book.get("asks", [])]
    if not bids or not asks:
        return {}
    bb, ba = bids[0][0], asks[0][0]
    mid = (bb + ba) / 2
    lo, hi = mid * (1 - band_bps / 1e4), mid * (1 + band_bps / 1e4)
    return {
        "spread_bps": (ba - bb) / mid * 1e4,
        "bid_depth_usd": sum(p * q for p, q in bids if p >= lo),
        "ask_depth_usd": sum(p * q for p, q in asks if p <= hi),
    }
