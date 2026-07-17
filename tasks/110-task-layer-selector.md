# 110 — Layer selector: file toggles + object-type buttons

## Status: Not started (deprioritized)

Originally scoped as an owner-priority task (`003`); moved to this number and out
of the reserved range as out-of-scope-for-now. Spec unchanged, just deprioritized —
see tasks/overview.md's Reserved range note.

## Goal

Replace the current one-checkbox-per-layer selector with two compact controls:
**one toggle per NLCS++ file** and **one button per object type** that switches that
type across all files at once.

## Background

The multi-file demo report exposes 27 individual layers (3 files × 9 categories) in
Kepler's stock layer panel; hiding one file means clicking nine eye icons. The
desired model treats *file* and *object type* as two independent dimensions. This
runs on the platform chosen in task 109 (custom viewer or Dekart fork).

## Specifications

- **File toggles**: one on/off control per loaded NLCS++ file (Voorbeeld, Revisie 1,
  …). Toggling a file shows/hides all of its layers in one action.
- **Object-type buttons**: one control per asset category (LSkabel, MSkabel,
  Amantelbuis, LSmof, LSoverdrachtspunt, OVLoverdrachtspunt, LSkast, MSstation,
  Grens). Toggling a type shows/hides that category **in every loaded file**.
- Combination semantics: an individual layer is visible **iff its file toggle is on
  AND its object-type toggle is on**. Turning a dimension off and on again restores
  the previous state of the other dimension (no state loss).
- The set of files and categories is derived from what is actually loaded — nothing
  hard-coded; a newly added drawing (task 109) appears with its toggle automatically,
  and a category present in only one file still gets a type button.
- Each control shows its identity clearly (file label; category name with its
  established color as a swatch).
- Default state on load: first file on, other files off, all object types on —
  matching the convention used in the demo reports.

## Acceptance criteria

- With three files loaded: one click on a file toggle hides all nine of its layers;
  one click on "LSmof" hides moffen in every visible file.
- Sequence "LSmof off → Revisie 1 on → LSmof on" results in moffen visible in all
  files whose file toggle is on — demonstrating the AND semantics and state
  restoration.
- Adding a fourth drawing at runtime produces a fourth file toggle without code
  changes.

## Dependencies

Task 109 (platform decision and viewer to build on).

## Out of scope

- Object-level selection/search (task 111).
- Per-layer styling controls beyond visibility.
