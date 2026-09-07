# ANT-FIG-005 - Predictive horizon and generate-ahead buffer

## Scientific purpose

Distinguish uncertain planning time from deterministic playback deadlines and buffer safety margins.

## Required content

Show current cursor, verified audio, generation in progress, future horizon,
person correction and negotiated plan-approval boundary, deadline, safety
margin, and fallback.

## Evidence and claim boundary

Governed by ANT-HYP-002 and ANT-CLM-005. Timing structure does not establish stability, optimality, or subjective benefit.

## Source plan

Generate the deterministic SVG with
`scripts/generate_publication_figures.py` using the architecture dossier and
the notation frozen by issue #39. Geometry encodes order and containment; it
does not encode measured latency or a validated optimal horizon.

## Accessibility plan

Label every interval directly, use pattern or border differences as well as color, and describe the timeline from left to right.

## Failure conditions

Reject unlabeled symbolic timing, invented numeric timing, missing
underrun/fallback behavior, or conflation of state uncertainty with buffer
uncertainty.
