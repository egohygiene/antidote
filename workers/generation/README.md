# Antidote generation worker

## Status

Executable deterministic mock worker pinned to Python `3.12.13` and uv
`0.11.33`. It implements the complete v1 NDJSON operation set, validates the
canonical generation contracts, and emits a synthetic WAV plus declared feature
reports. It has no PyTorch, model package, model weights, network, telemetry,
database, or personal-history dependency.

## Responsibility

The local Python worker:

- report adapters, models, licenses, controls, durations, hardware, and
  restrictions;
- loads an immutable built-in mock identity and verifies its declared hash;
- validate and execute an immutable generation specification;
- stream non-sensitive progress and support cooperative cancellation;
- analyze declared acoustic features and control adherence;
- return artifacts, hashes, runtime metadata, downgrades, warnings, and failure
  classification.

It will not access the local database, search personal history, decide consent,
update a personal model, control publication, or reinterpret a participant's
response.

The mock is executable evidence for protocol behavior only. Rust supervision,
Tauri sidecar permissions, production filesystem paths, playback, real model
generation, and an end-to-end session remain unimplemented.

## Mock behavior

- input lines are strict UTF-8 JSON objects bounded to 65,536 bytes;
- validation completes before an output directory is created;
- completed WAV files are published atomically from temporary files;
- cancellation removes temporary and partial artifacts;
- closing stdin cooperatively cancels and drains active mock jobs;
- progress includes only stage, fraction, and elapsed time;
- timeout, partial output, and crash simulations are visibly classified;
- repeated canonical fixtures produce SHA-256
  `2fca813bc0f01e9f54a3fe2dbe19a6edd81cd016a051d693158bccc78d682b7b`.

The golden digest covers the WAV bytes, not a therapeutic, musical, model, or
cross-platform audio-quality claim.

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
printf '%s\n' '{"protocol_version":"1.0.0","request_id":"health-local","operation":"health","payload":{}}' \
  | uv run --project workers/generation --locked antidote-generation-worker
```

The generated module under `src/antidote_generation/generated/` is a disposable,
committed projection. Change `contracts/schemas/` and run
`make mvp-contracts`; do not edit generated types directly.
