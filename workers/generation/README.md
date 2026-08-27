# Antidote generation worker

## Status

Target scaffold. No model implementation or weight dependency is selected.

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
