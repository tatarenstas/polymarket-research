"""Command line: ``pmresearch catalog build|report``."""

from __future__ import annotations

import argparse
from pathlib import Path

from .catalog.build import DEFAULT_ROOT, build_catalog
from .catalog.report import snapshot_report

DEFAULT_DATASETS = ["TimeSeventeen/Polymarket-v1", "TimeSeventeen/Polymarket-v2"]


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="pmresearch")
    sub = p.add_subparsers(dest="cmd", required=True)
    cat = sub.add_parser("catalog", help="dataset catalog and schema inspector").add_subparsers(
        dest="action", required=True
    )

    b = cat.add_parser("build", help="snapshot file listing + Parquet footers at a pinned revision")
    b.add_argument("datasets", nargs="*", default=DEFAULT_DATASETS)
    b.add_argument("--revision", help="commit sha or branch (single dataset only); default: main resolved to sha")
    b.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    b.add_argument("--workers", type=int, default=8)
    b.add_argument("--force", action="store_true", help="rebuild an existing snapshot")

    r = cat.add_parser("report", help="Markdown summary of catalog snapshots")
    r.add_argument("snapshots", nargs="+", type=Path, help="catalog/<owner>__<name>/<revision> directories")
    r.add_argument("-o", "--output", type=Path)

    a = p.parse_args(argv)
    if a.action == "build":
        if a.revision and len(a.datasets) != 1:
            p.error("--revision needs exactly one dataset")
        for ds in a.datasets:
            print(build_catalog(ds, a.revision, root=a.root, workers=a.workers, force=a.force))
    else:
        text = "\n".join(snapshot_report(s) for s in a.snapshots)
        if a.output:
            a.output.write_text(text)
        print(text)


if __name__ == "__main__":
    main()
