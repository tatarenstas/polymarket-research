## TimeSeventeen/Polymarket-v1

- revision `5aa1b9d52316a8b2e789e81c8ae42c7ed532e8aa` (Hub lastModified 2026-08-30T02:33:57+00:00)
- catalogued 2026-11-12T03:27:40+00:00; 2152 Parquet files, 0 footer errors

| layer | files | rows | size GB | partitions | first | last | event time min (UTC) | event time max (UTC) | schemas |
| --- | ---: | ---: | ---: | --- | --- | --- | --- | --- | ---: |
| `CTF` | 5 | 838,688,922 | 8.54 | none | — | — | — | — | 4 |
| `OrderFilled` | 42 | 1,201,580,990 | 27.38 | month | 2022_11 | 2026_04 | 2022-11-21 19:50:09 | 2026-04-28 11:00:40 | 1 |
| `daily_aligned` | 1,248 | 601,934,424 | 13.18 | day | 2022_11_21 | 2026_04_28 | 2022-11-21 19:50:09 | 2026-04-28 11:00:40 | 1 |
| `daily_aligned_multi` | 857 | 144,175,988 | 3.63 | day | 2023_12_22 | 2026_04_28 | 2023-12-22 03:18:40 | 2026-04-28 11:00:40 | 1 |

**Checks**

- `CTF`: no issues
- `OrderFilled`: partition window fits: utc=41, utc,utc+8=1
- `daily_aligned`: missing daily partitions: 7 (2022-11-24..2022-11-27, 2022-12-04..2022-12-05, 2022-12-10); partition window fits: utc=1246, utc,utc+8=2
- `daily_aligned_multi`: missing daily partitions: 2 (2023-12-31, 2024-01-04); partition window fits: utc=854, utc,utc+8=3

**Schemas**

- `07927aeaec4eac2b` (1 files; CTF): id:string, condition_id:string, oracle:string, question_id:string, outcome_slot_count:int64
- `16f5699ecbad0b86` (42 files; OrderFilled): id:string, maker:string, taker:string, block_timestamp:int64, maker_asset_id:string, taker_asset_id:string, maker_direction:string, taker_direction:string, token_asset_id:string, token_amount:double, usdc_amount:double, price:double, fee_usdc:double
- `34557dae9a75276c` (2 files; CTF): id:string, stakeholder:string, collateral_token:string, parent_collection_id:string, condition_id:string, partition:list<element: string>, usdc_amount:double
- `75d764a3d97abd88` (1 files; CTF): id:string, redeemer:string, collateral_token:string, parent_collection_id:string, condition_id:string, index_sets:list<element: string>, usdc_amount:double
- `cabbe5ad3de323fb` (1 files; CTF): id:string, condition_id:string, oracle:string, question_id:string, outcome_slot_count:int64, payout_numerators:list<element: string>
- `f23d37b3ed033fd1` (857 files; daily_aligned_multi): asset_id:large_string, block_timestamp:int64, price:double, maker:large_string, taker:large_string, taker_direction:large_string, usdc_amount:double, fee_usdc:double, condition_id:large_string, outcome_seq:int64, neg_risk:large_string, category:large_string, category_refined:large_string, outcome_label:large_string, winning_outcome_label:large_string, resolution_status:large_string, taker_base_fee:double, maker_base_fee:double, opens_at:timestamp[us, tz=UTC], close_at:timestamp[us, tz=UTC], resolved_at:timestamp[us, tz=UTC], market_slug:large_string, p_event:double, D:int8, neg_risk_market_id:large_string
- `faffd27189525001` (1248 files; daily_aligned): asset_id:large_string, block_timestamp:int64, price:double, maker:large_string, taker:large_string, taker_direction:large_string, usdc_amount:double, fee_usdc:double, condition_id:large_string, outcome_seq:int64, neg_risk:large_string, category:large_string, category_refined:large_string, outcome_label:large_string, winning_outcome_label:large_string, resolution_status:large_string, taker_base_fee:double, maker_base_fee:double, opens_at:timestamp[us, tz=UTC], close_at:timestamp[us, tz=UTC], resolved_at:timestamp[us, tz=UTC], market_slug:large_string, p_event:double, D:int8

## TimeSeventeen/Polymarket-v2

- revision `d1a73f368ea8d5af456105c272edd73bc46a4626` (Hub lastModified 2026-11-11T20:21:00+00:00)
- catalogued 2026-11-12T03:28:47+00:00; 664 Parquet files, 0 footer errors

| layer | files | rows | size GB | partitions | first | last | event time min (UTC) | event time max (UTC) | schemas |
| --- | ---: | ---: | ---: | --- | --- | --- | --- | --- | ---: |
| `OrderFilled` | 222 | 963,660,925 | 55.19 | day | 2026_04_03 | 2026_11_10 | 2026-04-03 12:52:59 | 2026-11-10 23:59:58 | 1 |
| `daily_aligned` | 221 | 503,449,258 | 8.95 | day | 2026_04_03 | 2026_11_10 | 2026-04-03 12:52:59 | 2026-11-10 23:59:58 | 1 |
| `daily_aligned_multi` | 221 | 102,636,299 | 2.52 | day | 2026_04_03 | 2026_11_10 | 2026-04-03 23:33:41 | 2026-11-10 23:59:58 | 1 |

**Checks**

- `OrderFilled`: missing daily partitions: 0; partition window fits: <unchecked>=9, utc=213; empty files: 9
- `daily_aligned`: missing daily partitions: 1 (2026-10-29); partition window fits: <unchecked>=10, utc=211; empty files: 10
- `daily_aligned_multi`: missing daily partitions: 1 (2026-10-29); partition window fits: <unchecked>=10, utc=211; empty files: 10

**Schemas**

- `4ea046699d15e1df` (222 files; OrderFilled): id:string, order_hash:string, maker:string, taker:string, timestamp:int64, maker_direction:string, taker_direction:string, token_asset_id:string, token_amount:double, usdc_amount:double, price:double, fee_usdc:double, builder:string, metadata:string
- `f23d37b3ed033fd1` (221 files; daily_aligned_multi): asset_id:large_string, block_timestamp:int64, price:double, maker:large_string, taker:large_string, taker_direction:large_string, usdc_amount:double, fee_usdc:double, condition_id:large_string, outcome_seq:int64, neg_risk:large_string, category:large_string, category_refined:large_string, outcome_label:large_string, winning_outcome_label:large_string, resolution_status:large_string, taker_base_fee:double, maker_base_fee:double, opens_at:timestamp[us, tz=UTC], close_at:timestamp[us, tz=UTC], resolved_at:timestamp[us, tz=UTC], market_slug:large_string, p_event:double, D:int8, neg_risk_market_id:large_string
- `faffd27189525001` (221 files; daily_aligned): asset_id:large_string, block_timestamp:int64, price:double, maker:large_string, taker:large_string, taker_direction:large_string, usdc_amount:double, fee_usdc:double, condition_id:large_string, outcome_seq:int64, neg_risk:large_string, category:large_string, category_refined:large_string, outcome_label:large_string, winning_outcome_label:large_string, resolution_status:large_string, taker_base_fee:double, maker_base_fee:double, opens_at:timestamp[us, tz=UTC], close_at:timestamp[us, tz=UTC], resolved_at:timestamp[us, tz=UTC], market_slug:large_string, p_event:double, D:int8
