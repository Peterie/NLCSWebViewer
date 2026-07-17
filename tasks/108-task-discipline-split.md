# 108 — Split GeoJSON output by discipline

## Status: Not started (deprioritized)

Originally scoped as an owner-priority task (`001b`, directly after task 001);
moved to this number and out of the reserved range as out-of-scope-for-now. Spec
unchanged, just deprioritized — see tasks/overview.md's Reserved range note.

## Goal

Split the converter's single merged GeoJSON (task 001) into **one file per
discipline** — Elec (electricity), Gas, and Telecom — plus a separate shared
boundary file. Amends task 001's single-file decision; does not revert it, since the
"one FeatureCollection per drawing" idea was right, it was just too coarse (mixes
disciplines that will eventually need independent upload/report handling) — see task
101's "one dataset + layer per category" concern that task 001 left unresolved.

## Background

The full NLCS Netbeheer schema (`data/NLCS_Netbeheer.xsd`) defines far more asset
categories than the current example files contain (which are electricity-only:
Enexis, Sterksel). Its top-level feature categories fall into recognizable prefix
groups: `LS*`/`MS*`/`HS*` (laag-/midden-/hoogspanning — electricity), `T*` (telecom:
`Tkabel`, `Tmof`, `Toverdrachtspunt`, `Tstation`, `Tbuis`, `TbuisAppendage`), and `G*`
(gas: `Gstation`, `Gleiding`, `Gafsluiter`, and about a dozen more `G*` fittings).

Two groups don't map cleanly to a single discipline by name alone, and per an owner
decision made when scoping this task, both get a **best-guess** assignment rather
than a 4th "unmapped" bucket:

- `KB*` (cathodic protection: `KBgelijkrichter`, `KBmeetpaal`, `KBmeetdraad`,
  `KBanode`, `KBdrainage`, `KBobject`) → **Gas**. Cathodic protection is
  predominantly applied to buried steel gas mains in NL grid-operator practice.
- `A*` generic/annotation categories (`Amantelbuis`, `AmantelbuisInhoud`,
  `Amarkeringsobject`, `AbeschermingVlak`, `Aopmerking`, `AbestandBijlage`,
  `Amaaiveldhoogte`, `Akunstwerk`, `Aaanlegtechniek`, `AinUittredepunt`,
  `Averplaatsing`) → **Elec**. Low-confidence choice — driven only by
  `Amantelbuis` being the one `A*` category actually present in this repo's example
  data, where it's a protective duct around LS/MS cables (already grouped with
  `LSkabel`/`MSkabel` in the pre-GeoJSON converter). Revisit if a real Gas or Telecom
  file turns up using these categories for something unrelated to electricity.

This mapping should live as a single lookup table in the converter (e.g. next to
`ASSET_CATS` in `scripts/nlcs2geojson.py`), not scattered logic, so it's easy to
correct later.

Per a second owner decision: the project boundary (`AprojectReferentie`) is **not**
duplicated into each discipline file. It stays its own file, since it's one polygon
per drawing regardless of how many disciplines are present, and duplicating it three
times would be redundant and a reproducibility footgun (three copies that must stay
identical).

## Specifications

- Converter output per drawing becomes 4 files instead of 1:
  `resources/<name>-boundary.geojson`, `resources/<name>-elec.geojson`,
  `resources/<name>-gas.geojson`, `resources/<name>-telecom.geojson`. Same
  `type: "Feature"` / `properties` shape as today per feature; only the split changes.
- A discipline file with zero matching features for a drawing is still written, as an
  empty `FeatureCollection` (`"features": []`) — not omitted. Consumers (task 101,
  the future viewer) can rely on all three always existing.
- Category → discipline mapping is a single table in the converter (see Background);
  unrecognized categories keep today's behavior (skipped, counted as `UNMAPPED`) —
  this task does not change task 103's open-ended-categories scope.
- `resources/` is regenerated for all three example files (all Elec-only today, so
  `gas.geojson`/`telecom.geojson` will be empty FeatureCollections until a Gas or
  Telecom example file exists) and stays byte-identically reproducible.
- Update task specs that assumed the single-merged-file shape from task 001 (002,
  101, 103) to reflect the 4-file-per-drawing output.

## Acceptance criteria

- Converting `data/enexis_voorbeeld_3092025_1554.xml` yields 4 valid GeoJSON files;
  `elec.geojson` contains all 787 non-boundary features from the task-001 baseline,
  `gas.geojson` and `telecom.geojson` are empty FeatureCollections, `boundary.geojson`
  has the 1 boundary feature.
- A synthetic test feature using a `G*` or `T*` category (e.g. built from the XSD,
  since no real Gas/Telecom example file exists yet) ends up in the corresponding
  discipline file.
- `resources/` regeneration check passes (byte-identical or regenerated + committed).

## Dependencies

Task 001 (done — this amends its single-file output).

## Out of scope

- Resolving task 101's per-category (not per-discipline) layer question — this task
  only changes the file split granularity from 1 to 4; per-category layers within a
  discipline are still a task 101 concern.
- Adding real Gas/Telecom example data (none exists in `data/` today).
- Changing which attributes are extracted (task 103).
