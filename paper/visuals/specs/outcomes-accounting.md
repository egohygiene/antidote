# ANT-TBL-006 - Null, negative, missing, interrupted, and adverse outcome accounting

## Scientific purpose

Make non-positive and unavailable observations impossible to hide through selective reporting.

## Required content

The current generated projection must reserve separate rows for null or
opposite-direction response, mismatch or unwanted intensity, burden, harm or
adverse response, missingness, and interruption. Each row names its source,
protocol, analysis, and blocked state without a count. A future promoted
version must add definitions, counts, denominators, provenance, and reporting
disposition.

## Evidence and claim boundary

Governed by ANT-HYP-003, ANT-OBS-003, ANT-CLM-003, ANT-CLM-007, and
ANT-NEG-004. Intensity is not automatic success and no current outcomes exist.

## Source plan

Generate the empty state from `ANT-REPORT-RESULTS-001` through
`scripts/generate_results_reporting.py`. A future value-bearing version must
derive from the reserved H1 flow, response, and safety packages after H1
authority and claim-ledger promotion; never enter values directly in LaTeX.

## Accessibility plan

Use category words instead of color severity alone and explain missing, declined, and interrupted records separately.

## Failure conditions

Reject fabricated zeroes, collapsed adverse categories, missing denominators, or promotion of mock and layout data.
