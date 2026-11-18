"""Summarize catalog snapshots as Markdown: coverage, gaps, schemas, partition checks."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import duckdb


def _iso(ts: int | None) -> str:
    return datetime.fromtimestamp(ts, UTC).strftime("%Y-%m-%d %H:%M:%S") if ts is not None else "—"


def _ranges(days: list[date]) -> list[str]:
    """Compress a sorted list of dates into 'a..b' ranges."""
    out: list[str] = []
    start = prev = None
    for d in days:
        if prev is not None and d == prev + timedelta(days=1):
            prev = d
            continue
        if start is not None:
            out.append(str(start) if start == prev else f"{start}..{prev}")
        start = prev = d
    if start is not None:
        out.append(str(start) if start == prev else f"{start}..{prev}")
    return out


def missing_days(labels: list[str]) -> list[date]:
    have = sorted({date(*map(int, lbl.split("_"))) for lbl in labels})
    if not have:
        return []
    want = {have[0] + timedelta(days=i) for i in range((have[-1] - have[0]).days + 1)}
    return sorted(want - set(have))


def snapshot_report(snapshot: Path) -> str:
    run = json.loads((snapshot / "run.json").read_text())
    schemas = json.loads((snapshot / "schemas.json").read_text())
    con = duckdb.connect()
    con.execute(f"create view m as select * from read_parquet('{snapshot / 'manifest.parquet'}')")

    lines = [
        f"## {run['repo_id']}",
        "",
        f"- revision `{run['revision']}` (Hub lastModified {run['hub_last_modified']})",
        f"- catalogued {run['ingested_at_utc']}; {run['parquet_files']} Parquet files, "
        f"{run['footer_errors']} footer errors",
        "",
        "| layer | files | rows | size GB | partitions | first | last | event time min (UTC) | event time max (UTC) | schemas |",
        "| --- | ---: | ---: | ---: | --- | --- | --- | --- | --- | ---: |",
    ]
    layers = con.execute(
        """
        select layer, count(*) files, sum(num_rows) rows_, sum(size_bytes)/1e9 gb,
               string_agg(distinct coalesce(partition_kind, 'none'), ',') kinds,
               min(partition_label) first_, max(partition_label) last_,
               min(ts_min) tmin, max(ts_max) tmax, count(distinct schema_fingerprint) nschema
        from m where path like '%.parquet' group by layer order by layer
        """
    ).fetchall()
    for layer, files, rows, gb, kinds, first, last, tmin, tmax, nschema in layers:
        lines.append(
            f"| `{layer}` | {files:,} | {int(rows or 0):,} | {gb:.2f} | {kinds} | {first or '—'} | "
            f"{last or '—'} | {_iso(tmin)} | {_iso(tmax)} | {nschema} |"
        )

    lines += ["", "**Checks**", ""]
    for (layer,) in con.execute("select distinct layer from m where path like '%.parquet' order by 1").fetchall():
        notes = []
        labels = [r[0] for r in con.execute(
            "select partition_label from m where layer=? and partition_kind='day'", [layer]).fetchall()]
        if labels:
            gaps = missing_days(labels)
            notes.append(f"missing daily partitions: {len(gaps)}" + (f" ({', '.join(_ranges(gaps)[:12])})" if gaps else ""))
        conv = con.execute(
            """select coalesce(partition_conventions, '<unchecked>') c, count(*) from m
               where layer=? and partition_kind is not null group by c order by c""", [layer]).fetchall()
        if conv:
            notes.append("partition window fits: " + ", ".join(f"{c or 'none'}={n}" for c, n in conv))
        incomplete = con.execute(
            "select count(*) from m where layer=? and ts_column is not null and ts_rg_with_stats < num_row_groups",
            [layer]).fetchone()[0]
        if incomplete:
            notes.append(f"files with incomplete time statistics: {incomplete}")
        errs = con.execute("select count(*) from m where layer=? and error is not null", [layer]).fetchone()[0]
        if errs:
            notes.append(f"footer errors: {errs}")
        empty = con.execute("select count(*) from m where layer=? and num_rows=0", [layer]).fetchone()[0]
        if empty:
            notes.append(f"empty files: {empty}")
        lines.append(f"- `{layer}`: " + "; ".join(notes) if notes else f"- `{layer}`: no issues")

    lines += ["", "**Schemas**", ""]
    for fp, s in schemas.items():
        cols = ", ".join(f"{n}:{t}" for n, t in s["columns"])
        lines.append(f"- `{fp}` ({s['files']} files; {', '.join(s['layers'])}): {cols}")
    return "\n".join(lines) + "\n"
