# Design Decisions

Date: 2026-04-04

## Chosen Interface

The project targets Microsoft Teams channel webhooks rather than Microsoft Graph.

Reason: webhooks are the simplest path for local scripts, CI jobs, and small Python programs that need to post messages without implementing Microsoft Entra authentication flows.

Consequence: this tool is best suited to posting into Teams channels, not normal 1:1 chats.

## Transport Design

The default HTTP transport remains the Python standard library via `urllib`.

Reason: this keeps the base install dependency-free.

Consequence: the project works out of the box on a standard Python install, while still supporting `requests` when a caller prefers it.

## Optional Requests Support

`requests` support is implemented as an optional transport selected at runtime.

Reason: some users prefer `requests` for operational familiarity, proxy handling, and debugging, but it should not be mandatory.

Consequence: the package exposes an optional dependency group instead of adding `requests` to the base dependency set.

## Retry Strategy

Retries use exponential backoff for `429` and `5xx` failures, plus transient connection errors.

Reason: these are the failure modes most likely to be temporary and recoverable.

Consequence: client-side retries improve reliability in CI and automation without retrying clear caller errors such as invalid payloads.

## Payload Input Format

The CLI accepts raw JSON payloads from a file or stdin and supports two modes: `teams` and `adaptive-card`.

Reason: callers sometimes already have full Teams webhook payloads, while other callers only want to supply Adaptive Card JSON and let the tool wrap it.

Consequence: the CLI covers both common integration shapes without requiring a second utility.

## Logging Format

CLI logging is written to stderr and supports `text`, `json`, or `none`.

Reason: stderr logging is easier to separate from command output, and JSON lines are easier for CI systems to parse.

Consequence: the command remains human-friendly by default while supporting machine-readable automation logs.

## Packaging Choice

Packaging is provided through `pyproject.toml` with a `teams-post` console script.

Reason: this is the smallest modern packaging step needed to make the tool installable and runnable as a named command.

Consequence: users can install locally with `python -m pip install -e .` and use `teams-post` without restructuring the project into a larger package layout.

## Environment Loading

The Makefile loads `TEAMS_WEBHOOK_URL` from a local `.env` file when present.

Reason: repeated shell exports are unnecessary overhead for a small automation project, and Make is a convenient entry point for common commands.

Consequence: local usage is simpler, while explicit shell exports still work when preferred.

## Test Strategy

Smoke tests are implemented with the standard library `unittest` module.

Reason: the project already works without third-party dependencies, so tests should preserve that property.

Consequence: test coverage stays lightweight and easy to run through `make test`.

## Repository Hygiene

Local environment files, virtual environments, and build artifacts are ignored through `.gitignore`.

Reason: this project generates local state that should not normally be committed.

Consequence: contributors can create `.env` and `.venv` locally without polluting version control.

## CI Integration

A sample GitHub Actions workflow posts a success or failure message to Teams after CI completes.

Reason: the project is intended for automation scenarios, so a concrete CI example reduces setup friction.

Consequence: users can adapt the sample quickly, but they still need to provide a `TEAMS_WEBHOOK_URL` repository secret.

## Local Environment File

A local `.env` file is created with a placeholder webhook value.

Reason: the Make-based workflow is easier to start using when the file already exists.

Consequence: the placeholder must be replaced before real posting, and `.gitignore` prevents the local secret from being committed.

## Broader Test Coverage

Tests now cover retry sequencing and CLI JSON logger output in addition to payload construction.

Reason: those behaviors are operationally important and easy to regress during CLI changes.

Consequence: `make test` gives better confidence that the automation behavior still matches expectations.
