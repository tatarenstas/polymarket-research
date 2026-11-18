import pyarrow as pa
import pyarrow.parquet as pq

from pmresearch.backtest.engine import connect, entries_sql, prepare, snapshots_sql, state_sql

DAY = 86400


def _tape(tmp_path):
    # One market, reference outcome loses (y=0). Trades: (ts, p, d)
    rows = [(1000, 0.40, 1), (2000, 0.42, -1), (5000, 0.45, 1), (6000, 0.38, -1), (DAY + 10, 0.30, -1)]
    n = len(rows)
    t = pa.table({
        "cid": ["m1"] * n, "ts": [r[0] for r in rows], "seq": pa.array([1] * n, pa.int8()),
        "p": [r[1] for r in rows], "d": pa.array([r[2] for r in rows], pa.int8()),
        "usdc": [100.0] * n, "price": [r[1] for r in rows], "fee": [0.0, 0.0, 1.0, 0.0, 0.0],
        "wallet": pa.array([1] * n, pa.uint64()), "y": pa.array([0] * n, pa.int8()),
        "close_ts": [10 * DAY] * n, "neg_risk": [False] * n, "nrm": pa.array([None] * n, pa.string()),
        "category": ["Politics"] * n, "slug": ["m1"] * n,
    })
    pq.write_table(t, tmp_path / "x.parquet")
    con = connect(str(tmp_path / "*.parquet"), db=":memory:")
    prepare(con)
    return con


def test_entries_use_next_same_side_fill(tmp_path):
    con = _tape(tmp_path)
    sig = "select 'm1' as cid, 1500 as t, s.side from (select unnest([1, -1]) side) s"
    rows = dict(
        (r[0], r[1:])
        for r in con.execute(f"select side, entry_ts, cost, payoff, ret from ({entries_sql(sig)})").fetchall()
    )
    # Buy reference -> next taker BUY after 1500 is ts=5000 at 0.45 with 1% fee; y=0 -> lose all.
    assert rows[1][0] == 5000 and abs(rows[1][1] - 0.45) < 1e-12 and rows[1][2] == 0
    assert abs(rows[1][3] - (-1 - 0.01)) < 1e-9
    # Buy opposite -> next taker SELL after 1500 is ts=2000 at p=0.42 -> cost 0.58, payoff 1.
    assert rows[-1][0] == 2000 and abs(rows[-1][1] - 0.58) < 1e-12
    assert abs(rows[-1][3] - (1 / 0.58 - 1)) < 1e-9


def test_latency_and_window(tmp_path):
    con = _tape(tmp_path)
    sig = "select 'm1' as cid, 1500 as t, -1 as side"
    got = con.execute(f"select entry_ts from ({entries_sql(sig, latency_s=1000)})").fetchall()
    assert got == [(6000,)]
    got = con.execute(f"select entry_ts from ({entries_sql(sig, latency_s=1000, window_s=100)})").fetchall()
    assert got == []


def test_price_guard_drops_off_market_fills(tmp_path):
    con = _tape(tmp_path)
    # Reference 0.30; next taker sell after 1500 is 0.42 (12c away) -> dropped at 3c, kept at 15c.
    sig = "select 'm1' as cid, 1500 as t, -1 as side, 0.30 as ref"
    assert con.execute(f"select count(*) from ({entries_sql(sig, ref_col='ref', max_dev=0.03)})").fetchall() == [(0,)]
    assert con.execute(f"select count(*) from ({entries_sql(sig, ref_col='ref', max_dev=0.15)})").fetchall() == [(1,)]


def test_state_is_point_in_time(tmp_path):
    con = _tape(tmp_path)
    st = con.execute(f"select t, p_last from ({state_sql(snapshots_sql(1))}) order by t").fetchall()
    # Snapshot at 3600 must see the trade at 2000 (0.42), not the later one at 5000.
    assert st[0] == (3600, 0.42)
    assert all(isinstance(x, tuple) for x in st)
