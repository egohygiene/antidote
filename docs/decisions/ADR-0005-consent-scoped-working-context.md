# ADR-0005: Project only explicitly consented context into a session

- Status: Accepted for MVP
- Date: 2026-08-27
- Decision owners: Ego Hygiene / Antidote
- Applies to: Personal context, memory, generation, and future Ego Hygiene integration

## Context

Moment-specific generation may benefit from journal writing, therapy-chat
history, prior sessions, or other personal records. Sending an entire history to
a model would weaken consent, privacy, inspectability, reproducibility, and the
ability to understand why a detail influenced a journey. Lossy memory extraction
alone can also discard information whose importance becomes clear later.

## Decision

Antidote preserves approved source records separately from derived views. For
each session, the person grants authority scoped by source, purpose, action,
time, and retention. The system derives an inspectable working projection under
that authority and shows it before journey planning or generation.

The projection records its source event IDs, derivation version, edits,
omissions, and expiry. A person may correct, exclude, or remove any derived
element. The generator sees the approved projection and accepted journey plan,
never unrestricted source history.

Consent to inspect, summarize, generate, retain, learn, synchronize, export,
and publish remain separate actions. Manual check-in and semantic entry remain
available without historical context.

## Implementation evidence

The synthetic desktop session shows the exact optional manual context before
planning, records only an explicitly confirmed session-scoped grant, and keeps
personal-model updates disabled. Missing confirmation writes no session event.
The worker receives the accepted journey specification rather than source
history. Historical Ego Hygiene sources, derived summarization, revocation UI,
and privacy-ready retention remain later work.

## Consequences

- Context use is more legible, purpose-limited, and reproducible.
- The prototype must model consent and projection provenance before deep Ego
  Hygiene integration.
- Smaller projections may reduce apparent relevance but lower exposure and
  reduce accidental meaning injection.
- Raw private records need not enter the Antidote repository or research export.

## Reconsider when

- User research shows the projection review is unusably burdensome;
- a stronger privacy-preserving context protocol provides equal or better
  agency and provenance;
- legal or ethical review requires stricter separation or retention limits.
