---
license: cc-by-4.0
language:
- en
tags:
- polymarket
- prediction-markets
- market-microstructure
- on-chain
- polygon
- parquet
configs:
- config_name: orderfilled
  data_files:
  - split: train
    path: OrderFilled/*.parquet
- config_name: daily_aligned
  data_files:
  - split: train
    path: daily_aligned/*.parquet
- config_name: daily_aligned_multi
  data_files:
  - split: train
    path: daily_aligned_multi/*.parquet
---

# Polymarket v2

**The record continues. A new contract era, made available for independent research.**

Time Seventeen organizes Polymarket v2 on-chain trading records on Polygon into raw and cleaned Parquet layers. The public release brings together observed fills and metadata-enriched analysis files, separating the source record from the transformations used to make it useful for research.

## Coverage and daily updates

The earliest published daily partition is **3 April 2026** (`2026_04_03.parquet`). This dataset is **updated daily**, publishing completed UTC-day partitions as source data becomes available and is processed. The archive start is a data-coverage boundary, not a claim about the platform's launch date or universal historical completeness.

At the documentation review on **2 November 2026 (Asia/Shanghai)**, the latest published partition in each of the three layers was **31 October 2026**. This is a dated observation, not a live counter. Check the repository file listing at a pinned revision for the actual latest date and available days. Daily updates do not imply an intraday feed or that the current UTC day is complete. Historical partitions may be revised as data and metadata are reconciled.

## Three published layers

| Directory | Role |
|---|---|
| `OrderFilled/` | Raw on-chain fill records for the v2 contract era |
| `daily_aligned/` | Cleaned, metadata-enriched and normalized binary-market analysis layer |
| `daily_aligned_multi/` | Cleaned analysis layer for multi-outcome markets |

```text
OrderFilled/YYYY_MM_DD.parquet
daily_aligned/YYYY_MM_DD.parquet
daily_aligned_multi/YYYY_MM_DD.parquet
README.md
```

These directories describe different representations or subsets of activity. Do not concatenate them and interpret their combined row count as unique trades or economic volume. Choose the analysis layer appropriate to the instrument universe; use the raw layer when the underlying record itself is the object of study.

Polymarket v1, Polymarket v2 and Polymarket US remain distinct releases. The US archive comes from public Time & Sales reports, not these Polygon logs. Do not import US reporting conventions or assume that v1 contract-era boundaries determine v2 coverage.

## Working with the data

Start with a small date range and inspect the actual Parquet schema before selecting columns. Preserve market and outcome identifiers, confirm timestamp units and distinguish a token's traded price from any event-normalized price. Side and probability conventions must be checked against the selected layer before aggregating across outcomes or market types.

For reproducibility, pin a repository revision and record the layer and partition list used. A cleaned file can incorporate market metadata obtained after the underlying trade, so point-in-time studies should establish when each joined field became observable rather than assume every column was available to a trader at execution time.

## Read one partition

Install `huggingface_hub` and `pyarrow`. The following example reads a single cleaned binary-market partition without downloading the full archive:

```python
from huggingface_hub import HfApi, hf_hub_download
import pyarrow.parquet as pq

repo = "TimeSeventeen/Polymarket-v2"
revision = HfApi(token=False).dataset_info(repo).sha
path = hf_hub_download(
    repo_id=repo, repo_type="dataset", revision=revision,
    filename="daily_aligned/2026_04_03.parquet", token=False,
)
file = pq.ParquetFile(path)
print(file.schema_arrow)
print(file.metadata.num_rows)
for batch in file.iter_batches(batch_size=5):
    print(batch.to_pylist())
    break
```

Use column projection and batch processing for larger studies. The Hub configurations are `orderfilled`, `daily_aligned` and `daily_aligned_multi`. Their `train` split is a file-loading convention, not a prepared statistical training/test division.

## Research scope

The archive supports examination of executed prices, trading activity and event-market microstructure within the published coverage. It is not a historical order-book, cancellation log, live executable quote service or a universal record of all economic activity. A transaction price is not automatically an exact physical probability; event definitions, settlement rules, fees, liquidity and coverage remain part of the interpretation.

## Access, license and attribution

The dataset is publicly available on Hugging Face under the repository's existing **CC BY 4.0** license.

- [Files and revision history](https://huggingface.co/datasets/TimeSeventeen/Polymarket-v2/tree/main)
- Curated by [Time Seventeen](https://huggingface.co/TimeSeventeen).

For attribution, reference **Time Seventeen, Polymarket v2**, the dataset URL, repository revision, selected layer and access date.
