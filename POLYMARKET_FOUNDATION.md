# Polymarket Research Foundation

## Purpose

Build a self-discovering research and execution-intelligence system for Polymarket.
The objective is not a rule-based bot that guesses individual events. The objective is
an evidence-driven probability-market research platform that learns from historical
executions, observes the complete live market state, measures executable costs, and
only permits an action when the expected edge survives honest out-of-sample testing.

This file is the canonical project context. It was created after the prior prototype
was deliberately moved to Trash; it describes the next implementation from a clean
workspace.

## Non-negotiable design principles

- No hard-coded market IDs, tickers, manually selected market pairs, price levels,
  alpha thresholds, or time horizons in decision logic.
- Discover the market universe dynamically from Polymarket metadata.
- Learn model parameters from time-ordered training data; never choose them because
  they look good on a single backtest.
- Read fees, tick sizes, minimum sizes, outcomes, market rules, status, and protocol
  version from the current market metadata rather than assuming them.
- Keep raw source records immutable and derive all features reproducibly.
- Separate research, paper execution, and live execution. No order key belongs in a
  research collector.
- A midpoint is not an execution price. Every economic claim must incorporate the
  correct side of the book, depth, fees, partial fills, and latency.
- Never represent sparse/coarse history as minute data. Preserve source resolution on
  every observation.

## Primary data sources

> **Catalog correction (2026-11-12, see `docs/findings/01-data-catalog.md`):** V1 and
> V2 are two *contract eras*, not raw-vs-enriched versions of one history. V1 covers
> the first-generation CTF Exchange, 2022-11-21 → 2026-04-28. V2 covers the new
> exchange contracts from 2026-04-03 onward and is updated daily. Both releases ship
> the same `OrderFilled` / `daily_aligned` / `daily_aligned_multi` layers, and only
> V1 has `CTF/`. Statements below that call V2 the enriched modelling table and V1 the
> audit layer are superseded. Pre-April-2026 research must use V1.

### 1. Polymarket-v2 historical dataset — current contract era

Source: https://huggingface.co/datasets/TimeSeventeen/Polymarket-v2

On-chain fills for the current (v2) exchange contracts, 2026-04-03 onward, published as
daily UTC partitions. `daily_aligned` held 503.4M rows at revision `d1a73f36`
(2026-11-11). It is Parquet and enriches trade records with market metadata and
normalized event-probability fields. The cleaned-layer schema is identical to V1's.

Important visible columns:

| Group | Fields |
| --- | --- |
| Identity | `asset_id`, `condition_id`, `market_slug`, `outcome_seq`, `outcome_label` |
| Time/lifecycle | `block_timestamp`, `opens_at`, `close_at`, `resolved_at`, `resolution_status` |
| Execution | `price`, `usdc_amount`, `maker`, `taker`, `taker_direction` |
| Cost | `fee_usdc`, `taker_base_fee`, `maker_base_fee` |
| Market structure | `neg_risk`, `category`, `category_refined` |
| Labels | `winning_outcome_label`, `p_event`, `D` |

`p_event` places YES and NO on one event-probability axis. `D` is the corresponding
normalized direction on that axis. This avoids a common mistake: a buy of NO must be
interpreted as downward pressure on the probability of YES, not as upward pressure.

Use Parquet lazily through DuckDB or Polars and initially filter to a narrow,
reproducible research universe (for example, resolved Politics markets). Do not clone
or download the entire multi-billion-row release blindly. Before production use,
inspect the current repository manifest and schema because the public dataset may be
updated after this document was written.

### 2. Polymarket-v1 historical dataset — audit and replication source

Dataset: https://huggingface.co/datasets/TimeSeventeen/Polymarket-v1

Paper: https://arxiv.org/html/2606.04217v1

The associated paper describes a complete first-generation CTF Exchange on-chain
trade archive spanning 2022-11-21 through 2026-04-28. Its central research value is
ground-truth aggressor direction derived from the settlement layer. The paper reports
1.20B trade records, 1.30M markets, and approximately $61B nominal volume. The
dataset viewer separately shows a `ctf` subset with 839M rows, so exact counts must
be confirmed from the selected release files rather than inferred from a headline.

