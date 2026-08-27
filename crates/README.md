# Antidote Rust crates

## Status

Target scaffold. No Cargo workspace or crate manifests exist yet.

Rust will own Antidote's domain and application authority. Frameworks and
providers remain outside the core. The initial intended boundaries are:

| Crate | Responsibility |
| --- | --- |
| `antidote-core` | Pure moment, consent, journey, session, response, safety, and adaptation behavior |
| `antidote-store` | Event, projection, SQLite, payload, and migration ports/adapters |
| `antidote-provenance` | Hashes, run manifests, model cards, W3C PROV concepts, and research export |
| `antidote-audio` | Playback, cancellation, analysis-reference, and export ports/adapters |

Crates integrate through explicit public types and ports. They do not import
React state, Python model objects, Tauri window types, or sibling repository
source.
