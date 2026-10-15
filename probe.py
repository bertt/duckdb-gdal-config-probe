"""Show that DuckDB's ST_Read ignores GDAL config options set after LOAD spatial.

Usage:
    uv run --with duckdb python probe.py
"""

import os
import subprocess
import sys
from pathlib import Path

PROBE = (Path(__file__).parent / "probe.json").as_posix()


def child(mode: str) -> None:
    import duckdb

    if mode == "before_load":
        os.environ["OGR_ORGANIZE_POLYGONS"] = "SKIP"
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    if mode == "after_load":
        os.environ["OGR_ORGANIZE_POLYGONS"] = "SKIP"
    if mode == "open_options":
        sql = f"SELECT ST_AsText(geom) FROM ST_Read('{PROBE}', open_options=['OGR_ORGANIZE_POLYGONS=SKIP'])"
    else:
        sql = f"SELECT ST_AsText(geom) FROM ST_Read('{PROBE}')"
    print(con.execute(sql).fetchone()[0])


def main() -> int:
    # Each case runs in a fresh process: the extension reads the environment once, at load.
    cases = [
        ("baseline (no option)", "none", "POLYGON"),
        ("env var set BEFORE LOAD spatial", "before_load", "MULTIPOLYGON"),
        ("env var set AFTER LOAD spatial", "after_load", "MULTIPOLYGON"),
        ("open_options=['OGR_ORGANIZE_POLYGONS=SKIP']", "open_options", "MULTIPOLYGON"),
    ]
    failed = 0
    for label, mode, expected in cases:
        out = subprocess.run(
            [sys.executable, __file__, "--child", mode], capture_output=True, text=True
        )
        wkt = out.stdout.strip() or out.stderr.strip().splitlines()[-1]
        got = "MULTIPOLYGON" if wkt.startswith("MULTIPOLYGON") else "POLYGON"
        ok = got == expected
        failed += not ok
        print(f"{'OK  ' if ok else 'FAIL'} {label}: expected {expected}, got {got}")
    print("\nFAIL lines mean the option was ignored (SKIP should split the hole into a 2nd polygon).")
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--child":
        child(sys.argv[2])
    else:
        sys.exit(main())
