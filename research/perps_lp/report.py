"""Print the latest summary of a paper LP run. Usage: uv run python research/perps_lp/report.py [run_dir]"""

import json
import sys
from pathlib import Path

run = Path(sys.argv[1]) if len(sys.argv) > 1 else sorted(Path("data/lp_paper").iterdir())[-1]
rows = [json.loads(line) for line in open(run / "summary.jsonl")]
last_t = max(r["t"] for r in rows)
latest = [r for r in rows if r["t"] == last_t]
print(f"run {run.name}; elapsed {latest[0]['elapsed_h']:.2f} h\n")
hdr = ("sym", "maker", "fills", "share%", "mscore", "uptime", "rew_lin$/d", "rew_frm$/d", "pnl$/d", "net_lin$/d",
       "net_frm$/d", "mo10s", "mo60s", "mo300s", "pos$")
print(" | ".join(f"{h:>10}" for h in hdr))


def fmt(v, nd=1):
    return f"{v:10.{nd}f}" if isinstance(v, (int, float)) else f"{'—':>10}"


for r in sorted(latest, key=lambda r: (r["sym"], r["maker"])):
    print(" | ".join([
        f"{r['sym']:>10}", f"{r['maker'][:10]:>10}", f"{r['fills']:10d}", fmt(100 * r.get("maker_share", 0), 2),
        fmt(r.get("maker_score", 0), 2), fmt(r.get("uptime", 0), 2), fmt(r.get("reward_linear_per_day", 0)),
        fmt(r.get("reward_formula_per_day", 0)), fmt(r["trading_pnl_per_day"]), fmt(r["net_per_day_linear"]),
        fmt(r["net_per_day_formula"]), fmt(r.get("markout_10s_bps")), fmt(r.get("markout_60s_bps")),
        fmt(r.get("markout_300s_bps")), fmt(r["pos_usd"], 0),
    ]))
