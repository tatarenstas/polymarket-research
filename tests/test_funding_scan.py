from pmresearch.funding_scan import MAKER_FEE, TAKER_FEE, book_metrics, fees_for, is_signal, parse

NOW = 1_794_612_000_000
T = NOW + 90_000


def tick(iid, sym, rate, mark="100", oi="1000"):
    return {"instrument_id": iid, "symbol": sym, "funding_rate": rate, "next_funding": T,
            "mark_price": mark, "open_interest": oi}


def test_fees_override_active_and_expired():
    fo = {"start_time": NOW - 1, "end_time": None,
          "tiers": [{"maker_fee_rate": "0.0000625", "taker_fee_rate": "0.0002"}]}
    assert fees_for({"fee_override": fo}, NOW) == (0.0000625, 0.0002)
    assert fees_for({"fee_override": {**fo, "end_time": NOW - 1}}, NOW) == (MAKER_FEE, TAKER_FEE)
    assert fees_for({}, NOW) == (MAKER_FEE, TAKER_FEE)


def test_parse_sorts_sides_and_net():
    rows = parse([tick(1, "A", "0.0001"), tick(2, "B", "-0.0008"), tick(3, "C", "0.0009")],
                 {3: {"close_only": True}}, NOW)
    assert [r.symbol for r in rows] == ["B", "A"]  # C dropped, sorted by |rate|
    b = rows[0]
    assert b.side == "LONG" and rows[1].side == "SHORT"
    assert abs(b.net_maker_bps - (8 - 2.5)) < 1e-9
    assert abs(b.net_taker_bps - (8 - 8)) < 1e-9
    assert b.oi_usd == 100_000
    assert b.ttl_s(NOW) == 90


def test_signal_window_and_threshold():
    r = parse([tick(1, "A", "0.0006")], {}, NOW)[0]
    assert is_signal(r, NOW, 0.0005, 120)
    assert not is_signal(r, NOW, 0.0005, 60)  # too early
    assert not is_signal(r, NOW, 0.001, 120)  # below threshold
    assert not is_signal(r, T + 1, 0.0005, 120)  # already settled


def test_book_metrics():
    book = {"bids": [["99.95", "10"], ["99.0", "100"]], "asks": [["100.05", "20"], ["101", "5"]]}
    m = book_metrics(book, band_bps=10)
    assert abs(m["spread_bps"] - 10) < 1e-6
    assert abs(m["bid_depth_usd"] - 999.5) < 1e-6
    assert abs(m["ask_depth_usd"] - 2001) < 1e-6
    assert book_metrics({"bids": [], "asks": []}) == {}
