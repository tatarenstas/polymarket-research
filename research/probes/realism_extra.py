"""Follow-up probe checks: one observation per market for calibration; fresh-wallet first bets."""
import duckdb

con = duckdb.connect()
con.execute("create view md as select *, coalesce(y_seq1, y_seq2) Y from 'data/probe/market_day.parquet' where y_seq1 is null or y_seq2 is null or y_seq1 = y_seq2")
con.execute("create view wm as select * from 'data/probe/wallet_market.parquet' where usdc >= 10")

print("### Calibration with ONE observation per market (first day in horizon), mid prices only")
con.sql("""
with h as (
  select *, case when days_to_close < 7 then 'b 1-7d' when days_to_close < 30 then 'c 7-30d' else 'd 30d+' end horizon
  from md where days_to_close >= 1 and vwap_p between 0.1 and 0.9 and usdc >= 100),
f as (select * from h qualify row_number() over (partition by condition_id, horizon order by day) = 1)
select horizon, neg_risk, count(*) markets, round(avg(vwap_p),3) mean_p, round(avg(Y),3) freq_Y,
       round(avg(Y)-avg(vwap_p),3) gap, round(1.96*stddev_samp(Y - vwap_p)/sqrt(count(*)),3) ci95
from f group by all order by all
""").show()

print("### Same, by top categories (30d+ and 7-30d pooled)")
con.sql("""
with h as (select * from md where days_to_close >= 7 and vwap_p between 0.1 and 0.9 and usdc >= 100),
f as (select * from h qualify row_number() over (partition by condition_id order by day) = 1)
select category_refined, count(*) markets, round(avg(Y)-avg(vwap_p),3) gap,
       round(1.96*stddev_samp(Y - vwap_p)/sqrt(count(*)),3) ci95
from f group by 1 having count(*) >= 400 order by markets desc
""").show()

print("### Fresh wallets: the wallet's FIRST market (taker), directional, mid price; by size of that first bet")
con.sql("""
with w as (select * from wm where role='taker'),
first as (select * from w qualify row_number() over (partition by wallet order by first_ts) = 1),
x as (select * from first where vwap_p between 0.15 and 0.85 and abs(net_dir) > 0.9)
select case when usdc >= 10000 then 'd >=10k' when usdc >= 1000 then 'c 1k-10k' when usdc >= 100 then 'b 100-1k' else 'a <100' end first_bet,
       count(*) wallets, round(avg(((net_dir > 0)::int = Y)::int),3) hit_rate,
       round(avg(case when net_dir > 0 then vwap_p else 1 - vwap_p end),3) implied_prob,
       round(sum(pnl)/sum(usdc),4) roi,
       round(1.96*sqrt(avg(((net_dir > 0)::int = Y)::int)*(1-avg(((net_dir > 0)::int = Y)::int))/count(*)),3) ci95_hit
from x group by 1 order by 1
""").show()

print("### Fresh wallets with a large first bet: within <7 days of close vs earlier")
con.sql("""
with w as (select * from wm where role='taker'),
first as (select * from w qualify row_number() over (partition by wallet order by first_ts) = 1),
x as (select *, (close_ts - first_ts)/86400 dtc from first where vwap_p between 0.15 and 0.85 and abs(net_dir) > 0.9 and usdc >= 1000)
select case when dtc < 1 then 'a <1d' when dtc < 7 then 'b 1-7d' else 'c 7d+' end to_close, count(*) wallets,
       round(avg(((net_dir > 0)::int = Y)::int),3) hit_rate,
       round(avg(case when net_dir > 0 then vwap_p else 1 - vwap_p end),3) implied_prob,
       round(sum(pnl)/sum(usdc),4) roi
from x group by 1 order by 1
""").show()
