---
schema: aether.architecture-document/v1
id: antidote-roadmap
title: Antidote Roadmap
kind: architecture-document
version: 0.5.0
status: provisional
owners:
  - egohygiene
created: 2026-08-26
updated: 2026-08-29
governed_by:
  - architecture-roadmap
depends_on:
  - antidote-vision
  - antidote-pillars
  - antidote-architecture
  - antidote-decisions
related:
  - antidote-purpose
  - antidote-principles
  - antidote-epistemology
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
updated: 2026-08-29
-->

## 2026-08-29 execution snapshot

> This evidence-reconciled snapshot is the issue-generation and visual-roadmap
> handoff. Generated HTML, JSON, progress views, issue plans, and commit lists
> remain projections of this source.

**Lifecycle:** research draft with prototype architecture bootstrap

**Current gate:** The MVP implementation sequence is deliberately paused after
issue #16. The paper-first workstream has frozen its evidence, novelty, thesis,
and section boundaries through issue #35 and now proves the continuous
publication loop before writing the design/protocol manuscript through issue
#48.

**North-star outcome:** An interpretable local research instrument that turns a
person's explicitly consented moment and sonic language into a reproducible
audio journey, records the response, and learns cautiously without making
clinical claims.

### Quest line

<!-- roadmap-step
id: ANT-Q01
status: complete
depends_on: []
issues: ["egohygiene/empathy#71", "egohygiene/antidote#2"]
-->

#### ANT-Q01 — Graduate the research workspace

**State:** `complete`

**Outcome:** Antidote has one standalone canonical home, immutable migration
provenance, and a reproducible native build derived from Beacon's profile.

**Exit criteria:**

- [x] Standalone bootstrap pull request is merged.
- [x] Every Empathy source file has a recorded disposition.
- [x] The manuscript builds and validates natively in both Beacon themes.
- [x] Make and Task share one project-owned build contract.
- [x] Empathy is migration history, not a runtime dependency.

<!-- roadmap-step
id: ANT-Q01A
status: active
depends_on: [ANT-Q01]
issues: ["egohygiene/antidote#4"]
-->

#### ANT-Q01A — Activate and verify the publication hub

**State:** `active`

**Outcome:** The custom Antidote domain provides stable paper, planned magazine,
download, manifest, and integrity routes through a gated product-owned workflow.

**Exit criteria:**

- [x] The repository contains the route and availability contract.
- [x] Pull requests validate the complete hub without deploying it.
- [x] Canonical metadata targets `https://antidote.egohygiene.io/`.
- [ ] Repository Pages settings, DNS, TLS, deployment gate, and live routes are
  verified together and recorded.

<!-- roadmap-step
id: ANT-Q02
status: complete
depends_on: [ANT-Q01]
issues: ["egohygiene/antidote#32", "egohygiene/antidote#33", "egohygiene/antidote#34", "egohygiene/antidote#35"]
-->

#### ANT-Q02 — Verify literature and novelty boundaries

**State:** `complete`

**Outcome:** A primary-source atlas separates overlap, open gaps, architecture
precedents, and candidate contribution claims across the research streams.

**Exit criteria:**

