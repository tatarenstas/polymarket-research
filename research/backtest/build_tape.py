"""Build a local, point-in-time trade tape from the pinned V1 cleaned layers.

One Parquet file per month under data/tape/v1/. Resolved markets only. The outcome
label (Y) and market metadata are stored on every row for convenience; the backtest
must only use them for scoring, never for entry decisions (except close_ts, which is
the scheduled end date known when the market is listed).

Usage: uv run python research/backtest/build_tape.py 2024-01 2025-12
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import duckdb

REV = "5aa1b9d52316a8b2e789e81c8ae42c7ed532e8aa"
SRC = f"hf://datasets/TimeSeventeen/Polymarket-v1@{REV}"
OUT = Path("data/tape/v1")


def months(a: str, b: str):
    y, m = map(int, a.split("-"))
    y2, m2 = map(int, b.split("-"))
    while (y, m) <= (y2, m2):
        yield y, m
        y, m = (y + (m == 12), m % 12 + 1)


def main(a: str, b: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("create secret hf (type huggingface, provider credential_chain)")
    con.execute("set http_retries = 12; set http_retry_wait_ms = 20000; set http_retry_backoff = 1.5")
    con.execute("set preserve_insertion_order = false")
    for y, m in months(a, b):
        dst = OUT / f"{y}_{m:02d}.parquet"
        if dst.exists():
            continue
        t = time.time()
        files = f"['{SRC}/daily_aligned/{y}_{m:02d}_*.parquet', '{SRC}/daily_aligned_multi/{y}_{m:02d}_*.parquet']"
        tmp = dst.with_suffix(".tmp")
        con.execute(f"""
        copy (
          select condition_id as cid, block_timestamp as ts, outcome_seq::tinyint as seq,
                 p_event as p, D::tinyint as d, usdc_amount as usdc, price, fee_usdc as fee,
                 hash(taker) as wallet,
                 (case outcome_seq when 1 then outcome_label = winning_outcome_label
                                   when 2 then outcome_label <> winning_outcome_label end)::tinyint as y,
                 epoch(close_at)::bigint as close_ts, (neg_risk = 'true') as neg_risk,
                 neg_risk_market_id as nrm, category_refined as category, market_slug as slug
          from read_parquet({files}, union_by_name = true)
          where resolution_status = 'resolved' and winning_outcome_label is not null
            and price > 0 and price < 1 and usdc_amount > 0
          order by cid, ts
        ) to '{tmp}' (format parquet, compression zstd, row_group_size 1000000)
        """)
        tmp.rename(dst)
        n = con.execute(f"select count(*) from '{dst}'").fetchone()[0]
        print(f"{dst.name}: {n:,} rows, {dst.stat().st_size / 1e6:.0f} MB, {time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main(*(sys.argv[1:3] if len(sys.argv) >= 3 else ("2024-01", "2025-12")))
