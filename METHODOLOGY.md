---
schema: aether.architecture-document/v1
id: antidote-methodology
title: Antidote Methodology
kind: architecture-document
version: 0.1.0
status: provisional
owners:
  - egohygiene
created: 2026-08-27
updated: 2026-08-27
governed_by:
  - architecture-methodology
depends_on:
  - antidote-principles
  - antidote-epistemology
  - antidote-ai-constitution
  - antidote-foundations
  - antidote-architecture
related:
  - antidote-purpose
  - antidote-vision
  - antidote-pillars
  - antidote-manifesto
supersedes: []
---

# Antidote Methodology

## Working method

Antidote combines design-science research with specification-, schema-, and
test-driven development:

> Experience → Question → Evidence → Model → Specify → Plan → Test → Implement
> → Observe → Interpret → Review → Publish → Reflect

## Research method

1. **Preserve the motivating observation:** Record lived experience as context
   without presenting it as efficacy evidence.
2. **Map adjacent evidence:** Separate music psychology, neuroscience,
   psychophysiology, psychedelic setting, adaptive intervention, generative
   audio, HCI, and provenance claims.
3. **Define falsifiable contributions:** State what semantic planning,
   moment-specificity, or longitudinal learning is expected to add.
4. **Build the transparent instrument:** Capture intended controls, generated
   output, realized features, exposure, and response independently.
5. **Begin within person:** Use repeated-session N-of-1 feasibility work before
   generalizing across participants.
6. **Predefine transitions:** Freeze protocol, variables, exclusions, stopping,
   analysis, and mutation rules before formal collection.
7. **Report layers honestly:** Distinguish control adherence, usability,
   experience, benefit, harm, mechanism, and clinical outcome.

## Engineering method

1. Inspect current source, architecture, risks, and neighboring ownership.
2. Update ontology or an accepted decision when a durable term or boundary
   changes.
3. Specify inputs, outputs, invariants, permissions, failures, versions, and
   acceptance criteria.
4. Encode stable process boundaries as independently validatable schemas.
5. Write unit, contract, integration, and failure tests before or with the
   narrow implementation.
6. Keep domain logic independent of Tauri, React, Python, model providers, and
   storage adapters.
7. Validate deterministic behavior and preserve relevant evidence.
8. Review architecture, safety, privacy, accessibility, licensing, operations,
   and scientific impact.
9. Merge through a reviewable branch; generated artifacts remain disposable.

## Prototype progression

| Level | Capability | Evidence required to advance |
| --- | --- | --- |
| 0 | Static contracts and fixtures | Schema and architecture consistency |
| 1 | Rule-guided local session | End-to-end provenance, cancellation, response capture, and failure tests |
| 2 | Descriptive N-of-1 summaries | Repeat-session integrity and understandable uncertainty |
| 3 | Human-selected advisory rankings | Comparative evidence and participant correction behavior |
| 4 | Constrained experimental adaptation | Frozen protocol, assignment validation, stop rules, and appropriate review |
| 5 | Optional multimodal research | Sensor consent, synchronization, calibration, data classification, and analysis plan |

## Quality gates

- Architecture frontmatter, identifiers, dependency graph, and links validate.
- JSON Schemas and fixtures validate independently of the desktop application.
- Rust, TypeScript, and Python boundaries share versioned contracts rather than
  duplicate domain rules.
- Model licenses, revisions, integrity hashes, remote code, hardware claims, and
  known failures are recorded.
- Context-projection, cancellation, negative response, deletion, and export
  failures receive first-class tests.
- Paper claims trace to source and experiment evidence.
- Human approval gates generation, playback, adaptation, external sharing, and
  publication where consequences warrant it.

## AI collaboration

AI may accelerate literature scouting, drafting, implementation, generation,
analysis, and verification within explicit scope. It must preserve provenance,
report uncertainty and failure, and never convert a recommendation or model
estimate into consent, an accepted decision, or a scientific claim.

## Evidence and uncertainty

- **Observed:** The repository already provides deterministic publication and
  validation interfaces.
- **Decided for the prototype:** Architecture and contracts precede framework
  scaffolding.
- **Proposed:** The first evaluation compares generic prompting, structured
  non-personalized journeys, and personal semantic journeys.
- **Open question:** Which parts of the local demo can supply publishable
  feasibility evidence without changing the protocol after implementation?
