# Antidote contracts

This directory owns the versioned, implementation-neutral boundaries shared by
the Rust core, React interface, Python model worker, fixtures, and research
tools.

## Rules

- JSON Schema is canonical for cross-language payload shape.
- Generated Rust, TypeScript, or Python types are disposable projections.
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
contract scaffold, not evidence that the runtime exists.
