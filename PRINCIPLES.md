---
schema: aether.architecture-document/v1
id: antidote-principles
title: Antidote Principles
kind: architecture-document
version: 0.1.0
status: provisional
owners:
  - egohygiene
created: 2026-08-27
updated: 2026-08-27
governed_by:
  - architecture-principles
depends_on:
  - antidote-purpose
  - antidote-vision
related:
  - antidote-pillars
  - antidote-manifesto
  - antidote-epistemology
  - antidote-ai-constitution
supersedes: []
---

# Antidote Principles

## Purpose

These principles guide choices when several technically valid options exist.
They do not replace evidence, policy, accepted decisions, consent, or protocol
review.

## 1. Personalize to the moment, not merely the profile

**Guidance:** Treat an individual's history as context for a current decision,
not a permanent label. Preserve the state, purpose, and time boundary of every
session.

**Trade-off:** A song that mattered once may not be appropriate later; the
system accepts uncertainty instead of forcing a stable preference model.

## 2. Make intent interpretable before generation

**Guidance:** Convert prose and selected context into an editable semantic and
temporal journey plan before invoking an audio model.

**Trade-off:** The extra planning step adds friction but makes disagreement,
model failure, and scientific comparison visible.

## 3. Consent precedes context

**Guidance:** A worker receives only the source-, purpose-, and session-scoped
projection a person approved. Consent to store, inspect, infer, generate,
retain, or publish are separate permissions.

**Trade-off:** Less context may reduce apparent relevance while protecting
agency and making the experiment reproducible.

## 4. Be imaginative in generation and conservative in interpretation

**Guidance:** Explore rich semantic and acoustic possibilities while keeping
source, hypothesis, observation, interpretation, and claim distinct.

**Trade-off:** Antidote may produce emotionally powerful experiences without
describing them as proof of a neurological mechanism or therapeutic effect.

## 5. Felt response outranks inferred emotion

**Guidance:** Separate what a model or analyzer predicts the audio expresses
from what the listener reports feeling, including mismatch, ambivalence, and
harm.

**Trade-off:** Subjective evidence is noisy, but substituting an automated label
would erase the phenomenon Antidote is meant to study.

## 6. Local source, replaceable adapters

**Guidance:** Keep personal state, consent, provenance, and domain rules local
and portable. Models, frameworks, renderers, and optional services remain
replaceable adapters.

**Trade-off:** Local execution introduces hardware and packaging constraints
that must remain visible.

## 7. Adaptation earns authority gradually

**Guidance:** Begin with explicit rules and descriptive N-of-1 learning. Advance
to recommendations or experimental policies only through reviewed evidence and
bounded safety rules.

**Trade-off:** The system improves more slowly but avoids turning sparse
subjective feedback into unreviewed autonomous experimentation.

## 8. Preserve provenance without preserving everything forever

**Guidance:** Record the lineage required to understand a run while supporting
purpose limitation, selective retention, export, and deletion.

**Trade-off:** Reproducibility and privacy can conflict; the consent and data
classification contract decides what may be retained or shared.

## Precedence and exceptions

Safety, present consent, human agency, privacy, and scientific honesty take
precedence over personalization quality, engagement, novelty, and speed.
Exceptions require a recorded rationale, narrow scope, review trigger, and
evidence that the person can stop or recover.

## Evidence and uncertainty

- **Observed:** Existing research notes already require evidence discipline and
  distinguish an originating experience from scientific validation.
- **Decided for the prototype:** No hidden optimization or unrestricted personal
  context enters the v0 loop.
- **Proposed:** Later protocols may test constrained adaptation under explicit
  assignment and stop rules.
- **Open question:** Which principles require machine-enforced contracts before
  the first participant-facing study?
