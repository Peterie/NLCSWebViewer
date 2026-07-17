# 004 — Object viewer sidebar

## Goal

A sidebar in the viewer that lists the objects of the loaded NLCS++ files, lets the
user **search** objects, and lets them **highlight** an object and **go to** it on the
map.

## Background

Tooltips answer "what is this thing I'm looking at"; the object viewer answers the
inverse: "where is the object I'm looking for". NLCS++ features carry identifying
attributes suited for this (Handle, feature ID, AssetId, category, status, street
fields where present). Runs on the platform chosen in task 002.

## Specifications

- **Sidebar** (collapsible) showing the objects of the loaded drawings, organized by
  file and object type, with a count per group. Respect the visibility state from
  task 003 (hidden groups are visually distinguished or filtered out — pick one and
  apply it consistently).
- **Search**: a text input filtering objects across all loaded files as the user
  types; matches against identifying attributes (at minimum: handle, feature ID,
  asset ID, category, status, functie). Show matches as a result list with enough
  context to tell similar objects apart (category, file, handle).
- **Highlight**: selecting an object from the list (or a search result) gives it a
  clearly visible highlight on the map, distinct from normal styling; the highlight
  persists until cleared or another object is selected.
- **Go to**: the same selection pans/zooms the map to the object (fit for lines and
  polygons, sensible fixed zoom for points). If the object's layer is currently
  hidden, either reveal it or tell the user why nothing appeared — never silently do
  nothing.
- **Detail view**: the selected object's full attribute set is shown in the sidebar
  (same fields the tooltips show, but persistent and readable).
- Performance: a full drawing (~800 features) must search and highlight without
  noticeable lag; the design should not assume the object list fits on one screen.

## Acceptance criteria

- Searching a known Handle (e.g. `612D` from the voorbeeld file) finds the LSkast,
  and selecting it highlights the cabinet and moves the map to it.
- Searching `AANSLUIT AFTAK` lists the moffen with that functie across all visible
  files.
- Selecting an object of a hidden category behaves per the chosen rule (reveals it or
  explains), and clearing the selection removes the highlight.
- The detail view shows all attributes of the selected object.

## Implementation notes (2026-07-17)

Delivered as a collapsible "Objecten zoeken" sidebar (`frontend/src/objects.js`),
top-right, mirroring the left layer panel. Two interaction-model decisions recorded
here since they refine the spec rather than following it literally:

- **Map click vs. sidebar selection behave differently.** Clicking an object directly
  on the map opens the detail panel only — no auto-highlight, no auto-pan, since the
  object is already visible (that's how it was clicked). Selecting a result from
  **search or the browse tree** opens the panel **and** highlights **and** pans/zooms,
  together — matching this task's acceptance-criteria example literally, and making
  sense because a search/browse hit may be off-screen or hidden. The detail panel
  always exposes `Highlight`/`Go to`/`Clear` as manual buttons regardless of how the
  object was selected.
- **Search is field-scoped, not multi-field.** A dropdown (Handle, Feature ID,
  Asset ID, Category, Status, Functie — this spec's stated minimum) picks which
  attribute a free-text, case-insensitive substring match runs against, rather than
  matching all of them at once. Search runs across **all loaded drawings regardless
  of visibility** (the "Specifications" section's wording) — the acceptance-criteria
  text says "visible files", which would conflict with the "reveal it" requirement for
  hidden objects; loaded-not-visible was treated as the intended reading.

"Reveal it" (hidden-layer handling) is implemented as an actual auto-reveal: selecting
an object via search/browse turns on its drawing and category toggles in the left
panel (checkbox included) before panning — not just a message. The highlight overlay
(`frontend/src/highlight.js`) is also independent of visibility toggles as a second
safety net, so a highlighted object is never invisible even in the reveal-declined
case (map-click, which never auto-reveals).

Hover tooltips (`frontend/src/popup.js`) are unchanged; only the old click-to-pin
popup was removed, replaced by the sidebar's detail view.

## Dependencies

Task 002 (platform); task 003 (visibility model it must respect).

## Out of scope

- Editing objects; the viewer stays read-only.
- Cross-drawing object identity/revision diffing (task 106).