- [x] Each promoted bibliography entry has a primary-source assessment.
- [x] MindMelody and other adaptive-audio comparators have a structured overlap
  analysis in the [issue #34 comparator and novelty matrix](research/notes/COMPARATOR_NOVELTY_MATRIX.md).
- [x] Architecture references are separated from implementation documentation
  in the [issue #33 evidence map](research/notes/ADAPTIVE_AUDIO_ARCHITECTURE.md).
- [x] The contribution statement is rewritten from verified evidence in the
  [issue #35 manuscript contract](paper/manuscript-contract.json) and
  [claim ledger](research/notes/CLAIM_LEDGER.md).
- [x] Unsupported efficacy and deterministic mechanism language is prohibited
  by the manuscript contract and claim ledger.

<!-- roadmap-step
id: ANT-Q02B
status: active
depends_on: [ANT-Q01A, ANT-Q02]
issues: ["egohygiene/antidote#31", "egohygiene/antidote#36", "egohygiene/antidote#37", "egohygiene/antidote#38", "egohygiene/antidote#39", "egohygiene/antidote#40", "egohygiene/antidote#41", "egohygiene/antidote#42", "egohygiene/antidote#43", "egohygiene/antidote#44", "egohygiene/antidote#45", "egohygiene/antidote#46", "egohygiene/antidote#47", "egohygiene/antidote#48"]
-->

#### ANT-Q02B — Write and continuously publish the first paper

**State:** `active`

**Outcome:** A source-governed design/protocol manuscript remains continuously
reviewable through reproducible PDF, accessible web, provenance, arXiv-source,
and custom-domain Pages projections, then advances through an explicit
feasibility-revision gate when qualifying evidence exists.

**Execution source:** [`paper/roadmap.md`](paper/roadmap.md)

**Exit criteria:**

- [x] The living source atlas and broader bibliography shelf are preserved
  without treating every entry as cited evidence.
- [x] Modeling, adaptive-control, real-time audio, and provenance architecture
  claims have primary-source or normative-standard anchors.
- [x] The novelty matrix supports the frozen thesis and contribution boundary.
- [ ] Every canonical manuscript section completes its evidence-specific issue.
- [ ] Figures and tables have governed source, captions, alt text, placement,
  and placeholder/final status.
- [ ] Table of contents, cross-references, PDF, accessible HTML, provenance, and
  source packaging pass the native build.
- [ ] The custom-domain web paper and PDF expose the reviewed source revision.
- [ ] The design/protocol manuscript contains no invented result or unsupported
  clinical or neurological-mechanism claim.

<!-- roadmap-step
id: ANT-Q02A
status: complete
depends_on: [ANT-Q01]
issues: ["egohygiene/antidote#7"]
-->

#### ANT-Q02A — Establish the architecture corpus and MVP contracts

**State:** `complete`

**Outcome:** Antidote has one coherent human-readable architecture graph,
accepted MVP boundaries, and a machine-readable interoperability starting
point.

**Exit criteria:**

- [x] All 18 Aether-shaped architecture documents exist, cross-link, and match
  Antidote's bounded context.
- [x] Existing publication ADRs and MVP ADRs resolve through one decision index.
- [x] Consent, moment context, journey, generation, and response schemas validate.
- [x] Repository and worker boundaries have honest README contracts.
- [x] The full repository validation suite passes on the review branch.

<!-- roadmap-step
id: ANT-Q03
status: active
depends_on: [ANT-Q02A]
issues: ["egohygiene/antidote#9", "egohygiene/antidote#10", "egohygiene/antidote#11", "egohygiene/antidote#12", "egohygiene/antidote#13", "egohygiene/antidote#14", "egohygiene/antidote#15", "egohygiene/antidote#16", "egohygiene/antidote#17", "egohygiene/antidote#18"]
-->

#### ANT-Q03 — Bootstrap the local application foundation

**State:** `active`

**Execution note:** Paused by maintainer direction after issue #16 while
ANT-Q02B is active. Issues #17 and #18 remain the next valid MVP sequence; the
pause does not change their architecture or acceptance criteria.

**Outcome:** A minimal Tauri/React shell, framework-independent Rust core,
SQLite adapter, and mock model worker execute one contract-tested session
without real generation.

**Current evidence:** Workspaces, shared contracts, the authoritative session
core and generation orchestrator, append-only local persistence, deterministic
mock worker, bounded Rust process supervision, and the accessible desktop
session are implemented through issue #16. The UI now composes exact consented
context, editable and approved journey revisions, immutable generation specs,
progress/cancellation/recovery, deliberate synthetic playback, adverse stops,
and response capture. Provenance export, packaging, and the remaining epic
integration evidence stay in the active sequence; the outcome above is not yet
complete.

**Exit criteria:**

- [x] Workspaces are reproducibly bootstrapped with pinned dependencies.
- [x] Generated Rust, TypeScript, and Python types agree with canonical schemas.
- [x] Consent, event, projection, journey, generation-job, cancellation, and
  response transitions pass unit and contract tests.
- [x] Synthetic fixtures contain no private or clinical data.
- [x] Local development and recovery are documented.

<!-- roadmap-step
id: ANT-Q04
status: planned
depends_on: [ANT-Q03, ANT-Q02]
issues: []
-->

#### ANT-Q04 — Complete the transparent audio vertical slice

**State:** `planned`

**Outcome:** One reviewed local model adapter turns an accepted journey into a
hashed audio artifact, supports deliberate playback and cancellation, captures
response, and exports provenance.

**Exit criteria:**

- [ ] Adapter license, model revision, integrity, remote-code, hardware, and
  output-rights assessment is recorded.
- [ ] Unsupported controls downgrade visibly or fail before generation.
- [ ] Stop, cancel, partial-output, model failure, and adverse-response paths
  pass end-to-end tests.
- [ ] Every run records its plan, parameters, artifact hashes, feature report,
  warnings, exposure, and response.
- [ ] No autonomous personalization is enabled.

<!-- roadmap-step
id: ANT-Q05
status: planned
depends_on: [ANT-Q02, ANT-Q04]
issues: []
-->

#### ANT-Q05 — Freeze the N-of-1 feasibility protocol

**State:** `planned`

**Outcome:** Variables, conditions, measures, assignments, analysis, safety,
consent, retention, and provenance are explicit before formal collection.

**Exit criteria:**

- [ ] Protocol and analysis plan are versioned.
- [ ] Conditions compare generic prompting, structured non-personalized
  journeys, and personal semantic journeys where feasible.
- [ ] Data schemas separate subjective, acoustic, behavioral, and optional
  physiological measures.
- [ ] Ethics, privacy, exclusion, and stop requirements are resolved.
- [ ] A pilot stop/go decision is recorded.

<!-- roadmap-step
id: ANT-Q06
status: planned
depends_on: [ANT-Q05]
issues: []
-->

#### ANT-Q06 — Run and report the feasibility study

**State:** `planned`

**Outcome:** The manuscript reports auditable observations and appropriately
bounded interpretations from the frozen protocol.

**Exit criteria:**

- [ ] Collection and analysis follow frozen versions or disclose mutations.
- [ ] Results are reproducible from approved, non-sensitive inputs.
- [ ] Felt response remains distinct from expressed emotion and acoustic
  adherence.
- [ ] Negative and null observations remain visible.
- [ ] Claims trace to evidence in the claim ledger.

<!-- roadmap-step
id: ANT-Q07
status: planned
depends_on: [ANT-Q01A, ANT-Q02]
issues: ["egohygiene/antidote#5"]
-->

#### ANT-Q07 — Author the first magazine edition

**State:** `planned`

**Outcome:** A real, evidence-bounded visual edition converts the paper's key
sections into understandable single-page insights without replacing the paper
as scientific source of truth.

**Exit criteria:**

- [ ] The edition has governed structured source and an editorial thesis.
- [ ] Every scientific statement remains traceable to the paper or source
  record.
- [ ] Native builds produce verified web, digital, and print projections.
- [ ] Accessibility, print, provenance, and checksum checks pass.
- [ ] The planned hub slot becomes available atomically with real artifacts.

### Roadmap-to-issue handoff

- A step is complete only when its exit criteria and required evidence are
  satisfied; commit count never determines progress.
- `ready` steps may become implementation issues after duplicate review.
- `planned` steps remain preview-only unless a reviewer deliberately activates
  them.
- Pull requests and commits should reference the relevant `Roadmap-Step`.
- Public projections use allowlisted build-time evidence and never expose
  private research plans, participant data, tokens, or consent records.

<!-- END ROADMAP EXECUTION SNAPSHOT -->

## Sequencing rationale

The paper may progress as a design/protocol manuscript while implementation is
paused, but it must preserve observed implementation status. A real generative
adapter must not harden scientific claims or experimental conditions
prematurely. The mock vertical slice tests authority and provenance first; the
real model slice tests technical feasibility; only then is the study protocol
frozen and run.

## Evidence and uncertainty

- **Observed:** Research and publication foundations are present; no runtime
  prototype or formal study data exists.
- **Decided for this roadmap:** The next executable milestone is a mock local
  contract slice, not a clinical or adaptive system.
- **Proposed:** Architecture work may generate issues after this corpus is
  reviewed.
- **Open question:** Whether model evaluation should be its own quest between
  the mock slice and full audio vertical slice.
