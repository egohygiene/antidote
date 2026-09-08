# Antidote v0.1.0 reviewable-preprint review

## Decision

**Disposition: suitable for public review as a design/protocol preprint.**

This is an evidence-bounded publication-readiness decision. It is not external
peer review, venue acceptance, ethics approval, clinical validation, proof of
safety, or evidence that the proposed system changes a person's state.

The complete machine-readable record is
[`reviewable-preprint-v0.1.0.json`](reviewable-preprint-v0.1.0.json). The JSON
record is validated by `scripts/check_reviewable_preprint.py` whenever the
paper declares a strong publication stage.

## Executive review

The paper's strongest contribution is not any individual adaptive-music
component. Prior work already covers current-to-target music selection,
physiological feedback, semantic planning, controllable affective generation,
and within-session adaptation. Antidote instead formalizes the complete path as
the research object: consented context, explicit semantic intent, a
time-indexed plan, generated acoustic realization, actual exposure, separately
reported response, and any later advisory update remain non-interchangeable,
inspectable records.

That contribution survives the review provided its epistemic boundary remains
visible. The current repository demonstrates a deterministic synthetic session
and a reproducible publication system. It does not demonstrate a qualifying
real model, a smoothly replanned listening session, a learned personal mapping,
human feasibility, therapeutic benefit, clinical safety, or a neurological
mechanism. RQ1 receives a design-level answer; RQ2 and RQ3 remain open.

## Review method and independence boundary

The review occurred after the section-by-section authoring and synthesis work.
It used separate HCI/readability, adaptive-audio/control, research-methods,
safety/privacy/human-authority, and reproducibility/publication lenses. Each
finding was reconciled against the canonical manuscript, claim ledger, source
records, visual manifest, protocol, reporting contract, and rendered outputs.

This procedural separation reduces the risk of simply repeating the drafting
logic. It does **not** create an independent human reviewer. No external peer,
ethics board, security assessor, accessibility specialist, clinician, or venue
has reviewed or endorsed version 0.1.0.

## Dependency disposition

