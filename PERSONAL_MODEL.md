---
schema: aether.architecture-document/v1
id: antidote-personal-model
title: Antidote Personal Model
kind: architecture-document
version: 0.1.0
status: provisional
owners:
  - egohygiene
created: 2026-08-27
updated: 2026-08-27
governed_by:
  - architecture-personal-model
depends_on:
  - antidote-purpose
  - antidote-vision
  - antidote-principles
  - antidote-epistemology
  - antidote-ontology
related:
  - antidote-pillars
  - antidote-manifesto
  - antidote-ai-constitution
  - antidote-foundations
supersedes: []
---

# Antidote Personal Model

## Purpose

Antidote is built around within-person meaning and change. This document makes
its limited assumptions about a person explicit. It is not a diagnosis, static
persona, psychological profile, identity model, or claim that a person's inner
state can be completely measured.

## People in scope

- the person creating and experiencing an audio journey;
- a participant reviewing or contributing research evidence;
- a researcher or maintainer interpreting the resulting record;
- people indirectly affected by shared audio or published claims.

## Moment model

For individual `i` at time `t`, Antidote treats available context as a bounded
state rather than an unrestricted biography:

\[
S^{ctx}_{i,t} = (L_{i,t}, P_{i,t}, V_{i,t})
\]

where `L` is the consented lossless source record, `P` is a set of derived
projections, and `V` contains provenance and version information. A working
view is purpose- and authority-constrained:

\[
c^{work}_{i,t} = \pi(S^{ctx}_{i,t}; A_{i,t})
\]

where `A` represents current authorization. The projection may be compact; the
source remains distinguishable and is never silently rewritten by the model.

## Human assumptions

- A person's needs, meanings, sensory tolerance, and response can change across
  minutes, days, environments, and life events.
- The same song can be transformative in one moment and merely pleasant—or
  unwelcome—in another.
- People can hold contradictory feelings and may not want every state changed.
- Self-report is meaningful evidence without being complete or perfectly
  stable.
- Intense emotion can be welcome catharsis, unwanted overwhelm, both, or neither;
  intensity alone is not success.
- Personal files, diagnostic labels, physiology, and prior choices do not fully
  represent a person.
- People need simple language, low cognitive load, interruption, and recovery,
  especially when distressed.

## Agency and consent boundaries

The person selects the current goal, context sources, semantic language,
exclusions, generation action, playback, retention, and whether evidence may
affect future suggestions. Every derived mapping must be inspectable,
correctable, and removable. Refusing context or learning does not block basic
manual generation.

## Personal mapping model

A personal mapping is a versioned estimate of relationships among moment,
semantic intent, realized acoustics, exposure, and response. It records evidence
and uncertainty rather than assigning permanent traits. A prior response can
inform the next proposal, but the current person decides whether it remains
relevant.

The v0 update rule is deliberately modest: record repeated associations,
surface them as observations, and require human selection before they influence
the next journey. It does not optimize automatically.

## Accessibility and dignity

Primary journeys remain keyboard-accessible, screen-reader legible,
reduced-motion compatible, and understandable without clinical or audio-
engineering vocabulary. The interface never blames the person for a mismatch,
failed generation, difficult response, or changed preference.

## Evidence and uncertainty

- **Observed:** The motivating account establishes that moment specificity is
  central to the research question.
- **Decided for the prototype:** Current context, durable history, derived
  projection, and personal mapping are separate inspectable records.
- **Proposed:** Later work may compare recency-weighted, context-conditioned,
  and human-edited mapping strategies.
- **Open question:** How long should different derived mappings remain relevant
  before the system asks the person to re-confirm them?
