# Antidote

[![Research paper](https://img.shields.io/github/actions/workflow/status/egohygiene/antidote/research-paper.yml?branch=main&style=for-the-badge&label=Research%20paper)](https://github.com/egohygiene/antidote/actions/workflows/research-paper.yml)
[![GitHub Pages](https://img.shields.io/github/actions/workflow/status/egohygiene/antidote/pages.yml?branch=main&style=for-the-badge&label=GitHub%20Pages)](https://github.com/egohygiene/antidote/actions/workflows/pages.yml)
[![Status](https://img.shields.io/badge/status-writing%20draft-FFD48A?style=for-the-badge)](./ROADMAP.md)

Antidote is a provisional research program about personalized, adaptive
generative audio. Its central question is:

> Can an adaptive system learn an individual mapping from interpretable sonic
> language to generated acoustic structure to affective response, and use that
> mapping to better target future state transitions?

The first paper is intentionally scoped as a methods, system, and N-of-1
feasibility study. The originating experience is a hypothesis generator, not
evidence of clinical efficacy or a neurological mechanism.

## Write and build

The manuscript, bibliography, figures, research notes, source records, and
native publication build are owned here. Start with
[`paper/README.md`](./paper/README.md), then replace the visibly marked draft
blocks under `paper/sections/` as the evidence work advances.

Use either developer interface:

```sh
make check-all
task check-all
```

Both call the same project-owned `scripts/tasks.py` implementation and build
without Beacon. Outputs are written to `build/<theme>/`:

- `paper.pdf`;
- `web/index.html`;
- an arXiv-oriented source archive;
- `provenance.json`.

Build the complete local publication site with either `make check-site` or
`task check-site`. The staged result appears under `_site/` and includes the
landing page, accessible paper, PDF, provenance, publication manifest, source
bundle, and SHA-256 inventory.

Beacon remains an optional control plane for profile inspection, planning,
transactional builds, and checksummed packaging:

```sh
python3 scripts/beacon.py doctor
python3 scripts/beacon.py plan
python3 scripts/beacon.py package
```

The immutable upstream revision is recorded in
`dependencies/beacon.lock.toml`; native Make and Task commands never resolve it.

Run `make inventory` to verify that migration evidence preserved byte-for-byte
still matches its recorded Empathy Git blobs.

## Research layout

```text
paper/                  canonical LaTeX manuscript, bibliography, and figures
scripts/                product-owned build, validation, Pages, and Beacon adapters
latex/, themes/, web/   standalone research-paper rendering kit
research/bootstrap/     preserved hypothesis-generating research snapshot
research/notes/         working evidence and claim ledgers
research/sources/       primary-source verification records
data/                   schemas and explicitly approved research data only
docs/decisions/         architectural decisions
dependencies/           immutable upstream dependency locks
docs/                   Pages landing source, activation guide, and decisions
```

See `MIGRATION.md` for the exact Empathy source commit, tree, and file-level
disposition. The old local templates were deliberately not migrated. The
current project-owned build kit is an auditable projection of Beacon's original
MIT-licensed profile, not a copy of those provisional templates.

## Pages publication

The workflow always builds a reviewable Pages artifact but deploys only when
the repository variable `PAGES_ENABLED` is exactly `true`. This keeps merges
green until the repository's Pages source and optional DNS are configured.

Activation steps are in [`docs/pages-activation.md`](./docs/pages-activation.md).
The default route is intended to be <https://egohygiene.github.io/antidote/>;
an optional custom domain remains a maintainer-controlled setting.

## Status and boundaries

- Project codename: provisional.
- Manuscript stage: draft.
- Formal study results: none collected.
- Public site: GitHub Pages selected; deployment activation pending.
- Agent package: not selected.
- Empathy runtime dependency: none.

Repository automation and non-manuscript documentation are MIT-licensed. The
draft manuscript remains all rights reserved until a publication license is
explicitly selected; see `paper/LICENSE.md`.
