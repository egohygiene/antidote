# Antidote generation worker

## Status

Executable Python workspace scaffold pinned to Python `3.12.13` and uv
`0.11.33`. Canonical-schema validation and generated type projections exist.
No worker process, model package, model implementation, or weight dependency is
selected.

## Responsibility

The local Python/PyTorch worker will:

- report adapters, models, licenses, controls, durations, hardware, and
  restrictions;
- load an explicitly pinned and integrity-checked model revision;
- validate and execute an immutable generation specification;
- stream non-sensitive progress and support cooperative cancellation;
- analyze declared acoustic features and control adherence;
- return artifacts, hashes, runtime metadata, downgrades, warnings, and failure
  classification.

It will not access the local database, search personal history, decide consent,
update a personal model, control publication, or reinterpret a participant's
response.

## Candidate evaluation

ACE-Step 1.5 is the leading first-adapter candidate because its published
interface exposes duration and musical controls and its model card identifies
an MIT license. MusicGen/AudioCraft remains a comparison baseline; official
weights carry a noncommercial license. No candidate lands until its code,
weights, license, remote-code requirement, training/output claims, controls,
hardware behavior, and known failures are audited.

## Protocol

See [`../../contracts/protocol/model-worker.v1.md`](../../contracts/protocol/model-worker.v1.md).

## Commands

The repository-owned path is `make mvp-check` or `task mvp:check`. For a focused
Python loop after bootstrap:

```sh
uv run --project workers/generation --locked pytest
uv run --project workers/generation --locked ruff check workers/generation
```

The generated module under `src/antidote_generation/generated/` is a disposable,
committed projection. Change `contracts/schemas/` and run
`make mvp-contracts`; do not edit generated types directly.
