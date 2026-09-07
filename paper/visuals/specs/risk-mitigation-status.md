# ANT-TBL-007 - Risk, mitigation, and unresolved status

## Scientific purpose

Keep risks, proposed controls, implemented controls, residual uncertainty, and blocking gates distinct.

## Required content

Project all seven governed risk families from
`paper/tables/risk-mitigation-status.json`. Include the affected evidence
layer, explicit status word, current control, residual risk, accountable owner,
and collection or publication gate. Preserve the register's false formal-
collection-authority state.

## Evidence and claim boundary

Governed by ANT-SRC-007, ANT-OBS-002, ANT-CLM-002, ANT-CLM-004,
ANT-CLM-005, ANT-CLM-006, ANT-NEG-003, and ANT-NEG-004. A mitigation
plan, synthetic test, local record, or provenance chain is not proof of safety,
consent, privacy, rights, validity, or benefit.

## Source plan

Generate deterministic LaTeX with `scripts/generate_risk_table.py` from the
versioned issue #43 register. Do not maintain a second hand-edited table.

## Accessibility plan

Write status words in every row, define every status below the table, and retain
an order from scientific validity through technical and human risk to research
authority without depending on color.

## Failure conditions

Reject hidden unresolved risks, ownerless gates, roster drift, proposed controls
marked implemented, formal collection authority, or a claim of perfect
mitigation. A stale LaTeX projection fails the repository check.
