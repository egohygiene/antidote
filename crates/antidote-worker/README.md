# Antidote worker supervisor

## Status

Implemented Rust process boundary for model-worker protocol v1. The supervisor
uses an explicit executable, argument vector, cleared environment, working
directory, and output root. It negotiates protocol and capabilities before
loading an immutable adapter/model identity.

The worker receives no database handle or session repository. The only
filesystem path sent in a generation request is a host-created directory below
the approved output root. Returned artifacts are canonicalized, bounded,
hashed, and checked against that directory before the Rust core can record a
result.

Progress, cancellation, health, timeout, process exit, malformed output,
partial artifacts, stderr draining, cleanup, and restart are covered by tests
against the deterministic Python worker. This is a development supervisor, not
an operating-system sandbox or a packaged end-user sidecar.
