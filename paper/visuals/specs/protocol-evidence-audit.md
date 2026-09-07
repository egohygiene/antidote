# ANT-TBL-008 - Supporting protocol and evidence audit

## Scientific purpose

Reconcile protocol, source, artifact, exposure, measure, evidence class, exclusion, and claim disposition in one appendix audit.

## Required content

Show the frozen protocol and reporting-contract identities, content digests,
D0/T0/T1/H1 stage states, collection-authority boundary, qualifying-source
availability, evidence class, activation gate, and current claim disposition.

## Evidence and claim boundary

Governed by ANT-CLM-003, ANT-CLM-004, and ANT-NEG-004. Auditability supports inspection but does not validate an outcome.

## Source plan

Generate deterministic LaTeX with `scripts/generate_visual_tables.py` from the
locked protocol, governed empty reporting contract, current stage states, and
claim-ledger boundaries. A later value-bearing audit must additionally project
qualifying code, model, analysis, exposure, instrument, exclusion, and review
records rather than editing the current table by hand.

## Accessibility plan

Use stable identifiers, repeated headers, textual dispositions, and a web layout that permits horizontal inspection without lost labels.

## Failure conditions

Reject sensitive records, mutable identifiers, untraceable exclusions, or use as a substitute for methods and results prose.
