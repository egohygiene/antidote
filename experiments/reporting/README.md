# Results reporting

This directory owns the versioned reporting contract for Antidote evidence.
It defines which source record, protocol version, analysis, evidence class, and
promotion review must exist before a result slot can contain a value.

[`results-reporting-v1.json`](results-reporting-v1.json) is intentionally an
empty-state contract. It does not contain study observations, benchmark values,
or example statistics. Its generated LaTeX tables display unavailable and
blocked states rather than substituting zeroes.

The contract distinguishes four evidence stages:

- `D0`: inspectable design artifacts;
- `T0`: synthetic mock-system conformance, pending MVP exit gate #18;
- `T1`: real-model technical qualification, currently blocked;
- `H1`: within-person record feasibility, currently blocked from collection.

A future result package must be added under `experiments/results/`, satisfy its
reserved record identity, preserve complete denominators and adverse or missing
records, and pass claim-ledger review before the manuscript can promote it.
