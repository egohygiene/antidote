# Getting started

## Current status

Antidote's research and publication system is executable. Its desktop MVP is an
architecture and contract scaffold; no Tauri, React, Rust, Python model worker,
or model dependency is present yet.

## Prerequisites for current checks

- Python 3;
- a POSIX-compatible shell for the existing scripts;
- Make or Task for the project-owned command interface;
- the LaTeX and Pandoc dependencies described by the publication diagnostics
  when building all output formats.

## Validate the repository

Use either equivalent interface:

```sh
make check-all
task check-all
```

For smaller publication loops, inspect available commands with:

```sh
make help
task --list
```

Outputs belong in `build/`, `dist/`, and `_site/` and are not canonical source.

## Navigate the research

1. Read [`README.md`](../README.md) and [`PURPOSE.md`](../PURPOSE.md).
2. Use [`META.md`](../META.md) to navigate the architecture corpus.
3. Read [`research/bootstrap/03-scientific-boundaries.md`](../research/bootstrap/03-scientific-boundaries.md).
4. Review [`research/notes/CLAIM_LEDGER.md`](../research/notes/CLAIM_LEDGER.md) before changing claims.
5. Verify primary-source records under `research/sources/`.

## Prepare for MVP implementation

Read these in order:

1. [`ONTOLOGY.md`](../ONTOLOGY.md);
2. [`SYSTEM.md`](../SYSTEM.md);
3. [`ARCHITECTURE.md`](../ARCHITECTURE.md);
4. [`DECISIONS.md`](../DECISIONS.md), especially ADR-0004 through ADR-0007;
5. [`contracts/README.md`](../contracts/README.md) and the model-worker protocol;
6. [`docs/architecture-overview.md`](architecture-overview.md);
7. [`ROADMAP.md`](../ROADMAP.md), beginning with `ANT-Q03` after the corpus is
   accepted.

Do not install a real audio model during workspace bootstrap. The first
executable slice uses a mock worker and synthetic fixtures so consent, state,
cancellation, provenance, and failure behavior can be tested independently of
GPU availability or a model license.

## Sensitive information

Do not place journal entries, therapy content, participant records, health data,
credentials, model tokens, or private generated audio in this public checkout.
Use synthetic inputs until protocol, consent, classification, encryption, and
retention boundaries are implemented and reviewed.
