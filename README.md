# Antidote

Antidote is a provisional research program about personalized, adaptive
generative audio. Its central question is:

> Can an adaptive system learn an individual mapping from interpretable sonic
> language to generated acoustic structure to affective response, and use that
> mapping to better target future state transitions?

The first paper is intentionally scoped as a methods, system, and N-of-1
feasibility study. The originating experience is a hypothesis generator, not
evidence of clinical efficacy or a neurological mechanism.

## Write and build

The manuscript, bibliography, figures, research notes, and source records are
owned here. Beacon owns the template and build implementation. The dependency
lock pins the exact Beacon revision used by CI.

```sh
make check-all
```

For local development beside a Beacon checkout, avoid the network fetch:

```sh
make check-all BEACON_ROOT="../beacon"
```

Outputs are written to `build/<theme>/`:

- `paper.pdf`;
- `web/index.html`;
- an arXiv source archive;
- `provenance.json`.

Run `make inventory` to verify that migration evidence preserved byte-for-byte
still matches its recorded Empathy Git blobs.

## Research layout

```text
paper/                  canonical LaTeX manuscript, bibliography, and figures
research/bootstrap/     preserved hypothesis-generating research snapshot
research/notes/         working evidence and claim ledgers
research/sources/       primary-source verification records
data/                   schemas and explicitly approved research data only
docs/decisions/         architectural decisions
dependencies/           immutable upstream dependency locks
```

See `MIGRATION.md` for the exact Empathy source commit, tree, and file-level
disposition. The old local templates were deliberately not migrated: Beacon's
versioned profile replaces them.

## Status and boundaries

- Project codename: provisional.
- Manuscript stage: draft.
- Formal study results: none collected.
- Public site: not selected.
- Agent package: not selected.
- Empathy runtime dependency: none.

Repository automation and non-manuscript documentation are MIT-licensed. The
draft manuscript remains all rights reserved until a publication license is
explicitly selected; see `paper/LICENSE.md`.
