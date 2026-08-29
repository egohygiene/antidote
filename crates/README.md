# Antidote Rust crates

## Status

Executable Cargo workspace pinned to Rust `1.97.1`. Contract types, runtime
JSON Schema validation, the framework-independent session core and generation
orchestrator, local SQLite/content-addressed storage adapters, and bounded model
worker supervision are implemented. Provenance, audio, and desktop-session
composition remain later boundaries.

Rust will own Antidote's domain and application authority. Frameworks and
providers remain outside the core. The initial intended boundaries are:

| Crate | Responsibility |
| --- | --- |
| `antidote-contracts` | Generated Rust types and validation against canonical JSON Schemas |
| `antidote-core` | Pure moment, consent, journey, session, response, safety, and adaptation behavior |
| `antidote-store` | Event, projection, SQLite, payload, and migration ports/adapters |
| `antidote-worker` | Strict NDJSON process supervision, capability policy, cancellation, recovery, and artifact verification |
| `antidote-provenance` | Hashes, run manifests, model cards, W3C PROV concepts, and research export |
| `antidote-audio` | Playback, cancellation, analysis-reference, and export ports/adapters |

Crates integrate through explicit public types and ports. They do not import
React state, Python model objects, Tauri window types, or sibling repository
source.

`antidote-core` depends only on `antidote-contracts`. `antidote-store` and
`antidote-worker` depend inward on core ports; the domain never depends on
SQLite, Python, or process APIs. Provenance and audio crates remain status-only
scaffolds until their owning issues land.
