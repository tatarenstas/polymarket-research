from pmresearch.pm_rewards import adjusted_mid, competitor_qmin, parse_book, qmin, reward_estimate, score, side_q


def test_score_matches_docs_worked_example():
    # docs: mid 0.50, v = 3c; 100 bid @0.49, 200 bid @0.48, 100 ask(m') @0.51
    q_one = score(3, 1) * 100 + score(3, 2) * 200 + score(3, 1) * 100
    assert abs(q_one - ((2 / 3) ** 2 * 100 + (1 / 3) ** 2 * 200 + (2 / 3) ** 2 * 100)) < 1e-12
    assert score(3, 3) == 0 and score(3, 4) == 0 and score(3, 0) == 1


def test_qmin_single_sided_rule():
    assert qmin(90, 0, 0.5) == 30  # single-sided scores at 1/c inside [0.10, 0.90]
    assert qmin(90, 0, 0.05) == 0  # must be two-sided outside
    assert qmin(90, 60, 0.5) == 60
    assert competitor_qmin(90, 60, 0.5) == 60 + 10


def test_book_parsing_and_adjusted_mid():
    book = {"bids": [{"price": "0.40", "size": "5"}, {"price": "0.45", "size": "10"}, {"price": "0.47", "size": "1"}],
            "asks": [{"price": "0.60", "size": "100"}, {"price": "0.55", "size": "50"}]}
    bids, asks = parse_book(book)
    assert bids[0] == (0.47, 1.0) and asks[0] == (0.55, 50.0)
    assert abs(adjusted_mid(bids, asks, min_size=5) - 0.50) < 1e-12  # 0.47 x 1 is below the cutoff
    # v = 10c: bid 0.45 at 5c -> 0.25*10, bid 0.40 at 10c -> 0
    assert abs(side_q(bids, 0.50, 10, 5) - 2.5) < 1e-12


def test_reward_estimate_share():
    book = {"bids": [{"price": "0.49", "size": "100"}], "asks": [{"price": "0.51", "size": "100"}]}
    r = reward_estimate(book, rate_per_day=100, v_cents=3, min_size=20, capital_usd=98)
    # we join at 0.49 / 0.51; shares = 98 / 0.98 = 100, same as the competitor -> 50%
    assert abs(r["shares"] - 100) < 1e-9
    assert abs(r["share"] - 0.5) < 1e-9 and abs(r["reward_per_day"] - 50) < 1e-9
