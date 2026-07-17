# Task Overview

Roadmap for turning the proven NLCS++ → Dekart pipeline into the full web upload
application described in [docs/spec](../docs/spec/01-overview.md).

## Reserved range

**Task numbers 0–100 are reserved** for tasks added by the project owner. Those tasks
take priority: they are to be completed **before** any task numbered 101 and up.
Tasks 001–004 are filled in; the remaining numbers in the range stay reserved.
`001b` is a lettered amendment slotted directly after 001 — it revises task 001's
output shape rather than adding new scope, so it isn't given its own number out of
the reserved range.

## How to use these tasks

Each task has its own spec file with goal, requirements, and acceptance criteria. The
specs are deliberately **stack-agnostic**: they describe behavior, not technology.
The implementation stack is chosen when a task is picked up. Work through the tasks in
numerical order unless dependencies say otherwise.

## Tasks (chronological)

| # | Task | Goal | Depends on |
|---|------|------|------------|
| 001 | [GeoJSON as conversion target](001-task-geojson-conversion.md) | Converter outputs GeoJSON instead of CSV; resources/ regenerated | — |
| 001b | [Split GeoJSON output by discipline](001b-task-discipline-split.md) | One GeoJSON per discipline (Elec/Gas/Telecom) + a shared boundary file, instead of one merged file | 001 |
| 002 | [NLCS++ upload button in the viewer](002-task-in-viewer-upload.md) | Add file via a button in the viewer; convert, show on map, store in resources/ | 001, 001b |
| 003 | [Layer selector redesign](003-task-layer-selector.md) | One toggle per file + one button per object type (across all files) | 002 |
| 004 | [Object viewer sidebar](004-task-object-viewer.md) | Search objects, highlight, and go to them on the map | 002, 003 |
| 005–100 | *(reserved for project owner)* | Prioritized pre-work | — |
| 101 | [Automate report creation](101-task-automate-report-creation.md) | One command: NLCS++ XML in → styled Dekart report out | 001, 001b |
| 102 | [Schema validation](102-task-schema-validation.md) | Reject invalid files before conversion, with actionable errors | — |
| 103 | [Converter hardening](103-task-converter-hardening.md) | Handle unknown categories and format variants gracefully | — |
| 104 | [Web upload app](104-task-web-upload-app.md) | Browser upload → progress → link to the Dekart map | 101, 102, 103 |
| 105 | [Drawing management](105-task-drawing-management.md) | List, replace, and delete uploaded drawings | 104 |
| 106 | [Revision comparison](106-task-revision-comparison.md) | View what changed between two revisions of a drawing | 101 |
| 107 | [Deployment & README](107-task-deployment-and-readme.md) | Reproducible setup instructions and a project README | 104 |

## Ordering rationale

Owner tasks first: switch the pipeline output to GeoJSON (001), split it by
discipline (001b), then build the viewer platform with in-viewer upload (002) and its
UI features (003, 004) on top. Task 002 opens with a recorded platform decision
(custom viewer vs Dekart fork) that also governs 003–004 and may absorb task 104 —
revisit 104 when reached.

Then the 101+ range: harden the pipeline (101–103) so the conversion path is
trustworthy, expose it through the web upload interface if still needed (104), add
lifecycle management (105), build the revision-comparison feature on top (106), and
finish with packaging and documentation (107).
