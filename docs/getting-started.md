# Getting started

## Current status

Antidote's research and publication system is executable. Its desktop MVP has
an executable workspace, shared v1 contracts, a framework-independent Rust
session core, and tested SQLite/content-addressed persistence adapters. The
deterministic mock worker is also executable as a standalone NDJSON process.
The desktop now invokes these layers for one end-to-end synthetic session,
including deliberate mock-WAV playback, response capture, adverse-event
handling, cancellation, and restart recovery. No real audio model, therapeutic
claim, packaged release, or autonomous personalization exists.

## Prerequisites for current checks

- Python 3;
- a POSIX-compatible shell for the existing scripts;
- Make or Task for the project-owned command interface;
- the LaTeX and Pandoc dependencies described by the publication diagnostics
  when building all output formats.

The MVP workspace additionally requires:

- Rust `1.97.1` with Clippy and rustfmt;
- Node `24.19.x` and pnpm `11.19.x`;
- Python `3.12.13` and uv `0.11.33`;
- the operating-system prerequisites documented by Tauri 2 for desktop builds.

See [`docs/mvp-toolchains.md`](mvp-toolchains.md) for the exact pin ownership,
developer platform matrix, Tauri capability baseline, and recovery boundary.

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

## Bootstrap and validate the MVP foundation

Restore the exact lockfile-backed dependencies:

```sh
make mvp-bootstrap
task mvp:bootstrap
```

Run the complete Rust, TypeScript, Python, Tauri, and shared-contract gate with
either equivalent interface:

```sh
make mvp-check
task mvp:check
```

Regenerate disposable language projections from canonical schemas with
`make mvp-contracts` or `task mvp:contracts`. CI uses
`make mvp-contracts-check` to fail when committed outputs drift. The common
fixture suite is `contracts/fixtures/cases.json` and contains synthetic,
non-clinical data only.

The focused persistence loop is:

```sh
cargo test --locked --package antidote-store
cargo clippy --locked --package antidote-store --all-targets --all-features -- --deny warnings
```

Storage recovery and current privacy limitations are documented in
[`crates/antidote-store/README.md`](../crates/antidote-store/README.md). The
adapter is developer-only and must receive synthetic content until encryption,
key recovery, retention, deletion, and privacy-review requirements are complete.

The focused mock-worker loop is:

```sh
uv run --project workers/generation --locked pytest
uv run --project workers/generation --locked ruff check workers/generation
printf '%s\n' '{"protocol_version":"1.0.0","request_id":"health-local","operation":"health","payload":{}}' \
  | uv run --project workers/generation --locked antidote-generation-worker
```

The worker accepts synthetic inputs only at this stage. Its exact envelopes,
operation payloads, message bound, and failure taxonomy are documented in
[`contracts/protocol/model-worker.v1.md`](../contracts/protocol/model-worker.v1.md).

Run the local desktop experience after bootstrap with:

```sh
pnpm --filter @egohygiene/antidote-desktop tauri dev
```

Use synthetic check-in text only. The desktop persists its active session in
Tauri's application-local data directory and reconstructs the screen from the
Rust/SQLite event record after a refresh or restart.

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
7. [`ROADMAP.md`](../ROADMAP.md), beginning with the active `ANT-Q03` sequence.

Do not install a real audio model during workspace bootstrap. The first
executable slice uses a mock worker and synthetic fixtures so consent, state,
cancellation, provenance, and failure behavior can be tested independently of
GPU availability or a model license.

If bootstrap is interrupted, remove only generated dependency/build directories
(`target/`, `node_modules/`, `apps/desktop/dist/`, and
`workers/generation/.venv/`) and rerun `make mvp-bootstrap`. Canonical source,
schemas, fixtures, and lockfiles must remain intact.

## Sensitive information

Do not place journal entries, therapy content, participant records, health data,
credentials, model tokens, or private generated audio in this public checkout.
Use synthetic inputs until protocol, consent, classification, encryption, and
retention boundaries are implemented and reviewed.
