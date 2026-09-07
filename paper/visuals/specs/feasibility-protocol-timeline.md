# ANT-FIG-008 - Feasibility protocol timeline

## Scientific purpose

Project the corrected, frozen `ANT-PROT-FEAS-001` version 1.1.0 session sequence without
turning a design protocol into collection authority or a completed study.

## Required content

Show the protocol's eight ordered stages: (1) authority and readiness, (2)
baseline and desired transition, (3) condition reveal and plan review, (4)
generation and verification, (5) explicit playback and exposure, (6) immediate
response within five minutes, (7) later aftereffect at 18--30 hours with a
24-hour target, and (8) review, closure, or pause. Mark the minimum 48-hour
interval between exposures and show stop, consent-revocation, technical-failure,
and adverse-response branches as interrupting rather than completing the flow.

## Evidence and claim boundary

Governed by ANT-HYP-003, ANT-CLM-003, ANT-CLM-004, and ANT-CLM-006.
`ANT-PROT-FEAS-001` version 1.1.0 is a frozen prospective design protocol with
`collection_authority` set to `false`; no stage, interval, branch, or completed
path is a participant observation or result.

## Source plan

Generate the deterministic SVG with
`scripts/generate_publication_figures.py` from
`experiments/protocols/antidote-feasibility-v1.1.json` and its v1.1.0 SHA-256 lock
`8d6848f148a627424c566f04381103779debd65b4563bd4712652e09cd715024`.
The byte-preserved v1.0.0 predecessor was superseded before collection under
issue #82.
The frozen JSON owns stage names, order, timing, and interruption semantics; the
visual is a projection and must be regenerated or rejected if those inputs are
superseded.

## Accessibility plan

Number stages, label optional and interruptible branches, and provide a linear long description with declared time intervals.

## Failure conditions

Reject invented timing, collapsed generation and playback authority, a missing
stage or interrupt branch, drift from the locked protocol, implied collection,
observed participant flow, or a clinical-treatment workflow.
