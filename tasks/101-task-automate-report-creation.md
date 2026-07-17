# 101 — Automate report creation

## Status: Done (2026-07-17)

Implemented as `scripts/create_report.py`. Diverges from this spec in two ways,
both owner decisions made before implementation: styling follows the owner's actual
hand-tuned `dekart/map-style.json` (one layer per file, single color, category as a
tooltip field) rather than the per-category-color design below, and every run always
creates a **new** report rather than tracking/reusing one per drawing (no
idempotency — stray reports are cleaned up manually). See CLAUDE.md's "Task 101 and
103 status" note for the full picture, including a lat/lon-swap bug caught during
testing.

## Goal

A single repo command that takes an NLCS++ XML file and produces a fully styled,
interactive Dekart report, printing the report URL. This formalizes what was done by
hand for the demo reports.

## Background

The flow was proven end-to-end on 2026-07-17, using per-category CSV output from what
was then `scripts/nlcs2csv.py` (see `resources/` for committed examples), and a
sequence of `dekart` CLI calls builds a report with one layer per asset category. Task
001 replaced that CSV output with GeoJSON, but also changed the output shape: the
converter (renamed to `scripts/nlcs2geojson.py`) now emits a **single merged
FeatureCollection per drawing** (boundary + all categories together, distinguished by
each feature's `category` property) instead of grouped/per-category files —
`resources/` now holds one flat `<name>.geojson` per example file. This was an owner
decision made during task 001, and it means the "one dataset + layer per category"
report structure described below can no longer be built by uploading separate
per-category files; whoever picks up this task must decide how to keep per-category
styling with a single uploaded dataset (e.g. Kepler layer filters keyed on `category`
against the one dataset, or splitting the merged GeoJSON into per-category slices at
upload time instead of at conversion time). The orchestration currently exists only as
untracked scratch scripts; this task brings it into the repo as a maintained tool.

## Specifications

- Input: path to one NLCS++ XML file. Output: a Dekart report URL on stdout; non-zero
  exit with a clear message on failure.
- Conversion reuses `scripts/nlcs2geojson.py`; do not duplicate its logic. It now
  produces one file for the whole drawing (see Background) — resolve the per-category
  layer question above before implementing.
- Report structure: one dataset + layer per asset category present in the file, plus
  the project boundary (Grens). Dataset names follow `<Drawing label> · <Category>`.
- Control-plane order per dataset: `create_dataset` → `update_dataset_name` →
  `create_file` → `dekart upload-file`; treat an upload as successful only when its
  completion status is `completed`.
- Apply the established styling conventions as the saved map config:
  - fixed color per category, identical across drawings (LSkabel orange, MSkabel
    blue-grey, Amantelbuis teal, LSmof pink, LSoverdrachtspunt green,
    OVLoverdrachtspunt yellow, LSkast/MSstation red tones, Grens blue outline-only);
  - hairline strokes (≤1 px), point radius ~3 px, dark basemap;
  - tooltips showing the NLCS attributes (category, status, bedrijfstoestand, functie,
    eigenaar, beheerder, datum_aanleg, handle);
  - initial view centered on the project boundary.
- Verify the result before reporting success (e.g. via `dekart snapshot`) and resolve
  the user-facing URL with `dekart report-url`.

### Known pitfalls (from the demo)

- `create_file` returns its id at `result.file_id`, unlike the other create tools.
- In the Kepler map config, every layer `dataId` and tooltip key must be the report
  **dataset id** (not file id or query id).
- Snapshots on a local OSS Dekart require the local snapshot capability
  (`dekart snapshot-local install`); the local renderer fits the view to data bounds
  and ignores the saved viewport, so pass explicit viewport parameters when framing
  matters.

## Acceptance criteria

- Running the command on `data/enexis_voorbeeld_3092025_1554.xml` yields a working
  report URL; the map shows the same layer set and styling as the demo report.
- Running it on each of the three example files succeeds.
- A failed upload or CLI error aborts with a readable message (no half-silent success).

## Dependencies

Task 001 (done — the pipeline output is GeoJSON; upload and layer binding must follow
that format instead of the CSV flow described from the demo).

## Out of scope

- Web interface (task 104), validation (task 102), multi-drawing reports.
