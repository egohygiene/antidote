---
schema: aether.architecture-document/v1
id: antidote-roadmap
title: Antidote Roadmap
kind: architecture-document
version: 0.1.0
status: provisional
owners:
  - egohygiene
created: 2026-08-26
updated: 2026-08-26
governed_by:
  - architecture-roadmap
depends_on:
  - antidote-architecture
related:
  - antidote-research-ownership
supersedes: []
---

# Antidote Roadmap

<!-- BEGIN ROADMAP EXECUTION SNAPSHOT -->
<!-- roadmap-manifest
schema: hygiene.roadmap/v1alpha1
repository: egohygiene/antidote
visibility: public
publication: central
route: /roadmap/antidote/
updated: 2026-08-26
-->
## 2026-08-26 execution snapshot

**Lifecycle:** manuscript development

**Current gate:** Establish a verified novelty map before freezing the first
study design.

**North-star outcome:** A careful, interpretable, longitudinal account of the
relationship among semantic intent, realized acoustic structure, and an
individual's measured response.

### Quest line

<!-- roadmap-step
id: ANT-Q01
status: completed
depends_on: []
issues: ["egohygiene/empathy#71", "egohygiene/antidote#2"]
-->
#### ANT-Q01 — Graduate the research workspace

**Outcome:** Antidote has one standalone canonical home, immutable migration
provenance, and a reproducible Beacon build.

**Exit criteria:**

- [x] Standalone bootstrap pull request is merged.
- [x] Every Empathy source file has a recorded disposition.
- [x] The manuscript builds and validates natively in both Beacon themes.
- [x] Make and Task share one project-owned build contract without Beacon.
- [x] Pages, PDF, web, source, and provenance projections are reviewable.
- [x] Empathy retains only migration history after the standalone source lands.

<!-- roadmap-step
id: ANT-Q02
status: in-progress
depends_on: [ANT-Q01]
issues: []
-->
#### ANT-Q02 — Verify the literature and novelty boundary

**Outcome:** A primary-source literature matrix separates overlap, open gaps,
and candidate contribution claims across the five research streams.

**Exit criteria:**

- [ ] Each bibliography entry has a source assessment.
- [ ] MindMelody and other closed-loop comparators have a structured overlap
  analysis.
- [ ] The contribution statement is rewritten from verified evidence.
- [ ] Unsupported efficacy and mechanism language is absent.

<!-- roadmap-step
id: ANT-Q03
status: planned
depends_on: [ANT-Q02]
issues: []
-->
#### ANT-Q03 — Freeze the N-of-1 feasibility protocol

**Outcome:** Variables, measures, mutations, analysis, safety, consent, and
provenance rules are explicit before formal data collection.

**Exit criteria:**

- [ ] Protocol and analysis plan are versioned.
- [ ] Data schema separates subjective, acoustic, behavioral, and optional
  physiological measures.
- [ ] Ethics and privacy review requirements are resolved.
- [ ] A pilot stop/go decision is recorded.

<!-- roadmap-step
id: ANT-Q04
status: planned
depends_on: [ANT-Q03]
issues: []
-->
#### ANT-Q04 — Run and report the feasibility study

**Outcome:** The manuscript reports auditable observations and appropriately
bounded interpretations from the frozen protocol.

**Exit criteria:**

- [ ] Collection and analysis follow the frozen versions or disclose changes.
- [ ] Results are reproducible from approved, non-sensitive inputs.
- [ ] Claims trace to evidence in the claim ledger.
- [ ] Beacon submission-ready validation passes.

<!-- END ROADMAP EXECUTION SNAPSHOT -->
