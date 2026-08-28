# Model worker protocol v1

## Status

Executable mock contract for the Antidote MVP. The implementation under
`workers/generation/` exercises this protocol without a model dependency.

## Boundary

The Rust control plane launches a local capability-scoped worker and exchanges
newline-delimited UTF-8 JSON over standard input and standard output. Standard
error is diagnostic only and must not carry protocol messages. Each request has
an ID, operation, protocol version, and operation-specific payload; each
response repeats the request ID.

The worker does not receive filesystem or database authority beyond explicitly
granted input and output locations. It receives the approved semantic projection
and immutable generation specification, never unrestricted personal history.

## Transport envelope

Each input line is one JSON object encoded as UTF-8 and terminated by `\n`. The
maximum encoded request line, including the newline, is 65,536 bytes. Duplicate
JSON keys, additional envelope fields, invalid UTF-8, non-object payloads, and
request IDs outside `[A-Za-z0-9._:-]{1,128}` fail closed.

```json
{
  "protocol_version": "1.0.0",
  "request_id": "request-001",
  "operation": "health",
  "payload": {}
}
```

The worker emits one or more response envelopes. `progress` can precede one
terminal `result` or `error`. An envelope never contains the submitted source
text merely to explain validation or progress.

```json
{
  "protocol_version": "1.0.0",
  "request_id": "request-001",
  "operation": "health",
  "kind": "result",
  "payload": {}
}
```

Protocol errors that occur before a request ID or operation is trusted use
`null` for that field. Error payloads contain only a stable `code`, a generic
`message`, and `retryable`; field paths may be reported, submitted values may
not.

## Operation payloads

| Operation | Required request fields | Result summary |
| --- | --- | --- |
| `hello` | `host{name,version}`, `supported_protocol_versions[]` | Worker/code identity and selected protocol |
| `capabilities` | optional `adapter_id` | Mock adapter/model, controls, duration, license, device, and restrictions |
| `load_model` | `adapter{id,version}`, `model{id,revision}`; optional model `artifact_hash` | Loaded immutable identity, device, memory, and warnings |
| `generate` | canonical `spec`, absolute `output_directory`; optional test-only `simulation` | Progress then canonical `generation-result.v1` |
| `analyze` | `artifact{path,sha256}`, `analyses[]` | Declared WAV features, analyzer identity, input/output hash, and warnings |
| `cancel` | `target_request_id` | `accepted`, `already_complete`, or `unsupported` |
| `health` | no fields | Readiness, loaded identity, active-job count, device, and resource summary |

The mock-only `simulation` object can select `normal`, `timeout`, `partial`, or
`crash` and can add a bounded per-chunk delay for cancellation tests. It is not
a model-adapter capability and must never cross into a production adapter.

Stable failure classes are `invalid_input`, `unsupported_version`,
`unknown_operation`, `message_too_large`, `unsupported_control`,
`model_not_loaded`, `cancelled`, `timeout`, `partial_output`,
`worker_crash`, `integrity_mismatch`, and `internal_error`.

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
- The deterministic mock writes WAV data to a temporary path and only publishes
  a completed artifact through an atomic replacement. Cancellation removes the
  temporary path; a simulated partial result is renamed and classified visibly.
- Closing standard input requests orderly worker shutdown: active mock jobs are
  cooperatively cancelled and drained so a detached process cannot leave an
  unclassified temporary artifact.

## Security review items

- Pin sidecar binary and model artifact hashes.
- Audit all required remote model code before enabling it.
- Constrain executable arguments and accessible paths through Tauri capabilities.
- Bound message and artifact sizes and reject path traversal.
- Redact personal payloads from logs and crash reports.
- Define timeout, cancellation, orphan-process, and partial-file cleanup behavior.
