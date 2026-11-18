"""Partition names in file paths and the time windows they claim to cover."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone

_DAY = re.compile(r"(?<!\d)(\d{4})_(\d{2})_(\d{2})\.parquet$")
_MONTH = re.compile(r"(?<!\d)(\d{4})_(\d{2})\.parquet$")

# Offsets we test a partition's timestamps against. The V1 README says files are
# "split by UTC+8" while also calling them UTC-day partitions; the catalog records
# which convention the footer statistics actually satisfy.
CONVENTIONS: dict[str, timezone] = {
    "utc": UTC,
    "utc+8": timezone(timedelta(hours=8)),
}


@dataclass(frozen=True)
class Partition:
    kind: str  # "day" | "month"
    label: str  # e.g. "2026_04_03" or "2026_04"
    year: int
    month: int
    day: int | None

    def window(self, tz: timezone) -> tuple[int, int]:
        """Half-open [start, end) epoch-second window of this partition in ``tz``."""
        start = datetime(self.year, self.month, self.day or 1, tzinfo=tz)
        if self.kind == "day":
            end = start + timedelta(days=1)
        else:
            end = datetime(self.year + self.month // 12, self.month % 12 + 1, 1, tzinfo=tz)
        return int(start.timestamp()), int(end.timestamp())


def parse_partition(path: str) -> Partition | None:
    if m := _DAY.search(path):
        y, mo, d = (int(x) for x in m.groups())
        return Partition("day", m.group(0).removesuffix(".parquet"), y, mo, d)
    if m := _MONTH.search(path):
        y, mo = (int(x) for x in m.groups())
        return Partition("month", m.group(0).removesuffix(".parquet"), y, mo, None)
    return None


def matching_conventions(part: Partition, ts_min: int, ts_max: int) -> list[str]:
    """Names of the conventions whose window contains [ts_min, ts_max]."""
    out = []
    for name, tz in CONVENTIONS.items():
        lo, hi = part.window(tz)
        if lo <= ts_min and ts_max < hi:
            out.append(name)
    return out
