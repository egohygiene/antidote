use std::fs;

use antidote_contracts::{ConsentGrant, WorkingContextProjection};
use antidote_core::{
    Clock, EventRepository, IdentifierKind, IdentifierSource, PortFailure, RecordedEvent,
    SESSION_EVENT_SCHEMA_VERSION, SessionCommand, SessionEvent, SessionService,
};
use antidote_store::{
    ContentAddressedStore, PayloadClassification, PayloadReference, ProjectionKind,
    SqliteEventStore, StoreError,
};
use serde::de::DeserializeOwned;
use serde_json::Value;
use tempfile::TempDir;

const SESSION_ID: &str = "session-storage-synthetic-1";
const NOW: &str = "2026-08-28T16:00:00Z";

#[derive(Debug, Clone, Copy)]
struct FixedClock;

impl Clock for FixedClock {
    fn now_rfc3339(&self) -> Result<String, PortFailure> {
        Ok(NOW.to_owned())
    }
}

#[derive(Debug, Default)]
struct DeterministicIdentifiers {
    next: u64,
}

impl IdentifierSource for DeterministicIdentifiers {
    fn next_id(&mut self, kind: IdentifierKind) -> Result<String, PortFailure> {
        self.next += 1;
        Ok(format!("{}-{}", identifier_prefix(kind), self.next))
    }
}

fn identifier_prefix(kind: IdentifierKind) -> &'static str {
    match kind {
        IdentifierKind::Event => "event",
        IdentifierKind::PlaybackApproval => "playback",
        IdentifierKind::Exposure => "exposure",
        IdentifierKind::SafetyEvent => "safety",
        IdentifierKind::ModelUpdateProposal => "model-update",
        IdentifierKind::ExportApproval => "export",
    }
}

fn fixture<T: DeserializeOwned>(name: &str) -> T {
    let suite: Value = serde_json::from_str(include_str!("../../../contracts/fixtures/cases.json"))
        .expect("canonical fixture suite parses");
    let data = suite["cases"]
        .as_array()
        .expect("fixture cases are an array")
        .iter()
        .find(|case| case["name"] == name)
        .expect("named fixture exists")["data"]
        .clone();
    serde_json::from_value(data).expect("valid fixture matches generated type")
}

fn start_event(id: &str, sequence: u64) -> RecordedEvent {
    RecordedEvent {
        schema_version: SESSION_EVENT_SCHEMA_VERSION.to_owned(),
        id: id.to_owned(),
        session_id: SESSION_ID.to_owned(),
        sequence,
        occurred_at: NOW.to_owned(),
        event: SessionEvent::SessionStarted {
            prior_model_snapshot: None,
        },
    }
}

#[test]
fn append_is_ordered_idempotent_and_optimistically_concurrent() {
    let mut store = SqliteEventStore::open_in_memory().expect("store opens");
    let event = start_event("event-start", 1);
    store
        .append_detailed(SESSION_ID, 0, std::slice::from_ref(&event))
        .expect("first append succeeds");
    store
        .append_detailed(SESSION_ID, 0, std::slice::from_ref(&event))
        .expect("exact retry is idempotent");
    assert_eq!(
        store.load_detailed(SESSION_ID).expect("stream loads"),
        vec![event]
    );
    store
        .verify_integrity()
        .expect("database and stream verify");

    let conflicting = start_event("event-other", 1);
    let error = store
        .append_detailed(SESSION_ID, 0, &[conflicting])
        .expect_err("different stale append conflicts");
    assert!(matches!(error, StoreError::ConcurrencyConflict { .. }));
}

#[test]
fn invalid_batch_rolls_back_without_partial_facts() {
    let mut store = SqliteEventStore::open_in_memory().expect("store opens");
    let invalid = vec![start_event("event-1", 1), start_event("event-3", 3)];
    let error = store
        .append_detailed(SESSION_ID, 0, &invalid)
        .expect_err("non-contiguous batch fails");
    assert!(matches!(error, StoreError::CorruptEventStream { .. }));
    assert!(
        store
            .load_detailed(SESSION_ID)
            .expect("prior stream remains readable")
            .is_empty()
    );
}

#[test]
fn named_projections_rebuild_with_source_lineage() {
    let store = SqliteEventStore::open_in_memory().expect("store opens");
    let mut service = SessionService::new(store, FixedClock, DeterministicIdentifiers::default());
    service
        .execute(
            SESSION_ID,
            SessionCommand::StartSession {
                prior_model_snapshot: None,
            },
        )
        .expect("session starts");

    let mut grant: ConsentGrant = fixture("consent-grant-valid");
    grant.session_id = SESSION_ID.to_owned();
    service
        .execute(SESSION_ID, SessionCommand::GrantConsent { grant })
        .expect("grant records");

    let mut projection: WorkingContextProjection = fixture("working-context-projection-valid");
    projection.session_id = SESSION_ID.to_owned();
    let expected_source_ids = projection.source_event_ids.clone();
    service
        .execute(
            SESSION_ID,
            SessionCommand::AcceptWorkingProjection { projection },
        )
        .expect("projection records");

    let (mut store, _, _) = service.into_parts();
    let before = store
        .projections(SESSION_ID, ProjectionKind::WorkingContext)
        .expect("projection reads");
    assert_eq!(before.len(), 1);
    for source_id in expected_source_ids {
        assert!(before[0].source_event_ids.contains(&source_id));
    }
    assert!(
        before[0]
            .source_event_ids
            .iter()
            .any(|id| id.starts_with("event-"))
    );
    assert_eq!(
        store
            .projections(SESSION_ID, ProjectionKind::ConsentGrant)
            .expect("consent view reads")
            .len(),
        1
    );

    store
        .rebuild_projections(SESSION_ID)
        .expect("rebuild succeeds");
    let after = store
        .projections(SESSION_ID, ProjectionKind::WorkingContext)
        .expect("rebuilt projection reads");
    assert_eq!(before, after);
}

