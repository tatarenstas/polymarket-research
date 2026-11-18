"""Latest summary of a stage-1 run. Usage: uv run python research/perps_lp/report_stage1.py [run_dir]"""

import json
import sys
from pathlib import Path

run = Path(sys.argv[1]) if len(sys.argv) > 1 else sorted(Path("data/lp_stage1").iterdir())[-1]
rows = [json.loads(line) for line in open(run / "summary.jsonl")]
last = max(r["t"] for r in rows)
latest = sorted((r for r in rows if r["t"] == last), key=lambda r: (r["sym"], r["maker"]))
print(f"run {run.name}; elapsed {latest[0]['elapsed_h']:.2f} h  (values per day are extrapolated)\n")
cols = [("sym", 9, "s"), ("maker", 10, "s"), ("fills", 6, "d"), ("share%", 7, ".1f"), ("uptime", 6, ".2f"),
        ("rew_lin", 8, ".0f"), ("rew_frm", 8, ".0f"), ("pnl/d", 8, ".0f"), ("NET_lin", 8, ".0f"), ("NET_frm", 8, ".0f"),
        ("mFee", 6, ".1f"), ("hFee", 6, ".1f"), ("hSlip", 6, ".1f"), ("fund", 6, ".2f"), ("hTr", 5, "d"),
        ("mo10", 6, ".1f"), ("mo60", 6, ".1f"), ("mo300", 6, ".1f"), ("netExp$", 8, ".0f")]
print(" ".join(f"{c:>{w}}" for c, w, _ in cols))
for r in latest:
    vals = [r["sym"], r["maker"], r["fills"], 100 * r.get("maker_share", 0), r.get("uptime", 0),
            r.get("reward_linear_per_day", 0), r.get("reward_formula_per_day", 0), r["pnl_per_day"],
            r["net_lin_per_day"], r["net_frm_per_day"], r["maker_fees"], r["hedge_fees"], r["hedge_slippage"],
            r["funding"], r["hedge_trades"], r.get("mo10s_bps"), r.get("mo60s_bps"), r.get("mo300s_bps"),
            r["net_exposure_usd"]]
    out = []
    for (c, w, f), v in zip(cols, vals):
        out.append(f"{'—':>{w}}" if v is None else f"{v:>{w}{f}}")
    print(" ".join(out))
