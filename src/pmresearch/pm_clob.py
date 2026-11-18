"""Read-only helpers for Polymarket's public CLOB REST API (no auth, no orders)."""

from __future__ import annotations

import datetime as dt
import time

import requests

API = "https://clob.polymarket.com"
WS_MARKET = "wss://ws-subscriptions-clob.polymarket.com/ws/market"


def session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = "curl/8.7.1"  # the default python UA gets 403 on some endpoints
    return s


def reward_markets(s: requests.Session, min_rate: float) -> list[dict]:
    """Markets with liquidity rewards, highest daily rate first, down to `min_rate` $/day.
    Adds m["rate"] = sum of rewards_config rate_per_day."""
    out, cur = [], None
    while True:
        q = {"page_size": 500, "order_by": "rate_per_day", "position": "DESC"}
        if cur:
            q["next_cursor"] = cur
        j = s.get(f"{API}/rewards/markets/multi", params=q, timeout=30).json()
        d = j.get("data") or []
        for m in d:
            m["rate"] = sum(c["rate_per_day"] for c in m.get("rewards_config") or [])
        out += [m for m in d if m["rate"] >= min_rate]
        cur = j.get("next_cursor")
        if not d or not cur or cur == "LTE=" or d[-1]["rate"] < min_rate:
            return out


def books(s: requests.Session, token_ids: list[str]) -> dict[str, dict]:
    """Batch order books keyed by token id (100 per request, 3 tries each)."""
    res = {}
    for i in range(0, len(token_ids), 100):
        chunk = token_ids[i:i + 100]
        for a in range(3):
            try:
                r = s.post(f"{API}/books", json=[{"token_id": t} for t in chunk], timeout=30)
                for b in r.json():
                    res[b["asset_id"]] = b
                break
            except Exception:
                time.sleep(1 + a)
    return res


def days_left(end_date: str | None, now: dt.datetime) -> float | None:
    if not end_date:
        return None
    try:
        end = dt.datetime.fromisoformat(end_date.replace(" ", "T").replace("Z", "+00:00"))
    except ValueError:
        return None
    if end.tzinfo is None:
        end = end.replace(tzinfo=dt.UTC)
    return (end - now).total_seconds() / 86400
