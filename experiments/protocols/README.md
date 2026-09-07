# Antidote experiment protocols

## Status

[`antidote-feasibility-v1.1.json`](antidote-feasibility-v1.1.json) is the current
frozen design/protocol record for the first staged technical and repeated-session
within-person evaluation. Issue #82 created it as a pre-collection corrective
successor to version 1.0.0. Its adjacent lock records the exact bytes, and its
version-matched append-only deviation log is empty.

[`antidote-feasibility-v1.json`](antidote-feasibility-v1.json) preserves the
superseded 1.0.0 bytes in-tree. Its SHA-256 is
`dbedbcbb74303373a7e00e95ad063b025d8cf6033864f4ad5a390d15703ba403`, as
recorded by its original lock. No qualifying record, exposure, or human
collection began under 1.0.0, so the correction reclassifies no observation.

Freezing either design does **not** authorize participant collection. Version
1.1.0 retains `collection_authority: false`, every human-collection activation
gate remains false, and no formal study data has been collected.

This directory will own versioned protocol definitions, condition assignments,
eligibility and exclusion rules, stop criteria, measures, timing, mutation
rules, analysis plans, and data classifications for Antidote studies.

The prospective H1 evaluation is a six-block, repeated-session N-of-1
feasibility series. Its frozen conditions are:

1. a generic text prompt;
2. a structured but non-personalized journey;
3. a personal semantic journey;

The auditory-beat layer is excluded from this protocol series. It would require a protocol
amendment, separate scientific justification, and review.

Every one of the six G/S/P orders appears once. Version 1.1.0 randomizes only
their assignment to the six chronological blocks, yielding exactly `6! = 720`
allowable schedules. It also commits one fixed seed per block and uses that seed
for all three conditions in the block. The conditions remain visibly different
bundles, so their contrasts cannot isolate personalization or another single
component.

The protocol must distinguish intended controls, realized acoustics, expressed
emotion, felt response, immediate usefulness or harm, and later aftereffect.
Implementation logs do not become formal study data until a frozen protocol and
consent/privacy boundary say they do.

The current desktop MVP and its v1 runtime payloads are not the H1 instrument.
Protocol timing, separate v2 consent enforcement, the v2 H1 response/correction
contract, assignment and seed enforcement, participant-facing safety and
accessibility behavior, and a minimum-data private research export all remain
blocking implementations. H1 tests record and provenance feasibility only; it
does not test advisory usefulness, efficacy, clinical safety, or mechanism.

## Change discipline

- Before a first qualifying record, a material protocol change creates a new
  semantic version, parallel immutable protocol artifact, lock, analysis plan,
  and review record.
- After a first qualifying record, the frozen file is immutable; amendments and
  deviations are appended with their affected records and evidence impact.
- Repository fixtures and mock-worker outputs remain synthetic technical
  evidence and never enter human-response denominators.
