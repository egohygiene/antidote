# Antidote continuity

This file is the durable handoff checkpoint for work that spans conversations.
It summarizes current execution state; it does not override `AGENTS.md`, the
architecture corpus, governed research records, the roadmaps, or live GitHub
state.

## Resume protocol

1. Read `AGENTS.md` and inspect the current branch, status, recent history, and
   repository shape.
2. Read the relevant canonical architecture, research, contract, and manuscript
   sources named by `AGENTS.md`.
3. Read this file, then verify its branch and issue statements against GitHub.
4. Continue only the next dependency-ready issue unless the user changes the
   order.

## Current checkpoint

- **Last merged baseline before this change:** `main` at
  `f9e23128a660066b3f64c73c4dd2d36554b6040a`, PR #90, completing issue #47.
- **Current change:** issue #48 is implemented on branch
  `codex/issue-48-reviewable-gate`; its pull request is not yet recorded in this
  checkpoint. The change promotes the paper to a reviewable design/protocol
  preprint, adds a durable review dossier and automated strong-stage gate, and
  audits the live publication. Check GitHub before treating it as merged.
- **Completion condition for #48:** merge the reviewed candidate, allow Pages
  to deploy that exact merge revision, then pass the cache-busted route,
  revision, manifest, and artifact-hash verifier. The existing live baseline is
  evidence for #47, not proof for the unmerged #48 candidate.
- **Next dependency-ready issue after that live proof:** #70, the magazine
  editorial contract and page map.
- **Scheduled site follow-up:** #89 owns publication-first launch-site polish
  after #74 and before #75. The issue now includes the React hydration mismatch
  discovered during #48 browser review.
- **Execution style:** one scoped issue and one reviewable pull request at a
  time; the maintainer performs merges.

## Publication state in this revision

- Paper version: `0.1.0`; repository publication stage:
  `submission-ready`, described publicly as a reviewable design/protocol
  preprint.
- Title: *Antidote: A Governed Framework for Inspectable Person-and-Moment
  Generative Audio Journeys*.
- Subtitle: *System Design and Prospective Feasibility Protocol*.
- RQ1 is answered only at the system-design level. RQ2 technical feasibility
  and RQ3 within-person advisory usefulness remain unanswered.
- The executable evidence remains a synthetic rule-guided session with a
  deterministic mock worker. No qualifying real-model package or formal human
  study exists; collection authority remains false.
- The manuscript contains 17 active final visuals and no active prose
  placeholders. The two evidence-contingent Results figures remain retired
  until qualifying T0 and T1 packages exist.
- The bibliography retains cited and additional-reading sources as separate,
  governed sets; it must not be reduced to only in-text citations.
- The review disposition is not peer review, venue acceptance, ethics approval,
  clinical validation, or evidence of safety, efficacy, mechanism, or human
  feasibility.

## Issue #48 material changes

- Added `paper/reviews/reviewable-preprint-v0.1.0.{json,md}` with the gate
  decision, all prerequisite evidence mappings, five separate reviewer lenses,
  eleven audit areas, twelve primary-source spot checks, justified deferrals,
  prohibited claims, open limitations, and post-merge verification contract.
- Added `scripts/check_reviewable_preprint.py` and regression tests. Strong
  publication stages now fail closed when review evidence, boundaries, source
  paths, #84's gated deferral, browser disposition, or post-merge contract
  drifts.
- Promoted `beacon-project.toml` to `submission-ready` and aligned README, site
  copy, citation metadata, manuscript contract `0.6.0`, roadmaps, availability
  language, rights statements, figure metadata, and source comments.
- Made external-link checks mandatory for every native strong-stage Make/Task
  path. Link probes are concurrent and fall back to a ranged GET when a host
  cannot reliably answer HEAD; real HTTP failures still fail the build.
- Reconciled the paper's public status as a design/protocol preprint with no
  formal human results, real-model qualification, collection authority, DOI,
  venue acceptance, or external peer review.
- Recorded a live-browser audit: the paper route has no horizontal overflow and
  all nine rendered figures expose alt text. The launch shell remains readable
  but logs React error 418 because the pinned Holon revision tries to hydrate
  static markup. This is an accepted paper-gate limitation tracked by #89, not
  a silently resolved defect.

## Verified evidence for this revision

- `make test`: 110 tests pass, including new review-stage and external-link
  compatibility coverage.
- Both neutral and Ego Hygiene themes pass two-clean-build byte-reproducibility
  for the 63-page PDF, accessible HTML, provenance record, and independently
  compiling arXiv archive. All PDF fonts are embedded and searchable.
- Eleven representative Ego Hygiene pages and two neutral pages were rasterized
  and visually inspected across title, navigation, prose, figures, Results,
  limitations, conclusion, references, and research shelf.
- Exact-pinned Holon
  `2600baff6f6d944094da81b77e1a9a2e9e7a1cd6` builds successfully; complete
  Pages staging passes route, fragment, manifest, checksum, and repeated-tree
  byte-equivalence checks.
- The canonical live baseline verifier passed revision
  `f9e23128a660066b3f64c73c4dd2d36554b6040a`, HTML SHA-256
  `5b5ad3cd934d7ab6b05b86f6b45d1e482db338163c375194fed460583b70bb72`,
  and PDF SHA-256
  `76e5e79b28971e31a0d4d8a3870cbe6804bd0c7341874b3ad69f831c655c7a77`.
- Twelve high-leverage records were reopened at their primary sources; the
  checked paraphrases and qualifications remain supported.
- **Environment limitation:** this managed workspace cancelled the final
  outbound URL batch during local `make check-content`. The artifact build had
  completed and the source records were independently checked, but the full
  `make check-all`, `task check-all`, Make/Task site equivalence, and live-link
  gate must be treated as pending until GitHub CI passes them for the committed
  candidate.

## Dependency-ordered publication path

1. Finish #48 — merge, deploy, and verify the exact live candidate revision.
2. #70 — freeze the magazine editorial contract and page map.
3. #71 — author the evidence-traceable magazine source.
4. #72 — design the magazine and produce editorial visuals.
5. #73 — build and verify magazine web, digital, and print artifacts.
6. #74 — publish the magazine and activate its hub slot.
7. #89 — polish the publication-first launch site around real paper and magazine
   artifacts.
8. #75 — create the combined versioned release and archival record.
9. #76 — prepare and publish the human-approved LinkedIn launch.

## Boundaries and unresolved work

- #48 is not complete until the merged candidate itself passes the exact live
  verifier. A successful local Pages stage or PR artifact is not that proof.
- #84 remains a mandatory gate before any H1 evidence admission or human
  collection. Its current deferral is valid only because collection authority
  is false and no H1 package exists.
- #89 owns the hydration fix plus aesthetic and usability polish for the
  publication hub; do not pull the broader redesign into the manuscript gate.
- The magazine and LinkedIn post may translate claims from the paper but may
  not introduce efficacy, mechanism, safety, or completed-study claims.
- Prototype and real-model work remains separately gated. It should not delay
  the publication-first path unless a paper claim explicitly depends on it.
- Do not activate human collection, autonomous personalization, or adaptation
  from this checkpoint.

## Required update at every issue handoff

Update this file in the issue's pull request with:

- the verified merged baseline and current branch or pull-request state;
- what materially changed and which canonical sources own it;
- exact validation results and any environment-limited checks;
- unresolved risks, blocked claims, and deferred work;
- the next dependency-ready issue and any roadmap-order change.

Keep historical detail in Git and GitHub. Replace stale checkpoint prose here
instead of turning this file into a chronological changelog.
