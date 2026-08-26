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
inputs. Do not add a second Markdown manuscript. The repository owns the
standalone build kit generated from Beacon's pinned research-paper profile;
do not make native builds reach back into a Beacon checkout.

```sh
make check-all
task check-all
```

Both interfaces delegate to `scripts/tasks.py`. Keep their commands and
overrides equivalent. Beacon remains an optional validation and packaging
control plane through `scripts/beacon.py`.

Run `make inventory` after changing preserved migration artifacts. Generated
files belong in `build/`, `dist/`, and `_site/` and must not be committed.
