# ANT-TBL-003 - Measurement and evidence matrix

## Scientific purpose

Map each non-interchangeable measurement layer to its instrument, timing, provenance, missingness, and permitted interpretation.

## Required content

Project every frozen measurement-registry row by stable ID: baseline state,
desired transition, semantic controls, acoustic realization, exposure,
perceived expression, felt state, appraisal, burden, missingness, and the
explicitly uncollected clinical-outcome row. For each row preserve the construct,
timing, instrument, scale, evidence class, provenance or contract path, and
prohibited inference. Keep immediate response and later aftereffect timing
visible without merging the records.

## Evidence and claim boundary

Governed by ANT-HYP-003, ANT-CLM-003, and ANT-CLM-006. Measurement separation
does not validate the custom instrument, remove measurement error, authorize
collection, or promote any feasibility field into a clinical outcome.

## Source plan

Generate deterministic LaTeX from the `measurement_registry` in
`experiments/protocols/antidote-feasibility-v1.1.json`, locked as
`ANT-PROT-FEAS-001` version 1.1.0 with SHA-256
`8d6848f148a627424c566f04381103779debd65b4563bd4712652e09cd715024`.
The byte-preserved v1.0.0 predecessor was superseded before collection under
issue #82.
Do not hand-maintain a second taxonomy in the table.

## Accessibility plan

Use row headers, concise definitions, repeated page headers, and a responsive web projection with no color-only status.

## Failure conditions

Reject missing or reordered registry IDs, merged response constructs,
unspecified timing, missing provenance or prohibited-inference text, drift from
the locked protocol, implied collection, or a clinical outcome inferred from
feasibility measures.
