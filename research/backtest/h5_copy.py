"""H5: copy wallets with a proven train-period record, with realistic delays.

Skill is estimated ONLY from markets that closed and stopped trading before the split
(no label leakage). Copies are simulated ONLY in the test period: the first trade of a
wallet in a market (price 0.05–0.95, >= $100) is the signal; we enter after a delay at
the next executable fill in the same direction and hold to resolution.
"""

from pmresearch.backtest.engine import SPLIT_TS, connect, entries_sql, prepare, show

con = connect()
prepare(con)

con.execute(f"""
create or replace table h5_skill as
with wm as (
  select t.wallet, t.cid,
         sum(t.usdc) usdc,
         sum(t.usdc / t.price * t.d * (m.y - t.p) - t.fee) pnl
  from tape t join markets m using (cid)
  where t.ts < {SPLIT_TS} and m.last_ts < {SPLIT_TS} and m.close_ts < {SPLIT_TS}
  group by all having sum(t.usdc) >= 10
)
select wallet, count(*) k, sum(pnl)/sum(usdc) roi, avg(pnl/usdc) / nullif(stddev_samp(pnl/usdc)/sqrt(count(*)), 0) t
from wm group by wallet having count(*) >= 20
""")
show(con, "Train-period wallet skill distribution", """
select count(*) wallets, count(*) filter (where t > 3) t_gt_3, count(*) filter (where t > 5) t_gt_5,
       count(*) filter (where t <= 0) t_le_0 from h5_skill""")

con.execute(f"""
create or replace table h5_signals as
with first as (
  -- first qualifying trade per (wallet, market); arg_min avoids a 130M-row window sort
  select wallet, cid, min(ts) as ts, arg_min(d, ts) as d, arg_min(p, ts) as p_ref
  from tape
  where ts >= {SPLIT_TS} and p between 0.05 and 0.95 and usdc >= 100
  group by wallet, cid
)
select f.cid, f.ts as t, f.d::int as side, f.wallet, f.p_ref,
       case when s.t > 5 then 'a t>5' when s.t > 3 then 'b 3<t<=5' when s.t > 0 then 'c 0<t<=3' else 'd t<=0' end as grp
from first f join h5_skill s using (wallet)
""")
print(con.execute("select grp, count(*) from h5_signals group by 1 order by 1").fetchall(), flush=True)
signals = "select * from h5_signals"
con.execute("drop table if exists h5_trades")
parts = []
for lat in (0, 60, 600, 3600, 6 * 3600):
    sql = f"select *, {lat} as delay_s from ({entries_sql(signals, latency_s=lat, window_s=86400, ref_col='p_ref', max_dev=0.03)})"
    if lat == 0:
        con.execute(f"create table h5_trades as {sql}")
    else:
        con.execute(f"insert into h5_trades by name {sql}")
    print("delay", lat, "done", flush=True)

show(con, "Copy results in TEST period by train skill group and delay (delay 0 = their own fill)", """
with cl as (select grp, delay_s, res_cluster, avg(ret) r from h5_trades group by all),
c as (select grp, delay_s, count(*) clusters, avg(r)/nullif(stddev_samp(r)/sqrt(count(*)),0) t from cl group by all)
select grp, delay_s, count(*) n, count(distinct wallet) wallets, round(avg((payoff>0)::int),3) winrate,
       round(avg(ret),4) mean_ret, round(median(ret),4) med_ret, round(avg(cost),3) avg_cost,
       any_value(c.clusters) clusters, any_value(round(c.t,1)) t_cluster
from h5_trades join c using (grp, delay_s) group by all order by grp, delay_s""")

show(con, "Top-skill copies (t>3) by price band, delay 60s", """
select case when cost < 0.3 then 'a <0.3' when cost < 0.5 then 'b 0.3-0.5' when cost < 0.7 then 'c 0.5-0.7'
            else 'd >=0.7' end cost_band,
       count(*) n, round(avg((payoff>0)::int),3) winrate, round(avg(ret),4) mean_ret
from h5_trades where grp in ('a t>5','b 3<t<=5') and delay_s = 60 group by 1 order by 1""")
