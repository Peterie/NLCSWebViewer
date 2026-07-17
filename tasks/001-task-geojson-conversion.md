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
tasks 109–111.

## Specifications

- The converter emits **one GeoJSON FeatureCollection per drawing** (one file per
  source XML file) — not the grouped/per-category CSV split used before. The boundary
  (`AprojectReferentie`) and every recognized asset category are features in the same
  file, distinguished by each feature's `category` property. This single-file shape
  was an explicit owner decision made during implementation, superseding the
  originally spec'd grouped (`boundary`/`lines`/`points`/`areas`) and `--per-category`
  outputs — those are dropped entirely, not kept as an option.
- Coordinates in WGS84 lon/lat (as now — this is also what the GeoJSON spec requires);
  current coordinate precision is kept.
- Each feature's `properties` carry the same attributes as the current CSV columns
  (category, handle, status, bedrijfstoestand, functie, subnettype, eigenaar,
  beheerder, datum_aanleg, netgekoppeld, bovengronds, asset_id, feature_id); the
  boundary feature keeps its own project fields instead (category, projectnummer,
  netbeheerder, tekeningtype, toelichting) — GeoJSON allows heterogeneous properties
  across features in one FeatureCollection.
- `resources/` is regenerated as one flat `<name>.geojson` per example file (replacing
  the old per-file subfolders); the CSV files are removed in the same change. The
  script name/docstring is updated to match (`nlcs2csv.py` no longer describes
  reality — renamed to `nlcs2geojson.py`).
- Verify Dekart still accepts the output via file upload and renders it, with tooltips
  showing the NLCS attributes.
- Update the references to CSV output and per-category/grouped output in later task
  specs (101, 103) and in the converter section of the docs if any doc mentions them
  specifically.

## Acceptance criteria

- Converting each of the three example files yields one valid GeoJSON file (passes a
  GeoJSON validator / loads in Kepler.gl) with feature counts identical to the CSV
  versions (293 lines / 486 points / 7 areas / 1 boundary for the voorbeeld file, all
  in the same FeatureCollection).
- The single-file GeoJSON uploaded to Dekart renders (mixed geometry types in one
  layer) and shows tooltips with the same attributes as before.
- No `.csv` files remain in `resources/`; regenerating `resources/` from the repo is
  reproducible as before.

## Dependencies

None — first of the owner-priority tasks.

## Out of scope

- Viewer/UI work (tasks 109–111).
- Changing which attributes are extracted (task 103).
