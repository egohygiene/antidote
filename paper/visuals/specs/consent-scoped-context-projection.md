# ANT-FIG-003 - Consent-scoped context projection

## Scientific purpose

Make minimization, revocation, expiration, and model-facing context boundaries inspectable.

## Required content

Show private context, consent purpose and fields, bounded working projection, exclusions, planning input, and immutable worker input.

## Evidence and claim boundary

Governed by ANT-CLM-002, ANT-CLM-004, and ANT-NEG-003. Consent and local execution do not prove privacy or meaningful consent.

## Source plan

Author deterministic SVG against the consent-grant and working-context-projection schemas.

## Accessibility plan

Use gate shapes plus explicit allowed, excluded, revoked, and expired labels; never rely on green and red alone.

## Failure conditions

Reject any path that bypasses consent, exposes sibling/private internals, or implies that all available context should be used.
