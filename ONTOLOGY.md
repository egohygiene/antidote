---
schema: aether.architecture-document/v1
id: antidote-ontology
title: Antidote Ontology
kind: architecture-document
version: 0.1.0
status: provisional
owners:
  - egohygiene
created: 2026-08-27
updated: 2026-08-27
governed_by:
  - architecture-ontology
depends_on:
  - antidote-purpose
  - antidote-vision
  - antidote-principles
  - antidote-epistemology
related:
  - antidote-pillars
  - antidote-manifesto
  - antidote-ai-constitution
  - antidote-personal-model
supersedes: []
---

# Antidote Ontology

## Domain scope

Antidote models the concepts required to plan, generate, experience, evaluate,
and learn from an interpretable audio journey for one person in one moment. The
ontology names conceptual identities and relationships; exact fields belong to
versioned schemas, and storage or code types remain implementation concerns.

## Canonical concepts

| Concept | Meaning |
| --- | --- |
| Individual | The person whose present choice and response anchor a session; not reducible to a profile |
| Moment | The bounded time and context in which a journey is requested |
| State observation | A self-report or optional measurement describing part of the current condition |
| Desired transition | A direction, quality, or trajectory the person wants to explore, not a guaranteed outcome |
| Context source | A journal excerpt, session note, manual statement, prior response, or other candidate input |
| Consent grant | Time-, source-, purpose-, and action-scoped authority to use context or perform an operation |
| Working projection | An inspectable, derived view created from approved sources for one purpose |
| Semantic descriptor | A word, metaphor, image, memory, relation, inclusion, exclusion, or other human-readable sonic meaning |
| Personal sonic mapping | An uncertain relationship between semantic meaning, acoustic realization, context, and prior response for one individual |
| Journey strategy | A high-level approach for moving from the current state toward the desired transition |
| Journey plan | An ordered, editable set of stages, intentions, constraints, and acoustic controls |
| Journey stage | A time-bounded portion of a plan with an intended role and transition conditions |
| Acoustic control | A requested property such as tempo, timbre, harmony, density, dynamics, spatiality, or rhythmic structure |
| Model adapter | A replaceable boundary that translates a generation specification to and from one model implementation |
| Generation specification | The immutable, versioned instruction set sent across the model boundary |
| Generation run | One attempted model invocation, including runtime state, warnings, and lineage |
| Audio artifact | A generated or assembled media object identified by content hash and format |
| Feature report | Measured acoustic properties and control-adherence estimates for an artifact |
| Exposure | The actual playback event through which a person encounters an artifact |
| Response observation | A self-report, behavior, or optional measurement associated with an exposure |
| Aftereffect | A response observation intentionally collected after the immediate session window |
| Personal model snapshot | A versioned, uncertain summary of within-person evidence at a point in time |
| Safety event | Distress, mismatch, adverse response, exclusion, stop, or other event requiring visibility or changed behavior |
| Experiment protocol | The versioned rules for assignments, measurements, analysis, exclusions, and stopping |
| Provenance record | Lineage connecting entities, activities, agents, derivations, code, models, and artifacts |

## Core relationships

- An **Individual** authorizes a **Consent grant** for selected **Context
  sources** in a **Moment**.
- A consent-constrained process derives a **Working projection** without
  replacing its source records.
- **State observations**, a **Desired transition**, a working projection, and
  **Personal sonic mappings** inform a proposed **Journey strategy**.
- A journey strategy becomes an editable **Journey plan** composed of **Journey
  stages**, **Semantic descriptors**, and **Acoustic controls**.
- A **Model adapter** executes a **Generation specification** as a **Generation
  run** and produces an **Audio artifact** plus warnings.
- Analysis derives a **Feature report** from the artifact; it does not establish
  the person's felt response.
- An **Exposure** connects actual playback to one or more **Response
  observations**, **Aftereffects**, or **Safety events**.
- Approved evidence may update a new **Personal model snapshot** while
  preserving the prior snapshot and the evidence responsible for the change.
- An **Experiment protocol** constrains assignments, measurements, adaptation,
  and interpretation.
- **Provenance records** connect every derived entity to the activity and agent
  that produced it.

## State distinctions

- Current state is not desired state.
- Intended acoustic control is not realized acoustic feature.
- Expressed emotion is not felt emotion.
- Immediate catharsis is not necessarily later benefit.
- Personal history is not the current moment.
- Model confidence is not participant certainty.
- Absence of reported harm is not proof of safety.

## Ownership boundaries

- Antidote owns these domain concepts and their public contracts.
- Ego Hygiene owns broader journal, therapy-chat, identity, and application
  concepts; Antidote consumes only versioned projections.
- Beacon owns reusable publication tooling, not Antidote's scientific or runtime
  ontology.
- Audio-model projects own their native prompt and inference conventions;
  adapters prevent those conventions from becoming Antidote's vocabulary.

## Evidence and uncertainty

- **Observed:** The research bootstrap defines the initial semantic–acoustic–
  response loop.
- **Decided for the prototype:** Consent grant, working projection, journey
  plan, generation run, exposure, and response remain separate records.
- **Proposed:** The JSON schemas under `contracts/schemas/` will encode the first
  interoperable subset of this ontology.
- **Open question:** Whether “journey strategy” and “journey plan” remain
  separate concepts after implementation experience.
