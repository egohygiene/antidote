---
schema: aether.architecture-document/v1
id: antidote-decisions
title: Antidote Decisions
kind: architecture-document
version: 0.2.0
status: provisional
owners:
  - egohygiene
created: 2026-08-27
updated: 2026-08-30
governed_by:
  - architecture-decisions
depends_on:
  - antidote-principles
  - antidote-epistemology
  - antidote-foundations
  - antidote-system
  - antidote-architecture
related:
  - antidote-purpose
  - antidote-vision
  - antidote-pillars
  - antidote-manifesto
supersedes: []
---

# Antidote Decisions

## Purpose

This file is the navigation index for durable Antidote decisions. Detailed
records live under [`docs/decisions/`](docs/decisions/). Issues coordinate work;
proposals explore alternatives; accepted records constrain implementation.

## Governance

Do not rewrite historical context to fit current understanding. Amend a record
for clarification that does not change its meaning; supersede it when the
decision changes materially. Prototype acceptance does not imply clinical,
study, or production approval.

## Decision index

| ID | Decision | Status | Record |
| --- | --- | --- | --- |
| ADR-0001 | Own research source in Antidote and consume Beacon by immutable revision | Superseded by ADR-0002 | [Record](docs/decisions/ADR-0001-research-ownership-and-beacon-consumption.md) |
| ADR-0002 | Own native publication execution and gate Pages deployment | Accepted | [Record](docs/decisions/ADR-0002-standalone-publication-and-pages.md) |
| ADR-0003 | Publish a catalog with honest future-format slots | Accepted | [Record](docs/decisions/ADR-0003-publication-hub-and-planned-slots.md) |
| ADR-0004 | Use a local-first desktop host with a Rust core and isolated model worker | Accepted for MVP | [Record](docs/decisions/ADR-0004-local-first-desktop-and-model-worker.md) |
| ADR-0005 | Project only explicitly consented context into a session | Accepted for MVP | [Record](docs/decisions/ADR-0005-consent-scoped-working-context.md) |
| ADR-0006 | Advance adaptation from rule-guided N-of-1 evidence | Accepted for MVP | [Record](docs/decisions/ADR-0006-adaptation-maturity-ladder.md) |
| ADR-0007 | Use append-only events and provenance-linked projections | Accepted for MVP | [Record](docs/decisions/ADR-0007-event-and-provenance-record.md) |
| ADR-0008 | Adopt Holon's exact-pinned site suite | Accepted | [Record](docs/decisions/ADR-0008-holon-site-suite-adoption.md) |

## Open decisions

- Minimum supported operating systems and GPU/CPU capability tiers.
- Storage encryption, key recovery, backup, and secure-deletion strategy.
- Initial model-adapter selection after hardware, license, remote-code, and
  control-adherence evaluation.
- Whether v0 analysis shares the generation worker or runs in a separate
  process.
- Which consent, safety, and data-classification controls require external
  review before non-developer use.
- Compatibility boundary for a future Ego Hygiene application integration.

## Evidence and uncertainty

- **Observed:** ADR-0001 through ADR-0003 and ADR-0008 govern the standalone
  publication system and exact-pinned shared site composition.
- **Decided for the prototype:** ADR-0004 through ADR-0007 define the first
  executable research-instrument boundary.
- **Proposed:** Machine-readable ADR frontmatter will follow the organization
  contract after Hygiene ratifies and versions it.
- **Open question:** Which MVP decisions should become active rather than
  provisional after the first vertical slice is demonstrated?

## Validation

Every index row resolves to one record and uses a unique identifier. The
records must agree with [ONTOLOGY.md](ONTOLOGY.md),
[SYSTEM.md](SYSTEM.md), [ARCHITECTURE.md](ARCHITECTURE.md), and the repository's
observed implementation state.
