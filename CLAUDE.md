# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

NLCSWebViewer makes **NLCS++ files** (the NLCS Netbeheer XML exchange format used by
Dutch grid operators; GML 3.2-based, schema in `data/NLCS_Netbeheer.xsd`) viewable on
an interactive web map using the project's **own viewer**: a MapLibre GL JS frontend
(`frontend/`) served by a FastAPI backend (`backend/`). This custom viewer replaced
Dekart as the display platform (platform decision recorded in
`tasks/002-task-in-viewer-upload.md`, 2026-07-17); Dekart remains available on the dev
machine for ad-hoc analysis only.

The single load-bearing architectural fact: **nothing renders NLCS++ XML directly**.
Everything in this repo exists to bridge that gap: parse the XML, transform Dutch RD
coordinates (EPSG:28992 / EPSG:7415 planar part) to WGS84, and deliver map-ready
GeoJSON that the viewer renders. Read `docs/spec/01-overview.md` →
`03-system-architecture.md` before architectural changes.

## Repository layout

- `docs/spec/` — conceptual architecture documents. **Convention: no low-level tech
  specs** (no versions, APIs, schemas, code, or config in these docs; naming products
  is fine). English prose with Dutch domain terms (LSkabel, mof, netbeheerder) kept
  as-is.
- `data/` — example NLCS++ files (one voorbeeld + two near-identical revisions of the
  same Sterksel project) and the official XSDs.
- `scripts/nlcs2geojson.py` — the converter. Python, needs pyproj.
- `backend/` — FastAPI app: lists/serves `resources/*.geojson` under `/api/drawings`
  and serves the built frontend from `out/frontend` when present.
- `frontend/` — the viewer: vanilla JS + Vite + maplibre-gl. Category styling lives in
  `frontend/src/categories.js` (the canonical color table, see map conventions below).
- `resources/` — converted map-ready output, one `<name>.geojson` per source file
  (boundary + all asset categories merged into a single FeatureCollection, one file per
  drawing — an owner decision made during task 001, superseding the per-category CSV
  split used for the very first demo). **Must remain byte-identically reproducible**
  from the converter (see below).
- `tasks/` — the roadmap. `overview.md` lists all tasks; numbers 0–100 are reserved
  for the project owner and are done **before** 101+. Task specs are deliberately
  stack-agnostic; the stack is chosen when a task is picked up.

## Commands

Setup (no system pip on the dev machine — use venv):

```bash
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt -r backend/requirements.txt
cd frontend && npm install
```

Converter:

```bash
.venv/bin/python scripts/nlcs2geojson.py data/enexis_voorbeeld_3092025_1554.xml out/enexis_voorbeeld_3092025_1554.geojson
```

Viewer — production mode (one server):

```bash
cd frontend && npm run build        # → out/frontend (gitignored)
.venv/bin/uvicorn backend.app:app --port 8010   # serves app + API on :8010
```

Viewer — dev mode (hot reload; Vite proxies /api to :8010):

```bash
.venv/bin/uvicorn backend.app:app --reload --port 8010   # terminal 1
cd frontend && npm run dev                                # terminal 2
```

Ports on this shared dev machine: **8000 and 5173 are taken by other users' apps** —
the backend uses 8010, and pass `--port <n> --strictPort` to Vite when its default is
busy (it silently hops to 5174 otherwise and you end up curling someone else's app).

Reproducibility check after converter changes (must show no diff, or regenerate and
commit `resources/` together with the code change):

```bash
for f in enexis_voorbeeld_3092025_1554 xml_revisie xml_revisie_2; do
  .venv/bin/python scripts/nlcs2geojson.py data/$f.xml resources/$f.geojson
done
git diff --quiet resources/ && echo IDENTICAL
```

There is no lint or test suite yet. Server-side code is Python, the frontend is
vanilla JS; task 002's upload endpoint should import the converter directly rather
than shelling out.

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

The dev machine is **shared** (multiple users run their own servers) and has **no sudo
and no Docker**. Everything runs rootless:

- Never suggest `sudo`/`docker` commands here; use the udocker shim
  (`~/.local/bin/udocker`) when a container is unavoidable.
- Headless browser verification: Playwright Chromium works rootless
  (`pip install playwright && playwright install chromium` in a venv); only system
  Firefox is preinstalled.

### Dekart (ad-hoc analysis only, no longer the viewer platform)

- This user's Dekart server: official image via udocker, `-v $HOME/dekart-data:/dekart/data`,
  port 8090 (**8080 belongs to another user's Dekart**). State: `~/dekart-data/dekart.db`
  (SQLite, directly readable).
- The `dekart` CLI and geosql skill referenced by earlier notes are **not installed**
  on this machine/account. The gRPC-web API works without them: POST to
  `http://localhost:<port>/Dekart/GetReportStream` (no `/api/v1` prefix, service name
  is plain `Dekart`), content-type `application/grpc-web+proto`, and the request
  **must include a StreamOptions field** (field 2; an empty message suffices) or the
  server rejects with "missing StreamOptions". The report's Kepler `map_config` JSON
  is embedded in the response and can be regexed out.
- Runs zero-config with `DEKART_DATASOURCE=USER`; only connection type is
  "Local Files" (file-upload mode; there is no warehouse connector).

## Dekart CLI pitfalls (historical — kept for ad-hoc Dekart work)

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

One layer per asset category, fixed colors identical across drawings. The canonical
values (extracted 2026-07-17 from the Kepler config of the Dekart multi-file demo
report and codified in `frontend/src/categories.js`):

| Category | Hex | Style |
|---|---|---|
| LSkabel | `#FC8D62` (orange) | line, 0.6 px |
| MSkabel | `#8DA0CB` (blue-grey) | line, 1.0 px |
| Amantelbuis | `#66C2A5` (teal) | line, 0.8 px |
| LSmof | `#E78AC3` (pink) | point, 3 px |
| LSoverdrachtspunt | `#A6D884` (green) | point, 3 px |
| OVLoverdrachtspunt | `#FFD92F` (yellow) | point, 3 px |
| LSkast | `#E65A5A` (red) | polygon fill |
| MSstation | `#B23C3C` (dark red) | polygon fill |
| Grens (boundary) | `#4682EB` (blue) | outline-only, 0.8 px |

All at 0.85 opacity. Dark basemap by default (PDOK BRT grijs as alternative), tooltips
showing the NLCS attributes, titles `<Drawing label> · <Category>`. Default
visibility: first drawing on, others off, all object types on.

The viewer implements file×category toggling natively (a layer is visible iff its
drawing toggle AND its category toggle are on) — the old Kepler workaround of one
dataset per (file × category) is only needed when building Dekart reports (task 101).

## Existing demo reports (local Dekart, historical)

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
