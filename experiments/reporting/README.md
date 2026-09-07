# Results reporting

This directory owns the versioned reporting contract for Antidote evidence.
It defines which source record, protocol version, analysis, evidence class, and
promotion review must exist before a result slot can contain a value.

[`results-reporting-v1.1.json`](results-reporting-v1.1.json) is the current
empty-state contract. It prospectively amends the issue #41 contract under
issue #82 and binds to protocol version 1.1.0. The original
[`results-reporting-v1.json`](results-reporting-v1.json) remains byte-preserved
as the version 1.0.0 historical record. Neither contract contains study
observations, benchmark values, or example statistics. Generated LaTeX tables
must display unavailable and blocked states rather than substituting zeroes.

The contract distinguishes four evidence stages:

- `D0`: inspectable design artifacts;
- `T0`: synthetic mock-system conformance, pending MVP exit gate #18;
- `T1`: real-model technical qualification, currently blocked;
- `H1`: within-person record feasibility, currently blocked from collection.

A future result package must be added under `experiments/results/`, satisfy its
reserved record identity, preserve complete denominators and adverse or missing
records, and pass claim-ledger review before the manuscript can promote it.

H1 repository packages are privacy-reviewed public envelopes, identified by a
`.public.json` suffix. They may contain aggregate accounting, prespecified
summaries, uncertainty, public-safe artifacts, and review dispositions. They
must validate against the reserved strict
`contracts/schemas/h1-public-result-envelope.v1.schema.json` contract before
promotion. They must not contain participant, session, consent-grant, or source-event
identifiers; raw or free-text responses; row-level observations; private paths;
per-record hashes; stable cross-package pseudonyms; or participant-event
timestamps.

The flow, response, safety, and audit envelopes must share the same evidence-set
identity and opaque, nonce-bound integrity commitment and must reconcile their aggregate
accounting before promotion. The underlying private evidence index, its random
commitment nonce, and all row-level records remain outside Git. A commitment is
an integrity aid, not evidence of anonymity, consent, authenticity, truth,
completeness, efficacy, or safety. Physiology remains disabled unless a later
governed protocol amendment separately authorizes it.
