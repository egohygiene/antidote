# Scroll source record

## Verified metadata

| Field | Value |
| --- | --- |
| Title | Context as an Environment: Programmatic Context Management for Long-Horizon Agents |
| Authors | Yin Lin; Elaine Ang; Erkang Zhu; Bolin Ding; Jingren Zhou |
| Identifier | arXiv:2608.21690 |
| Version reviewed | Version 1, 2026-08-21 |
| Primary source | https://arxiv.org/abs/2608.21690 |
| Source type | Non-peer-reviewed computer-science preprint |
| Reviewed | 2026-09-05 |

## Source claims assessed

- Scroll represents a session with an append-only event log and a persistent,
  typed execution environment rather than repeatedly serializing all state
  into a model prompt.
- Programs materialize explicit projections into the model's bounded working
  view while lossless historical records remain addressable.
- The paper reports benchmark gains and also analyzes retrieval and reasoning
  failures in which retained evidence does not guarantee the right inference.

## Limitations and unresolved questions

- The work evaluates long-horizon language-model agents, not personal health
  records, consent workflows, affect estimation, or generated music.
- It is a new preprint and its reported results have not been independently
  replicated for Antidote's task or local runtime.
- Lossless retention creates its own security, deletion, and governance risks.

## Allowed manuscript use

Use as emerging-system precedent for separating source history, derived state,
and a deliberately materialized working projection, and as a caution that
available evidence does not ensure correct interpretation.

## Prohibited manuscript use

Do not claim that Scroll establishes health-data privacy, meaningful consent,
correct psychological interpretation, or the safety or effectiveness of
Antidote's context architecture.
