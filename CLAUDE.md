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
- `data/` — example NLCS++ files (started as one voorbeeld + two near-identical
  revisions of the same Sterksel project; more real-world files get dropped in here
  over time, e.g. `scholtensteeg.xml`) and the official XSDs. Not every file in this
  folder is necessarily converted into `resources/` yet — check before assuming.
- `scripts/nlcs2geojson.py` — the converter. Python, needs pyproj.
- `scripts/create_report.py` — task 101: converts an XML file and publishes it as a
  styled Dekart report in one command (imports `nlcs2geojson`, shells out to the
  `dekart` CLI). Prints the report URL to stdout; see CLAUDE.md's task 101/103 status
  note below for what it does and doesn't handle.
- `resources/` — converted map-ready output, one `<name>.geojson` per source file
  (boundary + all asset categories merged into a single FeatureCollection, one file per
  drawing — an owner decision made during task 001, superseding the per-category CSV
  split used for the very first demo). **Must remain byte-identically reproducible**
  from the converter (see below).
- `dekart/` — captured Dekart report config: `map-style.json` (a real `map_config` the
  owner hand-tuned in the UI, saved so it can be reapplied to new reports) and a
  `README.md` explaining what's portable vs report-specific in it. Treat this as the
  **current source of truth for styling**, ahead of prose descriptions elsewhere.
- `README.md` — human-facing operational steps (currently: how to run the local Dekart
  server). `CLAUDE.md` (this file) is guidance for Claude Code; keep the two in sync
  where they overlap rather than letting one go stale.
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

Publish a styled Dekart report for one drawing (requires local Dekart running, see
Dev environment below):

