---
schema: aether.architecture-document/v1
id: antidote-epistemology
title: Antidote Epistemology
kind: architecture-document
version: 0.1.0
status: provisional
owners:
  - egohygiene
created: 2026-08-27
updated: 2026-08-27
governed_by:
  - architecture-epistemology
depends_on:
  - antidote-purpose
  - antidote-principles
related:
  - antidote-vision
  - antidote-pillars
  - antidote-manifesto
  - antidote-ai-constitution
supersedes: []
---

# Antidote Epistemology

## Scope

This document governs how Antidote classifies evidence, experience, model
outputs, provenance, confidence, conflict, and revision. It applies to the
paper, prototype, experiment records, generated explanations, and future Ego
Hygiene integration. It does not predetermine which scientific hypothesis is
true.

## Evidence discipline

Antidote preserves the following chain:

| Layer | Meaning |
| --- | --- |
| Source | What an external primary or authoritative source actually establishes |
| Hypothesis | What Antidote proposes could be true |
| Observation | What occurred in a recorded session or experiment |
| Interpretation | What a person or analysis suggests the observation may mean |
| Claim | What the manuscript or product states as supported |

No layer silently promotes itself to the next. A generated explanation is not a
source, and a compelling experience is not automatically a general claim.

## Claim states

| State | Meaning |
| --- | --- |
| Observed | Directly supported by a recorded artifact, measurement, or repository/runtime check |
| Self-reported | Reported by the participant and preserved as their account |
| Model-estimated | Produced by a named model or analyzer under recorded conditions |
| Decided | Accepted through repository or protocol governance |
| Inferred | Reasoned from evidence but not directly observed |
| Proposed | Recommended direction not yet accepted or implemented |
| Assumed | Working premise required for current design |
| Unverified | Plausible statement not yet checked against an adequate source |
| Open question | Known gap requiring evidence or a human choice |

## Evidence order

1. Frozen protocol evidence, reproducible runs, validated schemas, artifact
   hashes, direct observations, and participant reports.
2. Peer-reviewed primary studies, systematic reviews, accepted decisions, and
   versioned specifications.
3. Current source, configuration, model cards, and authoritative technical
   documentation.
4. Maintainer notes, issue history, preprints, vendor claims, and secondary
   summaries, labeled by source type.
5. Inference, recommendation, analogy, and lived experience, each labeled with
   its limits.

Evidence strength depends on the claim. A model card may establish an exposed
control or license claim but cannot establish a therapeutic outcome.

## Measurement distinctions

Antidote does not collapse these variables:

- intended state transition;
- acoustic properties measured in the generated artifact;
- emotion or meaning the audio appears to express;
- emotion or meaning the listener actually reports feeling;
- immediate usefulness or harm;
- later aftereffect;
- clinical outcome.

The first five may be studied in an early feasibility prototype. The last
requires a different level of protocol, review, evidence, and language.

## Provenance and conflict

Every material observation should identify the approved input projection,
journey-plan version, model and code revisions, parameters, seed when
available, output hash, analysis version, response instrument, and protocol.
Conflicting responses remain visible; recency and intensity do not erase prior
evidence. A later interpretation may supersede an earlier model view without
rewriting the original event.

## Revision

Claims are revised when stronger evidence appears, a source changes, a model or
analysis is invalidated, a participant corrects their record, or an accepted
decision supersedes an assumption. Raw approved events remain distinguishable
from derived projections so new interpretations can be regenerated.

## Evidence and uncertainty

- **Observed:** The repository already maintains scientific-boundary and claim
  ledger records.
- **Decided for the prototype:** The event/provenance record preserves model
  estimates separately from participant reports.
- **Proposed:** Future evidence tooling may validate claim-to-source links
  automatically.
- **Open question:** Which uncertainty representation will remain understandable
  during an emotionally focused session?
