# ADR-0004: Use a local-first desktop host with a Rust core and isolated model worker

- Status: Accepted for MVP
- Date: 2026-08-27
- Decision owners: Ego Hygiene / Antidote
- Applies to: Demo MVP prototype

## Context

Antidote needs an emotionally focused interface, durable local state, explicit
permission boundaries, and access to rapidly evolving open audio-generation
models. The user selected a React interface and Rust backend. Most viable audio
generation implementations currently depend on Python, PyTorch, CUDA, and
model-specific preprocessing. Reimplementing those stacks in Rust would delay
the research question and obscure comparison with published implementations.

A browser application plus an always-running server would also make the local
ownership and process boundary less clear than a packaged desktop research
instrument.

## Decision

The MVP uses:

- Tauri 2 as the local desktop host;
- React and TypeScript for the interface;
- a framework-independent Rust domain core for consent, state transitions,
  orchestration, storage, provenance, policy, and progress events;
- SQLite plus content-addressed local files as the source-of-truth adapters;
- a replaceable, permission-scoped Python/PyTorch sidecar for generation and
  audio analysis;
- a small versioned protocol whose operations include capability discovery,
  model loading, generation, analysis, cancellation, and health.

The Rust core must not depend on Tauri. A later Axum adapter may expose the same
application ports for an Ego Hygiene integration without moving the canonical
local record into a required web service.

The sidecar receives an immutable generation specification and approved semantic
projection—not database credentials or unrestricted personal-history access.

## Implementation evidence

The deterministic mock worker under `workers/generation/` now implements the
complete v1 NDJSON operation set without PyTorch, weights, network access, or
database authority. It validates before filesystem mutation, writes synthetic
WAV artifacts atomically, reports stable identity and hashes, redacts progress,
and classifies cancellation and simulated failure paths. The Rust supervisor
under `crates/antidote-worker/` now applies explicit process configuration,
protocol negotiation, capability checks, correlation, bounded progress,
cancellation, timeouts, restart, redacted diagnostics, output-directory grants,
and artifact integrity verification. The core generation orchestrator owns the
only state-changing commands and records an untrusted worker failure as failed.

The webview still receives no shell or sidecar permission: model execution is a
Rust application adapter, not a JavaScript capability. The Tauri host now
exposes a named-command session API, opens the application-local SQLite record,
supervises the developer mock worker, and returns recoverable projections to
React. Packaged external binaries, operating-system sandboxing, privacy-ready
production data paths, and real-model execution remain unimplemented and are
not implied by this evidence.

## Consequences

- Rust remains the unambiguous authority boundary while Python remains a
  replaceable inference implementation.
- The system can compare models without changing its domain ontology.
- Packaging, model integrity, `trust_remote_code`, GPU compatibility, and worker
  cancellation become explicit engineering and security work.
- CPU-only or low-memory support is not claimed until measured.
- A pure-Rust inference path through Candle or ONNX remains possible after
  operator and numerical compatibility are proven.

## Reconsider when

- A suitable generator runs reliably through a maintained Rust-native runtime;
- the sidecar prevents required packaging or sandboxing on a supported desktop;
- a future Ego Hygiene host supplies an equivalent local process and permission
  boundary through a versioned contract.
