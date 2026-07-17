# 002 — NLCS++ upload button in the viewer

## Goal

A button in the map viewer through which a user manually adds an NLCS++ XML file. The
file is converted automatically, the result appears as layers on the map, and the
converted GeoJSON is stored in the repo's `resources/` folder.

## Background

Stock Dekart offers no extension point for a custom button, so this task starts with a
**platform decision** that also determines tasks 003 and 004:

- **Custom viewer app** — build our own viewer (e.g. on Kepler.gl or MapLibre) that
  embeds the map and owns the whole UI. Dekart can remain alongside for ad-hoc
  analysis. Fits the NLCSWebViewer name; most freedom, most work.
- **Fork Dekart** — modify Dekart's React frontend (AGPL) to add the button and later
  UI changes. One tool, but a fork to maintain against upstream.

The decision must be made and **recorded in this task file** as the first step, and
the architecture docs (`docs/spec/`) updated accordingly, since they currently state
Dekart is used unmodified.

## Platform decision (2026-07-17)

**Chosen: custom viewer app**, built on MapLibre GL JS with a Python backend that
serves the converted GeoJSON drawings.

Rationale:

- Stock Dekart has no UI extension points, and a fork would mean maintaining AGPL
  React code against upstream for every UI task in this range (002–004).
- A custom viewer owns the whole UI, which is exactly what tasks 002–004 (and likely
  104) need; it also fits the NLCSWebViewer name.
- The converter already outputs map-ready WGS84 GeoJSON (task 001), which MapLibre
  consumes directly — no extra hand-off machinery.
- Dekart remains available alongside for ad-hoc analysis; nothing is removed.

Display parity with the established Dekart maps was delivered as groundwork under
this decision (viewer app in `frontend/`, backend in `backend/`, category styling
extracted from the established Dekart report). The upload button below remains this
task's deliverable on top of that groundwork. The architecture docs were updated:
see `docs/spec/03-system-architecture.md` and `docs/spec/04-visualization.md`.

## Specifications

- A clearly visible control in the viewer UI ("Add NLCS++ file" or similar) that opens
  a file picker accepting NLCS++ XML.
- On submit, server-side processing runs the conversion pipeline (converter from task
  001; schema validation once task 102 exists) and:
  - the drawing's layers appear on the map without a manual page reload, following the
    established per-category layer and styling conventions;
  - the converted GeoJSON is written to `resources/<drawing-name>.geojson` on disk —
    **write-only**: committing to git remains a manual developer action;
  - conversion errors are shown to the user in readable form; nothing is stored or
    shown for a failed conversion.
- Multiple drawings can be added in one session; adding a drawing that already exists
  (same name) replaces its layers and its `resources/` folder content.
- Relationship to task 104 (web upload app): this task delivers upload *inside the
  viewer*; when 104 is reached, evaluate whether a separate upload page still adds
  value or 104 is absorbed by this work — record the outcome in 104's spec.

## Acceptance criteria

- From a running viewer, adding `data/enexis_voorbeeld_3092025_1554.xml` via the
  button shows the drawing on the map and creates
  `resources/enexis_voorbeeld_3092025_1554/` with the converted GeoJSON.
- Adding the same file again replaces (does not duplicate) both the layers and the
  stored output.
- Adding an invalid XML shows an error and leaves map and `resources/` untouched.
- The platform decision (custom viewer vs fork) is recorded in this file and
  `docs/spec/` reflects it.

## Dependencies

Task 001 (GeoJSON pipeline).

## Out of scope

- Layer selector redesign (task 003) and object viewer (task 004).
- Automatic git commits of `resources/`.
- Authentication.
