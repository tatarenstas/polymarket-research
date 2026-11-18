"""Data catalog: pinned, footer-only inventory of the historical Parquet releases.

Nothing in this package downloads row data. Every number comes from the Hub file
listing (sizes, LFS sha256) or from Parquet footers (row counts, schema, column
statistics) read with HTTP range requests at a pinned revision.
"""
