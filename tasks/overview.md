# Task Overview

Roadmap for turning the proven NLCS++ → Dekart pipeline into the full web upload
application described in [docs/spec](../docs/spec/01-overview.md).

## Reserved range

**Task numbers 0–100 are reserved** for tasks added by the project owner. Those tasks
take priority: they are to be completed **before** any task numbered 101 and up.

## How to use these tasks

Each task has its own spec file with goal, requirements, and acceptance criteria. The
specs are deliberately **stack-agnostic**: they describe behavior, not technology.
The implementation stack is chosen when a task is picked up. Work through the tasks in
numerical order unless dependencies say otherwise.

## Tasks (chronological)

| # | Task | Goal | Depends on |
|---|------|------|------------|
| 0–100 | *(reserved for project owner)* | Prioritized pre-work | — |
| 101 | [Automate report creation](101-task-automate-report-creation.md) | One command: NLCS++ XML in → styled Dekart report out | — |
| 102 | [Schema validation](102-task-schema-validation.md) | Reject invalid files before conversion, with actionable errors | — |
| 103 | [Converter hardening](103-task-converter-hardening.md) | Handle unknown categories and format variants gracefully | — |
| 104 | [Web upload app](104-task-web-upload-app.md) | Browser upload → progress → link to the Dekart map | 101, 102, 103 |
| 105 | [Drawing management](105-task-drawing-management.md) | List, replace, and delete uploaded drawings | 104 |
| 106 | [Revision comparison](106-task-revision-comparison.md) | View what changed between two revisions of a drawing | 101 |
| 107 | [Deployment & README](107-task-deployment-and-readme.md) | Reproducible setup instructions and a project README | 104 |

## Ordering rationale

Harden the pipeline first (101–103) so the conversion path is trustworthy, then expose
it through the web upload interface (104), add lifecycle management (105), build the
revision-comparison feature on top (106), and finish with packaging and documentation
(107).
