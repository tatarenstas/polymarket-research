# Cross-Venue Sports Hedging & Best Odds Monitor

## Objective

Build a read-first system that compares Polymarket sports contracts with betting
exchanges and sportsbooks, identifies the best available opposing prices, verifies
whether contracts actually have the same payout semantics, and measures the
**executable** hedge or arbitrage capacity.

This is not a generic odds-comparison table. A displayed price difference is not an
arbitrage opportunity unless all payout scenarios, rules, execution costs, and
available sizes have been checked.

## Core definitions

### Exact cross-venue arbitrage

For two truly opposite binary contracts with a $1 payout, the necessary economic
condition is:

```text
effective_cost(Polymarket YES) + effective_cost(external NO) < 1
```

`effective_cost` includes the executable ask or lay/back construction, venue fees,
commission, slippage/depth, stake limits, currency conversion, withdrawal costs, and
the cost of capital while funds are locked.

The condition is necessary but not sufficient. Both contracts must have identical
outcome, time, void, settlement, and resolution semantics.

### Sportsbook decimal-odds conversion

For decimal odds `o`, the gross implied cost of a $1 payoff is:

```text
implied_cost = 1 / o
```

For a two-way event, a simple comparison is therefore:

```text
Polymarket YES effective cost + 1 / decimal_odds(external NO) < 1
```

For a 1X2 sport market, Polymarket `NO` may mean `draw OR opponent win`. A hedge may
need two external legs, and the total cost must include both. Do not treat a single
opponent-win bet as a hedge if a draw remains uncovered.

## Contract equivalence precedes price comparison

Every proposed relationship must be classified before it enters an executable queue:

```text
EXACT_EQUIVALENT   same event and same payoff in every scenario
EXACT_OPPOSITE     one payout is exactly the other's complement
PARTIAL_HEDGE      limits loss but leaves scenarios uncovered
NESTED             one condition logically implies another
CORRELATED_ONLY    historical/statistical relationship, not a hedge
RULES_MISMATCH     material difference in settlement conditions
UNKNOWN            insufficient evidence
```

The matcher must compare and retain evidence for:

- sport, league, participants, and scheduled start;
- market type: winner, 1X2, spread, total, prop, outright, etc.;
- regular time versus overtime/extra innings/penalties;
- draws, pushes, voids, postponements, cancellations, and player-start rules;
- official result source and settlement timing;
- early payout, cash-out, and rule-change clauses;
- currency/collateral and venue-specific withdrawal conditions.

Only `EXACT_EQUIVALENT` and `EXACT_OPPOSITE` can be presented as a potential locked
arbitrage. The others are hedges or relative-value observations and must show residual
risk explicitly.

## Venue roles

### Polymarket

Use official Gamma/CLOB/Data APIs and CLOB WebSocket for market discovery, rules,
current order-book depth, executable side prices, trading constraints, and live
updates.

### Betting exchanges

An exchange with official market and order APIs is the preferred external hedge venue
because it can offer both back and lay pricing plus visible liquidity. Betfair's
Exchange API documents market discovery, odds/volumes, order placement and a live
market/order stream.

### Sportsbooks and odds aggregators

An odds aggregator is a **discovery** source: it locates events and candidate best
lines across many bookmakers. It does not prove that a stake is still accepted, that
the displayed line is fresh, or that an automated order can be placed. Each offered
price therefore needs a freshness timestamp, accepted-stake confirmation, and venue
capability status.

### Pinnacle

Pinnacle can be a useful sharp-price reference. Its current API access is bespoke and
requires approval, so it must not be assumed as a freely available production
dependency.

## Duel: explicit policy constraint

The text quoted from Duel's Referral FAQ concerns **affiliate/referral payouts**, not
an automatic bettor rebate or a guaranteed reduction of a sports bet's cost.

The FAQ says the first sports payout shared an implicit 2% house edge at 100%, later
payouts shared 50%, and these payments are not sustainable long term. That revenue is
external to a bettor's execution/payout matrix, subject to referral eligibility and
program changes, and cannot be counted as locked hedge profit.

Duel's current sports rules state that cross-book arbitrage is prohibited and that
automated systems, bots, scripts, or scanners used to place or assist in placing bets
are prohibited; bets may be voided. Duel therefore must not be used as an automated
execution leg in this project.

Permitted research role for Duel, subject to its terms and local law:

```text
reference price / manual comparison source
```

Not permitted project role:

```text
automated hedge execution
arbitrage execution
guaranteed profit-share input
```

Sources verified 2026-11-13:

- https://duel.com/referral-faq
- https://duel.com/policies/sports-betting-rules
- https://duel.help/sports-betting/sportsbook-margin-explained

## Product: Best Odds Monitor

Each row in the monitor should represent a verified candidate relationship, not just
a shared event name.

| Field | Required meaning |
| --- | --- |
| Canonical event | Normalized sport, league, participants, and start time |
| Contract mapping | Exact outcome mapping and evidence from both venue rules |
| Polymarket leg | Best executable price, fee, depth, and timestamp |
| External leg(s) | Best offered opposing price, commission, accepted stake/depth, and timestamp |
| All-in cost | Total cash required for the complete payoff matrix |
| Worst-case payout | Payout in every outcome scenario |
| Net locked edge | Worst-case payout less all-in cost, after all known costs |
| Capacity | Smallest executable size across every required leg |
| Freshness | Age of the oldest price/rule snapshot |
| Execution risk | One-leg, partial-fill, rejection, and settlement-risk assessment |
| Classification | Exact, partial, correlated, mismatch, or unknown |

## Recommended launch sequence

1. Read-only Polymarket plus one odds aggregator; store every quote snapshot.
2. Start only with pre-match, two-way markets without draws: tennis, basketball,
   selected baseball, or MMA match winner.
3. Implement semantic contract matching and a human-reviewable rules-difference view.
4. Add a betting exchange with an official API as the first external executable venue.
5. Calculate full payoff matrices and capacity using actual book depth, not last price.
6. Run paper hedges: measure quote decay, acceptance rates, partial fills, and
   one-leg exposure before enabling any execution.
7. Extend to 1X2 markets only after multi-leg draw handling and void-rule comparisons
   are proven.
8. Treat all sportsbooks without authorized execution APIs as monitoring-only venues.

## Limits and safety

- Do not scrape or automate a venue contrary to its terms.
- Do not bypass account, stake, geographic, or access restrictions.
- Maintain separate capital and position reconciliation per venue.
- Preserve the exact rules and prices used for every alert; rules change over time.
- A positive visible spread is not a positive executable edge until both legs are
  actually fillable at the required size.
- Live/in-play sports should be a later phase because delays, suspensions, and
  information asymmetry materially increase one-leg risk.

## Sources

- https://docs.polymarket.com/getting-started/api
- https://developer.betfair.com/exchange-api/
- https://the-odds-api.com/
- https://www.pinnacle.com/en/api
