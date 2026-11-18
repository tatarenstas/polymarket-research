"""V2 holdout (2026-04 → 2026-10 entries) of the H2 rules fixed on V1. No parameter changes.

A  taker, one entry per market: buy the opposite side when the reference last traded at
   5–30c with >= 30 days to scheduled close (daily snapshots, 60s latency, 1-day window)
B  taker, every daily snapshot (as in the V1 grid)
C  maker: realised fills that sold the reference to a taker buying at 5–30c, >= 30 d to close
M  mirror: buying the reference itself at 1–20c (should lose if the bias persists)
"""

from pmresearch.backtest.engine import connect, entries_sql, prepare, show, snapshots_sql, state_sql

con = connect("data/tape/v2/*.parquet", db="data/bt_v2.duckdb")
prepare(con, force=True)

show(con, "Universe: markets with scheduled close <= 2026-11-01 listed >= 29 d before close", """
select coalesce(status, 'unresolved') status, count(distinct cid) markets, count(*) trades, round(sum(usdc)/1e6,1) usdc_m
from tape_raw group by 1 order by 2 desc""")
show(con, "Label-consistent resolved markets used", """
select count(*) markets, count(distinct cluster) clusters, round(sum(volume)/1e6,1) usdc_m,
       round(avg(y),3) share_ref_won, min(to_timestamp(close_ts))::date first_close, max(to_timestamp(close_ts))::date last_close
from markets""")

con.execute(f"""
create or replace table st as
select * from ({state_sql(snapshots_sql(24))})
where days_to_close >= 30 and p_last >= 0.01 and p_last < 0.30
""")
sig_no = "select cid, t, -1 as side, p_last from st where p_last >= 0.05"
sig_yes = "select cid, t, 1 as side, p_last from st where p_last < 0.20"
con.execute(f"create or replace table v2_no as {entries_sql(sig_no, latency_s=60)}")
con.execute(f"create or replace table v2_yes as {entries_sql(sig_yes, latency_s=60)}")


def summary(src: str) -> str:
    return f"""
    with tr as ({src}),
    cl as (select res_cluster, avg(ret) r from tr group by 1),
    c as (select count(*) clusters, avg(r) cl_mean, avg(r)/nullif(stddev_samp(r)/sqrt(count(*)),0) t from cl)
    select count(*) n, round(avg((payoff>0)::int),3) winrate, round(avg(ret),4) mean_ret,
           round(any_value(c.cl_mean),4) cluster_mean_ret, any_value(c.clusters) clusters, round(any_value(c.t),2) t_cluster,
           round(avg(hold_days),1) hold_d, round(median(entry_usdc),1) med_fill_usdc
    from tr, c"""


show(con, "A. Taker, one entry per market (rule fixed on V1)",
     summary("select * from v2_no qualify row_number() over (partition by cid order by entry_ts) = 1"))
show(con, "A by entry price band", """
with f as (select * from v2_no qualify row_number() over (partition by cid order by entry_ts) = 1)
select case when p_last < 0.1 then 'a 5-10c' when p_last < 0.2 then 'b 10-20c' else 'c 20-30c' end band,
       count(*) n, round(avg((payoff>0)::int),3) winrate, round(avg(ret),4) mean_ret, count(distinct res_cluster) clusters
from f group by 1 order by 1""")
show(con, "B. Taker, every daily snapshot", summary("select * from v2_no"))
show(con, "M. Mirror: buy the reference at 1-20c, one entry per market",
     summary("select * from v2_yes qualify row_number() over (partition by cid order by entry_ts) = 1"))

con.execute("""
create or replace table v2_maker as
select t.cid, t.ts, t.p, t.usdc, m.cluster, 1 - m.y as payoff, (1 - m.y) / (1 - t.p) - 1 as ret,
       t.usdc / t.p * (1 - t.p) as capital
from tape t join markets m using (cid)
where t.d = 1 and t.p >= 0.05 and t.p < 0.30 and m.close_ts - t.ts >= 30 * 86400
""")
show(con, "C. Maker side (capital-weighted)", """
with cl as (select cluster, sum(ret*capital)/sum(capital) r from v2_maker group by 1),
c as (select count(*) clusters, avg(r) cl_mean, avg(r)/nullif(stddev_samp(r)/sqrt(count(*)),0) t from cl)
select count(*) fills, round(sum(capital)/1e6,2) maker_capital_m, round(avg((payoff>0)::int),3) winrate,
       round(sum(ret*capital)/sum(capital),4) cap_w_ret, round(any_value(c.cl_mean),4) cluster_mean_ret,
       any_value(c.clusters) clusters, round(any_value(c.t),2) t_cluster
from v2_maker, c""")
show(con, "C by month", """
select strftime(to_timestamp(ts), '%Y-%m') as ym, count(*) fills, round(sum(capital)/1e6,2) capital_m,
       round(sum(ret*capital)/sum(capital),4) cap_w_ret, count(distinct cluster) clusters
from v2_maker group by 1 order by 1""")
show(con, "C: top and bottom clusters", """
(select 'best' k, any_value(m.slug) slug, round(sum(ret*capital)/1e3,1) pnl_k from v2_maker v join markets m using (cid)
 group by v.cluster order by pnl_k desc limit 5)
union all
(select 'worst', any_value(m.slug), round(sum(ret*capital)/1e3,1) from v2_maker v join markets m using (cid)
 group by v.cluster order by 3 asc limit 5)""")

# Robustness: only markets scheduled to close by 2026-08-31, where >= 96% of markets are resolved
# (later closes still have many unresolved markets: metadata lag / ongoing events).
CLEAN = "res_close_ts <= epoch(timestamp '2026-09-01')"
show(con, "ROBUST A. Taker one entry per market, close <= 2026-08-31",
     summary(f"select * from v2_no where {CLEAN} qualify row_number() over (partition by cid order by entry_ts) = 1"))
show(con, "ROBUST M. Mirror, close <= 2026-08-31",
     summary(f"select * from v2_yes where {CLEAN} qualify row_number() over (partition by cid order by entry_ts) = 1"))
show(con, "ROBUST C. Maker, close <= 2026-08-31", """
with v as (select v.* from v2_maker v join markets m using (cid) where m.close_ts <= epoch(timestamp '2026-09-01')),
cl as (select cluster, sum(ret*capital)/sum(capital) r from v group by 1),
c as (select count(*) clusters, avg(r) cl_mean, avg(r)/nullif(stddev_samp(r)/sqrt(count(*)),0) t from cl)
select count(*) fills, round(sum(capital)/1e6,2) maker_capital_m, round(avg((payoff>0)::int),3) winrate,
       round(sum(ret*capital)/sum(capital),4) cap_w_ret, round(any_value(c.cl_mean),4) cluster_mean_ret,
       any_value(c.clusters) clusters, round(any_value(c.t),2) t_cluster
from v, c""")
