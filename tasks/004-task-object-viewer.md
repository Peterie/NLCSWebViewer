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

## Dependencies

Task 002 (platform); task 003 (visibility model it must respect).

## Out of scope

- Editing objects; the viewer stays read-only.
- Cross-drawing object identity/revision diffing (task 106).