#### V1: what it contains

V1 is a **protocol-lifecycle archive**, not merely a price table. Its repository
structure includes four distinct families:

| Family | Meaning | Research value |
| --- | --- | --- |
| `OrderFilled/` | Monthly on-chain settlement records for matched trades | Canonical trade tape and true aggressor direction |
| `CTF/splits.parquet` | Collateral split into complementary outcome-token sets | Separates minting inventory from an ordinary buy trade |
| `CTF/merges.parquet` | Balanced outcomes merged back into collateral | Identifies inventory unwinds outside the order book |
| `CTF/redemptions.parquet` | Winning outcomes redeemed after resolution | Tracks settlement/cash-out behaviour |
| `CTF/preparations.parquet` | CTF preparation operations | Completes the collateral/position-operation lifecycle |
| `CTF/resolutions.parquet` | Outcome resolution operations | Provides on-chain terminal-state evidence |
| `daily_aligned/`, `daily_aligned_multi/` | Derived, analysis-oriented tables | Inspect their exact release schemas before treating them as canonical raw events |

The primary `OrderFilled` unit is a maker–taker match. A single aggressive order can
match several resting orders, producing several rows that share a transaction hash
but differ in log index. The published event key is `id = chainId_blockNumber_logIndex`;
the datasets carry no transaction hash, so mapping to transactions needs a Polygon
log join. The paper describes the trade tape as containing
block time, transaction hash, market/condition identifier, token/asset identifier,
execution price, trade quantity, maker address, taker address, and ground-truth taker
direction.

This distinction matters: a collateral `split` is not CLOB trading volume. It creates
a complete token set; a `merge` and `redemption` are likewise position operations,
not ordinary market executions. V1 lets a researcher avoid falsely treating these
on-chain operations as directional trades.

#### Why V1's ground truth matters

For a binary market, the economic event-probability direction differs from the raw
buy/sell label when the traded leg is NO. A purchase of NO is economically a decrease
in the probability of YES. The paper normalizes every record to a common event axis.
It also reports that common price-tick rules used to infer trade direction are nearly
random in aggregate on this venue. Therefore, do not recreate a direction label from
price changes when V1's settlement-derived direction is available.

V1 also allows analysis that a pure price-history endpoint cannot support:

- trade-level maker/taker concentration and repeated participant behavior;
- flow persistence, price impact, and realized post-trade response;
- separation of execution volume from CTF inventory operations;
- resolution and redemption timing;
- relayer/broker routing filters when estimating independent aggressor flow;
- exact reconstruction of a time-respecting trade tape over the archived V1 period.

#### V1 boundaries and release validation

V1 does **not** provide a permanent record of off-chain resting quotes, order adds,
cancellations, or complete L2 book state. Its block timestamp is settlement timing,
not necessarily the exact matching-engine timestamp. It is exceptional for executions
and position operations, but cannot by itself simulate queue position or exact
contemporaneous spread/depth.

At revision `5aa1b9d5` (2026-08-30) the manifest confirms the paper: `OrderFilled`
runs through `2026_04`, with a maximum event time of 2026-04-28 11:00 UTC and exactly
1,201,580,990 rows. The "839M" viewer figure is the `CTF` layer. Partitions are UTC
days, despite the README's "UTC+8" remark. Always pin the revision and use the
catalog (`pmresearch catalog build`) as the source of truth for a reproducible run.

#### Correct role of V1 beside V2

Each release is used for its own era. Within an era, `daily_aligned` /
`daily_aligned_multi` is the modelling table and `OrderFilled` (plus `CTF/` for V1) is
the lineage/audit layer. Use the audit layer whenever a result depends on trade
direction, lifecycle semantics, or position operations. A robust feature should be
explainable as:

`raw OrderFilled event -> documented normalization/join -> daily_aligned feature`.

