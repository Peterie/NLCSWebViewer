# 107 — Deployment & README

## Goal

Anyone with the repo can get the whole system running locally from written
instructions alone: Dekart server, dekart CLI, pipeline, and (once task 104 exists)
the web upload app — plus a proper project README.

## Background

The current working setup was assembled interactively and is documented nowhere in the
repo: Dekart runs via **udocker** (rootless, no Docker daemon — required because the
machine has no sudo), the dekart CLI lives in a Python venv with the local snapshot
capability installed, and the geosql skill assists agent workflows. None of that is
reproducible from the repository today.

## Specifications

- **README.md** at repo root: what the project is (one paragraph, linking to
  docs/spec), repository layout (data/, docs/, resources/, scripts/, tasks/),
  quick-start pointer to the deployment guide, and how the tasks/ folder works
  (including the 0–100 reserved range).
- **Deployment guide** covering, as verified steps:
  - Dekart server: standard route (Docker, port 8080) *and* the rootless route
    (udocker) for machines without root, including where Dekart's state lives;
  - dekart CLI: install in a venv, `dekart init` against localhost, the local
    snapshot capability for headless rendering;
  - pipeline usage: converter invocation, and the task-101 command once it exists;
  - the web app (task 104): how to start it and where to reach it.
- Instructions must be tested by following them on a clean checkout (fresh venv, fresh
  Dekart state) — not transcribed from memory.
- Keep the established documentation conventions: English, Dutch domain terms, no
  pinned versions where avoidable.

## Acceptance criteria

- A newcomer following only README + deployment guide reaches a running Dekart with
  one example drawing viewable as a report.
- Every command in the guide has been executed as written during this task.
- README links (docs/spec, tasks/overview.md) resolve on GitHub.

## Dependencies

Task 104 (to document the app); the Dekart/CLI portions can be drafted earlier.

## Out of scope

- Production hosting, TLS, SSO/authentication.
- CI/CD pipelines.
