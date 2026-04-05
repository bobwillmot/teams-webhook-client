# ADR 0001: Project Foundations

## Status

Accepted

## Context

This repository is a small Python utility for posting messages into Microsoft Teams from local scripts, CI jobs, and lightweight automation. The project needs a transport strategy, payload model, packaging approach, logging behavior, testing strategy, and basic repository hygiene that keep the default install simple while still supporting operational use.

## Decision

The project uses Microsoft Teams channel webhooks instead of Microsoft Graph for the primary integration path.

The default HTTP transport remains the Python standard library via `urllib`, while `requests` support is available as an optional runtime transport.

Retries use exponential backoff for `429`, `5xx`, and transient transport failures.

The CLI accepts raw JSON payloads from a file or stdin and supports both full Teams payloads and Adaptive Card documents.

Packaging is defined in `pyproject.toml` and exposes a `teams-post` console command.

CLI logging is written to stderr and supports `text`, `json`, and `none` formats.

Tests use the standard library `unittest` module.

The repository tracks request transcripts and implementation history under `docs/agent-transcripts/`, and long-lived design decisions under `docs/adr/`.

## Consequences

The project stays usable on a standard Python installation without mandatory third-party dependencies.

The tool is well-suited to Teams channels, CI workflows, and small automation scripts, but it is not designed for authenticated 1:1 chat or broader Graph-based messaging scenarios.

Operational behavior such as retries, payload ingestion, and structured logging is documented and testable.

Repository history is easier to navigate because conversational records and durable design decisions now live in dedicated documentation folders.