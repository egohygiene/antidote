# Writing the Antidote paper

The canonical manuscript is `paper/paper.tex`, which assembles the numbered
files under `paper/sections/`. Write directly in those LaTeX section files. Do
not create a parallel Markdown manuscript.

Use [`paper/roadmap.md`](roadmap.md) as the durable writing sequence. It links
the evidence, section, figure, synthesis, and live-publication issues and
defines the resume protocol for future contributors and conversations.

[`manuscript-contract.json`](manuscript-contract.json) is the frozen issue #35
writing contract. It owns the working identity, thesis, research questions,
contributions, publication-stage ladder, terminology, claim policy, and the
purpose, evidence, visual, dependency, completion, and prohibition boundary for
every canonical LaTeX source. Before drafting a section, read its contract and
the linked entries in
[`CLAIM_LEDGER.md`](../research/notes/CLAIM_LEDGER.md).

The evidence corpus has three distinct layers:

- the complete living atlas at
  [`research/atlas/literature-voyage-v0.1.md`](../research/atlas/literature-voyage-v0.1.md);
- the verified, intentionally broader bibliography shelf in
  [`references.bib`](references.bib); and
- citations actually used by the numbered manuscript sections.

Current source states and promotion requirements live in
[`research/sources/`](../research/sources/). Run
`python3 scripts/check_sources.py` to verify stable identities, duplicate
identifiers, source-record coverage, and the cited-versus-shelf distinction.

## Scientific visuals

[`visuals/manifest.json`](visuals/manifest.json) governs the complete figure
and table inventory. It assigns every visual a stable ID, owning section,
scientific purpose, label, dimensions, lifecycle state, source mode,
specification, caption, alt text, long description, provenance, license,
claim-ledger boundary, and paper-owned reuse policy.

Caption text remains outside image pixels. The committed
[`visuals/captions.tex`](visuals/captions.tex) registry is generated from the
manifest and consumed by `\AntidoteFigure` and `\AntidoteTable`. Exact diagrams
use deterministic SVG; scientific tables use governed LaTeX and structured
inputs where applicable. Generated images are reserved for conceptual/editorial
artwork and require prompt provenance plus human verification.

Read the complete production and accessibility contract in
[`visuals/README.md`](visuals/README.md). Validate it directly with:

```sh
python3 scripts/check_visuals.py
```

## Current section map

| File | Writing purpose | Evidence gate |
| --- | --- | --- |
| `01-introduction.tex` | Inspectability problem, staged research questions, and bounded contribution preview | Frozen thesis and novelty boundary |
| `02-related-work.tex` | Primary-source synthesis and comparison | Governed source and comparator records |
| `03-system-design.tex` | Components, interfaces, state, and provenance | Distinguish proposed design from implemented system |
| `04-methods.tex` | Feasibility protocol and analysis plan | Freeze before formal collection |
| `05-results.tex` | Auditable observations and analyses | No results until the frozen protocol runs |
| `06-discussion.tex` | Evidence-proportional interpretation | Separate feasibility, efficacy, and mechanism |
| `07-limitations-and-ethics.tex` | Validity threats, safety, privacy, and review | Resolve ethics requirements before collection |
| `08-availability-and-contributions.tex` | Reproducibility, access, funding, and roles | Verify identifiers and contributor approvals |
| `09-conclusion.tex` | Whole-paper answer and evidence-gated handoff | Reconcile body, claims, results status, and limitations |
| `appendix.tex` | Versioned protocol checklist and supporting material | Keep consistent with the frozen protocol |

## Placeholder contract

Every Lorem Ipsum paragraph is wrapped in `\AntidotePlaceholder`. The rendered
PDF and web paper label these blocks as draft layout filler and explicitly state
that they are not evidence. Replace a whole macro invocation when writing that
section; do not remove the warning while leaving filler behind.

Draft builds warn about the remaining blocks. Changing `paper.stage` in
`beacon-project.toml` to `submission-ready` or `published` makes any remaining
placeholder a validation error.

## Feedback loop

Use either interface to build, validate, and serve the same complete local
publication while writing:

```sh
make preview HOLON_SOURCE=../holon
task preview HOLON_SOURCE=../holon
```

Open `http://127.0.0.1:8000/paper/` for the accessible paper and
`http://127.0.0.1:8000/antidote.pdf` for the PDF. Stop the server with `Ctrl-C`.
The complete workflow, CI artifact names, merged-revision check, and LaTeX,
Pandoc, Pages, DNS/TLS, and stale-cache troubleshooting live in
[`docs/paper-preview.md`](../docs/paper-preview.md).

Run the full source and artifact checks before opening a pull request:

```sh
python3 scripts/check_sources.py
python3 scripts/check_visuals.py
make check-all
task check-site HOLON_SOURCE=../holon
```

The PDF appears at `build/egohygiene/paper.pdf`, the accessible paper at
`build/egohygiene/web/index.html`, and the complete local Pages projection at
`_site/index.html`.