Never concatenate V1 and V2 blindly. Carry an explicit `contract_era`, reconcile the
raw schemas (V2 raw uses `timestamp`, adds `order_hash`/`builder`/`metadata`, and
drops `maker_asset_id`/`taker_asset_id`), choose the 2026-04 cut-over from data, keep
the source release and revision, and split train/test periods strictly by time.

Use v1 to:

- audit or reproduce results against rawer CTF/on-chain records;
- verify transformation and direction-normalization assumptions;
- benchmark models across the full V1 lifecycle;
- study structural changes, fee reforms, maker concentration, and settlement data.

Do not assume v1 and v2 dataset names equal Polymarket protocol versions. Treat the
dataset versions as releases until the source metadata proves their exact contract
coverage.

### 3. Official Polymarket APIs — current state and live continuity

API overview: https://docs.polymarket.com/getting-started/api

Official surfaces:

| Surface | Base / channel | Use |
| --- | --- | --- |
| Gamma API | `https://gamma-api.polymarket.com` | Discover events/markets and market metadata |
| CLOB API | `https://clob.polymarket.com` | Current order books, prices, and order lifecycle |
| Data API | `https://data-api.polymarket.com` | Trades, price history, activity, positions, holders, analytics |
| Relayer API | `https://relayer-v2.polymarket.com` | Gasless wallet and position operations |
| Market WebSocket | `wss://ws-subscriptions-clob.polymarket.com/ws/market` | Public book, price, trade, and lifecycle updates |
| User WebSocket | `wss://ws-subscriptions-clob.polymarket.com/ws/user` | Authenticated own order and trade updates |

The APIs are the live continuation of the historical datasets. They supply new market
definitions, current books, live fills, updated fees and trading constraints, and the
post-dataset time period. The system must persist every raw live event before deriving
features, because historical full L2 order-book/cancel/replace archives are not
provided as a guaranteed public API product.

### 4. Perps are a separate integration

Docs: https://docs.polymarket.com/perps/overview

Perpetuals have their own market model, margin, funding, liquidation, state, and
WebSocket. They may be a useful later research vertical, but must not be mixed with
binary prediction-market labels or risk logic merely because both products share the
Polymarket brand.

### 5. Builder / on-chain layer

Builder docs: https://docs.polymarket.com/programs/builders/overview
Contracts: https://docs.polymarket.com/resources/contracts

After research has demonstrated a robust user-facing use case, a separate Builder
product can route user orders through a custom application and receive attribution for
routed volume. Relayer and contract integration also support position operations such
as split, merge, and redeem. This is an application/business layer, not proof of
trading alpha.

## What the combined stack enables

### Historical market-quality and calibration research

Train only on markets resolved before the validation period. Estimate whether market
quality and calibration differ by category, probability regime, time-to-close,
liquidity, fee regime, event structure, and participant composition.

The target is not simply `will this outcome win?`. Useful targets include:

- future probability change over a learned/validated horizon;
- final calibration error versus the current event probability;
- executable cost and price impact;
- persistence or reversal of normalized taker flow;
- likelihood that a market is too illiquid to trade safely;
- relationship stability between semantically related markets.

### Microstructure research with correct direction labels

The v1 paper finds that naïve tick-rule and bulk-volume trade-direction inference is
near random in aggregate for this market design. Historical labels from the datasets
therefore make it possible to study flow without introducing a known measurement
error at the first step.

Potential features:

- normalized signed volume and signed notional;
- order-flow autocorrelation and run length;
- maker/taker concentration;
- realized short-horizon impact and reversion;
- trade-size-dependent impact;
- fees and net realized economics;
- time remaining until close/resolution;
- cross-market response timing.

### Dynamic wallet and participant research

Historical maker/taker identifiers can be used to construct time-respecting wallet
features: category specialization, maker-versus-taker behavior, timing of entries,
post-fee historical performance, concentration, and stability. The system must never
equate historical PnL with future skill without a forward test and selection-bias
controls.

### Semantic probability graph

Gamma market rules and outcomes can be compiled into source-grounded formal claims.
The system then proposes logical relations, such as inclusion, mutual exclusion,
shared thresholds, shared deadlines, or common underlying events. Historical records
test whether a relation is stable; live CLOB data tests whether an apparent deviation
is executable after costs.

