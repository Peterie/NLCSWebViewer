# Dekart map style

`map-style.json` is a snapshot of a Dekart report's `map_config` — the same JSON
structure the `dekart` CLI's `update_report_map_config` tool writes. It was pulled
from report `735d42c7-fba5-40d0-9e9d-a3b382403ddd` on 2026-07-17 after manually
configuring the layers and tooltip in the Dekart UI the way the project owner wants
new reports to look.

It captures two things:

- **Tooltip fields** (`config.visState.interactionConfig.tooltip.fieldsToShow`): the
  same 8 fields for every dataset in that report — `category`, `functie`, `status`,
  `bedrijfstoestand`, `beheerder`, `datum_aanleg`, `netgekoppeld`, `subnettype`.
- **Drawing style** (`config.visState.layers[*].config`): one `geojson`-type layer
  per uploaded file, each with its own fixed color, stroke color/width, point radius,
  and `filled: false` / `stroked: true` (outline-only rendering — no fill).

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

There's no CLI tool yet that does this automatically (that's what task 101 is for).
For now: give the target report id to whoever/whatever is driving the `dekart` CLI,
resolve that report's actual dataset ids via `get_report_properties`, substitute
those ids into a copy of this file's `layers[*].config.dataId` and the
`fieldsToShow` keys, and push the result with `update_report_map_config`.
