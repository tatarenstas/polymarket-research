"""Polymarket (prediction-market CLOB) liquidity-reward scoring, per the official methodology
(docs.polymarket.com/market-makers/liquidity-rewards, read 2026-11-14). Pure functions, no I/O.

  S(v, s) = ((v - s) / v)^2            v = max spread (cents), s = distance from the
                                         size-cutoff-adjusted midpoint (cents); b = 1 pre-game
  Q_one = sum S * bid size (m) + sum S * ask size (m')   -> on the YES book: YES bids
  Q_two = sum S * ask size (m) + sum S * bid size (m')   -> on the YES book: YES asks
  Q_min = max(min(Q1, Q2), max(Q1, Q2) / c)  if 0.10 <= mid <= 0.90, else min(Q1, Q2); c = 3
  reward = rate_per_day * (our Q_min / sum of all makers' Q_min), averaged over ~1440 samples/day

The YES and NO books are mirrors, so the YES book carries all resting liquidity: a NO bid
at q is a YES ask at 1 - q. Sizes are in shares.

The competitors' sum of Q_min is not observable per maker. `competitor_qmin` uses
min(Q1, Q2) + |Q1 - Q2| / c: the matched depth counts as two-sided and the excess as
single-sided. This is exact if every maker quotes either fully two-sided or one-sided.
"""

from __future__ import annotations

C = 3.0


def score(v_cents: float, s_cents: float) -> float:
    if s_cents < 0 or s_cents >= v_cents:
        return 0.0
    return ((v_cents - s_cents) / v_cents) ** 2


def parse_book(book: dict) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    """Bids best-first (descending), asks best-first (ascending)."""
    bids = sorted(((float(o["price"]), float(o["size"])) for o in book.get("bids", [])), reverse=True)
    asks = sorted((float(o["price"]), float(o["size"])) for o in book.get("asks", []))
    return bids, asks


def adjusted_mid(bids, asks, min_size: float) -> float | None:
    """Midpoint ignoring levels smaller than the reward min size."""
    bb = next((p for p, q in bids if q >= min_size), None)
    ba = next((p for p, q in asks if q >= min_size), None)
    if bb is None or ba is None:
        return None
    return (bb + ba) / 2


def side_q(levels, mid: float, v_cents: float, min_size: float) -> float:
    return sum(score(v_cents, abs(p - mid) * 100) * q for p, q in levels if q >= min_size)


def qmin(q1: float, q2: float, mid: float) -> float:
    if 0.10 <= mid <= 0.90:
        return max(min(q1, q2), max(q1, q2) / C)
    return min(q1, q2)


def competitor_qmin(q1: float, q2: float, mid: float) -> float:
    if 0.10 <= mid <= 0.90:
        return min(q1, q2) + abs(q1 - q2) / C
    return min(q1, q2)


def our_quote(bids, asks, mid: float, tick: float, improve: bool) -> tuple[float, float] | None:
    """Prices for a two-sided quote: join the best levels, or step one tick inside when the
    spread leaves room (never crossing or touching the other side)."""
    if not bids or not asks:
        return None
    b, a = bids[0][0], asks[0][0]
    if improve and a - b >= 3 * tick - 1e-9:
        b, a = b + tick, a - tick
    return round(b, 6), round(a, 6)


def reward_estimate(book: dict, rate_per_day: float, v_cents: float, min_size: float,
                    capital_usd: float, tick: float = 0.01, improve: bool = False) -> dict | None:
    """Daily reward for quoting `capital_usd` two-sided, against the current book.

    Two-sided quote = YES bid at b plus NO bid at 1 - a (that is, a YES ask at a), so it needs
    no inventory: capital = shares * (b + 1 - a) and shares = capital / (1 - (a - b)).
    """
    bids, asks = parse_book(book)
    mid = adjusted_mid(bids, asks, min_size)
    if mid is None:
        return None
    q = our_quote(bids, asks, mid, tick, improve)
    if q is None:
        return None
    b, a = q
    shares = capital_usd / max(1e-9, 1 - (a - b))
    if shares < min_size:
        return None
    q1c, q2c = side_q(bids, mid, v_cents, min_size), side_q(asks, mid, v_cents, min_size)
    comp = competitor_qmin(q1c, q2c, mid)
    ours = qmin(score(v_cents, abs(mid - b) * 100) * shares, score(v_cents, abs(a - mid) * 100) * shares, mid)
    share = ours / (ours + comp) if ours > 0 else 0.0
    return {
        "mid": mid, "bid": b, "ask": a, "spread_c": (asks[0][0] - bids[0][0]) * 100,
        "shares": shares, "q_ours": ours, "q_comp": comp, "share": share,
        "reward_per_day": rate_per_day * share,
        "reward_per_1k_day": rate_per_day * share / capital_usd * 1000,
    }
