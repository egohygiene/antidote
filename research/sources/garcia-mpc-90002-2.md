# Model predictive control source record

## Verified metadata

| Field | Value |
| --- | --- |
| Title | Model Predictive Control: Theory and Practice—A Survey |
| Authors | Carlos E. García; David M. Prett; Manfred Morari |
| Venue | Automatica 25(3), 335–348 |
| DOI | 10.1016/0005-1098(89)90002-2 |
| Version reviewed | Version of record, May 1989 |
| Primary source | https://doi.org/10.1016/0005-1098(89)90002-2 |
| Source type | Peer-reviewed control-theory survey |
| Reviewed | 2026-08-29 |

## Source claims assessed

- MPC uses an explicit model to predict system behavior over a finite horizon.
- It supports constrained objectives and repeated application of a newly
  optimized control action as observations arrive.
- Robustness is not automatic merely because a controller is called MPC.

## Limitations and unresolved questions

- The source addresses engineered processes with identifiable models, not a
  person's affective experience.
- Antidote has no validated state-transition model, objective function, or
  stability result.
- “Receding horizon” is therefore a formal design analogy until evaluated.

## Allowed manuscript use

Use to define the receding-horizon pattern: predict a bounded future, optimize
under constraints, commit only the next action, observe, and replan.

## Prohibited manuscript use

Do not imply that affect is a controllable plant, that the proposed controller
is stable or optimal, or that MPC precedent establishes benefit.
