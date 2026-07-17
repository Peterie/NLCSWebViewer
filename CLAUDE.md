# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

NLCSWebViewer makes **NLCS++ files** (the NLCS Netbeheer XML exchange format used by
Dutch grid operators; GML 3.2-based, schema in `data/NLCS_Netbeheer.xsd`) viewable on
an interactive web map using [Dekart](https://dekart.xyz) / Kepler.gl.

The single load-bearing architectural fact: **Dekart cannot read NLCS++ XML** — it
only visualizes query results and uploaded map-ready geodata files. Everything in this
repo exists to bridge that gap: parse the XML, transform Dutch RD coordinates
(EPSG:28992 / EPSG:7415 planar part) to WGS84, and deliver map-ready output that
Dekart renders. Read `docs/spec/01-overview.md` → `03-system-architecture.md` before
architectural changes.

## Repository layout

- `docs/spec/` — conceptual architecture documents. **Convention: no low-level tech
  specs** (no versions, APIs, schemas, code, or config in these docs; naming products
  is fine). English prose with Dutch domain terms (LSkabel, mof, netbeheerder) kept
  as-is.
- `data/` — example NLCS++ files (one voorbeeld + two near-identical revisions of the
  same Sterksel project) and the official XSDs.
- `scripts/nlcs2geojson.py` — the converter (only real code so far). Python, needs pyproj.
- `resources/` — converted map-ready output, one `<name>.geojson` per source file
  (boundary + all asset categories merged into a single FeatureCollection, one file per
  drawing — an owner decision made during task 001, superseding the per-category CSV
  split used for the very first demo). **Must remain byte-identically reproducible**
  from the converter (see below).
- `tasks/` — the roadmap. `overview.md` lists all tasks; numbers 0–100 are reserved
  for the project owner and are done **before** 101+. Task specs are deliberately
  stack-agnostic; the stack is chosen when a task is picked up.

## Commands

Converter (venv with pyproj required; no system pip on the dev machine — use venv):

```bash
python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
.venv/bin/python scripts/nlcs2geojson.py data/enexis_voorbeeld_3092025_1554.xml out/enexis_voorbeeld_3092025_1554.geojson
```

Reproducibility check after converter changes (must show no diff, or regenerate and
commit `resources/` together with the code change):

```bash
for f in enexis_voorbeeld_3092025_1554 xml_revisie xml_revisie_2; do
  .venv/bin/python scripts/nlcs2geojson.py data/$f.xml resources/$f.geojson
done
git diff --quiet resources/ && echo IDENTICAL
```

There is no build, lint, or test suite yet. `index.js`/`package.json` are an empty
Node scaffold; whether future app code is Node or Python is decided per task.

## Working style

- The project owner wants **questions asked instead of assumptions made** — for
  design decisions, use explicit questions with options (this preference was stated
  at project start and has held throughout).
- Work is committed and pushed to `origin/main` per completed unit of work, on the
  owner's request — don't commit speculatively.
- Git identity is configured globally (Peter Callaars <peter.callaars@gmail.com>)
  since 2026-07-17; history before that was rewritten once to fix an auto-generated
  hostname identity. Don't rewrite published history again without explicit request.

## Dev environment (this machine)

The dev machine has **no sudo and no Docker**. Everything runs rootless:

- Dekart server: official image via **udocker** — start with
  `~/.local/bin/udocker run dekart` (background it), serves http://localhost:8080.
  State persists inside the container rootfs under `~/.udocker`.
- `dekart` CLI: installed in `~/.local/venvs/dekart`, on PATH as `dekart`, already
  initialized against localhost. Headless snapshots need the installed
  `dekart snapshot-local` capability (Playwright Chromium).
- Never suggest `sudo`/`docker` commands here; use the udocker shim.
- The **geosql skill** is installed (`~/.claude/skills/geosql`) — invoke it for
  Dekart map-building work; it documents the CLI workflows this repo relies on.
- The only Dekart connection is **"Local Files"** (`CONNECTION_TYPE_LOCAL`), so the
  dekart CLI always operates in **file-upload mode** — there is no warehouse
  connector; don't attempt query mode.
- This Dekart build runs zero-config with `DEKART_DATASOURCE=USER` and file upload
  enabled; the OSS server has no server-side snapshot renderer (hence
  `snapshot-local`).

## Dekart CLI pitfalls (all discovered the hard way)

- Control-plane order for file-upload mode: `create_report` → `create_dataset` →
  `update_dataset_name` → `create_file` → `dekart upload-file`; success only when the
  completion status is `completed`.
- `create_file` returns its id at `result.file_id` — unlike the other create tools
  (`result.id`). A missed id silently becomes `None` and crashes the upload call.
- In Kepler map configs, every layer `config.dataId`, filter `dataId`, and tooltip
  key must be the **dataset id** — not file id, query id, or dataset label.
- The local snapshot renderer fits the view to data bounds and ignores the saved
  viewport; pass explicit `--zoom --lat --lon` when framing matters.
- There is no CLI tool to delete a report; stray reports must be removed in the
  Dekart UI. Don't create reports speculatively.
- Resolve user-facing URLs with `dekart report-url`, never from `report_path` or raw
  tool responses.
- A `map_config` missing `mapState` crashes Kepler client-side (`Cannot set properties
  of undefined (setting 'latitude')`) — the page never reaches its "loaded" flag, so
  `dekart snapshot` hangs and times out with no useful error instead of failing fast.
  Diagnosed by driving the snapshot render URL with a throwaway Playwright script
  (the `dekart` venv already has playwright installed:
  `~/.local/venvs/dekart/bin/python`) and reading `page.on("pageerror", ...)`. Always
  include `config.mapState` (at least `latitude`/`longitude`/`zoom`) when building
  `map_config` by hand.
- For a `geojson`-type layer over an uploaded (not queried) file, `columns.geojson`
  must be `"_geojson"` for a raw `.geojson` file upload, vs the literal WKT column
  name (e.g. `"geometry"`) for a CSV-with-WKT upload — they're processed differently
  client-side.

## Established map conventions

One layer per asset category, fixed colors identical across drawings: LSkabel orange,
MSkabel blue-grey, Amantelbuis teal, LSmof pink, LSoverdrachtspunt green,
OVLoverdrachtspunt yellow, LSkast/MSstation red tones, project boundary (Grens) blue
outline-only. Hairline strokes, ~3 px points, dark basemap, tooltips showing the NLCS
attributes. Dataset naming: `<Drawing label> · <Category>`.

Multi-file viewing is emulated in stock Kepler by creating **one dataset per
(file × category)** and toggling layer visibility (default: first file visible,
others hidden). This is a workaround, not the desired UX — tasks 002–004 replace it
with real file/object-type toggles on a platform chosen in task 002 (custom viewer vs
Dekart fork; stock Dekart has no UI extension points).

This convention was established using the old per-category CSV/GeoJSON files. As of
task 001 (2026-07-17) the converter emits one merged GeoJSON per drawing instead
(`resources/<name>.geojson`, all categories in one FeatureCollection); getting back to
one-dataset-per-category for a report now requires an extra split step at
upload/report-build time (task 101), not just uploading converter output directly.

## Existing demo reports (local Dekart)

- `16cfa6ff-8734-468b-a9d2-3c5b5e8ba820` — single-file demo of the voorbeeld drawing.
- `0369a54a-8c47-4ccb-9ef2-a536d805a5e3` — "NLCS++ multi-file viewer" (all three
  files, 27 datasets).
- Two stray *empty* reports titled "NLCS++ viewer — Enexis voorbeeld & revisies" may
  still exist from a failed scripted run; they are safe to delete via the UI.
- `5cffe9d7-4819-43f3-aabc-025f880e93cf` — "Task 001 GeoJSON verification
  (single-file)", the single merged-GeoJSON layer for the voorbeeld drawing, kept as
  evidence the new converter output renders in Dekart with working tooltips.
- Two throwaway debug reports from diagnosing the `mapState` crash (a small-subset
  GeoJSON test and a small CSV+WKT test) are safe to delete via the UI; their ids
  weren't kept since they carry no lasting value.

## Domain notes worth knowing

- A drawing = one `AprojectReferentie` (project metadata + boundary polygon) plus a
  flat list of asset features. Treat the category set as open-ended (the XSD defines
  far more than the example files contain).
- `AmantelbuisInhoud` has no geometry of its own — skipping it is correct.
- LSkast footprints are drawn centimetre-scale; they are invisible until zoomed far
  in. That is the data, not a bug.
- Example-file ground truth (used as conversion sanity checks): voorbeeld = 293 line
  features (286 LSkabel, 6 MSkabel, 1 Amantelbuis), 486 points, 7 area features,
  ~7.9 km total cable length, located in Sterksel (Noord-Brabant).
