use std::error::Error;
use std::fmt::{Display, Formatter};

/// A fail-closed domain-policy or state-transition violation.
#[derive(Debug, Clone, PartialEq, Eq)]
#[non_exhaustive]
pub enum DomainError {
    /// The session has not received its start event.
    SessionNotStarted,
    /// The session has already received its start event.
    SessionAlreadyStarted,
    /// The session is closed and cannot accept further commands.
    SessionClosed,
    /// A nested contract belongs to another session.
    WrongSession,
    /// A canonical contract rejected the supplied value.
    InvalidContract { contract: &'static str },
    /// A timestamp is not valid RFC 3339.
    InvalidTimestamp,
    /// Event replay encountered an unexpected sequence number.
    InvalidEventSequence,
    /// An event identifier or entity identifier is empty.
    EmptyIdentifier,
    /// The referenced consent grant does not exist.
    ConsentMissing,
    /// More than one grant could authorize an implicit selection.
    ConsentAmbiguous,
    /// The referenced consent grant has been revoked.
    ConsentRevoked,
    /// The referenced consent grant is expired.
    ConsentExpired,
    /// The referenced consent grant does not authorize the required purpose.
    ConsentWrongPurpose,
    /// The referenced consent grant does not authorize the required action.
    ConsentWrongAction,
    /// The grant does not permit a derived working projection.
    ConsentProjectionNotAllowed,
    /// The grant does not permit a personal-model update.
    ConsentLearningNotAllowed,
    /// A consent identifier has already been recorded.
    ConsentAlreadyExists,
    /// The referenced working projection does not exist.
    ProjectionMissing,
    /// The working projection has expired.
    ProjectionExpired,
    /// A working-projection item still awaits human review.
    ProjectionReviewPending,
    /// The working projection references an invalid grant.
    ProjectionConsentMismatch,
    /// No moment context has been recorded.
    MomentMissing,
    /// A moment context already exists for the current session progression.
    MomentAlreadyRecorded,
    /// No journey plan exists.
    JourneyMissing,
    /// A journey plan already exists and must be superseded explicitly later.
    JourneyAlreadyExists,
    /// A journey plan is not in the required draft state.
    JourneyNotDraft,
    /// The journey plan has not received explicit human approval.
    JourneyNotApproved,
    /// Journey duration, stage order, lineage, or hash is inconsistent.
    JourneyInvalid,
    /// No generation job exists.
    GenerationMissing,
    /// A non-terminal generation job already exists.
    GenerationAlreadyActive,
    /// The generation job has not received explicit human approval.
    GenerationNotApproved,
    /// The generation job is not running.
    GenerationNotRunning,
    /// The generation job has already reached a terminal state.
    GenerationTerminal,
    /// The generation specification or result does not match the approved plan.
    GenerationMismatch,
    /// A successful generation result does not contain a usable audio artifact.
    GeneratedAudioMissing,
    /// Playback has not received explicit approval for the selected artifact.
    PlaybackNotApproved,
    /// An artifact does not match the approved or generated content hash.
    ArtifactMismatch,
    /// An exposure is already active.
    ExposureAlreadyActive,
    /// The referenced exposure does not exist.
    ExposureMissing,
    /// The referenced exposure is not currently playing.
    ExposureNotActive,
    /// The response window is inconsistent with actual exposure state.
    ResponseWindowInvalid,
    /// A safety halt blocks continuation until it is acknowledged.
    SafetyHaltActive,
    /// No matching safety halt exists to acknowledge.
    SafetyHaltMissing,
    /// The referenced response observation does not exist.
    ResponseMissing,
    /// No personal-model update proposal exists.
    ModelUpdateMissing,
    /// A personal-model update proposal is already pending.
    ModelUpdateAlreadyPending,
    /// The personal-model update is no longer pending.
    ModelUpdateNotPending,
    /// The proposal does not build from the current personal-model snapshot.
    ModelSnapshotMismatch,
    /// The proposal cites response evidence that cannot authorize learning.
    ModelEvidenceInvalid,
    /// No matching export approval exists.
    ExportApprovalMissing,
    /// The approved export has already been recorded as shared.
    ExportAlreadyShared,
    /// A supplied SHA-256 digest is malformed.
    InvalidSha256,
}

impl Display for DomainError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        let message = match self {
            Self::SessionNotStarted => "session has not started",
            Self::SessionAlreadyStarted => "session has already started",
            Self::SessionClosed => "session is closed",
            Self::WrongSession => "value belongs to another session",
            Self::InvalidContract { contract } => {
                return write!(formatter, "{contract} contract validation failed");
            }
            Self::InvalidTimestamp => "timestamp is not valid RFC 3339",
            Self::InvalidEventSequence => "event sequence is not contiguous",
            Self::EmptyIdentifier => "identifier must not be empty",
            Self::ConsentMissing => "required consent grant is missing",
            Self::ConsentAmbiguous => "consent selection is ambiguous",
            Self::ConsentRevoked => "consent grant is revoked",
            Self::ConsentExpired => "consent grant is expired",
            Self::ConsentWrongPurpose => "consent grant has the wrong purpose",
            Self::ConsentWrongAction => "consent grant has the wrong action",
            Self::ConsentProjectionNotAllowed => "consent does not allow a derived projection",
            Self::ConsentLearningNotAllowed => "consent does not allow a personal-model update",
            Self::ConsentAlreadyExists => "consent identifier already exists",
            Self::ProjectionMissing => "working projection is missing",
            Self::ProjectionExpired => "working projection is expired",
            Self::ProjectionReviewPending => "working projection still awaits review",
            Self::ProjectionConsentMismatch => "working projection consent is invalid",
            Self::MomentMissing => "moment context is missing",
            Self::MomentAlreadyRecorded => "moment context is already recorded",
            Self::JourneyMissing => "journey plan is missing",
            Self::JourneyAlreadyExists => "journey plan already exists",
            Self::JourneyNotDraft => "journey plan is not a draft",
            Self::JourneyNotApproved => "journey plan is not approved",
            Self::JourneyInvalid => "journey plan is inconsistent",
            Self::GenerationMissing => "generation job is missing",
            Self::GenerationAlreadyActive => "generation job is already active",
            Self::GenerationNotApproved => "generation job is not approved",
            Self::GenerationNotRunning => "generation job is not running",
            Self::GenerationTerminal => "generation job is terminal",
            Self::GenerationMismatch => "generation lineage is inconsistent",
            Self::GeneratedAudioMissing => "generated result contains no usable audio",
            Self::PlaybackNotApproved => "playback is not approved",
            Self::ArtifactMismatch => "artifact hash does not match",
            Self::ExposureAlreadyActive => "an exposure is already active",
            Self::ExposureMissing => "exposure is missing",
            Self::ExposureNotActive => "exposure is not active",
            Self::ResponseWindowInvalid => "response window conflicts with exposure state",
            Self::SafetyHaltActive => "a safety halt blocks continuation",
            Self::SafetyHaltMissing => "matching safety halt is missing",
            Self::ResponseMissing => "response observation is missing",
            Self::ModelUpdateMissing => "personal-model update proposal is missing",
            Self::ModelUpdateAlreadyPending => "a personal-model update is already pending",
            Self::ModelUpdateNotPending => "personal-model update is not pending",
            Self::ModelSnapshotMismatch => "personal-model base snapshot does not match",
            Self::ModelEvidenceInvalid => "personal-model evidence is invalid",
            Self::ExportApprovalMissing => "export approval is missing",
            Self::ExportAlreadyShared => "export is already recorded as shared",
            Self::InvalidSha256 => "SHA-256 digest is malformed",
        };
        formatter.write_str(message)
    }
}

