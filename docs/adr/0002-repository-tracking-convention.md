# ADR 0002: Repository Tracking Convention

## Status

Accepted

## Context

The repository previously stored project conversation history and design notes in top-level Markdown files. That approach worked for a single session, but it does not scale cleanly as more requests, implementation updates, and long-lived decisions accumulate.

The project needs a consistent in-repo convention for recording short-lived request history separately from durable technical decisions.

## Decision

Agent request transcripts, chat summaries, and implementation history are stored as dated Markdown files under `docs/agent-transcripts/`.

Long-lived technical and workflow decisions are stored as numbered ADRs under `docs/adr/`.

Top-level ad hoc tracking files should not be added for these purposes unless a stronger repository convention replaces this one later.

## Consequences

Repository history is easier to navigate because transient work logs and durable decisions are separated.

Future sessions can append new records without editing older transcripts or renumbering prior ADRs.

The root of the repository stays focused on source, configuration, and primary project documentation rather than accumulating session notes.