Issues #32 through #47 are closed and each has a repository evidence artifact.
The skeleton and pre-collection correction issues (#77 and #82) are also
closed. Their exact evidence mapping is retained in the machine-readable
review record.

Issue #84 is deliberately deferred. It hardens how a future H1 package may be
admitted. Because the current manuscript contains no H1 package and collection
authority remains false, it does not block a no-collection design/protocol
preprint. It remains a hard gate before any H1 evidence can enter Results or
support a claim.

## Primary-source spot checks

Twelve high-leverage records were checked again against their primary arXiv,
publisher, standards-body, or public-health source on 2026-09-07. The checks
covered MindMelody, AffectMachine-Classical, the personalized affective music
player, the binaural-beat systematic review, JITAI, model-predictive control,
CONSORT feasibility guidance, SPENT, W3C PROV-DM, WHO health-AI ethics,
WHO--ITU safe listening, and the music-induced-harm model.

The review confirmed the manuscript's important qualifications:

- MindMelody's architecture and reported evaluation belong to a preprint and
  do not establish Antidote efficacy or novelty.
- AffectMachine assessed perceived emotional expression, not whether its music
  caused benefit or a desired felt state.
- JITAI and model-predictive control supply transferable design patterns, not a
  validated Antidote decision rule or affect controller.
- The binaural-beat literature does not support a reliable universal
  frequency-to-state or brainwave-entrainment claim.
- Reporting standards improve transparency; they do not provide ethics
  approval, causal validity, or clinical status.
- Provenance assists inspection but does not prove truth, consent, ownership,
  privacy, or reproducibility.
- Safe-listening and AI-governance sources create obligations and cautions;
  citing them does not establish conformance or safety.

No verbatim source quotation is needed for the paper's central claims. The
reviewed manuscript uses bounded paraphrase and source attribution.

## Audit dispositions

| Area | Disposition | Result |
| --- | --- | --- |
| Conceptual coherence | Resolved | Title, thesis, abstract, RQs, contributions, conclusion, and terminology agree. |
| Literature and novelty | Resolved | Component precedent is acknowledged; only the bounded inspectability contribution remains. |
| Claims and citations | Resolved | Forty-three citation keys resolve; the broader additional-reading shelf remains separate. |
| System and equations | Accepted limitation | The formal model is inspectable but still proposed or partially synthetic where labeled. |
| Methods and Results | Resolved | Protocol and empty-state reporting are frozen; no human result is implied. |
| Ethics, safety, privacy | Accepted limitation | Risks and gates are explicit; no present control proves safety or authorizes collection. |
| Metadata and licensing | Resolved | Identities, roles, funding, conflicts, AI assistance, and all-rights-reserved manuscript status are explicit. |
| Visuals and accessibility | Resolved | Seventeen active visuals are final; two evidence-contingent Results figures remain retired. |
| Reproducibility | Resolved | Make and Task share one deterministic PDF/web/provenance/arXiv implementation. |
| Live publication | Accepted limitation | The exact issue #47 revision and advertised HTML/PDF hashes were verified. The paper route is readable; the launch shell's inherited hydration mismatch is tracked in #89. |
| Independent review | Accepted limitation | A separate tool-assisted pass exists; external human peer review does not. |

## Browser and responsive-surface audit

The canonical paper route was opened in a browser at a 1363 CSS-pixel viewport.
It exposed the full section sequence, nine rendered figures, alt text for every
figure, 163 links, and no horizontal overflow. The staged candidate separately
passed deterministic route, fragment, heading, landmark, alt-text, checksum,
and repeated-staging checks. The managed review browser could not reach the
workspace-local server, so this record does not claim a browser rendering of
unmerged files.

The browser pass also found a launch-shell hydration defect. The visible shell
remains readable, but it logs React production error 418 and regenerates the
server tree on the client. The accepted Holon revision emits the server tree
with `renderToStaticMarkup` and subsequently calls `hydrateRoot`; React's
[official API documentation](https://react.dev/reference/react-dom/server/renderToStaticMarkup)
states that static-markup output cannot be hydrated, and
[error 418](https://react.dev/errors/418) identifies the observed server/client
mismatch. This does not affect the standalone static paper route, PDF, route
catalog, or integrity proofs, so it is accepted for this paper-review gate and
assigned to issue #89 before the combined paper-and-magazine launch. It is not
silently classified as resolved.

## Live baseline and candidate handoff

The merged issue #47 baseline
`f9e23128a660066b3f64c73c4dd2d36554b6040a` passed the cache-busted live
checker at <https://antidote.egohygiene.io/>. The checker recomputed:

- accessible HTML SHA-256:
  `5b5ad3cd934d7ab6b05b86f6b45d1e482db338163c375194fed460583b70bb72`;
- PDF SHA-256:
  `76e5e79b28971e31a0d4d8a3870cbe6804bd0c7341874b3ad69f831c655c7a77`.

Those hashes document the reviewed baseline, not the issue #48 candidate.
After this review change is merged, the Pages deployment must bind the site to
the merge SHA and pass the same route, revision, manifest, and hash checks. A
successful pull-request artifact or bare HTTP 200 is insufficient.

## Remaining gates

- T1 must qualify a real model, analyzer, long-form timing behavior, output
  rights, and control adherence before RQ2 can be revised.
- Issue #84 and every H1 activation gate must pass before formal collection or
  any human record is admitted.
- Issue #89 must resolve or explicitly disposition the inherited launch-shell
  hydration mismatch before the combined paper-and-magazine launch.
- A later frozen advisory evaluation is required before RQ3 can be answered.
- Any venue submission, DOI, external peer review, or archival release is a
  later publication decision.
- The magazine and launch copy may simplify this paper, but they may not
  strengthen its claims.
