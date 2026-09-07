# ANT-TBL-005 - Exposure and response completeness

## Scientific purpose

Prevent generation, playback, completion, and response availability from being treated as the same event.

## Required content

The current generated projection must show the flow, immediate-response, and
later-response slots with their reserved source records, protocol version,
frozen analyses, and blocked states. A future promoted version must include
generated, verified, played, completed, interrupted, declined, missing,
immediate-response, and later-aftereffect fields with denominators.

## Evidence and claim boundary

Governed by ANT-HYP-003, ANT-OBS-003, ANT-CLM-003, ANT-CLM-007, and
ANT-NEG-004. Missingness is not neutral response and generation is not
exposure.

## Source plan

Generate the empty state from `ANT-REPORT-RESULTS-001` through
`scripts/generate_results_reporting.py`. A future value-bearing version must
derive from `ANT-REC-H1-FLOW-001` and `ANT-REC-H1-RESPONSE-001` after H1
authority and claim-ledger promotion; never enter values directly in LaTeX.

## Accessibility plan

Spell out status words, preserve denominators, use row and column headers, and avoid icon-only completeness states.

## Failure conditions

Reject silent exclusions, collapsed states, unknown denominators, or any row lacking provenance to an exposure record.
