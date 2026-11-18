# pmresearch

Evidence-driven Polymarket research: prediction markets (CLOB) and Polymarket Perps. The aim
is to find what actually works (tradable strategies, or information products as the
fallback) and to record negative results as carefully as positive ones. Nothing here places
real orders; all live tools are read-only on public endpoints. Not investment advice.

- Project context: [`POLYMARKET_FOUNDATION.md`](POLYMARKET_FOUNDATION.md)
- Concepts: [`concepts/`](concepts/)
- **Results: [`docs/findings/`](docs/findings/); start with
  [`08-strategy-map.md`](docs/findings/08-strategy-map.md)** (what works, what doesn't, what is untested)
- Literature notes (read independently of our hypotheses): [`docs/literature/`](docs/literature/)

## Setup

```bash
uv sync
uv run pytest
```

## Layout

| Path | What |
| --- | --- |
| `src/pmresearch/catalog/` | Dataset catalog and schema inspector (`pmresearch catalog ...`) |
| `src/pmresearch/backtest/engine.py` | DuckDB backtest engine over the point-in-time trade tape |
| `src/pmresearch/lp_paper.py` | Perps liquidity-reward simulator (maker with delayed Binance hedge) |
| `src/pmresearch/funding_scan.py` | Perps funding scanner logic |
| `src/pmresearch/pm_rewards.py` | Prediction-market liquidity-reward scoring (official formula) |
| `src/pmresearch/pm_mm_paper.py`, `pm_clob.py` | Paper market maker for prediction markets; public CLOB REST helpers |
| `research/probes/` | Realism probe: calibration and wallet edge (findings `02`) |
| `research/backtest/` | Tape builders and H1–H5 backtests, V2 holdout (findings `03`, `04`) |
| `research/perps_lp/` | Perps: LP paper tests, stage 1, funding snipe, funding scanner (findings `05`–`07`) |
| `research/pm_mm/` | Prediction-market market making with rewards: reward scan, maker edge, paper test (findings `09`) |
| `research/nex/` | NEX sandbox (Polygon Amoy) order-lifecycle smoke test; runs only on the allowlisted server |
| `tests/` | Unit tests for the library code |

## Data

`data/` is git-ignored (~18 GB) and fully reproducible:

| Path | Produced by |
| --- | --- |
| `data/probe/` | `research/probes/realism_probe.py` (reads the Hugging Face datasets) |
| `data/tape/v1`, `data/tape/v2` | `research/backtest/build_tape.py`, `build_tape_v2.py` |
| `data/bt.duckdb`, `data/bt_v2.duckdb` | DuckDB caches created by the backtests |
| `data/lp_paper/`, `data/lp_stage1/` | Perps LP paper runs (`run_paper.py`, `run_stage1.py`) |
| `data/funding_scanner/` | `funding_scanner.py` logs |
| `data/pm_mm/` | `reward_scan.py` snapshots and prediction-market MM paper runs |

## Data catalog

Snapshot the Hugging Face releases at a pinned revision. Only the file listing and Parquet
footers are read; no row data is downloaded:

```bash
uv run pmresearch catalog build                      # V1 + V2 at current main, resolved to a sha
uv run pmresearch catalog build TimeSeventeen/Polymarket-v2 --revision <sha>
uv run pmresearch catalog report catalog/*/* -o catalog/REPORT.md
```

Each snapshot lands in `catalog/<owner>__<name>/<revision>/` (`run.json`, `manifest.parquet`,
`schemas.json`, the dataset card). Snapshots are immutable; an existing one is rebuilt only
with `--force`.

## Live tools (read-only)

```bash
uv run python research/perps_lp/funding_scanner.py --min-rate 0.0005   # Perps funding signals
uv run python research/pm_mm/reward_scan.py --capital 1000               # where PM rewards pay most
```
