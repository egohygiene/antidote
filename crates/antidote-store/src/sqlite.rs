use std::path::Path;

use antidote_core::{
    EventRepository, PortFailure, RecordedEvent, SESSION_EVENT_SCHEMA_VERSION, Session,
    SessionEvent,
};
use rusqlite::{Connection, OptionalExtension, Transaction, TransactionBehavior, params};
use serde::{Deserialize, Serialize};

use crate::artifact::sha256;
use crate::{StoreError, StoreResult};

const CURRENT_SCHEMA_VERSION: i64 = 1;
const INITIAL_MIGRATION: &str = include_str!("../migrations/0001_initial.sql");

/// Coarse local classification kept separate from payload bytes.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PayloadClassification {
    /// Private data limited to the current local session boundary.
    SessionPrivate,
    /// Data approved for a bounded local research workflow but not publication.
    RestrictedResearch,
    /// Data separately reviewed and approved for a public export.
    PublicExport,
}

impl PayloadClassification {
    const fn as_str(self) -> &'static str {
        match self {
            Self::SessionPrivate => "session_private",
            Self::RestrictedResearch => "restricted_research",
            Self::PublicExport => "public_export",
        }
    }

    fn parse(value: &str) -> StoreResult<Self> {
        match value {
            "session_private" => Ok(Self::SessionPrivate),
            "restricted_research" => Ok(Self::RestrictedResearch),
            "public_export" => Ok(Self::PublicExport),
            _ => Err(StoreError::InvalidIdentifier),
        }
    }
}

/// Database reference to content stored outside `SQLite`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PayloadReference {
    /// Content digest used by the filesystem store.
    pub sha256: String,
    /// Coarse access classification.
    pub classification: PayloadClassification,
    /// Path relative to an approved content namespace.
    pub relative_path: String,
    /// Declared media type.
    pub media_type: String,
    /// Exact object length.
    pub size_bytes: u64,
    /// Immutable event that authorized or produced the payload, when applicable.
    pub source_event_id: Option<String>,
    /// RFC 3339 registration time supplied by the application edge.
    pub created_at: String,
}

/// Named disposable view rebuilt from immutable events.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProjectionKind {
    /// Consent grants and revocations.
    ConsentGrant,
    /// Accepted working-context projections.
    WorkingContext,
    /// Present-moment context records.
    MomentContext,
    /// Proposed and approved journey-plan facts.
    JourneyPlan,
    /// Generation request, lifecycle, and result facts.
    GenerationRun,
    /// Generated artifact metadata, never artifact bytes.
    Artifact,
    /// Playback approvals and actual exposure facts.
    Exposure,
    /// Felt response observations.
    Response,
    /// Explicit safety events and acknowledgements.
    SafetyEvent,
    /// Prior snapshots and proposed/accepted model changes.
    ModelSnapshot,
    /// Privacy-reviewed export approvals and share facts.
    Export,
}

impl ProjectionKind {
    const fn table(self) -> &'static str {
        match self {
            Self::ConsentGrant => "consent_grants",
            Self::WorkingContext => "projections",
            Self::MomentContext => "moment_contexts",
            Self::JourneyPlan => "journey_plans",
            Self::GenerationRun => "generation_runs",
            Self::Artifact => "artifacts",
            Self::Exposure => "exposures",
            Self::Response => "responses",
            Self::SafetyEvent => "safety_events",
            Self::ModelSnapshot => "model_snapshots",
            Self::Export => "export_records",
        }
    }

    const fn name(self) -> &'static str {
        match self {
            Self::ConsentGrant => "consent_grant",
            Self::WorkingContext => "working_context",
            Self::MomentContext => "moment_context",
            Self::JourneyPlan => "journey_plan",
            Self::GenerationRun => "generation_run",
            Self::Artifact => "artifact",
            Self::Exposure => "exposure",
            Self::Response => "response",
            Self::SafetyEvent => "safety_event",
            Self::ModelSnapshot => "model_snapshot",
            Self::Export => "export",
        }
    }

    const fn all() -> &'static [Self] {
        &[
            Self::ConsentGrant,
            Self::WorkingContext,
            Self::MomentContext,
            Self::JourneyPlan,
            Self::GenerationRun,
            Self::Artifact,
            Self::Exposure,
            Self::Response,
            Self::SafetyEvent,
            Self::ModelSnapshot,
            Self::Export,
        ]
    }
}

