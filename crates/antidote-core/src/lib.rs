//! Framework-independent Antidote domain and application boundary.
//!
//! The crate owns consent-aware session transitions and immutable events while
//! remaining independent of Tauri, storage engines, Python, audio devices,
//! generation models, and publication infrastructure.

mod application;
mod domain;
mod error;
mod ports;

pub use application::{GenerationOrchestrationOutcome, GenerationOrchestrator, SessionService};
pub use domain::{
    ConsentSelection, ExportApproval, Exposure, ExposureState, ExposureStopReason, GenerationJob,
    GenerationJobState, JourneyApprovalState, JourneyState, ModelUpdateProposal, ModelUpdateState,
    PersonalModelSnapshot, PlaybackApproval, RecordedEvent, SESSION_EVENT_SCHEMA_VERSION,
    SafetyEvent, SafetyEventKind, Session, SessionCommand, SessionEvent,
};
pub use error::{ApplicationError, DomainError, PortFailure};
pub use ports::{
    ArtifactStorePort, AudioPort, Clock, EventRepository, ExportPort, IdentifierKind,
    IdentifierSource, WorkerInvocationPort,
};

pub(crate) use domain::require_identifier;

pub use antidote_contracts as contracts;

/// Honest implementation status exposed to scaffold smoke tests.
pub const IMPLEMENTATION_STATUS: &str = "authoritative-session-core-v1";

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn status_names_the_authoritative_session_core() {
        assert_eq!(IMPLEMENTATION_STATUS, "authoritative-session-core-v1");
    }
}
