# ANT-FIG-007 - Provenance, privacy review, and fail-closed export

## Scientific purpose

Show how reproducibility records remain subordinate to consent, minimization, review, and explicit export authority.

## Required content

Show events, versions, hashes, export candidate, consent check, redaction, privacy review, approval, blocked paths, manifest, and checksums.

## Evidence and claim boundary

Governed by ANT-CLM-004 and ANT-NEG-003. Provenance cannot prove truth, ownership, privacy, safety, or benefit.

## Source plan

Generate the deterministic SVG with
`scripts/generate_publication_figures.py` from the provenance ADR, schemas,
issue #43 privacy audit, and fail-closed export policy.

## Accessibility plan

Use numbered gates with pass, fail, and unresolved words; describe all blocked paths and their recorded reasons.

## Failure conditions

Reject automatic export, silent redaction, missing consent scope, mutable hashes, or a privacy-guarantee implication.