/// One inspectable derived record with explicit immutable-event lineage.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ProjectionRecord {
    /// Unique derived record identifier.
    pub record_id: String,
    /// Domain entity correlated across lifecycle facts.
    pub entity_id: String,
    /// Owning session.
    pub session_id: String,
    /// Full source event serialized as JSON.
    pub record: serde_json::Value,
    /// Event identifiers that contributed to this projection record.
    pub source_event_ids: Vec<String>,
    /// Position of the primary source event in the session stream.
    pub source_sequence: u64,
}

/// `SQLite` implementation of Antidote's immutable event repository.
#[derive(Debug)]
pub struct SqliteEventStore {
    connection: Connection,
}

impl SqliteEventStore {
    /// Open or create a database and apply repository-owned migrations.
    ///
    /// # Errors
    ///
    /// Returns a migration, compatibility, or database failure.
    pub fn open(path: impl AsRef<Path>) -> StoreResult<Self> {
        let connection = Connection::open(path)?;
        Self::from_connection(connection)
    }

    /// Open an isolated in-memory database, primarily for adapter tests.
    ///
    /// # Errors
    ///
    /// Returns a migration or database failure.
    pub fn open_in_memory() -> StoreResult<Self> {
        Self::from_connection(Connection::open_in_memory()?)
    }

    fn from_connection(connection: Connection) -> StoreResult<Self> {
        connection.execute_batch(
            "PRAGMA foreign_keys = ON; PRAGMA journal_mode = WAL; PRAGMA synchronous = FULL;",
        )?;
        let version: i64 = connection.pragma_query_value(None, "user_version", |row| row.get(0))?;
        if version > CURRENT_SCHEMA_VERSION {
            return Err(StoreError::Database(rusqlite::Error::InvalidQuery));
        }
        if version < 1 {
            connection.execute_batch(INITIAL_MIGRATION)?;
            connection.execute(
                "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (1, '2026-08-28T00:00:00Z')",
                [],
            )?;
        }
        Ok(Self { connection })
    }

    /// Load and verify a complete immutable event stream.
    ///
    /// # Errors
    ///
    /// Returns an integrity, serialization, or database failure.
    pub fn load_detailed(&self, session_id: &str) -> StoreResult<Vec<RecordedEvent>> {
        require_identifier(session_id)?;
        load_events(&self.connection, session_id)
    }

    /// Transactionally append immutable events with optimistic concurrency and
    /// retry idempotency, then rebuild disposable projections.
    ///
    /// # Errors
    ///
    /// Returns a conflict, integrity, serialization, or database failure.
    pub fn append_detailed(
        &mut self,
        session_id: &str,
        expected_version: u64,
        events: &[RecordedEvent],
    ) -> StoreResult<()> {
        require_identifier(session_id)?;
        validate_append_batch(session_id, expected_version, events)?;
        let transaction = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let actual_version = current_version(&transaction, session_id)?;
        if actual_version != expected_version {
            if batch_already_present(&transaction, session_id, expected_version, events)? {
                transaction.commit()?;
                return Ok(());
            }
            return Err(StoreError::ConcurrencyConflict {
                session_id: session_id.to_owned(),
                expected: expected_version,
                actual: actual_version,
            });
        }

        for event in events {
            let json = serde_json::to_string(event)?;
            let digest = sha256(json.as_bytes());
            transaction.execute(
                "INSERT INTO events(session_id, sequence, event_id, schema_version, occurred_at, event_json, event_sha256) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
                params![
                    event.session_id,
                    to_i64(event.sequence)?,
                    event.id,
                    event.schema_version,
                    event.occurred_at,
                    json,
                    digest,
                ],
            )?;
        }
        rebuild_session(&transaction, session_id)?;
        transaction.commit()?;
        Ok(())
    }

    /// Rebuild all named projections for one session from immutable events.
    ///
    /// # Errors
    ///
    /// Returns an integrity, serialization, or database failure. The prior
    /// projections remain intact if rebuilding cannot complete.
    pub fn rebuild_projections(&mut self, session_id: &str) -> StoreResult<()> {
        require_identifier(session_id)?;
        let transaction = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        rebuild_session(&transaction, session_id)?;
        transaction.commit()?;
        Ok(())
    }

