"""H4: do sharp 60-minute price moves revert (fade) or continue (momentum)?

Shock = |p(end of minute) - p(60 min earlier)| >= theta, prior price in [0.10, 0.90],
>= 1 day to scheduled close. At most one shock per market per 6 hours.
Entry 60s after the shock bar at the next executable fill. Exits: after 1h / 6h / 24h
at the next fill on the other side of the book, or hold to resolution.
"""

from pmresearch.backtest.engine import SPLIT_TS, connect, entries_sql, prepare, show

con = connect()
prepare(con)

con.execute("""
create or replace table bars as
select cid, ts // 60 as minute, arg_max(p, ts) as p, sum(usdc * d) as flow, sum(usdc) as vol
from tape group by all
""")

con.execute("""
create or replace table h4_signals as
with lag as (
  select b.cid, b.minute, b.p, b.flow, b.vol, a.p as p_prev
  from bars b asof join bars a on b.cid = a.cid and a.minute <= b.minute - 60
),
sh as (
  select l.*, l.p - l.p_prev as delta, (m.close_ts - (l.minute + 1) * 60) / 86400 as days_to_close
  from lag l join markets m using (cid)
  where l.p_prev between 0.10 and 0.90 and abs(l.p - l.p_prev) >= 0.05
    and m.close_ts - (l.minute + 1) * 60 >= 86400
)
select * from sh
qualify row_number() over (partition by cid, minute // 360 order by minute) = 1
""")
print(con.execute("select count(*), count(distinct cid) from h4_signals").fetchall())

signals = """
select cid, (minute + 1) * 60 as t, p as p_ref, delta, abs(delta) as size, days_to_close, s.mode,
       case when s.mode = 'fade' then -sign(delta) else sign(delta) end::int as side
from h4_signals, (select unnest(['fade', 'momentum']) as mode) s
"""
con.execute(f"create or replace table h4_entries as {entries_sql(signals, latency_s=60, window_s=3600, ref_col='p_ref', max_dev=0.03)}")

# Early exits: we sell what we hold into the opposite side of the book.
exits = []
for h in (3600, 6 * 3600, 86400):
    exits.append(f"""
    select e.*, {h} as exit_after,
      case when e.side = 1 then x.p else 1 - x.p end as exit_value, x.fee / x.usdc as exit_fee
    from (select * from h4_entries where side = 1) e asof join sells x on e.cid = x.cid and x.ts >= e.entry_ts + {h}
    union all by name
    select e.*, {h} as exit_after,
      case when e.side = 1 then x.p else 1 - x.p end as exit_value, x.fee / x.usdc as exit_fee
    from (select * from h4_entries where side = -1) e asof join buys x on e.cid = x.cid and x.ts >= e.entry_ts + {h}
    """)
con.execute(f"""
create or replace table h4_trades as
select *, exit_value / cost - 1 - coalesce(fee_rate, 0) - coalesce(exit_fee, 0) as ret_exit
from ({' union all by name '.join(exits)})
""")

show(con, "Shock follow-through: fade vs momentum by shock size and exit horizon", f"""
with tr as (select *, case when entry_ts < {SPLIT_TS} then 'train' else 'test' end period,
                   case when size >= 0.20 then 'c >=20c' when size >= 0.10 then 'b 10-20c' else 'a 5-10c' end sz
            from h4_trades),
cl as (select period, mode, sz, exit_after, res_cluster, avg(ret_exit) r from tr group by all),
c as (select period, mode, sz, exit_after, count(*) clusters, avg(r)/nullif(stddev_samp(r)/sqrt(count(*)),0) t
      from cl group by all)
select period, mode, sz, exit_after / 3600 as exit_h, count(*) n, round(avg((ret_exit > 0)::int), 3) winrate,
       round(avg(ret_exit), 4) mean_ret, round(median(ret_exit), 4) med_ret, any_value(round(c.t, 1)) t_cluster
from tr join c using (period, mode, sz, exit_after)
group by all order by mode, sz, exit_h, period desc""")

show(con, "Hold to resolution instead", f"""
with tr as (select *, case when entry_ts < {SPLIT_TS} then 'train' else 'test' end period,
                   case when size >= 0.20 then 'c >=20c' when size >= 0.10 then 'b 10-20c' else 'a 5-10c' end sz
            from h4_entries)
select period, mode, sz, count(*) n, round(avg((payoff > 0)::int), 3) winrate, round(avg(ret), 4) mean_ret
from tr group by all order by mode, sz, period desc""")
