import math

from pmresearch.lp_paper import RewardTracker, VirtualMaker, harmonic, maker_score, side_score, tier_weight


def test_tier_weights_and_side_score():
    assert tier_weight(4.9) == 1.0 and tier_weight(7) == 0.25 and tier_weight(15) == 0.10 and tier_weight(25) == 0
    mid = 100.0
    # 3 bps -> weight 1; 8 bps -> 0.25; 30 bps -> 0
    levels = [(99.97, 100.0), (99.92, 100.0), (99.70, 100.0)]
    s = side_score(levels, mid)
    assert math.isclose(s, 99.97 * 100 + 99.92 * 100 * 0.25)
    # cap at $100k per tier
    assert side_score([(99.99, 5000.0)], mid) == 100_000.0
    assert side_score([(99.99, 5000.0)], mid, cap=False) > 100_000.0


def test_harmonic_and_maker_score():
    assert harmonic(10, 0) == 0 and math.isclose(harmonic(10, 10), 10)
    assert maker_score(0.005) == 0 and math.isclose(maker_score(0.25), 1.0) and maker_score(0.5) == 1.0


def test_quote_fill_and_accounting_unhedged():
    m = VirtualMaker("t", size_usd=1000, offset_bps=10, requote_s=0)
    m.requote(0, 100.0)
    assert math.isclose(m.bid, 99.9) and math.isclose(m.ask, 100.1)
    # taker sells at 99.9 -> touches our bid -> we buy
    f = m.on_trade(1, "short", 99.9, 3.0, 100.0)
    assert f and f.side == 1 and math.isclose(m.pos, 3.0)
    assert math.isclose(m.fees, 99.9 * 3 * 0.000125)
    # mark at 100: pnl = 3*(100-99.9) - fee
    assert math.isclose(m.pnl(100.0), 0.3 - m.fees)
    # a taker buy below our ask does not fill us
    assert m.on_trade(2, "long", 100.05, 1.0, 100.0) is None


def test_through_only_and_inventory_limit_and_hedge():
    c = VirtualMaker("c", size_usd=1000, offset_bps=10, requote_s=0, through_only=True)
    c.requote(0, 100.0)
    assert c.on_trade(1, "short", 99.9, 1.0, 100.0) is None  # touch is not enough
    assert c.on_trade(2, "short", 99.8, 1.0, 100.0) is not None
    lim = VirtualMaker("l", size_usd=1000, offset_bps=10, requote_s=0, max_inv_usd=50)
    lim.requote(0, 100.0)
    lim.on_trade(1, "short", 99.9, 1.0, 100.0)  # long $100 > limit
    lim.requote(2, 100.0)
    assert lim.bid is None and lim.ask is not None
    h = VirtualMaker("h", size_usd=1000, offset_bps=10, requote_s=0, hedged=True, hedge_bps=5)
    h.requote(0, 100.0)
    h.on_trade(1, "short", 99.9, 2.0, 100.0)
    assert h.pos == 0
    expected = 2 * (100 - 99.9) - 2 * 99.9 * 0.000125 - 2 * 100 * 5e-4
    assert math.isclose(h.pnl(100.0), expected)


def test_reward_tracker():
    m = VirtualMaker("t", size_usd=1000, offset_bps=3, requote_s=0)
    m.requote(0, 100.0)
    r = RewardTracker()
    book_b, book_a = [(99.98, 10.0)], [(100.02, 10.0)]  # $1k-ish per side competitor
    for _ in range(10):
        r.sample(m, book_b, book_a, 100.0)
    e = r.estimates(pool_per_day=800, maker_share=0.05)
    assert e["uptime"] == 1.0 and 350 < e["reward_linear_per_day"] < 450
    assert e["maker_score"] > 0 and e["reward_formula_per_day"] > 0
    assert r.estimates(800, maker_share=0.0)["reward_formula_per_day"] == 0


def test_delayed_hedge_maker():
    from pmresearch.lp_paper import DelayedHedgeMaker

    m = DelayedHedgeMaker("d", size_usd=1000, offset_bps=10, requote_s=0, max_inv_usd=1000,
                          hedge_delay_s=1.0, hedge_fee=0.0005, skew_bps=0)
    m.requote(0, 100.0)
    m.on_trade(0, "short", 99.9, 2.0, 100.0)  # we buy 2 @ 99.9 on Polymarket
    assert m.pos == 2.0 and m.due == [1000]
    m.on_hedge_quote(500, 99.0, 99.2)  # not due yet
    assert m.hpos == 0
    m.on_hedge_quote(1000, 99.0, 99.2)  # due: sell 2 at hedge bid 99.0
    assert m.hpos == -2.0 and m.hedge_trades == 1
    assert math.isclose(m.hedge_fees, 2 * 99.0 * 0.0005)
    # both legs marked: poly mid 99.1, hedge mid 99.1 -> net = 2*(99.0-99.9) - fees
    expected = 2 * (99.0 - 99.9) - m.fees - m.hedge_fees
    assert math.isclose(m.pnl2(99.1, 99.1), expected)


def test_skew_and_threshold():
    from pmresearch.lp_paper import DelayedHedgeMaker

    m = DelayedHedgeMaker("s", size_usd=1000, offset_bps=10, requote_s=0, max_inv_usd=1000,
                          skew_bps=10, hedge_threshold_usd=500)
    m.pos = 5.0  # +$500 at mid 100 -> frac 0.5 -> center 99.95
    m.requote(0, 100.0)
    assert math.isclose(m.bid, 99.95 * 0.999) and math.isclose(m.ask, 99.95 * 1.001)
    m.due = [0]
    m.on_hedge_quote(0, 99.9, 100.1)  # net $500 is not above threshold -> no hedge
    assert m.hpos == 0
    m.apply_funding("poly", 0.001, 100.0)  # long pays
    assert math.isclose(m.funding, -0.5)
