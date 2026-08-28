use antidote_contracts::{GenerationResult, GenerationSpec};

use crate::{PortFailure, RecordedEvent};

/// Entity classes whose identifiers are supplied by an injected adapter.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum IdentifierKind {
    /// Immutable event-envelope identifier.
    Event,
    /// Explicit playback-approval identifier.
    PlaybackApproval,
    /// Actual exposure identifier.
    Exposure,
    /// Safety-event identifier.
    SafetyEvent,
    /// Proposed personal-model update identifier.
    ModelUpdateProposal,
    /// Privacy-reviewed export approval identifier.
    ExportApproval,
}

/// Supplies the current time without coupling the core to an operating system.
pub trait Clock {
    /// Return the current instant as an RFC 3339 timestamp.
    ///
    /// # Errors
    ///
    /// Returns a redacted failure when the clock is unavailable.
    fn now_rfc3339(&self) -> Result<String, PortFailure>;
}

/// Supplies deterministic or production identifiers at the application edge.
pub trait IdentifierSource {
    /// Return the next identifier for one entity class.
    ///
    /// # Errors
    ///
    /// Returns a redacted failure when an identifier cannot be allocated.
    fn next_id(&mut self, kind: IdentifierKind) -> Result<String, PortFailure>;
}

/// Persists and reloads immutable session events.
pub trait EventRepository {
    /// Load the complete ordered event stream for one session.
    ///
    /// # Errors
    ///
    /// Returns a redacted failure when the stream cannot be read.
    fn load(&self, session_id: &str) -> Result<Vec<RecordedEvent>, PortFailure>;

    /// Append events only when the stored stream still has `expected_version`.
    ///
    /// # Errors
    ///
    /// Returns a redacted failure on storage, concurrency, or integrity errors.
    fn append(
        &mut self,
        session_id: &str,
        expected_version: u64,
        events: &[RecordedEvent],
    ) -> Result<(), PortFailure>;
}

/// Invokes a capability-scoped generation worker without granting domain authority.
pub trait WorkerInvocationPort {
    /// Execute one already-approved immutable generation specification.
    ///
    /// # Errors
    ///
    /// Returns a redacted failure when the worker cannot complete the operation.
    fn generate(&mut self, specification: &GenerationSpec)
    -> Result<GenerationResult, PortFailure>;

    /// Request cooperative cancellation of one worker request.
    ///
    /// # Errors
    ///
    /// Returns a redacted failure when cancellation cannot be delivered.
    fn cancel(&mut self, generation_spec_id: &str) -> Result<(), PortFailure>;
}

/// Controls deliberate audio playback while leaving exposure truth in the core.
pub trait AudioPort {
    /// Begin playback of one verified artifact hash.
    ///
    /// # Errors
    ///
    /// Returns a redacted failure when playback cannot start.
    fn play(&mut self, artifact_sha256: &str) -> Result<(), PortFailure>;

    /// Stop current playback.
    ///
    /// # Errors
    ///
    /// Returns a redacted failure when the stop request cannot be applied.
    fn stop(&mut self) -> Result<(), PortFailure>;
}

/// Stores and verifies content-addressed artifacts outside the domain crate.
pub trait ArtifactStorePort {
    /// Confirm that an artifact exists and matches the expected content hash.
    ///
    /// # Errors
    ///
    /// Returns a redacted failure on missing, inaccessible, or mismatched content.
    fn verify(&self, artifact_sha256: &str) -> Result<(), PortFailure>;
}

/// Writes only a previously approved and privacy-reviewed export payload.
pub trait ExportPort {
    /// Persist one export and return its manifest SHA-256 digest.
    ///
    /// # Errors
    ///
    /// Returns a redacted failure when the export cannot be completed safely.
    fn export(&mut self, approval_id: &str, payload: &[u8]) -> Result<String, PortFailure>;
}
