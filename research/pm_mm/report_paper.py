"""Report for a prediction-market MM paper run (research/pm_mm/run_paper.py).

Usage: uv run python research/pm_mm/report_paper.py [run_dir] [--markets]

Per variant: rewards accrued, inventory PnL marked to mid, net, $/day per $1k quoted, fills,
and fill markouts (mid h later minus fill price, signed for our side) at 1 min / 1 h / 1 day.
"""

from __future__ import annotations

import bisect
import json
import sys
from collections import defaultdict
from pathlib import Path


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    run = Path(args[0]) if args else sorted(Path("data/pm_mm/paper").iterdir())[-1]
    cfg = json.loads((run / "config.json").read_text())
    q = {m["cid"]: m["question"] for m in cfg["markets"]}
    rows = [json.loads(line) for line in open(run / "samples.jsonl")]
    fills = [json.loads(line) for line in open(run / "fills.jsonl")]
    if not rows:
        print("no samples yet")
        return
    t0, t1 = min(r["t"] for r in rows), max(r["t"] for r in rows)
    days = max((t1 - t0) / 86400, 1e-9)
    last = {}
    mids = defaultdict(list)
    for r in rows:
        last[r["cid"]] = r
        if r["mid"] is not None:
            mids[r["cid"]].append((r["t"], r["mid"]))
    cap_total = cfg["capital"] * len(last)
    print(f"run {run.name}: {len(last)} markets, {days * 24:.1f} h, quoted ${cfg['capital']:.0f} per market "
          f"(${cap_total:,.0f} per variant). $/day are extrapolated.\n")

    def mid_after(cid, t, h):
        xs = mids[cid]
        i = bisect.bisect_left(xs, (t + h, -1))
        return xs[i][1] if i < len(xs) else None

    mo = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))  # maker -> h -> [pnl, notional]
    for f in fills:
        sgn = 1 if f["side"] == 1 else -1
        for h in (60, 3600, 86400):
            m = mid_after(f["cid"], f["t"], h)
            if m is not None:
                x = mo[f["maker"]][h]
                x[0] += sgn * (m - f["price"]) * f["q"]
                x[1] += f["q"] * (f["price"] if sgn == 1 else 1 - f["price"])

    hdr = f"{'variant':<12}{'reward$':>9}{'invPnL$':>9}{'net$':>8}{'net/d':>8}{'per$1k/d':>9}{'fills':>7}{'filled$':>9}" \
          f"{'mo1m':>7}{'mo1h':>7}{'mo1d':>7}"
    print(hdr)
    for n in cfg["variants"]:
        rew = sum(r["mk"][n][1] for r in last.values())
        pnl = sum(r["mk"][n][2] or 0 for r in last.values())
        nf = sum(r["mk"][n][8] for r in last.values())
        filled = sum(f["q"] * (f["price"] if f["side"] == 1 else 1 - f["price"]) for f in fills if f["maker"] == n)
        m = [mo[n][h][0] / mo[n][h][1] if mo[n][h][1] else None for h in (60, 3600, 86400)]
        ms = "".join(f"{x:>+7.1%}" if x is not None else f"{'—':>7}" for x in m)
        net = rew + pnl
        print(f"{n:<12}{rew:>9.2f}{pnl:>+9.2f}{net:>+8.2f}{net / days:>+8.1f}{net / days / cap_total * 1000:>+9.2f}"
              f"{nf:>7}{filled:>9.0f}{ms}")

    if "--markets" in sys.argv:
        n = "join_q"
        print(f"\nper market ({n}):")
        print(f"{'rate/d':>7}{'share':>7}{'reward$':>9}{'invPnL$':>9}{'fills':>6}{'yes':>7}{'no':>7}  question")
        avg_share = defaultdict(list)
        for r in rows:
            avg_share[r["cid"]].append(r["mk"][n][0])
        for cid, r in sorted(last.items(), key=lambda kv: -(kv[1]["mk"][n][1] + (kv[1]["mk"][n][2] or 0))):
            x = r["mk"][n]
            s = sum(avg_share[cid]) / len(avg_share[cid])
            print(f"{r['rate']:>7.0f}{s:>7.0%}{x[1]:>9.2f}{(x[2] or 0):>+9.2f}{x[8]:>6}{x[3]:>7.0f}{x[4]:>7.0f}  {q[cid][:60]}")


if __name__ == "__main__":
    main()
