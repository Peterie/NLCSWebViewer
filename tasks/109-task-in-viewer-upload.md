# 109 — NLCS++ upload button in the viewer

## Status: Not started (deprioritized)

Originally scoped as an owner-priority task (`002`, right after task 001); moved to
this number and out of the reserved range as out-of-scope-for-now. Spec unchanged,
just deprioritized — see tasks/overview.md's Reserved range note.

## Goal

A button in the map viewer through which a user manually adds an NLCS++ XML file. The
file is converted automatically, the result appears as layers on the map, and the
converted GeoJSON is stored in the repo's `resources/` folder.

## Background

Stock Dekart offers no extension point for a custom button, so this task starts with a
**platform decision** that also determines tasks 110 and 111:

- **Custom viewer app** — build our own viewer (e.g. on Kepler.gl or MapLibre) that
  embeds the map and owns the whole UI. Dekart can remain alongside for ad-hoc
  analysis. Fits the NLCSWebViewer name; most freedom, most work.
- **Fork Dekart** — modify Dekart's React frontend (AGPL) to add the button and later
  UI changes. One tool, but a fork to maintain against upstream.

The decision must be made and **recorded in this task file** as the first step, and
the architecture docs (`docs/spec/`) updated accordingly, since they currently state
Dekart is used unmodified.

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
  `resources/enexis_voorbeeld_3092025_1554.geojson`.
- Adding the same file again replaces (does not duplicate) both the layers and the
  stored output.
- Adding an invalid XML shows an error and leaves map and `resources/` untouched.
- The platform decision (custom viewer vs fork) is recorded in this file and
  `docs/spec/` reflects it.

## Dependencies

Task 001 (GeoJSON pipeline).

## Out of scope

- Layer selector redesign (task 110) and object viewer (task 111).
- Automatic git commits of `resources/`.
- Authentication.
