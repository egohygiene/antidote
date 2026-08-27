---
schema: aether.architecture-document/v1
id: antidote-design-system
title: Antidote Design System
kind: architecture-document
version: 0.1.0
status: provisional
owners:
  - egohygiene
created: 2026-08-27
updated: 2026-08-27
governed_by:
  - architecture-design-system
depends_on:
  - antidote-personal-model
  - antidote-design
related:
  - antidote-purpose
  - antidote-vision
  - antidote-principles
  - antidote-pillars
supersedes: []
---

# Antidote Design System

## Purpose and scope

This document defines reusable semantic language for Antidote's desktop
experience, research views, documentation, diagrams, reports, publication hub,
and future Ego Hygiene projection. It does not freeze a component framework,
token package, or final visual identity.

## Semantic roles

| Role | Meaning |
| --- | --- |
| Cosmos | Quiet containing background for reflection and orientation |
| Surface | Bounded information, choice, or evidence area |
| Current | The person's reported starting state |
| Transition | Desired direction or movement, never a guaranteed result |
| Intent | Human-readable semantic meaning and journey purpose |
| Acoustic | Generated or measured sound structure |
| Response | What the person reports or what an optional instrument observes |
| Personal | Within-person evidence or user-authored meaning |
| Provenance | Source, model, transformation, version, and artifact lineage |
| Success | Completed and verified technical operation—not emotional efficacy |
| Caution | Uncertainty, intensity, mismatch, downgrade, or review required |
| Stop | Immediate interruption or safety boundary |
| Unknown | Missing, unverified, unsupported, or intentionally withheld state |

## Status vocabulary

Use `draft`, `planned`, `approved`, `queued`, `generating`, `partial`,
`generated`, `validated`, `playing`, `stopped`, `responded`, `failed`,
`blocked`, `expired`, and `unknown` consistently. Do not use `healed`, `treated`,
`optimized`, or `effective` as runtime statuses.

## Canonical patterns

- **Moment card:** current state, desired transition, duration, and uncertainty.
- **Consent lens:** selected sources, exact purpose, derived projection, expiry,
  and actions allowed.
- **Semantic palette:** personal descriptors, meanings, inclusions, exclusions,
  and confidence.
- **Journey storyboard:** ordered stages with role, duration, semantic intent,
  acoustic controls, and transition rationale.
- **Generation card:** adapter, model revision, resource estimate, supported and
  downgraded controls, seed, progress, cancel, and warnings.
- **Listening field:** minimal playback with persistent pause, stop, intensity,
  and skip controls.
- **Response constellation:** felt state, resonance, mismatch, helpfulness,
  intensity, harm, notes, and optional later follow-up.
- **Evidence drawer:** immutable identifiers, hashes, feature report,
  provenance, protocol, and export classification.
- **Learning proposal:** mapping change, supporting sessions, uncertainty, and
  accept/edit/reject/forget actions.

## Information hierarchy

1. Present choice, exclusions, and safety.
2. The proposed journey in the person's language.
3. Generation or playback state and immediate controls.
4. Response and optional reflection.
5. Technical parameters, provenance, and research detail.

## Visual direction

The visual language may use the current Antidote navy, cream, teal, violet, and
gold family with soft waveform, constellation, and neural motifs. Decoration
must not obscure state, encode meaning only by color, or imitate medical-device
authority. Calm negative space and progressive disclosure take precedence over
dense dashboards during check-in and listening.

## Motion and sound

- Motion indicates transition or progress but respects reduced-motion settings.
- Waveforms are explanatory or decorative, never the only status signal.
- UI sounds default off during listening and never compete with the artifact.
- Spatial effects and auditory-beat layers are explicit, bypassable processing
  choices with dry previews and evidence notices.

## Evidence and uncertainty

- **Observed:** Antidote's publication hub and research figure establish an
  initial visual family.
- **Decided for the prototype:** Semantic roles are stable before concrete
  React tokens or components.
- **Proposed:** Ego Hygiene tokens may later implement these roles through a
  versioned package.
- **Open question:** Which parts of the publication identity transfer cleanly
  into a sustained, low-stimulation listening interface?
