"""V2 holdout tape: markets listed >= 29 days before their scheduled close, closing on or
before CUTOFF. Conditioning on the scheduled close date (known ex ante) avoids the bias of
keeping only markets that already resolved early. All resolution statuses are kept so the
share of still-unresolved markets can be reported; y is null for them.

Usage: uv run python research/backtest/build_tape_v2.py
"""

from __future__ import annotations

import time
from pathlib import Path

import duckdb
import pyarrow.parquet as pq
from huggingface_hub import HfFileSystem
from io import BytesIO

REV = "d1a73f368ea8d5af456105c272edd73bc46a4626"
SRC = f"hf://datasets/TimeSeventeen/Polymarket-v2@{REV}"
OUT = Path("data/tape/v2")
CUTOFF = "2026-11-01"
MONTHS = [(2026, m) for m in range(4, 12)]


SELECT = f"""
  select condition_id as cid, block_timestamp as ts, outcome_seq::tinyint as seq,
         p_event as p, D::tinyint as d, usdc_amount as usdc, price, fee_usdc as fee,
         hash(taker) as wallet,
         case when resolution_status = 'resolved' and winning_outcome_label is not null then
           (case outcome_seq when 1 then outcome_label = winning_outcome_label
                             when 2 then outcome_label <> winning_outcome_label end)::tinyint end as y,
         epoch(close_at)::bigint as close_ts, (neg_risk = 'true') as neg_risk,
         neg_risk_market_id as nrm, category_refined as category, market_slug as slug,
         resolution_status as status, epoch(opens_at)::bigint as opens_ts
  from src
  where close_at <= timestamp '{CUTOFF}'
    and (opens_at is null or close_at - opens_at >= interval 29 days)
    and price > 0 and price < 1 and usdc_amount > 0
"""


def main() -> None:
    """Fetch each daily file whole (one Hub request per file, which keeps us far below the
    resolver rate limit that per-column range reads hit), filter in memory, keep matches."""
    OUT.mkdir(parents=True, exist_ok=True)
    fs = HfFileSystem()
    base = f"datasets/TimeSeventeen/Polymarket-v2@{REV}"
    con = duckdb.connect()
    con.execute("set preserve_insertion_order = false")
    for y, m in MONTHS:
        dst = OUT / f"{y}_{m:02d}.parquet"
        if dst.exists():
            continue
        t = time.time()
        paths = sorted(fs.glob(f"{base}/daily_aligned/{y}_{m:02d}_*.parquet")
                       + fs.glob(f"{base}/daily_aligned_multi/{y}_{m:02d}_*.parquet"))
        con.execute("drop table if exists acc")
        for i, path in enumerate(paths):
            for attempt in range(6):
                try:
                    data = fs.cat_file(path)
                    break
                except Exception as e:  # rate limit or transient network error
                    if attempt == 5:
                        raise
                    time.sleep(60 * (attempt + 1))
            src = pq.read_table(BytesIO(data))  # noqa: F841 (referenced by DuckDB as 'src')
            if "neg_risk_market_id" not in src.column_names:
                import pyarrow as pa
                src = src.append_column("neg_risk_market_id", pa.nulls(src.num_rows, pa.large_string()))
            verb = "create table acc as" if i == 0 else "insert into acc"
            con.execute(f"{verb} {SELECT}")
        tmp = dst.with_suffix(".tmp")
        con.execute(f"copy (select * from acc order by cid, ts) to '{tmp}' (format parquet, compression zstd, row_group_size 1000000)")
        tmp.rename(dst)
        n = con.execute("select count(*) from acc").fetchall()[0][0]
        print(f"{dst.name}: {n:,} rows from {len(paths)} files, {time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main()
