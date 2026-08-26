# ADR-0003: Publish a catalog with honest future-format slots

- Status: Accepted
- Date: 2026-08-26
- Decision owners: Ego Hygiene / Antidote
- Related issues: `egohygiene/antidote#4`, `egohygiene/antidote#5`
- Amends: ADR-0002's optional custom-domain contract

## Context

Antidote has a standalone research-paper build and a gated GitHub Pages
projection. The selected public domain is `antidote.egohygiene.io`, and the
product also needs a stable home for an eventual magazine. Reserving that home
must not fabricate an edition, artifact, or scientific claim.

The site also needs to remain independently understandable by people and by
future publication tooling. One paper-specific manifest cannot describe both
available and future formats without weakening its meaning.

## Decision

Antidote owns a publication hub with stable paper, magazine, download, and
integrity routes. `publication.json` continues to describe the current paper.
A separate deterministic `site.json` catalogs public routes and publication
slots.

Slot status is explicit. An `available` slot may list only artifacts that exist
and whose SHA-256 digests validate. A `planned` slot has an empty artifact list
and no publication stage or manifest. Activating a slot is an atomic source and
build change, not a content-management toggle.

The custom domain is fixed in the source publication configuration. A
`PAGES_CUSTOM_DOMAIN` workflow variable, when present, must match that value.
The GitHub project URL remains a technical fallback but is not canonical.
Pull-request workflows build and validate the full site; only the gated
`main` workflow may deploy.

Actual magazine authoring is separate work under issue #5. It must preserve the
project-owned Make/Task build boundary established in ADR-0002.

## Consequences

- Readers can distinguish what is available from what is merely intended.
- Automation has one stable route and slot inventory without overloading the
  paper manifest.
- Broken, escaping, unhashed, or fabricated artifacts fail staging.
- Canonical URLs remain consistent across human pages, manifests, and
  structured data.
- The future magazine can activate without restructuring the site, but only
  after real source and verified artifacts land together.
- Relay and organization-wide Pages refactoring remain downstream work after
  the consumer contract is proven.
