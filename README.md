# Antidote

[![Research paper](https://img.shields.io/github/actions/workflow/status/egohygiene/antidote/research-paper.yml?branch=main&style=for-the-badge&label=Research%20paper)](https://github.com/egohygiene/antidote/actions/workflows/research-paper.yml)
[![GitHub Pages](https://img.shields.io/github/actions/workflow/status/egohygiene/antidote/pages.yml?branch=main&style=for-the-badge&label=GitHub%20Pages)](https://github.com/egohygiene/antidote/actions/workflows/pages.yml)
[![MVP foundation](https://img.shields.io/github/actions/workflow/status/egohygiene/antidote/mvp.yml?branch=main&style=for-the-badge&label=MVP%20foundation)](https://github.com/egohygiene/antidote/actions/workflows/mvp.yml)
[![Status](https://img.shields.io/badge/status-writing%20draft-FFD48A?style=for-the-badge)](./ROADMAP.md)

Antidote is a provisional research program about personalized, adaptive
generative audio. Its central question is:

> Can an adaptive system learn an individual mapping from interpretable sonic
> language to generated acoustic structure to affective response, and use that
> mapping to better target future state transitions?

The first paper is intentionally scoped as a methods, system, and N-of-1
feasibility study. The originating experience is a hypothesis generator, not
evidence of clinical efficacy or a neurological mechanism.

## Architecture and prototype status

Antidote now has a provisional Ego Hygiene architecture corpus and the first
implementation-neutral contracts for a local demo MVP. The runtime target is a
Tauri 2 desktop host with a React interface, a framework-independent Rust domain
and control plane, SQLite plus local content-addressed artifacts, and an
isolated Python/PyTorch model worker.

The pinned Rust, Tauri/React, and Python workspaces compile and validate the
same synthetic contract fixtures. The framework-independent Rust session core
and SQLite/content-addressed persistence adapters are implemented and tested. A
packaged deterministic Python mock worker now exercises the complete v1 NDJSON
protocol and creates synthetic WAV artifacts without an AI model. These layers
are not wired into the desktop yet; no real model generation, playback
experience, or autonomous adaptation behavior exists.

Start with:

- [`META.md`](./META.md) for the 18-document architecture graph;
- [`ARCHITECTURE.md`](./ARCHITECTURE.md) for runtime and publication structure;
- [`ONTOLOGY.md`](./ONTOLOGY.md) for the moment–journey–audio–response language;
- [`DECISIONS.md`](./DECISIONS.md) for accepted MVP boundaries;
- [`docs/getting-started.md`](./docs/getting-started.md) for the current developer path;
- [`contracts/README.md`](./contracts/README.md) for cross-language payloads.

## Write and build

The manuscript, bibliography, figures, research notes, source records, and
native publication build are owned here. Start with
[`paper/README.md`](./paper/README.md), then replace the visibly marked draft
blocks under `paper/sections/` as the evidence work advances.
Scientific figures and tables are allocated through the
[`paper/visuals/manifest.json`](./paper/visuals/manifest.json) contract before
assets become active.

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

Build the complete local publication site with either
`make check-site HOLON_SOURCE=../holon` or
`task check-site HOLON_SOURCE=../holon`. The Holon path must be the exact
commit recorded in `publication/antidote-site-suite.lock.json`. The staged
result appears under `_site/` and includes the
publication hub, accessible paper, stable PDF, planned magazine route,
downloads index, provenance, publication and site manifests, source bundle,
and complete SHA-256 inventory.

For a served PDF and browser feedback loop, run
`make preview HOLON_SOURCE=../holon` or its Task equivalent. See
[`docs/paper-preview.md`](./docs/paper-preview.md) for PR
artifact review, merged-revision verification, and troubleshooting.

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

Bootstrap and validate the MVP foundation through the same interface:

```sh
make mvp-bootstrap
make mvp-check
```

The Task equivalents are `task mvp:bootstrap` and `task mvp:check`. Contract
types are regenerated with `make mvp-contracts`; CI uses
`make mvp-contracts-check` to reject drift. None of these commands downloads a
model or accepts personal data.

## Research layout

```text
paper/                  canonical LaTeX manuscript, bibliography, visual manifest, figures, and tables
scripts/                product-owned build, validation, Pages, and Beacon adapters
latex/, themes/, web/   standalone research-paper rendering kit
research/bootstrap/     preserved hypothesis-generating research snapshot
research/atlas/         complete living literature voyage and reading order
research/notes/         working evidence and claim ledgers
research/sources/       source catalog, lifecycle rules, and verification records
data/                   schemas and explicitly approved research data only
apps/desktop/           pinned Tauri and React workspace; session UI remains target
crates/                 Rust contract, domain, store, provenance, and audio boundaries
workers/generation/     executable deterministic mock worker; real adapters remain target
contracts/              canonical schemas, manifest, fixtures, and process protocol
experiments/protocols/  future frozen study and analysis definitions
docs/decisions/         detailed architectural decision records
dependencies/           immutable upstream dependency locks
docs/                   architecture guides, Pages source, activation, and decisions
```

See `MIGRATION.md` for the exact Empathy source commit, tree, and file-level
disposition. The old local templates were deliberately not migrated. The
current project-owned build kit is an auditable projection of Beacon's original
MIT-licensed profile, not a copy of those provisional templates.

## Pages publication

The workflow materializes Holon's exact-pinned LaunchKit/Zensical site suite,
composes Antidote's byte-preserved publication artifacts, and always uploads a
reviewable Pages artifact. It deploys only when
the repository variable `PAGES_ENABLED` is exactly `true`. This keeps merges
green until the repository's Pages source, DNS, and TLS are configured.

The canonical route is <https://antidote.egohygiene.io/>. GitHub's
<https://egohygiene.github.io/antidote/> route remains a technical fallback,
not a second canonical publication URL. Activation and rollback steps are in
[`docs/pages-activation.md`](./docs/pages-activation.md).

After a successful `main` deployment, `make live-check` rejects stale routes,
revision disagreement, and artifact hashes that do not match the published
manifests.

The stable public route contract is:

- `/` — publication catalog;
- `/docs/`, `/architecture/`, and `/legal/` — shared-framework public surfaces
  populated and governed by Antidote;
- `/paper/` and `/antidote.pdf` — available paper editions;
- `/magazine/` — an explicitly planned slot with no fabricated download;
- `/downloads/` — available paper artifacts and integrity evidence;
- `/publication.json`, `/site.json`, `/site-suite.provenance.json`, and
  `/SHA256SUMS` — machine-readable publication and composition state.

Actual magazine authoring is tracked separately in
[issue #5](https://github.com/egohygiene/antidote/issues/5).

## Status and boundaries

- Project codename: provisional.
- Manuscript stage: draft.
- Formal study results: none collected.
- Public site: custom-domain GitHub Pages hub implemented; deployment
  activation and TLS verification remain maintainer-controlled.
- Agent package: not selected.
- Empathy runtime dependency: none.
- Local prototype: an accessible Tauri/React synthetic session composes the
  authoritative Rust core, local persistence, deterministic mock worker,
  deliberate playback, response capture, safety halts, and restart recovery;
  real-model audio, privacy hardening, packaging, and study use remain incomplete.
- Formal study data: none collected.

Repository automation and non-manuscript documentation are MIT-licensed. The
draft manuscript remains all rights reserved until a publication license is
explicitly selected; see `paper/LICENSE.md`.
