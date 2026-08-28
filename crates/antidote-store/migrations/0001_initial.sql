PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
  version INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
  session_id TEXT NOT NULL,
  sequence INTEGER NOT NULL CHECK (sequence > 0),
  event_id TEXT NOT NULL UNIQUE,
  schema_version TEXT NOT NULL,
  occurred_at TEXT NOT NULL,
  event_json TEXT NOT NULL,
  event_sha256 TEXT NOT NULL CHECK (length(event_sha256) = 64),
  PRIMARY KEY (session_id, sequence)
);

CREATE TRIGGER IF NOT EXISTS events_no_update
BEFORE UPDATE ON events
BEGIN
  SELECT RAISE(ABORT, 'events are immutable');
END;

CREATE TRIGGER IF NOT EXISTS events_no_delete
BEFORE DELETE ON events
BEGIN
  SELECT RAISE(ABORT, 'events are immutable');
END;

CREATE TABLE IF NOT EXISTS payloads (
  sha256 TEXT PRIMARY KEY CHECK (length(sha256) = 64),
  classification TEXT NOT NULL,
  relative_path TEXT NOT NULL UNIQUE,
  media_type TEXT NOT NULL,
  size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
  source_event_id TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS consent_grants (
  record_id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL,
  session_id TEXT NOT NULL,
  record_json TEXT NOT NULL,
  source_event_id TEXT NOT NULL,
  source_sequence INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS projections (
  record_id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL,
  session_id TEXT NOT NULL,
  record_json TEXT NOT NULL,
  source_event_id TEXT NOT NULL,
  source_sequence INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS moment_contexts (
  record_id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL,
  session_id TEXT NOT NULL,
  record_json TEXT NOT NULL,
  source_event_id TEXT NOT NULL,
  source_sequence INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS journey_plans (
  record_id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL,
  session_id TEXT NOT NULL,
  record_json TEXT NOT NULL,
  source_event_id TEXT NOT NULL,
  source_sequence INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS generation_runs (
  record_id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL,
  session_id TEXT NOT NULL,
  record_json TEXT NOT NULL,
  source_event_id TEXT NOT NULL,
  source_sequence INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS artifacts (
  record_id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL,
  session_id TEXT NOT NULL,
  record_json TEXT NOT NULL,
  source_event_id TEXT NOT NULL,
  source_sequence INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS exposures (
  record_id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL,
  session_id TEXT NOT NULL,
  record_json TEXT NOT NULL,
  source_event_id TEXT NOT NULL,
  source_sequence INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS responses (
  record_id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL,
  session_id TEXT NOT NULL,
  record_json TEXT NOT NULL,
  source_event_id TEXT NOT NULL,
  source_sequence INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS safety_events (
  record_id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL,
  session_id TEXT NOT NULL,
  record_json TEXT NOT NULL,
  source_event_id TEXT NOT NULL,
  source_sequence INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS model_snapshots (
  record_id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL,
  session_id TEXT NOT NULL,
  record_json TEXT NOT NULL,
  source_event_id TEXT NOT NULL,
  source_sequence INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS export_records (
  record_id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL,
  session_id TEXT NOT NULL,
  record_json TEXT NOT NULL,
  source_event_id TEXT NOT NULL,
  source_sequence INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS projection_lineage (
  projection_kind TEXT NOT NULL,
  record_id TEXT NOT NULL,
  source_event_id TEXT NOT NULL,
  PRIMARY KEY (projection_kind, record_id, source_event_id)
);

CREATE INDEX IF NOT EXISTS events_by_session
  ON events (session_id, sequence);
CREATE INDEX IF NOT EXISTS lineage_by_source
  ON projection_lineage (source_event_id, projection_kind, record_id);

PRAGMA user_version = 1;
