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

## Comparison with ogr2ogr

`ogr2ogr` honours the variable (bash; in PowerShell use `$env:OGR_ORGANIZE_POLYGONS="..."`):

```
ogr2ogr -f GPKG probe_default.gpkg "ESRIJSON:probe.json" -nln layer
OGR_ORGANIZE_POLYGONS=ONLY_CCW ogr2ogr -f GPKG probe_only_ccw.gpkg "ESRIJSON:probe.json" -nln layer
OGR_ORGANIZE_POLYGONS=SKIP ogr2ogr -f GPKG probe_skip.gpkg "ESRIJSON:probe.json" -nln layer
```

To see the difference in the output geometry, print the WKT instead:

```
ogr2ogr -f CSV /vsistdout/ "ESRIJSON:probe.json" -lco GEOMETRY=AS_WKT                                # POLYGON (with hole)
OGR_ORGANIZE_POLYGONS=ONLY_CCW ogr2ogr -f CSV /vsistdout/ "ESRIJSON:probe.json" -lco GEOMETRY=AS_WKT  # POLYGON (with hole)
OGR_ORGANIZE_POLYGONS=SKIP ogr2ogr -f CSV /vsistdout/ "ESRIJSON:probe.json" -lco GEOMETRY=AS_WKT      # MULTIPOLYGON (hole is a 2nd polygon)
```

`probe.json` is too small to show a speed difference. The reason this matters is a
real ArcGIS layer with two very large polygons, where skipping the ring-containment
analysis is much faster (`time` on the same data):

```
OGR_ORGANIZE_POLYGONS=ONLY_CCW ogr2ogr -f GPKG layer_only_ccw.gpkg "ESRIJSON:https://services-eu1.arcgis.com/SMnoOtmU2UWf0vRp/ArcGIS/rest/services/Potentieleruimtevergrotennat/FeatureServer/0/query?where=1%3D1&outFields=*&f=json" -nln layer
# real    0m38.796s

ogr2ogr -f GPKG layer_default.gpkg "ESRIJSON:https://services-eu1.arcgis.com/SMnoOtmU2UWf0vRp/ArcGIS/rest/services/Potentieleruimtevergrotennat/FeatureServer/0/query?where=1%3D1&outFields=*&f=json" -nln layer
# real    2m9.443s
```

Through DuckDB's `ST_Read` the same layer takes about 145 s either way, because the
option cannot be applied.
