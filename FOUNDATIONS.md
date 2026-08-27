---
schema: aether.architecture-document/v1
id: antidote-foundations
title: Antidote Foundations
kind: architecture-document
version: 0.1.0
status: provisional
owners:
  - egohygiene
created: 2026-08-27
updated: 2026-08-27
governed_by:
  - architecture-foundations
depends_on:
  - antidote-purpose
  - antidote-principles
  - antidote-epistemology
related:
  - antidote-vision
  - antidote-pillars
  - antidote-manifesto
  - antidote-ai-constitution
supersedes: []
---

# Antidote Foundations

## Foundational assumptions

- A person's response to music depends on the individual, moment, environment,
  meaning, expectations, and realized audio; population-level mappings remain
  incomplete.
- A desired transition is an intention to explore, not a promised outcome.
- Semantic intent, acoustic realization, and felt response are related but
  distinct layers.
- Human-readable plans and controls improve agency and make scientific
  comparison possible.
- The local event record and approved files are canonical; summaries, personal
  models, dashboards, and publications are derived projections.
- Human authority, privacy, safety, accessibility, provenance, and scientific
  humility are architectural constraints.
- A standalone local prototype should remain useful even when Ego Hygiene adds
  broader context or hosted services.

## Enduring constraints

- Do not make a mutable default branch, sibling checkout, or unpublished API a
  runtime dependency.
- Do not send unrestricted journal, therapy-chat, physiological, or identity
  history to a model worker.
- Do not treat audio-model prompts, embeddings, or analyzer outputs as canonical
  descriptions of a person.
- Do not hide generation parameters, model revisions, warnings, or failed runs.
- Do not enable online experimental optimization without a reviewed protocol
  and explicit consent.
- Do not commit private participant records, secrets, proprietary model weights,
  or unreviewed exports to the public repository.
- Do not claim cross-platform, offline, real-time, sensor, or clinical support
  beyond verified evidence.

## Trust zones

| Zone | Trust boundary |
| --- | --- |
| Human input | May be sensitive, ambiguous, incomplete, or corrected later |
| Local application core | Holds consent, canonical events, state transitions, and policy authority |
| Local model worker | Executes narrow generation and analysis operations without unrestricted storage access |
| Model artifacts | Third-party code and weights require license, integrity, and remote-code review |
| Generated media | Untrusted derived output until validated, hashed, reviewed, and intentionally played or shared |
| Optional external services | Separate availability, authentication, privacy, cost, and replacement boundary |
| Research/publication output | Must exclude sensitive source material and preserve claim/evidence distinctions |

## Success properties

The foundation is healthy when interpretable intent, moment-specific journeys,
local agency, reproducible evidence, and cautious longitudinal learning can be
tested independently and composed without hidden authority transfer.

## Evidence and uncertainty

- **Observed:** The publication system already separates canonical sources from
  disposable build outputs and pins cross-repository dependencies.
- **Decided for the prototype:** The runtime adopts the same ownership and
  provenance discipline.
- **Proposed:** Encrypted local storage and signed export manifests are later
  hardening steps, not current capabilities.
- **Open question:** Which storage-encryption approach best preserves portable
  local ownership and recoverability across supported desktops?
