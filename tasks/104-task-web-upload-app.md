# 104 — Web upload app

## Status: Not started

## Goal

The upload interface from
[docs/spec/03-system-architecture.md](../docs/spec/03-system-architecture.md): a user
opens a web page, uploads an NLCS++ XML file, sees progress and errors, and receives a
link to the interactive Dekart map of their drawing.

## Background

Tasks 101–103 provide the trusted pipeline (validate → convert → build report). This
task puts a browser front door on it. The user's mental model, per the docs: *"I
upload a drawing, I get a map."*

## Specifications

- Upload page: file selection + submit; NLCS++ XML only; files are hundreds of KB to a
  few MB.
- Server side orchestrates the pipeline: schema validation (102) → conversion (103) →
  report creation (101). Reuse those components; no duplicated pipeline logic.
- Feedback states, visible to the user: received → validating → converting → building
  map → done (with the report URL as a clickable link), or a failure state showing the
  validation/conversion error in drawer-readable form.
- Rejected files (invalid schema, wrong type, oversized) never reach Dekart.
- The app runs alongside the Dekart server as its own service (deployment context per
  docs/spec 03); the stack is chosen at pickup — note the repo already has a Node.js
  scaffold (`package.json`, `index.js`) and a Python converter, either direction is
  acceptable.
- Concurrent uploads must not interleave state (two users uploading simultaneously get
  two correct reports).

## Acceptance criteria

- Uploading `data/enexis_voorbeeld_3092025_1554.xml` through the browser produces a
  working report link; the map matches the task-101 output for the same file.
- Uploading an invalid file shows the validation error on the page; no report is
  created.
- Two uploads in quick succession both succeed with distinct reports.

## Dependencies

Tasks 101, 102, 103.

## Out of scope

- Authentication/authorization (single-team local deployment for now).
- Drawing lifecycle beyond a single upload (task 105).
- Automated/batch ingestion (future consideration in the docs).