```bash
.venv/bin/python scripts/create_report.py data/enexis_voorbeeld_3092025_1554.xml
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

**Superseded — see `dekart/map-style.json` for the actual current style.** The
paragraph below describes the *original* per-category-color convention from the very
first CSV-based demo. It is not what's actually in use anymore: the owner has since
hand-configured reports with a *different* style (one layer per whole file, single
fixed color per layer, `category` shown only as a tooltip field, not a color channel)
and had that captured as the reusable `dekart/map-style.json`. Keeping the old prose
here for history/context, but don't implement against it — implement against the
JSON.

<details>
<summary>Original (superseded) convention</summary>

One layer per asset category, fixed colors identical across drawings: LSkabel orange,
MSkabel blue-grey, Amantelbuis teal, LSmof pink, LSoverdrachtspunt green,
OVLoverdrachtspunt yellow, LSkast/MSstation red tones, project boundary (Grens) blue
outline-only. Hairline strokes, ~3 px points, dark basemap, tooltips showing the NLCS
attributes. Dataset naming: `<Drawing label> · <Category>`.

Multi-file viewing is emulated in stock Kepler by creating **one dataset per
(file × category)** and toggling layer visibility (default: first file visible,
others hidden). This is a workaround, not the desired UX — tasks 109–111 (formerly
002–004, moved out of the owner-priority range) replace it with real file/object-type
toggles on a platform chosen in task 109 (custom viewer vs Dekart fork; stock Dekart
has no UI extension points).

</details>

This convention was established using the old per-category CSV/GeoJSON files. As of
task 001 (2026-07-17) the converter emits one merged GeoJSON per drawing instead
(`resources/<name>.geojson`, all categories in one FeatureCollection); getting back to
one-dataset-per-category for a report now requires an extra split step at
upload/report-build time (task 101), not just uploading converter output directly.

## Task 101 and 103 status (as of 2026-07-17): done

- **103** (converter hardening): `scripts/nlcs2geojson.py` no longer has a fixed
  `ASSET_CATS` allowlist — any feature with a convertible geometry is included,
  category is purely descriptive now. Attribute extraction is generic (every
  simple-text child element survives, snake_cased from its tag name, in addition to
  the canonical `ATTR_COLS` set). Geometry support extended to `gml:Curve` made of
  straight `LineStringSegment`s; anything else unconvertible (`Surface`, curved
  `Curve` segments, empty `Geometry`) is skipped with a per-category, per-reason count
  in the printed summary — never crashes. Verified via a synthetic edge-case XML
  (kept only as a scratch file, not committed) covering: a brand-new category with
  valid geometry, a straight-segment `Curve`, a curved `Curve`, a `Surface`, and a
  missing `Geometry`. Fixed a factual error this surfaced: `AmantelbuisInhoud` *does*
  have its own geometry (see Domain notes) — it was only ever excluded by the old
  allowlist, not because it lacks geometry as previously documented here.
- **101** (automate report creation): `scripts/create_report.py`. Takes one XML
  path, converts it (writing to `resources/<name>.geojson`, same as manual usage),
  publishes it as a new Dekart report styled from `dekart/map-style.json` (dataset id
  substituted, viewport computed from the data's bounding box), verifies via
  `dekart snapshot`, and prints the report URL. Always creates a **new** report on
  every run — no id tracking, so re-running on the same file leaves the old report as
  a stray (owner's explicit choice: simplicity over avoiding stray-report cleanup).
  Styling follows `dekart/map-style.json`'s shape (one layer per file, single color,
  category as a tooltip field), not the original per-category-color design in the
  task spec — that spec text is now stale/historical, not current behavior.
  **Bug caught during testing**: the viewport-computation helper returned
  `(lon, lat, zoom)` but was unpacked as `(lat, lon, zoom)`, silently swapping the
  two — the first test report pointed the map near the equator off Africa instead of
  Sterksel. `dekart snapshot` "succeeded" anyway (a swapped-but-valid lat/lon range
  doesn't error), so this needed an actual visual check of the rendered snapshot to
  catch, not just a non-crashing exit code — worth remembering as a review reflex.

## Existing demo reports (local Dekart)

**All reports were archived by the owner on 2026-07-17** (via the Dekart UI's
Archive action — there is no delete/archive tool exposed through the `dekart` CLI's
MCP interface, even though the underlying `ArchiveReport` gRPC method exists in
Dekart's own client code; confirmed by grepping the served JS bundle for it and
finding it's not in `dekart tools`' list). This includes `735d42c7-...`, the report
`dekart/map-style.json` was captured from — archiving is presumed non-destructive
(a hide/soft-delete toggle, not deletion), but there is currently **no active
report** in local Dekart to point to as a working example. The style/tooltip
config lives on in `dekart/map-style.json` regardless of that source report's
archived state.

Next time a report is built (e.g. via `scripts/create_report.py`), record its id
and purpose here again.

## Domain notes worth knowing

- A drawing = one `AprojectReferentie` (project metadata + boundary polygon) plus a
  flat list of asset features. Treat the category set as open-ended (the XSD defines
  far more than the example files contain).
- `AmantelbuisInhoud` **does** have its own `Geometry` (a `LineString` co-located with
  its parent `Amantelbuis`'s duct, via a `MantelbuisID` foreign key) — this note used
  to say the opposite and was wrong; it was only ever excluded by the converter's old
  fixed category allowlist, which task 103 removed. It represents the cable/pipe
  actually running inside the duct (see its `Labeltekst`, e.g. `GPLK 4x50Cu`) and is
  now converted like everything else.
- LSkast footprints are drawn centimetre-scale; they are invisible until zoomed far
  in. That is the data, not a bug.
- Example-file ground truth (used as conversion sanity checks): voorbeeld = 293 line
  features (286 LSkabel, 6 MSkabel, 1 Amantelbuis), 486 points, 7 area features,
  ~7.9 km total cable length, located in Sterksel (Noord-Brabant). As of task 103
  (open-ended categories), the converted output also includes 2 `AmantelbuisInhoud`
  line features on top of that — 789 total features in `resources/
  enexis_voorbeeld_3092025_1554.geojson`, not 787.
- The converter's known-category allowlist (`ASSET_CATS` in `scripts/nlcs2geojson.py`)
  is manually maintained and **will have gaps on real-world files** — the three
  original Enexis examples are electricity-only and don't exercise most of the
  schema. Case in point: `MSmof` (medium-voltage cable joint, the obvious MS
  counterpart of the already-handled `LSmof`) was missing until the new
  `scholtensteeg.xml` example surfaced it via `UNMAPPED:MSmof` in the conversion
  summary. When adding a new example file, always check the printed `UNMAPPED:*`
  counts for categories that clearly pair with an existing one before assuming
  task 103 is the only place to fix this — an obvious 1:1 pairing (like `LSmof` /
  `MSmof`) is a same-session fix, not a task-103-only concern.