#[test]
fn interrupted_sqlite_transaction_leaves_no_event() {
    let directory = TempDir::new().expect("temporary directory exists");
    let database = directory.path().join("antidote.sqlite3");
    drop(SqliteEventStore::open(&database).expect("store initializes"));

    let connection = rusqlite::Connection::open(&database).expect("raw connection opens");
    connection
        .execute_batch("BEGIN IMMEDIATE")
        .expect("transaction begins");
    connection
        .execute(
            "INSERT INTO events(session_id, sequence, event_id, schema_version, occurred_at, event_json, event_sha256) VALUES (?1, 1, 'interrupted', '1.0.0', ?2, '{}', ?3)",
            rusqlite::params![SESSION_ID, NOW, "0".repeat(64)],
        )
        .expect("uncommitted insert occurs");
    drop(connection);

    let store = SqliteEventStore::open(&database).expect("store reopens");
    assert!(
        store
            .load_detailed(SESSION_ID)
            .expect("rolled-back stream loads")
            .is_empty()
    );
}

#[test]
fn event_hash_corruption_fails_visibly() {
    let directory = TempDir::new().expect("temporary directory exists");
    let database = directory.path().join("antidote.sqlite3");
    let mut store = SqliteEventStore::open(&database).expect("store initializes");
    store
        .append_detailed(SESSION_ID, 0, &[start_event("event-start", 1)])
        .expect("event appends");
    drop(store);

    let connection = rusqlite::Connection::open(&database).expect("raw connection opens");
    let immutable_error = connection
        .execute(
            "UPDATE events SET event_json = '{}' WHERE session_id = ?1",
            [SESSION_ID],
        )
        .expect_err("immutability trigger blocks ordinary mutation");
    assert!(immutable_error.to_string().contains("events are immutable"));
    connection
        .execute_batch("DROP TRIGGER events_no_update")
        .expect("test removes immutability trigger");
    connection
        .execute(
            "UPDATE events SET event_json = '{}' WHERE session_id = ?1",
            [SESSION_ID],
        )
        .expect("test simulates external corruption");
    drop(connection);

    let store = SqliteEventStore::open(&database).expect("store reopens");
    let error = store
        .load_detailed(SESSION_ID)
        .expect_err("corruption is visible");
    assert!(matches!(error, StoreError::CorruptEventStream { .. }));
}

#[test]
fn content_store_is_atomic_deduplicated_and_hash_verified() {
    let directory = TempDir::new().expect("temporary directory exists");
    let abandoned_directory = directory.path().join("objects").join("aa");
    fs::create_dir_all(&abandoned_directory).expect("temporary shard exists");
    let abandoned = abandoned_directory.join(".antidote-tmp-abandoned");
    fs::write(&abandoned, b"partial").expect("abandoned partial exists");

    let objects =
        ContentAddressedStore::open(directory.path().join("objects")).expect("content store opens");
    assert!(!abandoned.exists());
    let first = objects
        .put(b"synthetic audio bytes")
        .expect("object stores");
    let second = objects
        .put(b"synthetic audio bytes")
        .expect("object deduplicates");
    assert!(first.created);
    assert!(!second.created);
    assert_eq!(first.sha256, second.sha256);
    assert_eq!(
        objects.read(&first.sha256).expect("object verifies"),
        b"synthetic audio bytes"
    );

    let wrong = "0".repeat(64);
    let error = objects
        .put_expected(&wrong, b"synthetic audio bytes")
        .expect_err("wrong expected hash fails before mutation");
    assert!(matches!(error, StoreError::HashMismatch { .. }));
    assert!(!objects.path_for(&wrong).expect("address resolves").exists());

    fs::write(&first.path, b"tampered").expect("test corrupts object");
    assert!(matches!(
        objects.verify_detailed(&first.sha256),
        Err(StoreError::CorruptObject { .. })
    ));
}

#[test]
fn classified_payload_reference_is_idempotent_but_not_reclassifiable() {
    let directory = TempDir::new().expect("temporary directory exists");
    let objects = ContentAddressedStore::open(directory.path().join("payloads"))
        .expect("payload store opens");
    let object = objects
        .put(b"synthetic private note")
        .expect("payload stores");
    let relative_path = object
        .path
        .strip_prefix(objects.root())
        .expect("object remains inside namespace")
        .to_string_lossy()
        .into_owned();
    let reference = PayloadReference {
        sha256: object.sha256.clone(),
        classification: PayloadClassification::SessionPrivate,
        relative_path,
        media_type: "text/plain".to_owned(),
        size_bytes: object.byte_length,
        source_event_id: None,
        created_at: NOW.to_owned(),
    };
    let mut store = SqliteEventStore::open_in_memory().expect("event store opens");
    store
        .register_payload(&reference)
        .expect("reference registers");
    store
        .register_payload(&reference)
        .expect("exact retry is idempotent");
    assert_eq!(
        store.payload(&object.sha256).expect("reference reads"),
        Some(reference.clone())
    );

    let mut changed = reference;
    changed.classification = PayloadClassification::PublicExport;
    assert!(matches!(
        store.register_payload(&changed),
        Err(StoreError::CorruptObject { .. })
    ));
}

#[test]
fn port_boundary_redacts_storage_details() {
    let mut store = SqliteEventStore::open_in_memory().expect("store opens");
    let invalid = vec![start_event("event-1", 2)];
    let error = EventRepository::append(&mut store, SESSION_ID, 0, &invalid)
        .expect_err("port fails closed");
    assert_eq!(error.operation(), "event_append");
    assert!(!error.to_string().contains(SESSION_ID));
}
