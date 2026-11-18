"""Snapshot scan: where do Polymarket liquidity rewards pay the most per $ of quoting capital?

Read-only, public endpoints:
  GET  clob.polymarket.com/rewards/markets/multi  (sorted by rate_per_day, paged)
  POST clob.polymarket.com/books                  (batch order books)

For every market with rate_per_day >= --min-rate, the script estimates our reward share for a
two-sided quote of --capital USD placed at the best bid/ask ("join") or one tick inside
("improve"). The competition is the current book (src/pmresearch/pm_rewards.py). This is a
single snapshot: books change minute by minute and other makers react. Fills, inventory and
adverse selection are NOT included; this ranks the opportunity only.

Output: data/pm_mm/scan_<UTC>.json and a printed summary.
Usage: uv run python research/pm_mm/reward_scan.py --capital 1000 --min-rate 20
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from pmresearch.pm_clob import books, days_left, reward_markets, session
from pmresearch.pm_rewards import reward_estimate


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--capital", type=float, default=1000)
    ap.add_argument("--min-rate", type=float, default=20)
    ap.add_argument("--top", type=int, default=30)
    args = ap.parse_args()

    s = session()
    mk = reward_markets(s, args.min_rate)
    yes = {m["condition_id"]: m["tokens"][0]["token_id"] for m in mk if m.get("tokens")}
    bk = books(s, list(yes.values()))
    now = dt.datetime.now(dt.UTC)
    rows = []
    for m in mk:
        b = bk.get(yes.get(m["condition_id"], ""))
        if not b:
            continue
        tick = float(b.get("tick_size") or 0.01)
        days = days_left(m.get("end_date"), now)
        for mode in ("join", "improve"):
            e = reward_estimate(b, m["rate"], float(m["rewards_max_spread"]), float(m["rewards_min_size"]),
                                args.capital, tick, improve=(mode == "improve"))
            if e:
                rows.append({"mode": mode, "question": m["question"], "event": m.get("event_slug"),
                             "condition_id": m["condition_id"], "rate": m["rate"],
                             "v": m["rewards_max_spread"], "min_size": m["rewards_min_size"],
                             "vol24": m.get("volume_24hr"), "days_left": days, "tick": tick, **e})
    out = Path("data/pm_mm") / f"scan_{now:%Y%m%dT%H%M}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"capital": args.capital, "markets": len(mk), "rows": rows}))

    tot = sum(m["rate"] for m in mk)
    print(f"{len(mk)} markets with rate >= ${args.min_rate}/day, pool ${tot:,.0f}/day; books {len(bk)}; saved {out}")
    for mode in ("join", "improve"):
        r = sorted((x for x in rows if x["mode"] == mode), key=lambda x: -x["reward_per_1k_day"])
        vals = [x["reward_per_1k_day"] for x in r]
        if not vals:
            continue
        print(f"\n[{mode}] reward per ${args.capital:,.0f} quoted, $/day: median {vals[len(vals)//2]:.2f}, "
              f"p90 {vals[len(vals)//10]:.2f}, markets >= $5/day: {sum(v >= 5 for v in vals)}, >= $20/day: {sum(v >= 20 for v in vals)}")
        print(f"{'$/day':>7} {'share':>6} {'pool':>6} {'v':>4} {'min':>4} {'mid':>5} {'sprd':>5} {'vol24':>8} {'days':>6}  question")
        for x in r[: args.top]:
            print(f"{x['reward_per_1k_day']*args.capital/1000:>7.1f} {x['share']:>6.1%} {x['rate']:>6.0f} {x['v']:>4} {x['min_size']:>4.0f} "
                  f"{x['mid']:>5.3f} {x['spread_c']:>5.1f} {(x['vol24'] or 0):>8.0f} {x['days_left'] if x['days_left'] is None else round(x['days_left'],1)!s:>6}  {x['question'][:62]}")


if __name__ == "__main__":
    main()
