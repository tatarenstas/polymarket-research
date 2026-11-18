"""How much does a passive maker earn or lose BEFORE rewards? V2 tape, 2026-04 -> 2026-10.

Every taker fill in the tape has a maker on the other side. With d = +1 when the taker buys
the event's YES axis at p, the maker is short YES at p; when d = -1 the maker is long YES.
Per share:
  to resolution: maker_pnl = -d * (y - p);       capital = p if maker long YES, else 1 - p
  markout(h):    maker_mo  = -d * (p_next - p),  p_next = first trade >= t + h in the market
Returns are per $ of maker capital, capital-weighted, plus an event-clustered mean and t
(cluster = NegRisk group or market). Resolved, label-consistent markets only.

The tape universe is markets listed >= 29 days before their scheduled close (see
build_tape_v2.py), so short-lived news markets are under-represented.

Usage: uv run python research/pm_mm/maker_edge_v2.py
"""

from __future__ import annotations

from pmresearch.backtest.engine import connect, prepare

BANDS = "case when p < .05 then '00-05' when p < .10 then '05-10' when p < .20 then '10-20' " \
        "when p < .40 then '20-40' when p < .60 then '40-60' when p < .80 then '60-80' " \
        "when p < .90 then '80-90' when p < .95 then '90-95' else '95-100' end"


def table(con, by: str, title: str) -> None:
    # cluster-robust t of the capital-weighted mean: r = sum(pnl)/sum(cap),
    # SE = sqrt(sum_c (pnl_c - r cap_c)^2) / sum(cap); share of capital in the top 10 clusters
    rows = con.execute(f"""
    with f as (select {by} as g, cluster, cap, pnl, mo1h, mo1d from fills),
    c as (select g, cluster, sum(cap) cap, sum(pnl) pnl from f group by 1, 2),
    tot as (select g, count(*) n, sum(cap) cap, sum(pnl) pnl, sum(mo1h) m1h, sum(mo1d) m1d from f group by 1),
    se as (select c.g, sqrt(sum(power(c.pnl - tot.pnl / tot.cap * c.cap, 2))) / any_value(tot.cap) se,
                  count(*) ncl from c join tot using (g) group by 1),
    top as (select g, sum(abs_pnl) top10 from (select g, abs(pnl) abs_pnl,
              row_number() over (partition by g order by abs(pnl) desc) rk from c) where rk <= 10 group by 1),
    absall as (select g, sum(abs(pnl)) a from c group by 1)
    select tot.g, n, tot.cap/1e6, tot.pnl/tot.cap, m1h/tot.cap, m1d/tot.cap, (tot.pnl/tot.cap)/se.se, ncl,
           top10 / a
    from tot join se using (g) join top using (g) join absall using (g) order by 1
    """).fetchall()
    print(f"\n{title}")
    print(f"{'group':<10}{'fills':>11}{'cap $M':>9}{'to res':>9}{'mo 1h':>8}{'mo 1d':>8}{'t(cl)':>7}{'events':>8}{'top10':>7}")
    for g, n, cap, ret, m1h, m1d, t, ncl, top in rows:
        print(f"{str(g):<10}{n:>11,}{cap:>9.1f}{ret:>+9.2%}{m1h:>+8.2%}{m1d:>+8.2%}{t:>7.1f}{ncl:>8,}{top:>7.0%}")


def main() -> None:
    con = connect("data/tape/v2/*.parquet", "data/bt_v2.duckdb")
    prepare(con)
    con.execute("""
    create or replace temp table fills as
    with t as (
      select t.cid, t.ts, t.p, t.d, t.usdc / t.price as sh, m.y, m.cluster, m.category,
             (m.close_ts - t.ts) / 86400.0 as days_left
      from tape t join markets m using (cid)
      where m.y is not null and t.p > 0 and t.p < 1
    ),
    h as (
      select t.*, n1.p as p1h from t asof left join tape n1 on n1.cid = t.cid and n1.ts >= t.ts + 3600
    ),
    dd as (
      select h.*, n2.p as p1d from h asof left join tape n2 on n2.cid = h.cid and n2.ts >= h.ts + 86400
    )
    select *, sh * (case when d = 1 then 1 - p else p end) as cap,
           sh * (-d) * (y - p) as pnl,
           sh * (-d) * (coalesce(p1h, y) - p) as mo1h,
           sh * (-d) * (coalesce(p1d, y) - p) as mo1d
    from dd
    """)
    n, cap, pnl = con.execute("select count(*), sum(cap), sum(pnl) from fills").fetchone()
    print(f"maker side of {n:,} fills, capital ${cap/1e6:,.0f}M, to resolution {pnl/cap:+.2%} per $")
    table(con, BANDS.replace("p <", "p <"), "By fill price (YES axis)")
    table(con, "case when days_left < 1 then 'a <1d' when days_left < 7 then 'b 1-7d' when days_left < 30 then "
               "'c 7-30d' else 'd >30d' end", "By time to scheduled close")
    table(con, "case when category in ('Sports','Soccer','NBA','FIFA World Cup','2026 FIFA World Cup','Games','Esports',"
               "'Tennis','MLB','NHL','NFL','WNBA') then 'sports' when category in ('Politics','Trump','Elections',"
               "'primary elections','Trump Presidency') then 'politics' when category in ('Iran','Geopolitics',"
               "'Middle East','Israel','Ukraine Peace Deal','Iran Regime','Strait of Hormuz','Iran Ceasefire') then "
               "'geopol' when category in ('Bitcoin','Ethereum','Crypto','Solana','XRP') then 'crypto' when category "
               "in ('Economy','Economic Policy','fomc','Fed','Finance','CPI') then 'macro' else 'other' end",
          "By category group")


if __name__ == "__main__":
    main()
