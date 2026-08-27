---
schema: aether.architecture-document/v1
id: antidote-system
title: Antidote System
kind: architecture-document
version: 0.1.0
status: provisional
owners:
  - egohygiene
created: 2026-08-27
updated: 2026-08-27
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
| Desktop experience | Target | Guides check-in, context approval, semantic editing, journey review, generation, playback, and response capture |
| Consent and context system | Contract scaffold | Records scoped grants and derives inspectable working projections from approved sources |
| State and intent system | Contract scaffold | Represents the moment, current state, desired transition, time horizon, inclusions, exclusions, and uncertainty |
| Journey planning system | Contract scaffold | Produces editable strategies, stages, semantic intent, acoustic controls, and safety constraints |
| Generation orchestration | Contract scaffold | Validates immutable generation specs, schedules work, reports progress, handles cancellation, and records outcomes |
| Model worker | Target | Loads pinned adapters, generates audio, analyzes artifacts, reports capabilities, and returns warnings through a narrow protocol |
| Audio realization system | Target | Validates, stores, assembles, previews, plays, stops, and exports audio without redefining model behavior |
| Response system | Contract scaffold | Separates intended, expressed, felt, immediate, adverse, and later response observations |
| Personal learning system | Target | Builds versioned within-person summaries and advisory mappings from approved evidence |
| Provenance and export system | Contract scaffold | Hashes artifacts, records entity/activity/agent lineage, and creates privacy-reviewed research exports |

“Contract scaffold” means a documented boundary and initial JSON Schema exist;
it does not claim an executable implementation.

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

- **Observed:** Research and publication systems are implemented and validated
  in CI.
- **Decided for the prototype:** The first executable vertical slice stops at
  rule-guided generation, playback, response capture, and inspectable history.
- **Proposed:** Advisory personalization and optional sensors follow only after
  the base record is reliable.
- **Open question:** Whether analysis belongs in the generation worker or a
  separately sandboxed worker after the first model comparison.
