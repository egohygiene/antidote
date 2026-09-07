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
| `consent-grant.v1.schema.json` | Implemented MVP authority over sources, purposes, actions, and retention |
| `consent-grant.v2.schema.json` | Prospective H1 authority, including distinct analyze and play scopes |
| `working-context-projection.v1.schema.json` | Inspectable derived context and its source lineage |
| `moment-context.v1.schema.json` | Current state, desired transition, horizon, and explicit constraints |
| `journey-plan.v1.schema.json` | Editable semantic stages, acoustic-control intentions, additive rule traces, control policy, revision lineage, and immutable plan hash |
| `generation-spec.v1.schema.json` | Immutable model-worker request |
| `generation-result.v1.schema.json` | Artifact, measured features, warnings, and failure state |
| `h1-public-result-envelope.v1.schema.json` | Strict aggregate-only, privacy-reviewed H1 public package envelope |
| `private-evidence-index.v1.schema.json` | Private commitment index; instances must remain outside Git |
| `response-observation.v1.schema.json` | Implemented MVP response boundary retained for byte-compatible replay |
| `response-observation.v2.schema.json` | Prospective H1 response, field-level missingness, later-window fields, and correction lineage |

The journey-plan additions are optional at the compatibility schema boundary so
older v1 readers remain valid. The Rust execution boundary requires them for a
new executable plan and verifies their hash, trace coverage, ruleset, lineage,
and policy before accepting a proposal.

The v2 consent and response schemas are prospective H1 contracts introduced by
the corrective audit in issue #82. They are generated and fixture-tested, but
the current desktop, Rust session events, and SQLite replay boundary remain on
v1 and are not protocol-qualified collection infrastructure. In particular,
the current MVP does not implement the frozen immediate/later instrument,
field-level missingness capture, response correction workflow, or H1 timing
scheduler. See [the v1-to-v2 migration note](migrations/response-and-consent-v1-to-v2.md);
adapters must not relabel a v1 record as qualifying H1 evidence.

Response v2 enforces the record-local shape of correction and missingness: an
original revision has null supersession fields, a later revision names a
superseded response and non-empty reason, every instrument scalar or optional
text is explicitly present, and every null has exactly one field-specific
reason while present values have none. A future H1 authority boundary must
still verify cross-record revision increments, prevent branching or reuse of a
superseded record, and enforce which fields are prompted in each window; JSON
Schema alone cannot establish those relationships.

Each v2 consent grant carries exactly one action so that inspect, project,
generate, analyze, play, retain, learn, and export authority can be revoked
independently. Multiple authorized actions require distinct grant IDs. A play
grant expresses scope only; the person must still approve the exact artifact
and deliberately start playback.

The H1 public envelope deliberately defines no participant, session, consent,
source-event, private-path, free-text-response, or per-record-hash field. Public
packages and the private evidence index share only the evidence-set ID,
commitment profile, evidence-set SHA-256, and aggregate record count. The
private index also contains a secret nonce, package-local opaque references,
and payload hashes; its instances and nonce stay outside Git. The public digest
is an integrity commitment, not proof of anonymization, consent,
authentication, truth, or completeness.

The model-worker transport is defined in
[`protocol/model-worker.v1.md`](protocol/model-worker.v1.md). The deterministic
mock under `workers/generation/` executes this transport through the bounded
Rust supervisor. That is evidence of protocol and supervision implementation,
not evidence of a real audio model or an end-to-end desktop session.

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

The seven implemented MVP payloads remain version `1.0.0`. The manifest also
contains additive prospective H1 consent, response, public-envelope, and
private-index contracts; their presence does not migrate stored v1 events or
activate collection. `ConsentGrantV2` and `ResponseObservationV2` use payload
version `2.0.0`; the two newly introduced envelope schemas use `1.0.0`. A
breaking field, meaning,
requiredness, enum, or validation change requires a new schema version, a new
`$id`, parallel fixtures, regenerated types, and a documented migration. Model
protocol envelopes remain separately versioned and are not generated from the
payload manifest.
