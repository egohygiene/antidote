# antidote-store

Planned Rust persistence adapters for the append-only event record, versioned
projections, consent records, classified payload references, artifact index,
and schema migrations.

SQLite and a content-addressed filesystem are the MVP candidates. Encryption,
key recovery, backup, secure deletion, tombstones, and projection invalidation
must be decided and tested before non-developer personal use.