    /// Read one named projection in deterministic event order.
    ///
    /// # Errors
    ///
    /// Returns a serialization or database failure.
    pub fn projections(
        &self,
        session_id: &str,
        kind: ProjectionKind,
    ) -> StoreResult<Vec<ProjectionRecord>> {
        require_identifier(session_id)?;
        let sql = format!(
            "SELECT record_id, entity_id, session_id, record_json, source_event_id, source_sequence FROM {} WHERE session_id = ?1 ORDER BY source_sequence, record_id",
            kind.table()
        );
        let mut statement = self.connection.prepare(&sql)?;
        let rows = statement.query_map([session_id], |row| {
            Ok((
                row.get::<_, String>(0)?,
                row.get::<_, String>(1)?,
                row.get::<_, String>(2)?,
                row.get::<_, String>(3)?,
                row.get::<_, String>(4)?,
                row.get::<_, i64>(5)?,
            ))
        })?;
        let mut records = Vec::new();
        for row in rows {
            let (record_id, entity_id, session_id, json, primary_source, sequence) = row?;
            let mut lineage_statement = self.connection.prepare(
                "SELECT source_event_id FROM projection_lineage WHERE projection_kind = ?1 AND record_id = ?2 ORDER BY source_event_id",
            )?;
            let lineage = lineage_statement
                .query_map(params![kind.name(), record_id], |lineage_row| {
                    lineage_row.get(0)
                })?
                .collect::<Result<Vec<String>, _>>()?;
            records.push(ProjectionRecord {
                record_id,
                entity_id,
                session_id,
                record: serde_json::from_str(&json)?,
                source_event_ids: if lineage.is_empty() {
                    vec![primary_source]
                } else {
                    lineage
                },
                source_sequence: to_u64(sequence)?,
            });
        }
        Ok(records)
    }

    /// Register a classified reference to externally stored content.
    ///
    /// Repeating the exact registration is idempotent. The same digest cannot
    /// be silently reclassified or pointed at another path.
    ///
    /// # Errors
    ///
    /// Returns an integrity or database failure.
    pub fn register_payload(&mut self, reference: &PayloadReference) -> StoreResult<()> {
        crate::artifact::require_sha256(&reference.sha256)?;
        require_identifier(&reference.media_type)?;
        require_identifier(&reference.created_at)?;
        if reference.relative_path.trim().is_empty()
            || Path::new(&reference.relative_path).is_absolute()
            || Path::new(&reference.relative_path)
                .components()
                .any(|component| matches!(component, std::path::Component::ParentDir))
        {
            return Err(StoreError::InvalidIdentifier);
        }
        if reference
            .source_event_id
            .as_deref()
            .is_some_and(|identifier| identifier.trim().is_empty())
        {
            return Err(StoreError::InvalidIdentifier);
        }
        let size_bytes = to_i64(reference.size_bytes)?;
        let changed = self.connection.execute(
            "INSERT OR IGNORE INTO payloads(sha256, classification, relative_path, media_type, size_bytes, source_event_id, created_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            params![
                reference.sha256,
                reference.classification.as_str(),
                reference.relative_path,
                reference.media_type,
                size_bytes,
                reference.source_event_id,
                reference.created_at,
            ],
        )?;
        if changed == 0 && self.payload(&reference.sha256)?.as_ref() != Some(reference) {
            return Err(StoreError::CorruptObject {
                digest: reference.sha256.clone(),
                path: reference.relative_path.clone().into(),
            });
        }
        Ok(())
    }

    /// Read one payload reference without reading its content.
    ///
    /// # Errors
    ///
    /// Returns an integrity or database failure.
    pub fn payload(&self, digest: &str) -> StoreResult<Option<PayloadReference>> {
        crate::artifact::require_sha256(digest)?;
        let stored = self
            .connection
            .query_row(
                "SELECT classification, relative_path, media_type, size_bytes, source_event_id, created_at FROM payloads WHERE sha256 = ?1",
                [digest],
                |row| {
                    Ok((
                        row.get::<_, String>(0)?,
                        row.get::<_, String>(1)?,
                        row.get::<_, String>(2)?,
                        row.get::<_, i64>(3)?,
                        row.get::<_, Option<String>>(4)?,
                        row.get::<_, String>(5)?,
                    ))
                },
            )
            .optional()?;
        stored
            .map(
                |(
                    classification,
                    relative_path,
                    media_type,
                    size_bytes,
                    source_event_id,
                    created_at,
                )| {
                    Ok(PayloadReference {
                        sha256: digest.to_owned(),
                        classification: PayloadClassification::parse(&classification)?,
                        relative_path,
                        media_type,
                        size_bytes: to_u64(size_bytes)?,
                        source_event_id,
                        created_at,
                    })
                },
            )
            .transpose()
    }

    /// Execute `SQLite`'s physical integrity check and verify every event digest.
    ///
    /// # Errors
    ///
    /// Returns an integrity or database failure.
    pub fn verify_integrity(&self) -> StoreResult<()> {
        let result: String = self
            .connection
            .query_row("PRAGMA integrity_check", [], |row| row.get(0))?;
        if result != "ok" {
            return Err(StoreError::CorruptEventStream {
                session_id: "database".to_owned(),
            });
        }
        let mut statement = self
            .connection
            .prepare("SELECT DISTINCT session_id FROM events ORDER BY session_id")?;
        let sessions = statement
            .query_map([], |row| row.get::<_, String>(0))?
            .collect::<Result<Vec<_>, _>>()?;
        for session_id in sessions {
            load_events(&self.connection, &session_id)?;
        }
        Ok(())
    }
}

