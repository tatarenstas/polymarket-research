"""H1–H3: state-conditioned buy-and-hold-to-resolution.

Every 24h snapshot of every open market, look only at the last traded price and the
scheduled time to close. For each (price band × horizon band × side) cell, buy $1 at
the next executable fill after 60s and hold to resolution.

H1 = mid-price bands, long horizons, side -1 (Yes overpriced on long horizons)
H2 = low bands, side -1 (longshots overpriced)
H3 = high bands, short horizons, side +1 (near-certain favourites)

Selection protocol: a cell is "selected" on TRAIN only (t_cluster > 3 and mean_ret > 0,
n clusters >= 100). Its TEST result is the honest estimate.
"""

from pmresearch.backtest.engine import SPLIT_TS, connect, entries_sql, prepare, show, snapshots_sql, state_sql

con = connect()
prepare(con)

show(con, "Scheduled close vs observed trading (is close_at a pre-announced end date?)", """
select count(*) markets,
  round(avg((last_ts > close_ts + 86400)::int), 3) traded_1d_after_close,
  round(avg((last_ts < close_ts - 7*86400)::int), 3) stopped_7d_before_close,
  round(avg((abs(last_ts - close_ts) < 3600)::int), 3) last_trade_within_1h_of_close
from markets""")

PBANDS = "[0.01, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.99]"
HBANDS = "[0, 1, 3, 7, 14, 30, 60, 100000]"

con.execute(f"""
create or replace table h13_state as
with st as ({state_sql(snapshots_sql(24))})
select st.*,
  list_filter({PBANDS}, lambda x: x <= p_last)[-1] as p_lo,
  list_filter({HBANDS}, lambda x: x <= days_to_close)[-1] as h_lo
from st where p_last >= 0.01 and p_last < 0.99
""")
print(con.execute("select count(*), count(distinct cid) from h13_state").fetchall())

signals = """
select cid, t, p_last, p_lo, h_lo, category, neg_risk, s.side
from h13_state, (select unnest([1, -1]) as side) s
"""
con.execute(f"create or replace table h13_trades as {entries_sql(signals, latency_s=60, ref_col='p_last', max_dev=0.03)}")

con.execute(f"""
create or replace table h13_cells as
with tr as (select *, case when entry_ts < {SPLIT_TS} then 'train' else 'test' end period from h13_trades),
cl as (select side, p_lo, h_lo, period, res_cluster, avg(ret) r, count(*) k from tr group by all),
c as (select side, p_lo, h_lo, period, count(*) clusters, avg(r) / nullif(stddev_samp(r)/sqrt(count(*)),0) t_cluster
      from cl group by all),
b as (select side, p_lo, h_lo, period, count(*) n, avg((payoff > 0)::int) winrate, avg(ret) mean_ret,
             avg(hold_days) hold_d, min(ret) worst from tr group by all)
select * from b join c using (side, p_lo, h_lo, period)
""")

show(con, "Cells selected on TRAIN (t_cluster>3, mean_ret>0, >=100 clusters) and their TEST result", f"""
with tr as (select * from h13_cells where period='train'), te as (select * from h13_cells where period='test')
select tr.side, tr.p_lo, tr.h_lo,
       tr.n n_tr, round(tr.winrate,3) win_tr, round(tr.mean_ret,4) ret_tr, round(tr.t_cluster,1) t_tr,
       te.n n_te, round(te.winrate,3) win_te, round(te.mean_ret,4) ret_te, round(te.t_cluster,1) t_te,
       te.clusters cl_te, round(te.hold_d,1) hold_d, round(te.mean_ret/nullif(te.hold_d,0)*365,2) ret_per_cap_yr,
       round(te.worst, 2) worst_te
from tr left join te using (side, p_lo, h_lo)
where tr.t_cluster > 3 and tr.mean_ret > 0 and tr.clusters >= 100
order by tr.side, tr.p_lo, tr.h_lo""")

print("cells tested on train:", con.execute("select count(*) from h13_cells where period='train' and clusters >= 100").fetchall()[0][0])

show(con, "Full grid, buy-the-opposite (side -1): TEST mean_ret by price band x horizon", """
pivot (select p_lo, h_lo, round(mean_ret, 3) r from h13_cells where period='test' and side=-1 and clusters >= 50)
on h_lo using any_value(r) order by p_lo""")

show(con, "Full grid, buy-reference (side +1): TEST mean_ret by price band x horizon", """
pivot (select p_lo, h_lo, round(mean_ret, 3) r from h13_cells where period='test' and side=1 and clusters >= 50)
on h_lo using any_value(r) order by p_lo""")

show(con, "TEST winrate, side -1", """
pivot (select p_lo, h_lo, round(winrate, 3) w from h13_cells where period='test' and side=-1 and clusters >= 50)
on h_lo using any_value(w) order by p_lo""")
