# Antidote Rust crates

## Status

Executable Cargo workspace scaffold pinned to Rust `1.97.1`. Contract types and
runtime JSON Schema validation are implemented; the domain and adapter crates
remain honest boundaries for later issues.

Rust will own Antidote's domain and application authority. Frameworks and
providers remain outside the core. The initial intended boundaries are:

| Crate | Responsibility |
| --- | --- |
| `antidote-contracts` | Generated Rust types and validation against canonical JSON Schemas |
| `antidote-core` | Pure moment, consent, journey, session, response, safety, and adaptation behavior |
| `antidote-store` | Event, projection, SQLite, payload, and migration ports/adapters |
| `antidote-provenance` | Hashes, run manifests, model cards, W3C PROV concepts, and research export |
| `antidote-audio` | Playback, cancellation, analysis-reference, and export ports/adapters |

Crates integrate through explicit public types and ports. They do not import
React state, Python model objects, Tauri window types, or sibling repository
source.

`antidote-core` currently depends only on `antidote-contracts`. The store,
provenance, and audio crates contain status-only scaffolds until their owning
issues land.