impl EventRepository for SqliteEventStore {
    fn load(&self, session_id: &str) -> Result<Vec<RecordedEvent>, PortFailure> {
        self.load_detailed(session_id)
            .map_err(|_| PortFailure::new("event_load"))
    }

    fn append(
        &mut self,
        session_id: &str,
        expected_version: u64,
        events: &[RecordedEvent],
    ) -> Result<(), PortFailure> {
        self.append_detailed(session_id, expected_version, events)
            .map_err(|_| PortFailure::new("event_append"))
    }
}

fn validate_append_batch(
    session_id: &str,
    expected_version: u64,
    events: &[RecordedEvent],
) -> StoreResult<()> {
    for (offset, event) in events.iter().enumerate() {
        require_identifier(&event.id)?;
        if event.session_id != session_id || event.schema_version != SESSION_EVENT_SCHEMA_VERSION {
            return Err(StoreError::CorruptEventStream {
                session_id: session_id.to_owned(),
            });
        }
        let offset = u64::try_from(offset).map_err(|_| StoreError::NumericOverflow)?;
        let expected_sequence = expected_version
            .checked_add(offset)
            .and_then(|value| value.checked_add(1))
            .ok_or(StoreError::NumericOverflow)?;
        if event.sequence != expected_sequence {
            return Err(StoreError::CorruptEventStream {
                session_id: session_id.to_owned(),
            });
        }
    }
    Ok(())
}

fn current_version(connection: &Connection, session_id: &str) -> StoreResult<u64> {
    let version: i64 = connection.query_row(
        "SELECT COALESCE(MAX(sequence), 0) FROM events WHERE session_id = ?1",
        [session_id],
        |row| row.get(0),
    )?;
    to_u64(version)
}

fn batch_already_present(
    connection: &Connection,
    session_id: &str,
    expected_version: u64,
    events: &[RecordedEvent],
) -> StoreResult<bool> {
    if events.is_empty() {
        return Ok(current_version(connection, session_id)? == expected_version);
    }
    for event in events {
        let stored: Option<(String, String)> = connection
            .query_row(
                "SELECT event_json, event_sha256 FROM events WHERE session_id = ?1 AND sequence = ?2",
                params![session_id, to_i64(event.sequence)?],
                |row| Ok((row.get(0)?, row.get(1)?)),
            )
            .optional()?;
        let expected_json = serde_json::to_string(event)?;
        let expected_digest = sha256(expected_json.as_bytes());
        if !stored.is_some_and(|(json, digest)| json == expected_json && digest == expected_digest)
        {
            return Ok(false);
        }
    }
    Ok(true)
}

