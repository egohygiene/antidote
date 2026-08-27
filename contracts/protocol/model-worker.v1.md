# Model worker protocol v1

## Status

Provisional contract for the Antidote MVP. No executable worker currently
implements it.

## Boundary

The Rust control plane launches a local capability-scoped worker and exchanges
newline-delimited UTF-8 JSON over standard input and standard output. Standard
error is diagnostic only and must not carry protocol messages. Each request has
an ID, operation, protocol version, and operation-specific payload; each
response repeats the request ID.

The worker does not receive filesystem or database authority beyond explicitly
granted input and output locations. It receives the approved semantic projection
and immutable generation specification, never unrestricted personal history.

## Operations

| Operation | Input | Output |
| --- | --- | --- |
| `hello` | Host and protocol versions | Worker identity and compatible versions |
| `capabilities` | Optional adapter filter | Models, licenses, controls, durations, hardware, and restrictions |
| `load_model` | Adapter, model ID, revision, integrity expectations | Loaded identity, device, memory, and warnings |
| `generate` | `generation-spec.v1` payload | Progress events followed by `generation-result.v1` |
| `analyze` | Artifact reference and requested analyses | Feature report, versions, and warnings |
| `cancel` | Target request ID | Accepted, already complete, or unsupported status |
| `health` | No personal payload | Readiness, active jobs, device class, and resource summary |

## Invariants

- Unknown protocol versions or operations fail closed.
- Payloads validate before model loading or filesystem mutation.
- Progress events contain no personal source text.
- Cancellation is cooperative and classifies every partial artifact.
- A successful response includes model, adapter, and code revisions; elapsed
  time; device class; parameters; input hash; output hashes; and warnings.
- Capability downgrades are explicit and require host-side policy approval.
- Worker crashes never mutate canonical session state directly.

## Security review items

- Pin sidecar binary and model artifact hashes.
- Audit all required remote model code before enabling it.
- Constrain executable arguments and accessible paths through Tauri capabilities.
- Bound message and artifact sizes and reject path traversal.
- Redact personal payloads from logs and crash reports.
- Define timeout, cancellation, orphan-process, and partial-file cleanup behavior.
