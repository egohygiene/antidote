# Antidote contracts

This directory owns the versioned, implementation-neutral boundaries shared by
the Rust core, React interface, Python model worker, fixtures, and research
tools.

## Rules

- JSON Schema is canonical for cross-language payload shape.
- Generated Rust, TypeScript, or Python types are disposable, committed review
  projections; edit schemas and regenerate rather than editing projections.
- A breaking semantic change requires a new schema version and migration plan.
- Model-native prompts and response objects stay behind adapters.
- Public fixtures contain only synthetic, non-clinical, non-identifying data.
- Validation occurs at every process, storage, import, and export boundary.

## Initial schemas

| Schema | Purpose |
| --- | --- |
| `consent-grant.v1.schema.json` | Authority over sources, purposes, actions, and retention |
| `working-context-projection.v1.schema.json` | Inspectable derived context and its source lineage |
| `moment-context.v1.schema.json` | Current state, desired transition, horizon, and explicit constraints |
| `journey-plan.v1.schema.json` | Editable semantic stages and acoustic-control intentions |
| `generation-spec.v1.schema.json` | Immutable model-worker request |
| `generation-result.v1.schema.json` | Artifact, measured features, warnings, and failure state |
| `response-observation.v1.schema.json` | Felt response, mismatch, harm, and optional aftereffect |

The model-worker transport is defined in
[`protocol/model-worker.v1.md`](protocol/model-worker.v1.md). These files are a
contract foundation, not evidence that the session runtime or worker exists.

## Generation and validation

`manifest.json` is the deterministic inventory. One repository-owned generator
emits:

- `crates/antidote-contracts/src/generated.rs`;
- `apps/desktop/src/generated/contracts.ts`; and
- `workers/generation/src/antidote_generation/generated/contracts.py`.

Regenerate and validate through either project interface:

```sh
make mvp-contracts
make mvp-contracts-check
```

The Task equivalents are `task mvp:contracts` and
`task mvp:contracts-check`. The check rejects generated drift and runs
`fixtures/cases.json` through Rust `jsonschema`, TypeScript Ajv, and Python
`jsonschema` with date-time formats enabled.

## Compatibility

The seven current payloads are version `1.0.0`. A breaking field, meaning,
requiredness, enum, or validation change requires a new schema version, a new
`$id`, parallel fixtures, regenerated types, and a documented migration. Model
protocol envelopes remain separately versioned and are not generated from the
payload manifest.
