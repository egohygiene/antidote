# ADR-0007: Use append-only events and provenance-linked projections

- Status: Accepted for MVP
- Date: 2026-08-27
- Decision owners: Ego Hygiene / Antidote
- Applies to: Local state, reproducibility, adaptation, and research export

## Context

Antidote must distinguish what the person entered, what the system derived,
what a model generated, what was actually played, what the person reported,
and what later interpretation changed. Updating one mutable session row would
erase lineage and make personal-model changes difficult to audit or reverse.

The system must also support privacy-aware retention; append-only does not mean
that sensitive payloads must remain forever.

## Decision

The local record uses immutable ordered events for actions and observations.
Large or sensitive payloads live in separately classified, content-addressed
files referenced by events. Current session state, working context, personal
models, dashboards, and exports are versioned projections linked to their source
events and derivation versions.

Every generation run records the input-plan hash, model and code revisions,
parameters, seed when supported, device class, timing, warnings, and output
hashes. Exposure events identify what was actually played. Response events
remain separate from acoustic-analysis events.

Research export follows W3C PROV concepts and may package approved runs as
RO-Crate. Deletion or redaction produces an auditable tombstone and makes
affected projections non-reproducible or partial rather than silently altering
history.

## Consequences

- Derived state can be rebuilt, compared, corrected, or rolled back.
- Personal-model updates remain attributable to evidence.
- SQLite transactions are sufficient for the MVP; audio does not need to live
  in database blobs.
- Retention, encryption, backup, key recovery, secure deletion, and projection
  invalidation require explicit implementation and tests.
- Event schema evolution must preserve compatibility or provide deterministic
  migration.

## Reconsider when

- measured complexity outweighs provenance benefits for the minimum vertical
  slice;
- an alternative local record preserves equivalent lineage, correction, and
  deletion semantics;
- privacy review requires a different payload or tombstone model.

## Implementation evidence

Issue #12 implements the first adapter under `crates/antidote-store/`:
versioned SQLite migrations, immutable and digest-verified event envelopes,
optimistic/idempotent appends, transactional projection rebuilding with
source-event lineage, a classified payload-reference registry, and atomic
content-addressed files. Focused tests cover interruption, rollback, stale
writes, exact retries, projection recovery, abandoned temporary files, and hash
corruption.

This evidence activates only the integrity and local-recovery portion of the
decision. Encryption, keys, backup, retention enforcement, tombstones, secure
deletion, and non-developer privacy review remain unresolved.
