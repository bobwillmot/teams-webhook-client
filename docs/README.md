# Documentation

This folder holds repository documentation that is more durable or more detailed than the project root `README.md`.

## Layout

- `adr/`: architecture decision records for durable technical and workflow choices.
- `agent-transcripts/`: dated request transcripts, implementation history, and chat summaries.

## Naming

- Keep conventional index files as `README.md`.
- Name ADRs as numbered kebab-case files such as `0001-short-title.md`.
- Name agent transcript files with the session date as `yyyy-mm-dd.md`.
- Put new general project documentation under `docs/` using lowercase hyphenated Markdown filenames by default.

## Tracking Rules

- Record long-lived technical decisions in `docs/adr/`.
- Record dated request history and implementation notes in `docs/agent-transcripts/`.
- Avoid adding new top-level tracking Markdown files when the content belongs in one of these folders.
