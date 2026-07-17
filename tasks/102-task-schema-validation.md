# 102 — Schema validation

## Status: Not started

## Goal

Validate an NLCS++ XML file against the official schema before conversion, rejecting
invalid files with errors a drawer can act on. This implements the "Validate" step of
the conversion pipeline in
[docs/spec/03-system-architecture.md](../docs/spec/03-system-architecture.md).

## Background

The schema ships with the repo: `data/NLCS_Netbeheer.xsd` (with the Enexis keuzelijst
variant `data/NLCS_NetbeheerEnexisV12.1Import_Keuzelijst.xsd`). The converter
currently assumes well-formed, schema-valid input; garbage reaching the map would
erode trust in the viewer.

## Specifications

- A validation step usable both standalone (validate a file, report result) and as a
  gate inside the pipeline (invalid input stops conversion).
- Validate against the NLCS Netbeheer XSD; support selecting a netbeheerder-specific
  keuzelijst schema when applicable.
- Error output must be actionable: element/line location and a human-readable message,
  not a raw parser dump. Multiple errors should be collected where feasible rather
  than failing on the first.
- Well-formedness errors (broken XML) and schema violations are reported distinctly.
- Valid files pass through unchanged; validation must not modify the input.

## Acceptance criteria

- All three example files in `data/` validate successfully.
- A deliberately corrupted copy (e.g. removed required element, wrong enum value,
  malformed tag) is rejected with a message naming the offending element/location.
- The pipeline from task 101 refuses to build a report for an invalid file once this
  gate is wired in.

## Dependencies

None. (Task 101 integrates it once both exist.)

## Out of scope

- Semantic/domain validation beyond the schema (e.g. topology checks).
- Web-facing error presentation (task 104).
