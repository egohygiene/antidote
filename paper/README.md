# Writing the Antidote paper

The canonical manuscript is `paper/paper.tex`, which assembles the numbered
files under `paper/sections/`. Write directly in those LaTeX section files. Do
not create a parallel Markdown manuscript.

## Current section map

| File | Writing purpose | Evidence gate |
| --- | --- | --- |
| `01-introduction.tex` | Problem, research question, and bounded contribution preview | Novelty language remains provisional |
| `02-related-work.tex` | Primary-source synthesis and comparison | Complete the source and novelty matrix first |
| `03-system-design.tex` | Components, interfaces, state, and provenance | Distinguish proposed design from implemented system |
| `04-methods.tex` | Feasibility protocol and analysis plan | Freeze before formal collection |
| `05-results.tex` | Auditable observations and analyses | No results until the frozen protocol runs |
| `06-discussion.tex` | Evidence-proportional interpretation | Separate feasibility, efficacy, and mechanism |
| `07-limitations-and-ethics.tex` | Validity threats, safety, privacy, and review | Resolve ethics requirements before collection |
| `08-availability-and-contributions.tex` | Reproducibility, access, funding, and roles | Verify identifiers and contributor approvals |
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

Use either interface while writing:

```sh
make build
task build
```

Run the full source and artifact checks before opening a pull request:

```sh
make check-all
task check-site
```

The PDF appears at `build/egohygiene/paper.pdf`, the accessible paper at
`build/egohygiene/web/index.html`, and the complete local Pages projection at
`_site/index.html`.
