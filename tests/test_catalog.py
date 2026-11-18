from datetime import date

import pyarrow as pa
import pyarrow.parquet as pq

from pmresearch.catalog.inspect import inspect_footer, schema_fingerprint
from pmresearch.catalog.partitions import matching_conventions, parse_partition
from pmresearch.catalog.report import _ranges, missing_days

DAY_START = 1751328000  # 2025-07-01 00:00:00 UTC


def test_parse_partition():
    d = parse_partition("daily_aligned/2025_07_01.parquet")
    assert (d.kind, d.label) == ("day", "2025_07_01")
    m = parse_partition("OrderFilled/2026_12.parquet")
    assert (m.kind, m.label) == ("month", "2026_12")
    assert m.window(__import__("datetime").UTC)[1] - m.window(__import__("datetime").UTC)[0] == 31 * 86400
    assert parse_partition("CTF/splits.parquet") is None


def test_conventions():
    d = parse_partition("x/2025_07_01.parquet")
    assert matching_conventions(d, DAY_START, DAY_START + 86399) == ["utc"]
    assert matching_conventions(d, DAY_START - 8 * 3600, DAY_START + 16 * 3600 - 1) == ["utc+8"]
    assert matching_conventions(d, DAY_START, DAY_START + 86400) == []
    assert matching_conventions(d, DAY_START, DAY_START + 3600) == ["utc", "utc+8"]


def test_inspect_footer(tmp_path):
    t = pa.table({"block_timestamp": pa.array([DAY_START + 5, DAY_START + 100, DAY_START + 86000], pa.int64()),
                  "price": [0.1, 0.2, 0.3]})
    f = tmp_path / "2025_07_01.parquet"
    pq.write_table(t, f, row_group_size=2)
    rec = inspect_footer(pq.ParquetFile(f), "daily_aligned/2025_07_01.parquet")
    assert rec["num_rows"] == 3 and rec["num_row_groups"] == 2
    assert (rec["ts_min"], rec["ts_max"], rec["ts_rg_with_stats"]) == (DAY_START + 5, DAY_START + 86000, 2)
    assert rec["partition_conventions"] == "utc"
    assert rec["schema_fingerprint"] == schema_fingerprint(t.schema)


def test_missing_days_and_ranges():
    gaps = missing_days(["2026_01_01", "2026_01_02", "2026_01_05", "2026_01_07"])
    assert gaps == [date(2026, 1, 3), date(2026, 1, 4), date(2026, 1, 6)]
    assert _ranges(gaps) == ["2026-01-03..2026-01-04", "2026-01-06"]
