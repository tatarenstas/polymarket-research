"""Quick realism probe (not a validated study): calibration and wallet edge on V1 2024–2025.

Two remote aggregation passes over the pinned V1 cleaned layers. Only aggregates are
stored locally under data/probe/. Unit conventions:

* Y      = 1 if the reference outcome (outcome_seq = 1) won, else 0
* edge   = D * (Y - p_event) per share, marked to resolution, for the taker;
           the maker holds the opposite side and gets -edge
* shares = usdc_amount / price (price of the traded token)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import duckdb

REV = "5aa1b9d52316a8b2e789e81c8ae42c7ed532e8aa"
SRC = f"hf://datasets/TimeSeventeen/Polymarket-v1@{REV}"
OUT = Path("data/probe")
FILES = [f"{SRC}/{layer}/{y}_*.parquet" for layer in ("daily_aligned", "daily_aligned_multi") for y in (2024, 2025)]


def base_sql(cols: str) -> str:
    files = ", ".join(f"'{f}'" for f in FILES)
    return f"""
    select {cols},
           case outcome_seq when 1 then outcome_label = winning_outcome_label
                            when 2 then outcome_label <> winning_outcome_label end::int as Y
    from read_parquet([{files}], union_by_name = true)
    where resolution_status = 'resolved' and winning_outcome_label is not null
      and price > 0 and price < 1 and usdc_amount > 0
    """


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("set preserve_insertion_order = false")
    # Token from `hf auth login` (~/.cache/huggingface/token); never passed explicitly.
    con.execute("create secret hf (type huggingface, provider credential_chain)")
    # Hub rate limits are fixed 5-minute windows: back off long enough to outlast one.
    con.execute("set http_retries = 12")
    con.execute("set http_retry_wait_ms = 20000")
    con.execute("set http_retry_backoff = 1.5")
    step = sys.argv[1] if len(sys.argv) > 1 else "all"

    if step in ("all", "calib"):
        t = time.time()
        con.execute(f"""
        copy (
          select condition_id, neg_risk, category_refined,
                 (block_timestamp // 86400) as day,
                 epoch(close_at) // 86400 - block_timestamp // 86400 as days_to_close,
                 sum(p_event * usdc_amount) / sum(usdc_amount) as vwap_p,
                 sum(usdc_amount) as usdc, count(*) as n,
                 avg(Y) filter (where outcome_seq = 1) as y_seq1,
                 avg(Y) filter (where outcome_seq = 2) as y_seq2,
                 -- consistency checks of the published normalization
                 sum((D <> (case when taker_direction = 'BUY' then 1 else -1 end)
                          * (case when outcome_seq = 1 then 1 else -1 end))::int) as d_mismatch,
                 sum((abs(p_event - case when outcome_seq = 1 then price else 1 - price end) > 1e-9)::int) as p_mismatch
          from ({base_sql("condition_id, neg_risk, category_refined, block_timestamp, close_at, p_event, usdc_amount, outcome_seq, D, taker_direction, price")})
          group by all
        ) to '{OUT}/market_day.parquet'
        """)
        print(f"calib pass {time.time() - t:.0f}s", flush=True)

    if step in ("all", "wallet"):
        t = time.time()
        con.execute(f"""
        copy (
          with b as ({base_sql("condition_id, category_refined, block_timestamp, close_at, p_event, price, usdc_amount, fee_usdc, D, taker, maker")}),
          legs as (
            select taker as wallet, 'taker' as role, condition_id, category_refined, block_timestamp, close_at, p_event,
                   usdc_amount, usdc_amount / price * D * (Y - p_event) - fee_usdc as pnl, Y, D as dir from b
            union all
            select maker, 'maker', condition_id, category_refined, block_timestamp, close_at, p_event,
                   usdc_amount, -(usdc_amount / price * D * (Y - p_event)), Y, -D from b
          )
          select wallet, role, condition_id, any_value(category_refined) as category,
                 min(block_timestamp) as first_ts, any_value(epoch(close_at)) as close_ts,
                 count(*) as n, sum(usdc_amount) as usdc, sum(pnl) as pnl,
                 sum(p_event * usdc_amount) / sum(usdc_amount) as vwap_p,
                 sum(dir * usdc_amount) / sum(usdc_amount) as net_dir, any_value(Y) as Y
          from legs group by wallet, role, condition_id
        ) to '{OUT}/wallet_market.parquet'
        """)
        print(f"wallet pass {time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main()
