"""H2 as one pre-registered rule (chosen from TRAIN pattern): buy the opposite side when the
reference trades at 5-30c with >= 30 days to scheduled close. Daily snapshots, 60s latency.
Evaluated on TEST with capacity, stability and concentration diagnostics."""
from pmresearch.backtest.engine import SPLIT_TS, connect, show

con = connect()
con.execute("""
create or replace table h2_rule as
select t.*, m.category, m.neg_risk, case when entry_ts < 1751328000 then 'train' else 'test' end period
from h13_trades t join markets m using (cid)
where side = -1 and p_lo >= 0.05 and p_lo < 0.30 and h_lo >= 30
""")
show(con, "H2 rule: overall", """
with cl as (select period, res_cluster, avg(ret) r from h2_rule group by all),
c as (select period, count(*) clusters, avg(r)/(stddev_samp(r)/sqrt(count(*))) t from cl group by 1)
select period, count(*) n, round(avg((payoff>0)::int),3) winrate, round(avg(ret),4) mean_ret,
       round(avg(cost),3) avg_cost, round(avg(hold_days),1) hold_d,
       round(avg(ret)/avg(hold_days)*365,3) ret_per_capital_yr, any_value(c.clusters) clusters, round(any_value(c.t),2) t_cluster,
       round(median(entry_usdc),0) med_fill_usdc, round(quantile_cont(entry_usdc, 0.25),0) p25_fill_usdc
from h2_rule join c using (period) group by period order by period desc""")
show(con, "H2 rule TEST by entry month", """
select strftime(to_timestamp(entry_ts), '%Y-%m') as ym, count(*) n, round(avg((payoff>0)::int),3) winrate,
       round(avg(ret),4) mean_ret, count(distinct res_cluster) clusters
from h2_rule where period='test' group by 1 order by 1""")
show(con, "H2 rule TRAIN by entry quarter", """
select strftime(to_timestamp(entry_ts), '%Y') || '-Q' || quarter(to_timestamp(entry_ts)) q, count(*) n,
       round(avg((payoff>0)::int),3) winrate, round(avg(ret),4) mean_ret
from h2_rule where period='train' group by 1 order by 1""")
show(con, "H2 rule by category and market type (both periods)", """
select period, category, neg_risk, count(*) n, round(avg((payoff>0)::int),3) winrate, round(avg(ret),4) mean_ret,
       count(distinct res_cluster) clusters
from h2_rule group by all having count(distinct res_cluster) >= 40 order by category, neg_risk, period desc""", rows=60)
show(con, "Concentration: share of TEST PnL from top-10 event clusters and worst clusters", """
with c as (select res_cluster, sum(ret) pnl, count(*) n from h2_rule where period='test' group by 1)
select round(sum(pnl) filter (where pnl > 0), 1) gross_win, round(sum(pnl) filter (where pnl < 0), 1) gross_loss,
       round(sum(pnl), 1) net, (select round(sum(pnl),1) from (select pnl from c order by pnl asc limit 10)) worst10_clusters,
       (select round(sum(pnl),1) from (select pnl from c order by pnl desc limit 10)) best10_clusters
from c""")
show(con, "Worst TEST clusters (one event can hold many daily entries)", """
select r.res_cluster, any_value(m.slug) example_slug, count(*) entries, round(sum(ret),1) pnl
from h2_rule r join markets m using (cid) where period='test' group by 1 order by pnl limit 8""")

show(con, "H2 with ONE entry per market (first qualifying day) - removes overweighting of long-lived markets", """
with f as (select * from h2_rule qualify row_number() over (partition by cid order by entry_ts) = 1),
cl as (select period, res_cluster, avg(ret) r from f group by all),
c as (select period, count(*) clusters, avg(r) cl_mean, avg(r)/(stddev_samp(r)/sqrt(count(*))) t from cl group by 1)
select period, count(*) markets, round(avg((payoff>0)::int),3) winrate, round(avg(ret),4) mean_ret,
       round(any_value(c.cl_mean),4) cluster_mean_ret, any_value(c.clusters) clusters, round(any_value(c.t),2) t_cluster,
       round(avg(hold_days),1) hold_d
from f join c using (period) group by period order by period desc""")

show(con, "Same, split by entry price band", """
with f as (select * from h2_rule qualify row_number() over (partition by cid order by entry_ts) = 1)
select period, p_lo, count(*) markets, round(avg((payoff>0)::int),3) winrate, round(avg(ret),4) mean_ret
from f group by all order by p_lo, period desc""")
