# ADR-0006: Advance adaptation from rule-guided N-of-1 evidence

- Status: Accepted for MVP
- Date: 2026-08-27
- Decision owners: Ego Hygiene / Antidote
- Applies to: Personalization, evaluation, and experimental adaptation

## Context

Antidote's long-term question involves a closed loop, but sparse subjective
feedback, changing baselines, emotional safety, and strong context effects make
premature online optimization scientifically weak and ethically risky. A
single intense or helpful experience cannot identify a stable action policy.

## Decision

Adaptation advances through explicit maturity levels:

1. rule-guided session planning with participant choice;
2. descriptive repeated-session N-of-1 summaries;
3. advisory strategy rankings with uncertainty and editable evidence;
4. constrained randomized or contextual-bandit studies under a frozen protocol;
5. optional multimodal studies with independent sensor consent and analysis.

The MVP implements level 1 and records the evidence required for level 2. It
does not autonomously choose experimental actions, optimize emotional intensity,
or interpret a skipped or stopped session as a reward signal.

Each later level requires explicit exit evidence, protocol changes, exclusion
and stop rules, and appropriate human or institutional review.

## Consequences

- “Closed loop” describes an inspectable learning architecture rather than
  unbounded autonomous control.
- The first useful system can exist before a statistically defensible policy.
- Storage and contracts must preserve decision points, options, tailoring
  variables, assignments, responses, and baseline context for future methods.
- Personal suggestions may improve more slowly, but each increase in authority
  is reviewable.

## Reconsider when

- repeated-session evidence shows the level boundaries are technically or
  scientifically inappropriate;
- an approved study protocol authorizes a bounded higher-level policy;
- adverse-event or privacy evidence requires reducing rather than increasing
  adaptation authority.

## Implementation evidence

Issue #15 implements maturity level 1 in `antidote-core`. One versioned rule
set deterministically maps a synthetic or approved moment context into a draft
journey with exact duration reconciliation, control-policy ceilings, per-choice
rationale and uncertainty, additive schema projections, and a canonical
SHA-256 plan hash. Person edits create a new revision; rejection, supersession,
and approval remain separate immutable events.

Boundary tests cover stable inputs, transition and duration properties,
contradictory preferences, exclusions, unsupported controls, stagewise-control
limits, intensity ceilings, missing traces, prohibited claim language, plan
tampering, and edited revision lineage. This activates only level 1. It adds no
LLM planning, inferred consent, clinical recommendation, response prediction,
longitudinal update, strategy ranking, or autonomous optimization.
