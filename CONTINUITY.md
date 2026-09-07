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
  `f4dc9326e07ad99d08557d0695e2bee8918657ec`, PR #88, completing issue #46.
- **Current change:** issue #47 on branch `codex/issue-47-synthesis` completes
  the title, abstract, conclusion, appendix claim index, and whole-paper
  coherence pass. Check GitHub before treating this change as merged.
- **Next issue after merge:** #48, the reviewable-paper and live-publication
  gate.
- **New scheduled follow-up:** #89, publication-first launch-site polish after
  the magazine is published by #74 and before the combined release in #75.
- **Execution style:** one scoped issue and one reviewable pull request at a
  time; the maintainer performs merges.

## Publication state in this revision

- Paper version: `0.1.0`; repository publication stage: `draft` until #48.
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

## Issue #47 material changes

- Finalized a structured, evidence-bounded abstract and synchronized the
  subtitle across paper metadata and the publication card.
- Replaced the conclusion reservation with a design-level answer, five bounded
  contributions, and explicit gates for RQ2 and RQ3.
- Added a reader-facing appendix index for source, hypothesis, observation,
  interpretation, accepted-claim, candidate, and rejected-claim classes.
- Removed the last two prose placeholders and tightened duplicated transitions
  in Related Work and Discussion.
- Advanced the manuscript contract to `0.5.0`, reconciled the claim ledger, and
  updated placeholder and manuscript regression tests.
- Added #89 and placed it after #74 and before #75 without conflating it with
  the later demo-dependent product-site work in #63--#66.

## Verified evidence for this revision

- `make test`: 102 tests pass.
- `make check-all`: neutral and Ego Hygiene PDF, accessible HTML, provenance,
  and arXiv-source outputs build reproducibly.
- `task check-all` with Task `3.53.1`: passes the same two-theme gate.
- `task check-site` against Holon
  `2600baff6f6d944094da81b77e1a9a2e9e7a1cd6`: complete Pages staging,
  routes, manifests, and checksums pass.
- Ego Hygiene PDF: 63 pages; title/abstract, conclusion, and claim-index pages
  were rendered and visually inspected after the final pagination fix.
- Source governance: 96 catalog sources, 48 verified bibliography entries, 43
  manuscript citation keys, 22 architecture mappings, 9 comparator rows, and 9
  novelty decisions pass validation.

## Dependency-ordered publication path

1. #48 — pass the reviewable-paper and live-publication gate.
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

- #48 owns holistic review and verification of the merged custom-domain paper
  and PDF. A successful local Pages stage is not the live-publication proof.
- #89 owns aesthetic and usability polish for the publication hub; do not pull
  that redesign into the manuscript gate.
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
