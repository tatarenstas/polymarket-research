"""Build an immutable catalog snapshot of a Hugging Face dataset at a pinned revision.

Output layout (one directory per dataset revision, never overwritten silently)::

    catalog/<owner>__<name>/<revision>/
        run.json         source URL, revision, Hub lastModified, ingestion time, versions
        manifest.parquet one row per repository file (sizes, sha256, footer facts)
        schemas.json     distinct Parquet schemas and which layers use them
        README.md        the dataset card at this revision (the claims we audit against)
"""

from __future__ import annotations

import json
import platform
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
from huggingface_hub import HfApi, HfFileSystem

from .. import __version__
from .inspect import inspect_footer, schema_columns, schema_fingerprint

DEFAULT_ROOT = Path("catalog")

MANIFEST_SCHEMA = pa.schema(
    [
        ("path", pa.string()),
        ("layer", pa.string()),
        ("size_bytes", pa.int64()),
        ("blob_id", pa.string()),
        ("lfs_sha256", pa.string()),
        ("num_rows", pa.int64()),
        ("num_row_groups", pa.int64()),
        ("num_columns", pa.int64()),
        ("created_by", pa.string()),
        ("schema_fingerprint", pa.string()),
        ("ts_column", pa.string()),
        ("ts_min", pa.int64()),
        ("ts_max", pa.int64()),
        ("ts_rg_with_stats", pa.int64()),
        ("partition_kind", pa.string()),
        ("partition_label", pa.string()),
        # Comma-separated conventions whose window contains [ts_min, ts_max];
        # "" = none fits, null = not checkable (no partition or incomplete stats).
        ("partition_conventions", pa.string()),
        ("error", pa.string()),
    ]
)


def snapshot_dir(repo_id: str, revision: str, root: Path = DEFAULT_ROOT) -> Path:
    return root / repo_id.replace("/", "__") / revision


def _layer(rel_path: str) -> str:
    return rel_path.split("/", 1)[0] if "/" in rel_path else "(root)"


def _with_retries(fn, *, attempts: int = 5, base: float = 1.0):
    for i in range(attempts):
        try:
            return fn()
        except Exception:
            if i == attempts - 1:
                raise
            time.sleep(base * 2**i + random.random())


def build_catalog(
    repo_id: str,
    revision: str | None = None,
    *,
    root: Path = DEFAULT_ROOT,
    workers: int = 8,
    force: bool = False,
    log=print,
) -> Path:
    api = HfApi(token=False)
    info = api.dataset_info(repo_id, revision=revision)
    sha = info.sha
    out = snapshot_dir(repo_id, sha, root)
    if (out / "manifest.parquet").exists() and not force:
        log(f"catalog for {repo_id}@{sha} already exists at {out}; pass --force to rebuild")
        return out

    fs = HfFileSystem(token=False)
    base = f"datasets/{repo_id}@{sha}"
    # find() pages through the full tree and fills fs's directory cache, so later
    # open() calls do not issue one metadata request per file.
    listing = _with_retries(lambda: fs.find(base, detail=True))
    log(f"{repo_id}@{sha[:12]}: {len(listing)} files listed")

    records: dict[str, dict[str, Any]] = {}
    for full, d in listing.items():
        rel = full.removeprefix(base + "/")
        lfs = d.get("lfs")
        records[rel] = {
            "path": rel,
            "layer": _layer(rel),
            "size_bytes": d.get("size"),
            "blob_id": d.get("blob_id"),
            "lfs_sha256": getattr(lfs, "sha256", None) if lfs else None,
        }

    schemas: dict[str, dict[str, Any]] = {}

    def inspect(rel: str) -> tuple[str, dict[str, Any], Any]:
        def go():
            with fs.open(f"{base}/{rel}", "rb", block_size=1 << 20) as f:
                pf = pq.ParquetFile(f)
                return inspect_footer(pf, rel), pf.schema_arrow

        try:
            rec, schema = _with_retries(go)
            return rel, rec, schema
        except Exception as e:  # recorded per file; the run continues
            return rel, {"error": f"{type(e).__name__}: {e}"[:500]}, None

    parquet = sorted(p for p in records if p.endswith(".parquet"))
    done = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(inspect, p) for p in parquet]
        for fut in as_completed(futures):
            rel, rec, schema = fut.result()
            records[rel].update(rec)
            if schema is not None:
                fp = schema_fingerprint(schema)
                entry = schemas.setdefault(fp, {"columns": schema_columns(schema), "layers": set(), "files": 0})
                entry["layers"].add(records[rel]["layer"])
                entry["files"] += 1
            done += 1
            if done % 200 == 0 or done == len(parquet):
                log(f"  footers {done}/{len(parquet)} ({time.time() - t0:.0f}s)")

    out.mkdir(parents=True, exist_ok=True)
    rows = [records[p] for p in sorted(records)]
    table = pa.Table.from_pylist(
        [{k: r.get(k) for k in MANIFEST_SCHEMA.names} for r in rows], schema=MANIFEST_SCHEMA
    )
    pq.write_table(table, out / "manifest.parquet")
    (out / "schemas.json").write_text(
        json.dumps(
            {fp: {**v, "layers": sorted(v["layers"])} for fp, v in sorted(schemas.items())},
            indent=2,
        )
    )
    if "README.md" in records:
        readme = _with_retries(lambda: fs.cat_file(f"{base}/README.md"))
        (out / "README.md").write_bytes(readme)

    import duckdb
    import huggingface_hub

    run = {
        "repo_id": repo_id,
        "source_url": f"https://huggingface.co/datasets/{repo_id}/tree/{sha}",
        "revision": sha,
        "revision_requested": revision or "main",
        "hub_last_modified": info.last_modified.isoformat() if info.last_modified else None,
        "ingested_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "files_listed": len(records),
        "parquet_files": len(parquet),
        "footer_errors": sum(1 for r in rows if r.get("error")),
        "method": "Hub tree listing + Parquet footer range reads; no row data downloaded",
        "versions": {
            "pmresearch": __version__,
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "pyarrow": pa.__version__,
            "huggingface_hub": huggingface_hub.__version__,
            "duckdb": duckdb.__version__,
        },
    }
    (out / "run.json").write_text(json.dumps(run, indent=2))
    log(f"wrote {out} ({run['footer_errors']} footer errors)")
    return out
