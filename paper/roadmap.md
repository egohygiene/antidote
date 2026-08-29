# Antidote paper roadmap

This roadmap is the durable execution handoff for the first Antidote research
paper. The canonical manuscript remains `paper/paper.tex` and the numbered
LaTeX files under `paper/sections/`; this file governs their order of work,
evidence gates, figures, and publication checkpoints.

The parent work item is
[issue #31](https://github.com/egohygiene/antidote/issues/31).

## Intended publication sequence

The first manuscript evolves through four deliberately different states:

1. **Writing preview** — incomplete, visibly labeled section drafts are
   continuously reviewable in PDF and accessible HTML.
2. **Design/protocol manuscript** — the literature synthesis, contribution
   boundary, system design, mathematical framework, and evaluation protocol are
   reviewable without implying human-outcome results.
3. **Feasibility revision** — technical or N-of-1 observations enter only after
   the relevant implementation and frozen-protocol gates produce auditable
   evidence.
4. **Reviewable preprint** — placeholders are absent, claims trace to verified
   sources or observations, and the complete publication gate passes.

A Pages deployment is a review surface. It is not peer review, a clinical
claim, a DOI-bearing release, or evidence that a proposed method works.

## Evidence model

The research corpus has three related but non-interchangeable layers:

| Layer | Purpose | May be broader than the paper? |
| --- | --- | --- |
| Living source atlas | Preserve useful discoveries, assessments, disagreements, and reading paths | Yes |
| Canonical bibliography shelf | Preserve verified bibliographic identities, including useful background material | Yes |
| Manuscript citations | Support or contextualize statements actually made in the paper | No |

An entry can be useful without being cited. Inclusion does not imply
endorsement, and architecture precedent does not establish therapeutic
efficacy.

## Work graph

### Wave P1 — Evidence and novelty

- [#32 — Consolidate the living source atlas and bibliography shelf](https://github.com/egohygiene/antidote/issues/32)
- [#33 — Scout adaptive-control and real-time generative-audio architecture](https://github.com/egohygiene/antidote/issues/33) — [evidence dossier](../research/notes/ADAPTIVE_AUDIO_ARCHITECTURE.md)
- [#34 — Build the comparator, evidence, and novelty matrix](https://github.com/egohygiene/antidote/issues/34) — [governed dossier](../research/notes/COMPARATOR_NOVELTY_MATRIX.md)
- [#35 — Freeze the paper thesis, contribution, and section contracts](https://github.com/egohygiene/antidote/issues/35)

The paper does not begin with prose inflation. It begins by testing whether the
claimed gap and contribution survive primary-source comparison.

### Wave P2 — Publication and visual foundations

- [#36 — Prove the continuous paper preview and Pages review loop](https://github.com/egohygiene/antidote/issues/36)
- [#45 — Establish the scientific figure and table system](https://github.com/egohygiene/antidote/issues/45)

Issue #36 is an early canary. It proves that every later section merge can be
inspected locally, in pull-request artifacts, and at the custom-domain web/PDF
routes. Issue #45 creates the figure manifest, caption registry, accessibility
contract, source specifications, and placeholder/final distinction before
visual production begins.

### Wave P3 — Core manuscript

- [#37 — Write the Introduction and research-gap section](https://github.com/egohygiene/antidote/issues/37)
- [#38 — Write Related Work and the evidence synthesis](https://github.com/egohygiene/antidote/issues/38)
- [#39 — Formalize the mathematical model and write System Design](https://github.com/egohygiene/antidote/issues/39)
- [#40 — Write the feasibility method and frozen evaluation protocol](https://github.com/egohygiene/antidote/issues/40)
- [#41 — Define Results and analysis reporting without inventing evidence](https://github.com/egohygiene/antidote/issues/41)

The Results issue creates an honest reporting contract. It does not authorize
invented values or promote synthetic fixtures into human evidence. Technical
evidence from MVP issue #18 may enter only after explicit claim-ledger review;
human-response findings require the later frozen protocol.

### Wave P4 — Interpretation, accountability, and figures

- [#42 — Write Discussion and bounded future directions](https://github.com/egohygiene/antidote/issues/42)
- [#43 — Write Limitations, ethics, safety, and privacy](https://github.com/egohygiene/antidote/issues/43)
- [#44 — Write availability, reproducibility, and contributor statements](https://github.com/egohygiene/antidote/issues/44)
- [#46 — Produce the core Antidote figures and evidence tables](https://github.com/egohygiene/antidote/issues/46)

Interpretation follows evidence and methods. It does not set their boundaries
retroactively.

### Wave P5 — Synthesis

- [#47 — Finalize the title, abstract, conclusion, and whole-paper coherence](https://github.com/egohygiene/antidote/issues/47)

The title and abstract are finalized late so they cannot promise more than the
completed body supports.

### Wave P6 — Reviewable-paper gate

- [#48 — Pass the reviewable-paper and live-publication gate](https://github.com/egohygiene/antidote/issues/48)

This gate reconciles source records, bibliography, claim ledger, manuscript,
figures, metadata, build outputs, Pages routes, checksums, and the roadmap.

## Canonical section ownership

| Canonical source | Primary issue | Completion boundary |
| --- | --- | --- |
| `01-introduction.tex` | #37 | Problem, moment-specific gap, question, bounded contribution preview |
| `02-related-work.tex` | #38 | Primary-source synthesis and comparator boundary |
| `03-system-design.tex` | #39 | Interpretable architecture, notation, status, and failure boundaries |
| `04-methods.tex` | #40 | Reproducible feasibility protocol and analysis plan |
| `05-results.tex` | #41 | Governed reporting structure; observations only when qualified |
| `06-discussion.tex` | #42 | Evidence-proportional interpretation and future directions |
| `07-limitations-and-ethics.tex` | #43 | Validity, risk, privacy, consent, and ethics status |
| `08-availability-and-contributions.tex` | #44 | Verified access, reproducibility, roles, funding, and conflicts |
| `appendix.tex` | #40, #41 | Frozen protocol checklist and supporting analysis material |
| title, abstract, conclusion, coordinator | #47 | Whole-paper synthesis and consistency |

## Initial visual inventory

The exact count may change during issue #45, but the first governed inventory
must consider:

1. literature landscape and comparator matrix;
2. person–moment–journey response model;
3. holistic closed-loop architecture;
4. consent-scoped context projection;
5. Semantic Intent Mixer and human control surface;
6. state estimation, receding horizon, and generate-ahead buffer;
7. semantic conditioning versus acoustic continuity/interpolation;
8. provenance, hashing, privacy review, and fail-closed export;
9. feasibility protocol timeline; and
10. evidence and claim classification.

Information design takes precedence over decoration. Exact diagrams and data
visuals must remain reproducible from governed source. Generated editorial
artwork requires recorded prompts/provenance and human verification of every
label.

## Resume protocol

A future contributor or conversation should:

1. read `AGENTS.md`, `EPISTEMOLOGY.md`, and this roadmap;
2. inspect issue #31 and the next unclosed, dependency-ready child;
3. read that issue's required source records and affected section contract;
4. change the canonical LaTeX or governed research source only;
5. update the claim ledger, bibliography, figure registry, or architecture
   document when the issue changes their owned boundary;
6. run `make check-all` and `task check-site`; and
7. record the merged evidence and live revision before advancing the roadmap.

MVP issues #17–#23 remain valid but paused. Paper work must describe their
capabilities as proposed or incomplete until checked-in, validated evidence
changes that status.
