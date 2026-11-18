"""H2, maker side: the resting order that SOLD the longshot to a taker who bought the
reference at 5-30c with >= 30 days to close. Realised fills only, so adverse selection is
included; queue position / fill probability is NOT modelled (needs live book data)."""
from pmresearch.backtest.engine import SPLIT_TS, connect, show

con = connect()
con.execute(f"""
create or replace table h2_maker as
select t.cid, t.ts, t.p, t.usdc, m.cluster, m.category, m.neg_risk,
       1 - t.p as cost, 1 - m.y as payoff, (1 - m.y) / (1 - t.p) - 1 as ret,
       (m.close_ts - t.ts) / 86400 as dtc, greatest(m.last_ts - t.ts, 0) / 86400 as hold_d,
       case when t.ts < {SPLIT_TS} then 'train' else 'test' end period
from tape t join markets m using (cid)
where t.d = 1 and t.p >= 0.05 and t.p < 0.30 and m.close_ts - t.ts >= 30 * 86400
""")
show(con, "Maker selling longshots (taker bought ref at 5-30c, >=30d to close)", """
with cl as (select period, cluster, sum(ret*usdc)/sum(usdc) r from h2_maker group by all),
c as (select period, count(*) clusters, avg(r) cl_mean, avg(r)/(stddev_samp(r)/sqrt(count(*))) t from cl group by 1)
select period, count(*) fills, round(sum(usdc)/1e6, 2) taker_usdc_m, round(sum(usdc/p*(1-p))/1e6, 2) maker_capital_m,
       round(avg((payoff>0)::int),3) winrate, round(sum(ret*usdc/p*(1-p))/sum(usdc/p*(1-p)),4) capital_weighted_ret,
       round(any_value(c.cl_mean),4) cluster_mean_ret, any_value(c.clusters) clusters, round(any_value(c.t),2) t_cluster,
       round(avg(hold_d),1) hold_d
from h2_maker join c using (period) group by period order by period desc""")
show(con, "Maker side by entry price band (capital-weighted)", """
select period, case when p < 0.1 then 'a 5-10c' when p < 0.2 then 'b 10-20c' else 'c 20-30c' end band,
       count(*) fills, round(sum(usdc/p*(1-p))/1e6,2) maker_capital_m, round(avg((payoff>0)::int),3) winrate,
       round(sum(ret*usdc/p*(1-p))/sum(usdc/p*(1-p)),4) cap_w_ret
from h2_maker group by all order by band, period desc""")
show(con, "TEST: maker capital deployable per month at these prices (market-wide upper bound)", """
select strftime(to_timestamp(ts), '%Y-%m') as ym, round(sum(usdc/p*(1-p))/1e6,2) maker_capital_m,
       round(sum(ret*usdc/p*(1-p))/sum(usdc/p*(1-p)),4) cap_w_ret, count(distinct cluster) clusters
from h2_maker where period='test' group by 1 order by 1""")
