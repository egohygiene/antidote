# antidote-store

Workspace scaffold for planned Rust persistence adapters for the append-only event record, versioned
projections, consent records, classified payload references, artifact index,
and schema migrations. Issue #12 owns implementation.

SQLite and a content-addressed filesystem are the MVP candidates. Encryption,
key recovery, backup, secure deletion, tombstones, and projection invalidation
must be decided and tested before non-developer personal use.
