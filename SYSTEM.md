---
schema: aether.architecture-document/v1
id: antidote-system
title: Antidote System
kind: architecture-document
version: 0.5.0
status: provisional
owners:
  - egohygiene
created: 2026-08-27
updated: 2026-08-29
governed_by:
  - architecture-system
depends_on:
  - antidote-foundations
  - antidote-ontology
related:
  - antidote-purpose
  - antidote-vision
  - antidote-principles
  - antidote-pillars
supersedes: []
---

# Antidote System

## Purpose and scope

This document identifies Antidote's logical systems and responsibilities. It
answers what the major systems do. [ARCHITECTURE.md](ARCHITECTURE.md) owns their
structural organization, process boundaries, and dependency direction.

## System inventory

| System | Current state | Responsibility |
| --- | --- | --- |
| Research workspace | Implemented | Owns manuscript, bibliography, source records, claim ledger, figures, protocols, and approved study evidence |
| Publication system | Implemented | Builds and validates PDF, accessible HTML, source archive, provenance, and the gated publication hub |
| Desktop experience | Workspace scaffold | Pinned host and honest status view exist; session interaction remains target |
| Consent and context system | Domain core + local persistence | Grants and reviewed projections have fail-closed policies plus rebuildable SQLite views; UI remains target |
| State and intent system | Authoritative domain core | Moment lineage and one-session transition rules execute independently of frameworks |
| Journey planning system | Authoritative domain core | Draft plans and exact human approval are distinct executable states; a planner remains target |
| Generation orchestration | Core + supervised adapter | Rust commands own start and terminal events; the bounded supervisor negotiates, checks capabilities, delivers progress, cancels, times out, verifies artifacts, and restarts |
| Model worker | Deterministic mock supervised | The packaged Python process exercises all v1 operations through the Rust supervisor; real model adapters remain target |
| Audio realization system | Target | Validates, stores, assembles, previews, plays, stops, and exports audio without redefining model behavior |
| Response system | Authoritative domain core | Actual exposure and felt response remain distinct, with response consent and safety-event transitions |
| Personal learning system | Authoritative proposal core | Evidence-scoped updates require separate proposal and acceptance; failed or rejected proposals preserve the prior snapshot |
| Provenance and export system | Storage lineage foundation | Immutable event hashes, content addresses, and projection source-event lineage exist; research-export packaging remains target |

“Domain core + local persistence” means pure Rust commands append through a
tested SQLite adapter and derive inspectable views. It does not claim desktop
composition, encryption/privacy readiness, a real audio
model, playback adapter, complete journey, or therapeutic effect.

## Primary interaction

1. The person starts a moment-specific session and records only the state detail
   they choose.
2. They choose a desired transition, duration, meanings, inclusions,
   exclusions, and optional context sources.
3. The consent system shows the exact working projection and allowed purpose.
4. The planner proposes a journey; the person edits or accepts it.
5. The orchestrator converts the accepted plan into an immutable generation
   specification and invokes a capability-compatible local worker.
6. The returned artifact is hashed and analyzed before it becomes playable.
7. The person controls playback and may stop, skip, or mark a safety event.
8. Immediate and optional later responses are recorded separately.
9. The system proposes any personal-model update and preserves its evidence.

## External systems

- Ego Hygiene journal, therapy-chat, and product context through future
  explicitly consented, versioned projections;
- Beacon for optional publication profile inspection, validation, and packaging;
- Relay and Egolint for repository workflow and conformance evidence;
- replaceable local audio-generation and analysis projects;
- optional operating-system audio, GPU, filesystem, export, or sensor adapters.

External systems are integrations, not hidden implementation units. Every
integration requires version, authorization, data, error, availability,
licensing, and replacement boundaries appropriate to its risk.

## Failure model

- Invalid or ambiguous consent prevents context projection.
- Unsupported model controls fail before generation or produce explicit
  downgrade warnings requiring review.
- Partial generation never masquerades as a completed artifact.
- Playback always exposes stop and recovery controls.
- A safety event halts automatic continuation and is never scored as successful
  engagement.
- Failed personal-model updates preserve the prior snapshot.
- Export fails closed when classification, redaction, hashes, or provenance are
  incomplete.

## Evidence and uncertainty

- **Observed:** Research and publication systems, the pure Rust session core,
  local event/artifact persistence adapters, and deterministic mock model
  worker and Rust process supervisor have integrity, recovery, transition,
  replay, lineage, cancellation, timeout, restart, redaction, and failure-class
  tests. Desktop command composition remains separate work.
- **Decided for the prototype:** The first executable vertical slice stops at
  rule-guided generation, playback, response capture, and inspectable history.
- **Proposed:** Advisory personalization and optional sensors follow only after
  the base record is reliable.
- **Open question:** Whether analysis belongs in the generation worker or a
  separately sandboxed worker after the first model comparison.
