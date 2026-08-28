# antidote-store

Local persistence adapters for the Antidote MVP authority boundary.

## Implemented boundary

- `SqliteEventStore` applies versioned migrations and implements the
  `antidote-core` event-repository port.
- Event envelopes are transactionally appended in deterministic session order,
  protected from update/delete by database triggers, and verified against a
  stored SHA-256 digest during every load.
- Optimistic expected-version checks reject stale writers. Repeating the exact
  append is idempotent; a different stale append fails visibly.
- Consent, working context, moments, journeys, generation runs, artifact
  metadata, exposures, responses, safety events, personal-model snapshots, and
  exports are disposable named projections rebuilt from the immutable stream.
- Every projection row links to its producing event. Working-context
  projections also retain their declared source-event lineage.
- `ContentAddressedStore` writes payload or artifact bytes through a temporary
  file, synchronizes them, and atomically links them to a lowercase SHA-256
  address. Exact content deduplicates; missing or altered content fails hash
  verification.
- The payload registry stores classification, relative path, media type, size,
  source-event reference, and registration time—never payload bytes.

Schema v1 is owned by `migrations/0001_initial.sql`. The database and object
root are supplied by the host adapter; `antidote-store` does not select a user
directory or grant a worker access to either location.

## Recovery and validation

`SqliteEventStore::verify_integrity` combines SQLite's physical integrity check
with event-order, envelope, digest, and domain-replay validation.
`rebuild_projections` replaces only derived rows inside one transaction. If
verification or rebuilding fails, previously committed events and projections
remain intact. `ContentAddressedStore::open` removes only its own abandoned
temporary-file pattern; it never guesses that an addressed object is disposable.

Run the focused checks with:

```sh
cargo test --locked --package antidote-store
cargo clippy --locked --package antidote-store --all-targets --all-features -- --deny warnings
```

## Developer-only data boundary

This implementation proves local integrity and recovery behavior; it is not a
privacy-readiness claim. Database rows and object bytes are currently
unencrypted at rest. Backup, key creation and recovery, operating-system secret
storage, secure deletion, tombstones, retention enforcement, projection
invalidation after deletion, and adversarial privacy review remain unresolved.

Use only synthetic, non-clinical, non-identifying content until those controls
are designed, implemented, tested, and reviewed. Do not point the current
adapter at journals, therapy transcripts, health records, participant data, or
private generated audio.