fn load_events(connection: &Connection, session_id: &str) -> StoreResult<Vec<RecordedEvent>> {
    let mut statement = connection.prepare(
        "SELECT sequence, event_json, event_sha256 FROM events WHERE session_id = ?1 ORDER BY sequence",
    )?;
    let rows = statement.query_map([session_id], |row| {
        Ok((
            row.get::<_, i64>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, String>(2)?,
        ))
    })?;
    let mut events = Vec::new();
    for row in rows {
        let (sequence, json, stored_digest) = row?;
        let expected_sequence = u64::try_from(events.len())
            .map_err(|_| StoreError::NumericOverflow)?
            .checked_add(1)
            .ok_or(StoreError::NumericOverflow)?;
        if to_u64(sequence)? != expected_sequence || sha256(json.as_bytes()) != stored_digest {
            return Err(StoreError::CorruptEventStream {
                session_id: session_id.to_owned(),
            });
        }
        let event: RecordedEvent = serde_json::from_str(&json)?;
        if event.session_id != session_id || event.sequence != expected_sequence {
            return Err(StoreError::CorruptEventStream {
                session_id: session_id.to_owned(),
            });
        }
        events.push(event);
    }
    Session::rehydrate(session_id, &events).map_err(|_| StoreError::CorruptEventStream {
        session_id: session_id.to_owned(),
    })?;
    Ok(events)
}

#[allow(clippy::too_many_lines)]
fn rebuild_session(transaction: &Transaction<'_>, session_id: &str) -> StoreResult<()> {
    let events = load_events(transaction, session_id)?;
    for kind in ProjectionKind::all() {
        let sql = format!("DELETE FROM {} WHERE session_id = ?1", kind.table());
        transaction.execute(&sql, [session_id])?;
    }
    transaction.execute(
        "DELETE FROM projection_lineage WHERE substr(record_id, 1, length(?1) + 1) = ?1 || ':'",
        [session_id],
    )?;

    let mut active_generation_id: Option<String> = None;
    for event in &events {
        let record = serde_json::to_value(event)?;
        match &event.event {
            SessionEvent::SessionStarted {
                prior_model_snapshot,
            } => {
                if let Some(snapshot) = prior_model_snapshot {
                    insert_projection(
                        transaction,
                        ProjectionKind::ModelSnapshot,
                        event,
                        &snapshot.id,
                        &record,
                        &[],
                    )?;
                }
            }
            SessionEvent::ConsentGranted { grant } => insert_projection(
                transaction,
                ProjectionKind::ConsentGrant,
                event,
                &grant.id,
                &record,
                &[],
            )?,
            SessionEvent::ConsentRevoked { consent_grant_id } => insert_projection(
                transaction,
                ProjectionKind::ConsentGrant,
                event,
                consent_grant_id,
                &record,
                &[],
            )?,
            SessionEvent::WorkingProjectionAccepted { projection } => insert_projection(
                transaction,
                ProjectionKind::WorkingContext,
                event,
                &projection.id,
                &record,
                &projection.source_event_ids,
            )?,
            SessionEvent::MomentRecorded { moment } => insert_projection(
                transaction,
                ProjectionKind::MomentContext,
                event,
                &moment.id,
                &record,
                &[],
            )?,
            SessionEvent::JourneyProposed { plan } => insert_projection(
                transaction,
                ProjectionKind::JourneyPlan,
                event,
                &plan.id,
                &record,
                &[],
            )?,
            SessionEvent::JourneyApproved { plan_id, .. } => insert_projection(
                transaction,
                ProjectionKind::JourneyPlan,
                event,
                plan_id,
                &record,
                &[],
            )?,
            SessionEvent::GenerationRequested { specification } => {
                active_generation_id = Some(specification.id.clone());
                insert_projection(
                    transaction,
                    ProjectionKind::GenerationRun,
                    event,
                    &specification.id,
                    &record,
                    &[],
                )?;
            }
            SessionEvent::GenerationApproved { .. }
            | SessionEvent::GenerationStarted
            | SessionEvent::GenerationCancelled => insert_projection(
                transaction,
                ProjectionKind::GenerationRun,
                event,
                active_generation_id.as_deref().unwrap_or(&event.id),
                &record,
                &[],
            )?,
            SessionEvent::GenerationResultRecorded { result } => {
                insert_projection(
                    transaction,
                    ProjectionKind::GenerationRun,
                    event,
                    &result.generation_spec_id,
                    &record,
                    &[],
                )?;
                for artifact in &result.artifacts {
                    insert_projection(
                        transaction,
                        ProjectionKind::Artifact,
                        event,
                        &artifact.sha256,
                        &serde_json::to_value(artifact)?,
                        &[],
                    )?;
                }
            }
            SessionEvent::PlaybackApproved { approval } => insert_projection(
                transaction,
                ProjectionKind::Exposure,
                event,
                &approval.id,
                &record,
                &[],
            )?,
            SessionEvent::ExposureStarted { exposure } => insert_projection(
                transaction,
                ProjectionKind::Exposure,
                event,
                &exposure.id,
                &record,
                &[],
            )?,
            SessionEvent::ExposureStopped { exposure_id, .. } => insert_projection(
                transaction,
                ProjectionKind::Exposure,
                event,
                exposure_id,
                &record,
                &[],
            )?,
            SessionEvent::ResponseRecorded { response, .. } => insert_projection(
                transaction,
                ProjectionKind::Response,
                event,
                &response.id,
                &record,
                &[],
            )?,
            SessionEvent::SafetyEventRecorded { safety_event } => insert_projection(
                transaction,
                ProjectionKind::SafetyEvent,
                event,
                &safety_event.id,
                &record,
                &[],
            )?,
            SessionEvent::SafetyEventAcknowledged { safety_event_id } => insert_projection(
                transaction,
                ProjectionKind::SafetyEvent,
                event,
                safety_event_id,
                &record,
                &[],
            )?,
            SessionEvent::ModelUpdateProposed { proposal } => insert_projection(
                transaction,
                ProjectionKind::ModelSnapshot,
                event,
                &proposal.candidate.id,
                &record,
                &[],
            )?,
            SessionEvent::ModelUpdateAccepted { proposal_id }
            | SessionEvent::ModelUpdateRejected { proposal_id }
            | SessionEvent::ModelUpdateFailed { proposal_id } => insert_projection(
                transaction,
                ProjectionKind::ModelSnapshot,
                event,
                proposal_id,
                &record,
                &[],
            )?,
            SessionEvent::ExportApproved { approval } => insert_projection(
                transaction,
                ProjectionKind::Export,
                event,
                &approval.id,
                &record,
                &[],
            )?,
            SessionEvent::ExportShared { approval_id, .. } => insert_projection(
                transaction,
                ProjectionKind::Export,
                event,
                approval_id,
                &record,
                &[],
            )?,
            SessionEvent::SessionClosed => {}
        }
    }
    Ok(())
}

