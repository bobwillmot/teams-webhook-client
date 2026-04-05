# ADR 0003: Documentation Index Convention

## Status

Accepted

## Context

The repository now uses `docs/adr/` for durable decisions and `docs/agent-transcripts/` for dated work history, but those folder-level conventions were only documented inside each subdirectory.

Without a top-level documentation index, contributors have to infer where new documentation belongs and which naming rules apply across the `docs/` tree.

## Decision

The repository uses `docs/README.md` as the canonical entry point for documentation layout and naming rules.

The root `README.md` and documentation subfolder `README.md` files should refer readers to `docs/README.md` instead of duplicating the full convention.

General project documentation added under `docs/` should follow lowercase hyphenated Markdown filenames unless an established convention requires otherwise.

## Consequences

Documentation placement and naming rules are easier to discover from a single entry point.

Future updates to documentation conventions can be made in one primary file and linked from other documentation.

The `docs/` tree stays consistent with the repository's ADR and transcript tracking conventions.
