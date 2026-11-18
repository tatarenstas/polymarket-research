"""Summaries for the realism probe. Reads data/probe/*.parquet produced by realism_probe.py."""

from __future__ import annotations

import duckdb

con = duckdb.connect()
con.execute("create view md as select * from 'data/probe/market_day.parquet'")
con.execute("create view wm as select * from 'data/probe/wallet_market.parquet'")


def show(title: str, sql: str) -> None:
    print(f"\n### {title}")
    con.sql(sql).show(max_width=250, max_rows=60)


show("Normalization checks", """
select count(*) market_days, count(distinct condition_id) markets,
       sum(n) trades, sum(d_mismatch) d_mismatch, sum(p_mismatch) p_mismatch,
       count(*) filter (where y_seq1 is not null and y_seq2 is not null and y_seq1 <> y_seq2) y_inconsistent
from md""")

con.execute("""
create view cal as
select *, coalesce(y_seq1, y_seq2) as Y,
       least(floor(vwap_p * 10), 9) / 10 as bucket,
       case when days_to_close < 1 then 'a <1d' when days_to_close < 7 then 'b 1-7d'
            when days_to_close < 30 then 'c 7-30d' else 'd 30d+' end as horizon
from md where (y_seq1 is null or y_seq2 is null or y_seq1 = y_seq2)
""")

show("Calibration, all categories (market-day units)", """
select bucket, count(*) n, round(avg(vwap_p), 3) mean_p, round(avg(Y), 3) freq_Y,
       round(avg(Y) - avg(vwap_p), 3) gap,
       round(1.96 * sqrt(avg(Y) * (1 - avg(Y)) / count(*)), 3) ci95_naive
from cal group by bucket order by bucket""")

show("Calibration gap (freq_Y - mean_p) by category x bucket, n>=300", """
pivot (select category_refined cat, bucket, round(avg(Y) - avg(vwap_p), 3) gap
       from cal group by all having count(*) >= 300)
on bucket using any_value(gap) order by cat""")

show("Calibration gap by horizon x bucket", """
pivot (select horizon, bucket, round(avg(Y) - avg(vwap_p), 3) gap from cal group by all having count(*) >= 300)
on bucket using any_value(gap) order by horizon""")

show("Brier score by horizon (lower = better), market-day units", """
select horizon, count(*) n, round(avg((vwap_p - Y)^2), 4) brier from cal group by 1 order by 1""")

# ---- wallets -------------------------------------------------------------------
SPLIT = "epoch(timestamp '2025-07-01')"
con.execute(f"""
create view wp as
select *, case when first_ts < {SPLIT} then 'disc' else 'test' end as period,
       pnl / usdc as roi
from wm where usdc >= 10
""")

show("Wallet universe", """
select role, period, count(distinct wallet) wallets, count(*) wallet_markets,
       round(sum(usdc)/1e9, 2) usdc_bn, round(sum(pnl)/1e6, 1) pnl_musd
from wp group by all order by all""")

show("Volume concentration (taker, all periods): share of notional by top wallets", """
with w as (select wallet, sum(usdc) u from wp where role='taker' group by 1),
r as (select u, row_number() over (order by u desc) rk, count(*) over () n, sum(u) over () tot from w)
select round(sum(u) filter (where rk <= n*0.001)/any_value(tot), 3) top_0_1pct,
       round(sum(u) filter (where rk <= n*0.01)/any_value(tot), 3) top_1pct,
       round(sum(u) filter (where rk <= n*0.1)/any_value(tot), 3) top_10pct
from r""")

# Per-wallet t-stat of market-level ROI in each period. Market = unit of independence.
con.execute("""
create view ws as
select wallet, role, period, count(*) k, sum(usdc) usdc, sum(pnl) pnl, sum(pnl)/sum(usdc) roi_w,
       avg(roi) mean_roi, stddev_samp(roi) sd_roi,
       avg(roi) / nullif(stddev_samp(roi) / sqrt(count(*)), 0) as t,
       avg(vwap_p) avg_entry_p
from wp group by all
""")

show("How many 'skilled' wallets in discovery vs chance (k >= 20 markets)", """
select role, count(*) wallets,
       count(*) filter (where t > 3) t_gt_3,
       round(count(*) * 0.00135, 1) expected_if_null_normal,
       count(*) filter (where t > 5) t_gt_5
from ws where period = 'disc' and k >= 20 group by role order by role""")

show("Out-of-sample: discovery-selected wallets evaluated in H2 2025", """
with d as (select wallet, role, t, avg_entry_p from ws where period='disc' and k >= 20),
     t as (select wallet, role, k, usdc, pnl, roi_w from ws where period='test')
select d.role,
       case when d.t > 3 then 'disc t>3' when d.t > 0 then 'disc 0<t<=3' else 'disc t<=0' end grp,
       count(t.wallet) wallets_active_in_test,
       round(sum(t.pnl) / sum(t.usdc), 4) pooled_test_roi,
       round(avg((t.roi_w > 0)::int), 3) share_positive,
       round(median(d.avg_entry_p), 2) med_entry_p
from d join t using (wallet, role) group by all order by 1, 2""")

show("Same, but disc t>3 wallets split by typical entry price (tail = sniping near-certain outcomes)", """
with d as (select wallet, role, t, avg_entry_p from ws where period='disc' and k >= 20 and t > 3),
     t as (select wallet, role, usdc, pnl, roi_w from ws where period='test')
select d.role, case when d.avg_entry_p between 0.15 and 0.85 then 'mid 0.15-0.85' else 'tails' end entry,
       count(*) wallets, round(sum(t.pnl)/sum(t.usdc), 4) pooled_test_roi,
       round(avg((t.roi_w > 0)::int), 3) share_positive, round(sum(t.pnl)/1e6, 2) test_pnl_musd
from d join t using (wallet, role) group by all order by 1, 2""")

show("Large, directional, mid-price, taker bets before close: hit rate by size decile of wallet's own history", """
with x as (
  select *, usdc / median(usdc) over (partition by wallet) as rel_size
  from wp where role = 'taker' and vwap_p between 0.15 and 0.85 and abs(net_dir) > 0.9
)
select case when rel_size >= 10 then '>=10x own median' when rel_size >= 3 then '3-10x'
            else '<3x' end size_vs_own, count(*) bets,
       round(avg(((net_dir > 0)::int = Y)::int), 3) hit_rate,
       round(avg(case when net_dir > 0 then vwap_p else 1 - vwap_p end), 3) implied_prob,
       round(sum(pnl)/sum(usdc), 4) roi
from x group by 1 order by 1""")
