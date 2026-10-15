# duckdb-gdal-config-probe

Minimal reproduction: DuckDB's spatial extension (`ST_Read`) only honours GDAL config
options such as `OGR_ORGANIZE_POLYGONS` if they are in the environment **before**
`LOAD spatial`. Setting them afterwards, or via `open_options`, has no effect, and
DuckDB offers no setting or function to change them.

`probe.json` is an EsriJSON polygon with a hole. With `OGR_ORGANIZE_POLYGONS=SKIP`,
GDAL returns a `MULTIPOLYGON` (the hole becomes a second polygon); by default it
returns a `POLYGON` with an interior ring.

```
uv run --with duckdb python probe.py
```

Expected: every case with `SKIP` returns `MULTIPOLYGON`, as `ogr2ogr` does.
Actual: only the "before LOAD" case does.

```
ogr2ogr -f CSV /vsistdout/ "ESRIJSON:probe.json" -lco GEOMETRY=AS_WKT   # POLYGON
OGR_ORGANIZE_POLYGONS=SKIP ogr2ogr -f CSV /vsistdout/ "ESRIJSON:probe.json" -lco GEOMETRY=AS_WKT   # MULTIPOLYGON
```
