# Dekart map style

`map-style.json` is a snapshot of a Dekart report's `map_config` — the same JSON
structure the `dekart` CLI's `update_report_map_config` tool writes. Originally
pulled from report `735d42c7-fba5-40d0-9e9d-a3b382403ddd` on 2026-07-17; updated the
same day from report `d6e0b67e-eb68-4769-aa50-95414948530a` ("scholtensteeg_revisie_3",
built by `scripts/create_report.py`) after the owner tweaked styling and basemap by
hand in the Dekart UI. Re-capture whenever the owner changes the style again — see
"Reapplying it to a new report" below for the gotcha that cost a round-trip finding
this out.

It captures three things:

- **Tooltip fields** (`config.visState.interactionConfig.tooltip.fieldsToShow`): the
  same 8 fields for every dataset in that report — `category`, `functie`, `status`,
  `bedrijfstoestand`, `beheerder`, `datum_aanleg`, `netgekoppeld`, `subnettype`.
- **Drawing style** (`config.visState.layers[*].config`): one `geojson`-type layer
  per uploaded file, `filled: false` / `stroked: true` (outline-only rendering — no
  fill), thin stroke (`thickness: 0.1`), point radius 10. Stroke color is
  **data-driven**, not fixed: `visualChannels.strokeColorField` is bound to the
  `status` attribute with a custom ordinal color map
  (`visConfig.strokeColorRange.colorMap`) — `BESTAAND` (existing) → dark red
  `#6F0D0D`, `NIEUW` (new) → green `#008750`. This is genuinely portable across
  reports as-is, since it references the `status` field by name, not by dataset id —
  no substitution needed for this part.
- **Basemap**: `config.mapStyle.styleType` is `"light"` (was `"dark"` in the original
  capture).

## What's portable and what isn't

Two parts of this file are tied to *this specific report* and cannot be copy-pasted
into another report as-is:

- `config.visState.layers[*].config.dataId` — a dataset UUID, different per report.
- The keys of `interactionConfig.tooltip.fieldsToShow` — also dataset UUIDs (the
  field *list* under each key is reusable; the key itself isn't).

`config.mapState` (the saved viewport: lat/lon/zoom bearing) is also specific to this
drawing's location — it's not part of "the style," it's just where this particular
report happened to be looking when it was saved.

## Reapplying it to a new report

`scripts/create_report.py` (task 101) automates this now: it takes an NLCS++ XML
file, converts it, uploads it, applies this style with a freshly substituted
dataset id, computes a viewport that fits the drawing, verifies via snapshot, and
prints the report URL. Run `.venv/bin/python scripts/create_report.py <xml file>`.

It always creates a **new** report — there's no id tracking to update an existing
one, so re-running it on the same file leaves the old report behind (clean up via
the Dekart UI; see CLAUDE.md's Dekart CLI pitfalls).

For anything the script doesn't cover (e.g. manually tweaking a report already in
the UI), the manual process is still: give the target report id to whoever/whatever
is driving the `dekart` CLI, resolve that report's actual dataset ids via
`get_report_properties`, substitute those ids into a copy of this file's
`layers[*].config.dataId` and the `fieldsToShow` keys, and push the result with
`update_report_map_config`.
