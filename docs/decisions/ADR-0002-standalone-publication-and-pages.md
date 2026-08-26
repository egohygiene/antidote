# ADR-0002: Own native publication execution and gate Pages deployment

- Status: Accepted
- Date: 2026-08-26
- Decision owners: Ego Hygiene / Antidote
- Related issue: `egohygiene/antidote#2`
- Supersedes: ADR-0001's Beacon runtime dependency
- Amended by: ADR-0003's selected custom domain and site catalog

## Context

Beacon pull request #18 made every initialized research paper responsible for a
complete build kit. Before this change, Antidote's Makefile resolved a pinned
Beacon checkout and executed scripts from that checkout. The content was owned
by Antidote, but the product was not independently buildable.

Reflector's compatibility canary established the desired organization boundary:
a publication owns its native build and public routes, while Beacon remains an
optional control plane. Antidote also needs a reviewable Pages surface before
the paper is complete, but repository Pages and DNS settings require explicit
maintainer activation.

## Decision

Antidote owns the Makefile, Taskfile, Python task adapter, renderer, checker,
styles, themes, web template, and Pages staging script generated from Beacon
`research-paper` `0.1.0`. Make and Task call the same local implementation and
never resolve Beacon.

The full Beacon commit remains pinned for intentional profile validation,
planning, transactional builds, packaging, and future upgrades. Those commands
are exposed separately through `scripts/beacon.py`.

The Pages workflow builds on pull requests and main. Deployment runs only when
the repository variable `PAGES_ENABLED` equals `true`. An optional
`PAGES_CUSTOM_DOMAIN` variable controls canonical URLs in the staged manifest;
the corresponding custom domain must still be configured in repository Pages
settings and DNS by a maintainer.

## Consequences

- Antidote remains buildable if Beacon is unavailable.
- Make, Task, Beacon, and future editors can target one project-owned execution
  contract.
- Build-kit upgrades are explicit diffs against an immutable Beacon revision.
- Pages activation cannot happen accidentally from a merge.
- Draft filler is allowed only through a visibly marked non-evidence macro and
  becomes a validation error at submission-ready or published stages.
- DOI, release, archive-deposit, and submission automation remain out of scope
  until the manuscript requires them.
