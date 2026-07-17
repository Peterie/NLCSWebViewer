# 001 — GeoJSON as conversion target

## Goal

Replace CSV with **GeoJSON** as the output format of the conversion pipeline. The
converter emits GeoJSON FeatureCollections, and `resources/` holds GeoJSON instead of
CSV.

## Background

The converter (`scripts/nlcs2csv.py`) currently writes CSVs with a WKT `geometry`
column — chosen for the first demo because Dekart's CSV upload was the shortest path.
GeoJSON is the more natural interchange format for this data: geometry is first-class
(no WKT-in-a-string), properties are typed, and it is the lingua franca of web map
tooling (Kepler.gl, MapLibre, QGIS) — which matters for the custom viewer work in
tasks 002–004.

## Specifications

- The converter emits, per drawing, the same logical outputs as today but as GeoJSON
  FeatureCollections: the grouped files (`boundary`, `lines`, `points`, `areas`) and,
  with `--per-category`, one file per asset category.
- Coordinates in WGS84 lon/lat (as now — this is also what the GeoJSON spec requires);
  current coordinate precision is kept.
- Each feature's `properties` carry the same attributes as the current CSV columns
  (category, handle, status, bedrijfstoestand, functie, subnettype, eigenaar,
  beheerder, datum_aanleg, netgekoppeld, bovengronds, asset_id, feature_id); the
  boundary keeps its project fields (projectnummer, netbeheerder, tekeningtype,
  toelichting).
- `resources/` is regenerated as GeoJSON for all three example files; the CSV files
  are removed in the same change. The script name/docstring is updated to match
  (`nlcs2csv.py` no longer describes reality — rename, e.g. `nlcs2geojson.py`).
- Verify Dekart still accepts the output via file upload and renders it with the same
  layer behavior as the CSV path did.
- Update the references to CSV output in later task specs (101, 103) and in the
  converter section of the docs if any doc mentions CSV specifically.

## Acceptance criteria

- Converting each of the three example files yields valid GeoJSON (passes a GeoJSON
  validator / loads in Kepler.gl) with feature counts identical to the CSV versions
  (293 lines / 486 points / 7 areas / 1 boundary for the voorbeeld file).
- A per-category GeoJSON uploaded to Dekart renders and shows tooltips with the same
  attributes as before.
- No `.csv` files remain in `resources/`; regenerating `resources/` from the repo is
  reproducible as before.

## Dependencies

None — first of the owner-priority tasks.

## Out of scope

- Viewer/UI work (tasks 002–004).
- Changing which attributes are extracted (task 103).
