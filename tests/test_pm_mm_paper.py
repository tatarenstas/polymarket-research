from pmresearch.pm_mm_paper import (
    ASK,
    BID,
    Book,
    PaperMaker,
    Params,
    _ceil_tick,
    _floor_tick,
    to_yes_trade,
)

P = Params(v_cents=4.5, min_size=20, rate_per_day=144, tick=0.01)


def book(bids, asks):
    b = Book()
    b.snapshot([{"price": str(p), "size": str(s)} for p, s in bids], [{"price": str(p), "size": str(s)} for p, s in asks])
    return b


def placed(m, bk, now=0.0):
    m.on_book(bk, P, now)
    m.on_time(bk, now + m.latency_s)
    return m


def test_no_token_trade_maps_to_yes_space():
    assert to_yes_trade(True, "BUY", 0.56) == (1, 0.56)
    assert to_yes_trade(False, "BUY", 0.45) == (-1, 0.55)  # NO buy = YES sell into bids


def test_tick_rounding():
    assert _floor_tick(0.49, 0.01) == 0.49 and _floor_tick(0.4899, 0.01) == 0.48
    assert _ceil_tick(0.51, 0.01) == 0.51 and _ceil_tick(0.5101, 0.01) == 0.52


def test_join_quote_after_latency_and_queue():
    bk = book([(0.49, 100), (0.48, 50)], [(0.51, 80)])
    m = PaperMaker("j", quote_shares=50, latency_s=1.0)
    m.on_book(bk, P, 0.0)
    m.on_time(bk, 0.5)
    assert m.orders[BID] is None  # not yet live
    m.on_time(bk, 1.0)
    assert m.orders[BID].price == 0.49 and m.orders[BID].queue == 100
    assert m.orders[ASK].price == 0.51 and m.orders[ASK].queue == 80


def test_queue_fill_and_trade_through():
    bk = book([(0.49, 100)], [(0.51, 80)])
    m = placed(PaperMaker("j", quote_shares=50), bk)
    assert m.on_trade(-1, 0.49, 60) == []  # consumes queue 100 -> 40
    assert m.orders[BID].queue == 40
    f = m.on_trade(-1, 0.49, 70)  # 40 ahead, 30 to us
    assert f == [(BID, 0.49, 30)] and m.yes == 30
    f = m.on_trade(-1, 0.48, 5)  # trade-through: the 5 that printed lower would have hit us
    assert f == [(BID, 0.49, 5)] and m.yes == 35
    f = m.on_trade(-1, 0.47, 100)  # capped by what is left
    assert f == [(BID, 0.49, 15)] and m.yes == 50 and m.orders[BID] is None
    assert abs(m.cash + 0.49 * 50) < 1e-9 and m.fills == 3


def test_touch_model_and_merge():
    bk = book([(0.49, 100)], [(0.51, 80)])
    m = placed(PaperMaker("t", quote_shares=50, fill_model="touch"), bk)
    m.on_trade(-1, 0.49, 10)  # buy 10 YES @0.49
    m.on_trade(1, 0.51, 10)  # sell 10 YES @0.51 = buy 10 NO @0.49 -> merge 10 pairs
    assert m.yes == 0 and m.no == 0
    assert abs(m.cash - 10 * 0.02) < 1e-9  # captured the 2c spread


def test_cancel_caps_queue_after_delay():
    bk = book([(0.49, 100)], [(0.51, 80)])
    m = placed(PaperMaker("j", quote_shares=50), bk)
    m.on_level(BID, 0.49, 30, now=5.0)
    m.on_time(bk, 5.5)
    assert m.orders[BID].queue == 100
    m.on_time(bk, 6.0)
    assert m.orders[BID].queue == 30


def test_inventory_limit_stops_bid():
    bk = book([(0.49, 100)], [(0.51, 80)])
    m = placed(PaperMaker("j", quote_shares=50, fill_model="touch"), bk)
    m.on_trade(-1, 0.48, 100)  # trade-through: +50 YES, at the limit
    assert m.target(bk, P)[BID] is None and m.target(bk, P)[ASK] == 0.51


def test_back_quotes_and_outside_v():
    bk = book([(0.49, 100)], [(0.51, 80)])
    m = PaperMaker("b", quote_shares=50, back_cents=1)
    assert m.target(bk, P) == {BID: 0.48, ASK: 0.52}
    wide = book([(0.40, 100)], [(0.60, 80)])  # 10c from mid > v 4.5c: no reward, no quote
    assert m.target(wide, P) == {BID: None, ASK: None}


def test_no_quote_on_wrong_side_of_mid():
    # 5-share ask at 0.53 is below min size; the adjusted mid uses the 0.80 ask -> mid 0.61
    bk = book([(0.42, 100)], [(0.53, 5), (0.80, 100)])
    m = PaperMaker("j", quote_shares=50)
    assert m.target(bk, P)[ASK] is None


def test_reward_share_against_book():
    bk = book([(0.49, 100)], [(0.51, 100)])
    m = placed(PaperMaker("j", quote_shares=100), bk)
    share, add = m.sample_reward(bk, P)
    assert abs(share - 0.5) < 1e-9 and abs(add - 144 / 1440 * 0.5) < 1e-12
