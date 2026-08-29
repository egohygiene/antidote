# ANT-TBL-005 - Exposure and response completeness

## Scientific purpose

Prevent generation, playback, completion, and response availability from being treated as the same event.

## Required content

Eventually include generated, verified, played, completed, interrupted, declined, missing, immediate-response, and later-aftereffect fields with denominators.

## Evidence and claim boundary

Governed by ANT-HYP-003, ANT-CLM-003, and ANT-NEG-004. Missingness is not neutral response and generation is not exposure.

## Source plan

Generate deterministic LaTeX from protocol-qualified event and response records after issue #41 approval.

## Accessibility plan

Spell out status words, preserve denominators, use row and column headers, and avoid icon-only completeness states.

## Failure conditions

Reject silent exclusions, collapsed states, unknown denominators, or any row lacking provenance to an exposure record.
