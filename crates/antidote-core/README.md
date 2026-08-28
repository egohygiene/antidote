# antidote-core

Framework-independent Rust domain and application crate. It owns the
authoritative, event-sourced session state machine introduced by issue #11.

The core models validated commands and immutable events for consent grants,
working projections, moments, journey approval, generation jobs, deliberate
playback, actual exposures, responses, safety halts, personal-model proposals,
and privacy-reviewed export approval. `SessionService` reloads and replays the
event stream before deciding each command, then appends with an expected
version.

Human approval is a separate transition before generation, playback,
adaptation acceptance, and export. Applicable consent is checked again at the
action boundary. Expired, revoked, ambiguous, and wrong-purpose grants fail
closed; safety events halt continuation; failed or rejected model updates leave
the prior snapshot unchanged.

Ports isolate time, identifiers, event persistence, worker invocation, audio,
artifact storage, and export. Deterministic in-memory adapters exercise the
state machine without a UI, database, Python process, audio device, or model.

It will not depend on Tauri, React, SQLite, Python, a particular audio model,
or publication tooling.