impl Error for DomainError {}

/// A redacted adapter failure safe to return through the application boundary.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PortFailure {
    operation: &'static str,
}

impl PortFailure {
    /// Create a failure that identifies only the bounded operation.
    #[must_use]
    pub const fn new(operation: &'static str) -> Self {
        Self { operation }
    }

    /// Return the failed adapter operation without exposing private payloads.
    #[must_use]
    pub const fn operation(&self) -> &'static str {
        self.operation
    }
}

impl Display for PortFailure {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{} adapter operation failed", self.operation)
    }
}

impl Error for PortFailure {}

/// Failure returned by the session application service.
#[derive(Debug)]
pub enum ApplicationError {
    /// A domain command failed closed.
    Domain(DomainError),
    /// A clock, identifier, or persistence adapter failed.
    Port(PortFailure),
}

impl Display for ApplicationError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Domain(error) => Display::fmt(error, formatter),
            Self::Port(error) => Display::fmt(error, formatter),
        }
    }
}

impl Error for ApplicationError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::Domain(error) => Some(error),
            Self::Port(error) => Some(error),
        }
    }
}

impl From<DomainError> for ApplicationError {
    fn from(error: DomainError) -> Self {
        Self::Domain(error)
    }
}

impl From<PortFailure> for ApplicationError {
    fn from(error: PortFailure) -> Self {
        Self::Port(error)
    }
}
