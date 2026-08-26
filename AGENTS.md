# Agent instructions

Antidote is a research publication repository, not a clinical product. Before
editing claims, methods, results, or conclusions, read:

- `research/bootstrap/03-scientific-boundaries.md`;
- `research/notes/CLAIM_LEDGER.md`;
- the relevant primary-source record under `research/sources/`.

Keep sources, hypotheses, observations, interpretations, and manuscript claims
explicitly distinguishable. The originating N-of-1 experience is
hypothesis-generating only. Do not introduce efficacy, treatment, diagnostic,
or neurological-mechanism claims without evidence and appropriate review.

The canonical manuscript is `paper/paper.tex` and its `paper/sections/`
inputs. Do not add a second Markdown manuscript or copy Beacon templates into
this repository. Build through the pinned Beacon research-paper profile:

```sh
make check-all BEACON_ROOT="../beacon"
```

Run `make inventory` after changing preserved migration artifacts. Generated
files belong in `build/` and must not be committed.