fn insert_projection(
    transaction: &Transaction<'_>,
    kind: ProjectionKind,
    event: &RecordedEvent,
    entity_id: &str,
    record: &serde_json::Value,
    additional_lineage: &[String],
) -> StoreResult<()> {
    require_identifier(entity_id)?;
    let record_json = serde_json::to_string(record)?;
    let record_id = format!(
        "{}:{}:{}:{}",
        event.session_id,
        event.id,
        kind.name(),
        sha256(record_json.as_bytes())
    );
    let sql = format!(
        "INSERT INTO {}(record_id, entity_id, session_id, record_json, source_event_id, source_sequence) VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
        kind.table()
    );
    transaction.execute(
        &sql,
        params![
            record_id,
            entity_id,
            event.session_id,
            record_json,
            event.id,
            to_i64(event.sequence)?,
        ],
    )?;
    transaction.execute(
        "INSERT OR IGNORE INTO projection_lineage(projection_kind, record_id, source_event_id) VALUES (?1, ?2, ?3)",
        params![kind.name(), record_id, event.id],
    )?;
    for source_event_id in additional_lineage {
        require_identifier(source_event_id)?;
        transaction.execute(
            "INSERT OR IGNORE INTO projection_lineage(projection_kind, record_id, source_event_id) VALUES (?1, ?2, ?3)",
            params![kind.name(), record_id, source_event_id],
        )?;
    }
    Ok(())
}

fn require_identifier(value: &str) -> StoreResult<()> {
    if value.trim().is_empty() {
        Err(StoreError::InvalidIdentifier)
    } else {
        Ok(())
    }
}

fn to_i64(value: u64) -> StoreResult<i64> {
    i64::try_from(value).map_err(|_| StoreError::NumericOverflow)
}

fn to_u64(value: i64) -> StoreResult<u64> {
    u64::try_from(value).map_err(|_| StoreError::NumericOverflow)
}
