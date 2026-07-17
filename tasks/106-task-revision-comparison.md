# 106 — Revision comparison

## Goal

Let a user see what changed between two revisions of the same drawing — the "future
consideration" from
[docs/spec/03-system-architecture.md](../docs/spec/03-system-architecture.md), now
promoted to a task.

## Background

The repo carries two revision files of the example drawing (`data/xml_revisie.xml`,
`data/xml_revisie_2.xml`). A multi-file Dekart report built on 2026-07-17 already
demonstrated the manual approach: per-file, per-category layer sets in one report that
the user toggles by eye icon. Those particular example revisions are near-identical
(same counts, all statuses `BESTAAND`), so real validation needs revisions with actual
changes; the NLCS `Status` attribute (BESTAAND / new / removed values) is the format's
own change signal on revision drawings.

## Specifications

- Input: two NLCS++ files identified as revisions of the same project (same project
  number; explicit user selection is acceptable).
- Produce one Dekart report from which the user can visually compare the two:
  - baseline capability: both revisions as toggleable per-category layer sets with
    consistent colors (as in the demo report), and/or Kepler's split-map mode for
    side-by-side viewing;
  - preferred addition: a computed **difference layer** highlighting features that are
    new, removed, or geometrically/attributively changed between the revisions
    (matching on stable identifiers where present — feature `ID`, `AssetId`, `Handle`
    — with a documented fallback when identifiers differ).
- Status-based styling: where a revision drawing carries meaningful `Status` values,
  color by status must be available.
- The comparison must state its method honestly in the report (e.g. a readme/legend:
  what was matched on, what counts as changed).

## Acceptance criteria

- Running the comparison on the two example revisions produces a report showing (per
  the difference method) that they are near-identical — the "no changes" case is
  rendered truthfully, not as an error.
- A synthetic revision pair with a moved cable, a removed mof, and an added kast shows
  each of those three differences distinctly.

## Dependencies

Task 101 (report building); benefits from 105 (drawing identity) but must not block on it.

## Out of scope

- Full CAD-style revision clouds/annotations.
- Cross-project comparison.
