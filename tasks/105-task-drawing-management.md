# 105 — Drawing management

## Status: Not started

## Goal

Give uploaded drawings a lifecycle: see what has been uploaded, replace a drawing by
re-uploading it, and delete a drawing — fulfilling the pipeline's "Load" contract in
[docs/spec/03-system-architecture.md](../docs/spec/03-system-architecture.md)
("Re-uploading the same drawing replaces its previous content rather than duplicating
it") in the file hand-off setting.

## Background

Dekart knows reports, not "drawings" (see docs/spec 04, *What Dekart does not do
here*): any notion of drawing identity and revisions must live in the upload app. The
demo left duplicate/stray reports behind precisely because nothing tracked what had
been created — and the Dekart CLI currently offers no report-deletion tool, so
deletion likely goes through the app's own bookkeeping plus the Dekart UI or API.

## Specifications

- The app keeps an inventory of uploaded drawings: drawing identity (e.g. project
  number + file name or content hash), upload time, source file, resulting report
  URL/id, and status.
- The upload page (task 104) grows a listing view of this inventory with links to each
  drawing's report.
- Re-uploading a drawing with the same identity **replaces** its report content
  (update the existing report's datasets, or create anew and retire the old) — the
  inventory must never show two live entries for one drawing.
- Deleting a drawing removes it from the inventory and retires its report; document
  clearly what "retire" means given Dekart's capabilities at implementation time.
- The inventory survives an app restart.

## Acceptance criteria

- After two uploads of different files, the listing shows both with working links.
- Re-uploading the first file leaves exactly one entry for it, pointing at a report
  with the new content.
- Deleting an entry removes it from the list, and the app no longer offers the dead
  report link.

## Dependencies

Task 104.

## Out of scope

- Multi-user ownership/permissions.
- Revision comparison (task 106) — this task only manages single-drawing identity.