The graph must not rely on manually maintained pairs. Candidate relations must retain
the source text and evidence that produced them.

### Live decision and execution intelligence

Live CLOB/WebSocket data can enrich an offline prediction with the state that history
cannot provide: current spread, depth, best executable buy/sell price, order-book
imbalance, trade flow, fee schedule, market status, and local latency.

An economic decision is only meaningful if:

`expected gross edge - fees - executable spread - depth impact - uncertainty > 0`

The quantities are model outputs or current exchange data, not arbitrary fixed
constants. Initially this layer should emit research observations and paper fills;
live order placement requires separate authorization and risk controls.

### Product possibilities

- research terminal for probability markets;
- political-market calibration and flow dashboard;
- market-quality/risk scoring API;
- wallet and liquidity intelligence;
- execution-quality assistant;
- Builder frontend once a product creates independent user value.

## Limits that must remain explicit

- No dataset is a profitable strategy by itself.
- Historical execution records are not complete historical CLOB L2 books. Capture
  live quote changes, cancels, and book depth from now onward.
- `block_timestamp` measures on-chain settlement timing, which is not necessarily the
  identical moment of off-chain matching-engine state.
- Protocol changes, category-specific fees, market migrations, and changes in trader
  composition can invalidate historical relationships. Use walk-forward validation
  and explicit regime segmentation.
- The API enables trading existing markets; it does not hand an integrator arbitrary
  control over market creation, resolution, or the matching engine.
- A model cannot react to information it does not ingest. External news, official
  result feeds, and source credibility may be later inputs, but must be separately
  sourced, timestamped, and audited.
- Never use a private key or a user trading credential in a downloader, feature job,
  or notebook.

## Target architecture

```text
Historical Parquet (V1 era 2022-11..2026-04, V2 era 2026-04..; cleaned layers model, raw/CTF audit)
  -> immutable raw lake
  -> identity and outcome normalisation
  -> time-respecting feature store
  -> walk-forward research / calibration / regime models

Gamma discovery
  -> current market universe, rules, outcomes, constraints

CLOB + Data API + WebSockets
  -> immutable live event log
  -> current executable-book state

Semantic graph + statistical models
  -> candidate relationship / probability / execution-cost estimates

Research gate
  -> alert / paper observation / paper fill
  -> only later: separately authorized execution service
```

## Recommended build sequence

1. Create a data catalog and schema inspector for both datasets; record source URL,
   file revision, row count, checksum when available, schema, and ingestion time.
   **Done 2026-11-12:** `pmresearch catalog build|report`, findings in
   `docs/findings/01-data-catalog.md`.
2. Query a small, explicit, reproducible resolved-Politics sample with DuckDB; do not
   download all data.
3. Validate IDs, outcome normalization, fees, resolution labels, duplicates, missing
   timestamps, and negative-risk behavior before modelling.
4. Build time-based train/validation/test splits. Never randomize future records into
   training folds.
5. Produce descriptive market-quality reports before any predictive model.
6. Add Gamma discovery plus a durable live CLOB event collector.
7. Recreate historical features in real time and measure live feature drift.
8. Add a paper execution simulator using book-side prices and current fees.
9. Promote only models that retain positive net results in strictly later data, across
   regimes, and after realistic execution assumptions.
10. Consider Builder/execution integration only after the research system has a clear,
    independently useful product or validated risk framework.

## Source list

- https://huggingface.co/datasets/TimeSeventeen/Polymarket-v2
- https://huggingface.co/datasets/TimeSeventeen/Polymarket-v1
- https://arxiv.org/html/2606.04217v1
- https://docs.polymarket.com/getting-started/api
- https://docs.polymarket.com/market-data/realtime-data
- https://docs.polymarket.com/market-data/prices-order-books
- https://docs.polymarket.com/programs/builders/overview
- https://docs.polymarket.com/perps/overview
- https://docs.polymarket.com/resources/contracts
