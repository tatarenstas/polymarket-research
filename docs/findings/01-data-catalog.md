# 01 — Data catalog: what the historical releases actually contain

Build step 1 of `POLYMARKET_FOUNDATION.md`. Produced by `pmresearch catalog build`
from the Hub file listing and Parquet footers only (no row data downloaded).
Generated detail: [`catalog/REPORT.md`](../../catalog/REPORT.md).

| Dataset | Pinned revision | Hub lastModified | Catalogued (UTC) |
| --- | --- | --- | --- |
| `TimeSeventeen/Polymarket-v1` | `5aa1b9d52316a8b2e789e81c8ae42c7ed532e8aa` | 2026-08-30 | 2026-11-12 03:27 |
| `TimeSeventeen/Polymarket-v2` | `d1a73f368ea8d5af456105c272edd73bc46a4626` | 2026-11-11 | 2026-11-12 03:28 |

## Coverage

| Release / layer | Files | Rows | Size | Event time (UTC) |
| --- | ---: | ---: | ---: | --- |
| V1 `OrderFilled` (monthly) | 42 | 1,201,580,990 | 27.4 GB | 2022-11-21 19:50 → 2026-04-28 11:00 |
| V1 `daily_aligned` (binary) | 1,248 | 601,934,424 | 13.2 GB | 2022-11-21 → 2026-04-28 |
| V1 `daily_aligned_multi` (neg-risk) | 857 | 144,175,988 | 3.6 GB | 2023-12-22 → 2026-04-28 |
| V1 `CTF` (5 tables) | 5 | 838,688,922 | 8.5 GB | — (no time column) |
| V2 `OrderFilled` (daily) | 222 | 963,660,925 | 55.2 GB | 2026-04-03 12:52 → 2026-11-10 23:59 |
| V2 `daily_aligned` | 221 | 503,449,258 | 9.0 GB | 2026-04-03 → 2026-11-10 |
| V2 `daily_aligned_multi` | 221 | 102,636,299 | 2.5 GB | 2026-04-03 → 2026-11-10 |

V1 CTF rows: splits 594.4M, redemptions 186.7M, merges 54.8M, preparations 1.45M,
resolutions 1.31M.

## Findings that change the plan

1. **V2 is not an enriched copy of V1; it is a different contract era.** V1 = the
   first-generation CTF Exchange, 2022-11-21 → 2026-04-28. V2 = the new exchange
   contracts, 2026-04-03 → present, updated daily. Both releases have the same three
   trade layers. The foundation's "V2 primary, V1 audit" split is therefore wrong:
   history before April 2026 exists *only* in V1, and V1 is also the only release
   with `CTF/` lifecycle tables. A long-horizon study needs both, joined on an
   explicit `contract_era` dimension, never concatenated blindly.
2. **The two eras overlap for 26 days (2026-04-03 → 04-28), but V2 is tiny there.**
   April 3–28 has 2.6M V2 raw fills versus 227M V1 fills for all of April. V2
   partitions 04-04 → 04-14 are empty files (zero rows), and real V2 volume starts
   mid-April. A cut-over date has to be chosen from the data, per market, not assumed.
3. **The confusing headline counts are now explained.** 1,201,580,990 is V1
   `OrderFilled` and matches the V1 README exactly. "839M" is the V1 **CTF** layer,
   not trades. "502M" was V2 `daily_aligned` at an earlier revision (503.4M now).
4. **V2 raw schema differs from V1 raw.** V2 `OrderFilled` has `timestamp` (not
   `block_timestamp`), `order_hash`, `builder`, `metadata`, and no
   `maker_asset_id`/`taker_asset_id`. The cleaned layers have identical schemas across
   eras (24 columns; 25 in `_multi`).
5. **The event key is `id = chainId_blockNumber_logIndex`, not a transaction hash.**
   No trade or CTF table carries `transaction_hash`. Mapping to transactions needs a
   Polygon log join.
6. **Partitions are UTC days, not UTC+8.** The V1 README says "Split by UTC +8". Footer
   statistics show every checkable partition fits the UTC window (V1: 2,141 files UTC;
   none fit only UTC+8). V2 likewise.
7. **Cleaned layers keep roughly 62–63% of raw rows.** V1 746M / 1,202M; V2 606M /
   964M. The READMEs explain the drop only as "relayer/router filtering". Before
   any volume or wallet analysis, step 3 should test on a sample whether the dropped
   rows are the per-match taker-side duplicate (the exchange contract appearing as
   `taker`) rather than only the two published relayer addresses. This is a
   hypothesis, not a measured result.

## Gaps and data-quality flags

- V2 `daily_aligned` and `daily_aligned_multi` are **missing 2026-10-29**, although V2
  `OrderFilled/2026_10_29` has 3.67M raw rows. That is a hole in the cleaned layers,
  not a quiet day.
- V2: 9–10 empty files per layer in 2026-04-04 → 04-16 (contract ramp-up).
- V1 `daily_aligned`: no files for 2022-11-24..27, 2022-12-04..05, 2022-12-10 (early,
  low-activity period; raw month files exist). V1 `daily_aligned_multi`: no files for
  2023-12-31 and 2024-01-04.
- The READMEs warn that cleaned layers join **frozen metadata observed after the
  trade** (`category`, resolution, fee rates, `close_at`). These columns are
  look-ahead information for point-in-time features. Use them for labels and
  universe selection, but do not treat them as known at execution time.

## Next (build step 2–3)

- Choose the first research universe per era (e.g. resolved Politics, V1 2024–2025),
  record the partition list against the pinned revisions above, and query it lazily
  with DuckDB over `hf://` paths.
- Validation queries: `id` uniqueness, raw→cleaned row reconciliation for a sample
  day, `D`/`p_event` recomputed from `taker_direction` + `outcome_seq`, fee fields
  versus `fee_usdc`, timestamp units, and neg-risk group consistency.
