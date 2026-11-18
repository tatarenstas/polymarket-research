# Informed-Flow Wallet Intelligence

## Objective

Identify **statistically unusual, potentially informed trading behaviour** from public
Polymarket and Polygon data.

This is not an "insider detector" and must never state that a wallet or person has
non-public, contractual, or illegal information. Public execution data cannot reveal
the source of a trader's knowledge, off-platform hedges, legal agreements, identity,
or intent. The correct output is an evidence-backed probability that a wallet's
behaviour has historically been early, directionally informative, and repeatable.

Preferred language:

```text
candidate informed-flow wallet
statistically unusual lead-to-move behaviour
behavioural cluster
```

Never output:

```text
insider
leaked information
proof of misconduct
identity claim without a reliable public source
```

## Core normalization

Every binary-market execution must be expressed on a common event-probability axis.

```text
p_event = price                    when the traded outcome is YES
p_event = 1 - price                when the traded outcome is NO

raw trade sign: BUY = +1, SELL = -1
outcome sign:   YES = +1, NO = -1

D = raw trade sign × outcome sign
```

`D = +1` means the taker expressed pressure in the direction of a higher probability
for the event. `D = -1` means pressure toward a lower probability. `D` is the
aggressor's economic direction, not a promise that the price will move next.

Examples:

| Raw execution | Equivalent event-probability stance | `D` |
| --- | --- | ---: |
| Buy YES | probability up | +1 |
| Sell YES | probability down | -1 |
| Buy NO | probability down | -1 |
| Sell NO | probability up | +1 |

## Inputs

| Source | Required use |
| --- | --- |
| Polymarket-v1 `OrderFilled` | Auditable historical maker/taker execution and direction labels |
| Polymarket-v1 CTF lifecycle tables | Filter split, merge, redemption, preparation, and resolution operations out of ordinary trade-flow analysis |
| Polymarket-v2 | `p_event`, `D`, fees, category, lifecycle metadata, resolved outcomes, market slug |
| Gamma API | Current market definition, rules, outcomes, category, deadlines, protocol details |
| CLOB/Data APIs | Current trades, book state, liquidity, positions, holders, and trading constraints |
| CLOB WebSocket | Live books, trades, price changes, market state; archive raw frames before modelling |
| Optional external sources | Timestamped public news and official results, to distinguish reaction to public information from unexplained early flow |

## What is measured

For every wallet execution, construct a time-respecting observation:

```text
wallet, market, event, outcome, timestamp
p_event, D, signed notional, fee
book/liquidity state, time-to-close, category, protocol regime
subsequent event-probability response and/or final resolved payoff
```

The basic directional-response label is conceptually:

```text
directional response = D × (future p_event - current p_event)
                       - fees
                       - realistic execution costs
```

The horizon is not hard-coded as a trading rule. It is selected and evaluated by
strictly time-ordered research and must be reported with the result.

## Evidence dimensions

### Timing advantage

Does the wallet trade before a subsequent probability movement, rather than after it?
Compare each trade against matched controls from the same historical state:

- probability level and outcome;
- category and market type;
- time to close/resolution;
- trade size and current liquidity;
- volatility and fee regime;
- market-wide contemporaneous flow.

### Net economic value

Measure performance after source-provided fees and conservative book-side execution
assumptions. Gross PnL or raw hit rate is insufficient.

### Repeatability

Require independent, chronologically later evidence. A wallet discovered from one
period must be evaluated in later untouched periods and, where possible, in distinct
events. Use uncertainty intervals and multiple-testing control across the wallet
universe.

### Selectivity and specialization

Measure whether the effect concentrates in coherent categories or event types. A
wallet that is repeatedly early in Politics but indistinguishable from baseline in
other categories is more informative than a broad winner selected after the fact.

### Conviction and abnormality

Compare a current trade to the wallet's own historical behaviour:

- notional relative to its normal size;
- concentration relative to its typical portfolio pattern;
- timing relative to close and known public information;
- whether it immediately hedges or offsets the position;
- whether it changes a long-standing market-making pattern.

### Cluster behaviour

Construct a behavioural graph from co-occurrence and time ordering, not identity
claims. Potential signals include repeated synchronized entry, similar market
selection, similar execution timing, and public on-chain funding relationships.
The output is a *behavioural cluster*, never an assertion that addresses share an
owner.

## Model outputs

Each wallet page should contain a time-stamped, explainable evidence record:

```text
wallet address / proxy-wallet mapping with source
category-specific lead-to-move score
net-of-cost historical score
sample size and independent time periods
uncertainty / confidence interval
current regime applicability
alternative explanations
supporting public executions and links to source events
```

The live engine emits an **informed-flow candidate alert**, not a trading command:

```text
wallet(s) acted
why current behaviour differs from their own baseline
which related markets are affected
whether current book conditions make any deviation executable
model confidence and counter-evidence
```

## Alternative explanations and mandatory controls

Potentially informed-looking behaviour may instead be:

- market making or inventory management;
- an off-platform hedge;
- a fast reaction to public news;
- a routing/relayer artifact;
- a statistical lucky streak or survivor bias;
- a team/fund/aggregator rather than one person;
- an artefact of market migration, changed fees, or bad entity mapping.

Every report must display these possibilities. A score must fall or become unavailable
when data is insufficient, source mappings are ambiguous, or the current regime is
outside the research support.

## Live workflow

```text
1. Live trade/book event arrives and is stored raw.
2. Resolve market, outcome, p_event, D, fee, and current executable book state.
3. Update wallet and behavioural-cluster features.
4. Compare the event with historical controls and the wallet's own baseline.
5. Link affected markets through the semantic graph.
6. Check whether any apparent deviation survives fees, spread, depth, and uncertainty.
7. Emit an explainable alert or a paper-trade observation; otherwise emit no action.
8. Reconcile later outcome with the original immutable evidence record.
```

Live execution is a separate, explicitly authorized service. It must never be enabled
merely because a wallet received a high score.

## Validation protocol

- Split data only by time; never random train/test split executions.
- Discover wallets/clusters in a training period and evaluate only later periods.
- Keep market/category, fee, protocol, and liquidity regimes explicit.
- Deduplicate raw events with their source event identity (`id` =
  `chainId_blockNumber_logIndex` in both releases' `OrderFilled`), qualified by
  contract era.
- Compare against matched-control wallets and randomized-entry baselines.
- Apply multiple-hypothesis correction: scanning millions of wallets otherwise creates
  false "geniuses" by chance.
- Report post-fee, post-impact economics and confidence intervals.
- Monitor live feature drift; retire scores that no longer transfer.

## Product role

This module is a Wallet Obsidian layer connected to the Market/Semantic Graph:

```text
wallet -> execution -> market -> event -> related markets
       -> behaviour cluster -> historical evidence -> live alert
```

Its value is explainable research and market observability. Any future use in an
execution system requires independent risk governance, paper validation, and respect
for applicable terms, laws, and market rules.

## Sources

- https://huggingface.co/datasets/TimeSeventeen/Polymarket-v1
- https://huggingface.co/datasets/TimeSeventeen/Polymarket-v2
- https://arxiv.org/html/2606.04217v1
- https://docs.polymarket.com/getting-started/api
- https://docs.polymarket.com/market-data/realtime-data
