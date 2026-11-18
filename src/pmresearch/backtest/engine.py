"""DuckDB building blocks: markets, snapshots, point-in-time state, executable entries, metrics."""

from __future__ import annotations

from pathlib import Path

import duckdb

SPLIT_TS = 1751328000  # 2025-07-01 00:00 UTC: train before, test from
DAY = 86400


def connect(tape_glob: str = "data/tape/v1/*.parquet", db: str = "data/bt.duckdb") -> duckdb.DuckDBPyConnection:
    Path(db).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(db)
    con.execute("set preserve_insertion_order = false")
    # 16 GB laptop: cap memory and spill to disk instead of crashing on big window/ASOF joins.
    con.execute("set memory_limit = '7GB'")
    con.execute("set threads = 6")
    con.execute("set temp_directory = 'data/tmp'")
    con.execute(f"create or replace view tape_raw as select * from read_parquet('{tape_glob}')")
    return con


def prepare(con: duckdb.DuckDBPyConnection, force: bool = False) -> None:
    """Market table (label-consistent markets only) and per-direction trade tables."""
    have = {r[0] for r in con.execute("select table_name from information_schema.tables").fetchall()}
    if "markets" in have and not force:
        return
    con.execute("""
    create or replace table markets as
    select cid, any_value(slug) slug, any_value(category) category, bool_or(neg_risk) neg_risk,
           any_value(nrm) nrm, coalesce(any_value(nrm), cid) cluster, max(close_ts) close_ts,
           min(y) y, min(ts) first_ts, max(ts) last_ts, count(*) n, sum(usdc) volume
    from tape_raw group by cid
    having min(y) = max(y) and max(close_ts) is not null and count(distinct close_ts) = 1
    """)
    con.execute("""
    create or replace table tape as
    select t.cid, t.ts, t.p, t.d, t.usdc, t.fee, t.wallet, t.price
    from tape_raw t semi join markets m using (cid)
    """)
    for name, d in (("buys", 1), ("sells", -1)):
        con.execute(f"create or replace table {name} as select cid, ts, p, usdc, fee from tape where d = {d}")


def snapshots_sql(step_hours: int) -> str:
    """Regular snapshot times for every market over its trading life."""
    step = step_hours * 3600
    return f"""
    select cid, unnest(range((first_ts // {step} + 1) * {step}, last_ts, {step})) as t
    from markets
    """


def state_sql(snapshots: str, stale_s: int = 3 * DAY) -> str:
    """Last traded price before each snapshot (point-in-time), with horizon to scheduled close."""
    return f"""
    select s.cid, s.t, tp.p as p_last, s.t - tp.ts as age_s,
           (m.close_ts - s.t) / {DAY} as days_to_close, m.category, m.neg_risk, m.cluster, m.y
    from ({snapshots}) s
    asof join tape tp on s.cid = tp.cid and tp.ts <= s.t
    join markets m on m.cid = s.cid
    where s.t - tp.ts <= {stale_s} and m.close_ts > s.t
    """


def entries_sql(
    signals: str,
    latency_s: int = 0,
    window_s: int = DAY,
    ref_col: str | None = None,
    max_dev: float | None = None,
) -> str:
    """Executable entries for signals with columns (cid, t, side, ...). Keeps signal columns.

    Buys of the reference (side +1) fill at the next taker *buy*; side -1 at the next
    taker *sell* of the reference (= a buy of the opposite token).

    ``ref_col``/``max_dev``: drop entries whose fill price (reference axis) is more than
    ``max_dev`` away from the signal's reference price. The next real fill can be an
    off-market print or follow a jump the signal never saw; such prices are not
    obtainable from a live book and inflated earlier results (see findings 04).
    """
    guard = f"and abs(entry_p - {ref_col}) <= {max_dev}" if ref_col and max_dev is not None else ""
    return f"""
    with sig as ({signals}),
    pos as (
      select s.*, b.ts as entry_ts, b.p as entry_p, b.fee / b.usdc as fee_rate, b.usdc as entry_usdc
      from (select * from sig where side = 1) s
      asof join buys b on s.cid = b.cid and b.ts >= s.t + {latency_s}
    ),
    neg as (
      select s.*, b.ts as entry_ts, b.p as entry_p, b.fee / b.usdc as fee_rate, b.usdc as entry_usdc
      from (select * from sig where side = -1) s
      asof join sells b on s.cid = b.cid and b.ts >= s.t + {latency_s}
    ),
    e as (select * from pos union all by name select * from neg)
    select e.*, m.y as y_res, m.close_ts as res_close_ts, m.last_ts as res_last_ts, m.cluster as res_cluster,
           case when side = 1 then entry_p else 1 - entry_p end as cost,
           case when side = 1 then m.y else 1 - m.y end as payoff,
           payoff / cost - 1 - coalesce(fee_rate, 0) as ret,
           greatest(m.last_ts - entry_ts, 0) / {DAY} as hold_days
    from e join markets m using (cid)
    where entry_ts - t <= {window_s} and cost > 0 {guard}
    """


def metrics_sql(trades: str, by: str = "") -> str:
    """Per-group metrics, split into train/test by entry time. Cluster = neg-risk event or market."""
    grp = f"{by}, " if by else ""
    return f"""
    with tr as (select *, case when entry_ts < {SPLIT_TS} then 'train' else 'test' end as period from ({trades})),
    cl as (
      select {grp} period, res_cluster, avg(ret) r from tr group by all
    ),
    clstat as (
      select {grp} period, count(*) clusters, avg(r) / nullif(stddev_samp(r) / sqrt(count(*)), 0) as t_cluster
      from cl group by all
    ),
    base as (
      select {grp} period, count(*) n, round(avg((payoff > 0)::int), 3) winrate,
             round(avg(ret), 4) mean_ret, round(median(ret), 4) median_ret,
             round(avg(cost), 3) avg_cost, round(avg(hold_days), 1) hold_d,
             round(avg(ret) / nullif(avg(hold_days), 0) * 365, 3) ret_per_capital_year,
             round(min(ret), 2) worst, round(median(entry_usdc), 0) med_fill_usdc
      from tr group by all
    )
    select b.*, c.clusters, round(c.t_cluster, 2) t_cluster
    from base b join clstat c using ({grp} period)
    order by {grp} period desc
    """


def show(con: duckdb.DuckDBPyConnection, title: str, sql: str, rows: int = 80) -> None:
    # Plain-text table via fetchall: DuckDB's .show() crashed (SIGTRAP) on some results.
    print(f"\n### {title}", flush=True)
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    data = [["" if v is None else str(v) for v in r] for r in cur.fetchall()]
    widths = [max([len(c)] + [len(r[i]) for r in data]) for i, c in enumerate(cols)]
    print(" | ".join(c.rjust(w) for c, w in zip(cols, widths)))
    print("-+-".join("-" * w for w in widths))
    for r in data[:rows]:
        print(" | ".join(v.rjust(w) for v, w in zip(r, widths)))
    if len(data) > rows:
        print(f"... {len(data) - rows} more rows")
    print(flush=True)
