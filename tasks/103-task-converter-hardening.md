# 103 — Converter hardening

## Goal

Make `scripts/nlcs2geojson.py` robust for real-world NLCS++ input: treat asset categories
as open-ended, tolerate optional data, and support other grid operators' variants —
as required by
[docs/spec/02-nlcs-data-format.md](../docs/spec/02-nlcs-data-format.md) ("a viewer
should treat the set of categories as open-ended rather than hard-coding exactly
these").

## Background

The converter was built against one Enexis example. It hard-codes a fixed allowlist of
known asset categories and **skips** categories outside it (they are only counted as
`UNMAPPED`). The full NLCS Netbeheer schema defines many more categories (gas, water,
telecom, MS/LS variants) that real files will contain. As of task 001 the converter
emits a single merged GeoJSON FeatureCollection per drawing (boundary + all asset
features together, distinguished by each feature's `category` property) rather than
grouped or per-category files, so "carried through" below means "included as a feature
in that one file," not routed to a separate output.

## Specifications

- Unknown categories are carried through, not dropped: include them as features in the
  single merged GeoJSON output, with `category` set from the source element tag.
- Attribute extraction becomes generic: capture all simple-text child elements of a
  feature (current known-attribute mapping stays as the canonical column set; extra
  attributes must at least survive into an extensible representation rather than being
  silently lost).
- Geometry handling covers the GML constructs the schema allows beyond the current
  three (e.g. multi-geometries or curves) — at minimum, fail loudly per feature with a
  count, never crash the whole conversion.
- A conversion summary reports, per category: converted, skipped, and why.
- Existing behavior for the three example files must not regress: regenerating
  `resources/` must remain byte-identical (or any intentional change must be
  regenerated and committed together with the code change).

## Acceptance criteria

- A synthetic test file containing a category outside the current groups (e.g. a gas
  or water asset from the XSD) converts with that category present in the output.
- A feature with an unsupported geometry construct produces a per-feature warning and
  does not abort the run.
- `resources/` regeneration check passes as described above.

## Dependencies

None. (Feeds into tasks 101 and 104.)

## Out of scope

- Coordinate systems other than Dutch RD (EPSG:28992 / 7415 planar part).
- Schema validation (task 102).
