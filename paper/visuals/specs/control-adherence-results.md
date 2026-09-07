# ANT-TBL-004 - Control-adherence results

## Scientific purpose

Reserve a reproducible technical-results structure without creating evidence before qualifying runs exist.

## Required content

The current generated projection must show each T0 or T1 slot, its reserved
source record, protocol version, frozen analysis, and unavailable state without
result values. A future promoted projection must add run identity, requested
controls, measured realization, adherence estimate, uncertainty, verification,
and failure notes.

## Evidence and claim boundary

Governed by ANT-OBS-002, ANT-OBS-003, ANT-CLM-003, ANT-CLM-007, and
ANT-NEG-004. Synthetic fixtures may validate code but cannot become human
outcomes.

## Source plan

Generate the empty state from `ANT-REPORT-RESULTS-001` through
`scripts/generate_results_reporting.py`. A future value-bearing version must
derive from `ANT-REC-T0-001` or `ANT-REC-T1-001` plus its frozen analysis and
claim-ledger promotion; never enter values directly in LaTeX.

## Accessibility plan

Use explicit units, textual verification states, machine-readable source data, and explanatory notes for missing metrics.

## Failure conditions

Reject hand-entered result values, absent hashes, unqualified simulated runs, or any implication of felt response or benefit.
