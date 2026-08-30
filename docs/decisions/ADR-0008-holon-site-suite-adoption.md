# ADR-0008: Adopt Holon's exact-pinned site suite

- Status: Accepted
- Date: 2026-08-30
- Issue: [#56](https://github.com/egohygiene/antidote/issues/56)
- Depends on: ADR-0002, ADR-0003

## Context

Antidote's hand-authored publication shell proved the paper-to-CI-to-custom-
domain feedback loop, but it duplicated general landing-page and documentation
infrastructure. Holon now owns a React/Vite foundation, LaunchKit profile,
Zensical profile, and composed site-suite profile. Identity issue #57 and PR
#62 proved that a consumer can adopt those profiles without vendoring their
implementation or surrendering its own content and visual identity.

Antidote must preserve its canonical paper routes, exact paper bytes,
checksums, provenance, reproducibility, evidence boundaries, and gated Pages
deployment while consuming the shared profiles.

## Decision

Antidote consumes Holon commit
`2600baff6f6d944094da81b77e1a9a2e9e7a1cd6`. The accepted profile identities,
Git blobs, SHA-256 digests, file inventories, composition order, and Zensical
dependency lock are recorded in
`publication/antidote-site-suite.lock.json`. The build fails closed if the
checkout or any accepted input drifts.

The composition order is:

1. Materialize Holon's React/Vite, LaunchKit, Zensical, and site-suite sources
   in a temporary clean room.
2. Supply Antidote-owned reviewed content, identity assets, and bounded adapter
   behavior.
3. Run Holon's complete site-suite verification and emit
   `site-suite.provenance.json`.
4. Overlay Antidote's already-governed paper HTML, PDF, source archive,
   publication manifests, magazine placeholder, and checksum inventory.

| Owner | Authority |
| --- | --- |
| Holon | Reusable framework, profiles, composition rules, and generic validation |
| Antidote | Content, visual inputs, research claims, paper artifacts, routes, provenance, and deployment |
| Identity #57 | Prior consumer evidence only; no runtime or source dependency |

The published runtime has no Holon, Identity, package-manager, or network
dependency. Make and Task accept an explicit `HOLON_SOURCE` checkout during
build; CI checks out the exact accepted commit and compares complete Make and
Task artifacts byte-for-byte.

## Preserved contracts

The routes `/paper/`, `/antidote.pdf`, `/magazine/`, `/downloads/`,
`/publication.json`, `/site.json`, `/provenance.json`, and `/SHA256SUMS` remain
stable. The suite adds `/docs/`, `/architecture/`, `/legal/`, and
`/site-suite.provenance.json`. Real paper HTML, PDF, provenance, and source
archive bytes are copied from the governed paper build; the site suite cannot
replace them.

No site copy may imply real-model output, human evidence, treatment effect, or
clinical readiness. Results remain constrained by the paper's claim ledger and
evidence gate.

## Consequences

- Shared web infrastructure can advance in Holon and be adopted through a new
  reviewed immutable pin.
- Local site preview needs the accepted Holon checkout; paper-only writing and
  `check-all` remain independent.
- Profile upgrades are explicit dependency changes with reproducibility and
  route review, not automatic updates.
- Rollback is a normal reviewed revert to the previous Antidote staging source;
  the paper artifacts remain independently reproducible throughout.

## Validation

Acceptance requires unit tests for route, metadata, integrity, stale-revision,
and ownership failures; Holon's complete suite check; exact input validation;
two deterministic Antidote staging runs; Make/Task artifact equivalence; and
the existing post-deploy live checker.
