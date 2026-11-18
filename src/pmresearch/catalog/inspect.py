"""Read one Parquet footer and turn it into a manifest record."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from .partitions import matching_conventions, parse_partition

# Event-time column names, in order of preference. V1 trade layers and V2 cleaned
# layers use ``block_timestamp``; the V2 raw OrderFilled layer uses ``timestamp``.
TIME_COLUMNS = ("block_timestamp", "timestamp")


def schema_columns(schema: pa.Schema) -> list[list[str]]:
    return [[f.name, str(f.type)] for f in schema]


def schema_fingerprint(schema: pa.Schema) -> str:
    canonical = json.dumps(schema_columns(schema), separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def time_stats(md: pq.FileMetaData, schema: pa.Schema) -> dict[str, Any]:
    """Min/max of the event-time column from row-group statistics (no data read)."""
    col = next((c for c in TIME_COLUMNS if c in schema.names), None)
    out: dict[str, Any] = {"ts_column": col, "ts_min": None, "ts_max": None, "ts_rg_with_stats": 0}
    if col is None:
        return out
    # Leaf index equals field index only for flat schemas; resolve by path to be safe.
    leaf = next(i for i in range(md.num_columns) if md.schema.column(i).path == col)
    lo = hi = None
    n = 0
    for r in range(md.num_row_groups):
        s = md.row_group(r).column(leaf).statistics
        if s is None or not s.has_min_max:
            continue
        n += 1
        lo = s.min if lo is None else min(lo, s.min)
        hi = s.max if hi is None else max(hi, s.max)
    out.update(ts_min=lo, ts_max=hi, ts_rg_with_stats=n)
    return out


def inspect_footer(pf: pq.ParquetFile, path: str) -> dict[str, Any]:
    md = pf.metadata
    schema = pf.schema_arrow
    rec: dict[str, Any] = {
        "num_rows": md.num_rows,
        "num_row_groups": md.num_row_groups,
        "num_columns": len(schema),
        "created_by": md.created_by,
        "schema_fingerprint": schema_fingerprint(schema),
        **time_stats(md, schema),
    }
    part = parse_partition(path)
    rec["partition_kind"] = part.kind if part else None
    rec["partition_label"] = part.label if part else None
    complete = rec["ts_min"] is not None and rec["ts_rg_with_stats"] == md.num_row_groups
    if part and complete:
        rec["partition_conventions"] = ",".join(matching_conventions(part, rec["ts_min"], rec["ts_max"]))
    else:
        rec["partition_conventions"] = None
    return rec
