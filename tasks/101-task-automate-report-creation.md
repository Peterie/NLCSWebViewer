# 101 — Automate report creation

## Goal

A single repo command that takes an NLCS++ XML file and produces a fully styled,
interactive Dekart report, printing the report URL. This formalizes what was done by
hand for the demo reports.

## Background

The flow was proven end-to-end on 2026-07-17: `scripts/nlcs2csv.py --per-category`
converts a drawing to per-category CSVs (see `resources/` for committed examples), and
a sequence of `dekart` CLI calls builds a report with one layer per asset category.
The orchestration currently exists only as untracked scratch scripts; this task brings
it into the repo as a maintained tool.

## Specifications

- Input: path to one NLCS++ XML file. Output: a Dekart report URL on stdout; non-zero
  exit with a clear message on failure.
- Conversion reuses `scripts/nlcs2csv.py` (per-category mode); do not duplicate its
  logic.
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

Task 001 (the pipeline output is GeoJSON by then; upload and layer binding must follow
that format instead of the CSV flow described from the demo).

## Out of scope

- Web interface (task 104), validation (task 102), multi-drawing reports.
