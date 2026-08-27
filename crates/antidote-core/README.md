# antidote-core

Framework-independent Rust domain and application crate. Its Cargo boundary and
contract dependency compile; issue #11 owns the first domain behavior.

It will own validated state transitions and policies for consent grants,
working projections, moments, journey plans, generation jobs, exposures,
responses, safety events, and personal-model proposals. It will depend on ports
for time, identifiers, storage, workers, audio, and export.

It will not depend on Tauri, React, SQLite, Python, a particular audio model,
or publication tooling.
