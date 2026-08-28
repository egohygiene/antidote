use std::collections::BTreeMap;

use antidote_contracts::{
    ConsentGrant, ConsentGrantAction, ConsentGrantPurpose, ConsentGrantStatus, GenerationResult,
    GenerationResultArtifactKind, GenerationResultStatus, GenerationSpec, JourneyPlan,
    JourneyPlanStatus, MomentContext, ResponseObservation, ResponseObservationWindow,
    WorkingContextProjection, WorkingContextProjectionSemanticItemUserReview, validate_contract,
};
use serde::{Deserialize, Serialize};
use time::{OffsetDateTime, format_description::well_known::Rfc3339};

use crate::{ApplicationError, DomainError, IdentifierKind, IdentifierSource};

/// Version of the immutable session-event envelope.
pub const SESSION_EVENT_SCHEMA_VERSION: &str = "1.0.0";

/// Explicit or exactly-one implicit consent selection for an authoritative action.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ConsentSelection {
    grant_ids: Vec<String>,
}

impl ConsentSelection {
    /// Select one named grant.
    #[must_use]
    pub fn explicit(grant_id: impl Into<String>) -> Self {
        Self {
            grant_ids: vec![grant_id.into()],
        }
    }

    /// Ask the core to resolve exactly one currently applicable grant.
    #[must_use]
    pub const fn automatic() -> Self {
        Self {
            grant_ids: Vec::new(),
        }
    }

    /// Build a selection for import and negative-boundary tests.
    #[must_use]
    pub fn from_grant_ids(grant_ids: Vec<String>) -> Self {
        Self { grant_ids }
    }
}

/// Current lifecycle state of a generation job.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum GenerationJobState {
    /// Specification recorded but not yet approved.
    Requested,
    /// A person approved invocation under current consent.
    Approved,
    /// A worker invocation is in progress.
    Running,
    /// A complete result with verified audio metadata was recorded.
    Generated,
    /// The person or system cancelled the job.
    Cancelled,
    /// A partial result was recorded and is not playable as complete output.
    Partial,
    /// Generation failed.
    Failed,
}

impl GenerationJobState {
    #[must_use]
    const fn is_terminal(self) -> bool {
        matches!(
            self,
            Self::Generated | Self::Cancelled | Self::Partial | Self::Failed
        )
    }
}

/// Human approval state for an editable journey plan.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum JourneyApprovalState {
    /// The plan remains editable and cannot authorize generation.
    Draft,
    /// The person approved this exact plan under the named grant.
    Approved {
        /// Grant that authorized journey planning at approval time.
        consent_grant_id: String,
        /// Approval time.
        approved_at: String,
    },
}

/// One journey plan plus its authority state.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct JourneyState {
    /// Canonical journey-plan contract.
    pub plan: JourneyPlan,
    /// Separate human-approval record; contract status alone is not authority.
    pub approval: JourneyApprovalState,
}

/// One generation job owned by the Rust authority boundary.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct GenerationJob {
    /// Immutable canonical generation specification.
    pub specification: GenerationSpec,
    /// Current authoritative job state.
    pub state: GenerationJobState,
    /// Grant selected when the person approved generation.
    pub consent_grant_id: Option<String>,
    /// Terminal worker result when one has been recorded.
    pub result: Option<GenerationResult>,
}

/// Explicit approval to play one exact generated artifact.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PlaybackApproval {
    /// Approval identifier.
    pub id: String,
    /// Approved content hash.
    pub artifact_sha256: String,
    /// Approval time.
    pub approved_at: String,
    /// Whether an exposure already consumed this approval.
    pub consumed: bool,
}

/// Lifecycle of an actual exposure, distinct from generation and intent.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ExposureState {
    /// The approved artifact is actively playing.
    Playing,
    /// Playback stopped and the actual stop time is recorded.
    Stopped {
        /// Stop time.
        stopped_at: String,
        /// Person- or system-visible stop classification.
        reason: ExposureStopReason,
    },
}

/// Classification for why actual playback stopped.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ExposureStopReason {
    /// The person deliberately stopped without reporting harm.
    PersonStopped,
    /// The artifact reached its end.
    Completed,
    /// Playback failed technically.
    PlaybackFailure,
    /// The person reported distress or another adverse response.
    AdverseResponse,
}

/// What was actually played, identified independently from the intended plan.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Exposure {
    /// Exposure identifier referenced by response contracts.
    pub id: String,
    /// Playback approval that authorized this exposure.
    pub approval_id: String,
    /// Content hash of the actual selected artifact.
    pub artifact_sha256: String,
    /// Actual playback start time.
    pub started_at: String,
    /// Actual exposure lifecycle.
    pub state: ExposureState,
}

/// Safety-event classification that never implies a successful outcome.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SafetyEventKind {
    /// The person indicated distress.
    Distress,
    /// The person identified a meaningful mismatch.
    Mismatch,
    /// The person reported possible harm or an adverse response.
    AdverseResponse,
    /// A declared exclusion was reached or violated.
    Exclusion,
    /// Playback was stopped because continuation was not appropriate.
    PlaybackStop,
    /// Another explicitly described safety-relevant event.
    Other,
}

/// One visible safety event that halts continuation until acknowledgement.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SafetyEvent {
    /// Safety-event identifier.
    pub id: String,
    /// Non-success classification.
    pub kind: SafetyEventKind,
    /// Person- or system-supplied description.
    pub description: String,
    /// Observation time.
    pub observed_at: String,
}

/// Versioned, uncertain within-person summary at one point in time.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PersonalModelSnapshot {
    /// Snapshot identifier.
    pub id: String,
    /// Monotonic version assigned by the proposing policy.
    pub version: u64,
    /// Human-readable, correctable summary rather than a permanent trait.
    pub summary: String,
    /// Response-event identifiers supporting this snapshot.
    pub evidence_response_ids: Vec<String>,
}

/// Review state of a proposed personal-model update.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ModelUpdateState {
    /// Awaiting explicit human acceptance or rejection.
    Pending,
    /// Accepted explicitly and made current.
    Accepted,
    /// Rejected explicitly without changing the prior snapshot.
    Rejected,
    /// Failed without changing the prior snapshot.
    Failed,
}

/// An inspectable proposed change that cannot update the model autonomously.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ModelUpdateProposal {
    /// Proposal identifier.
    pub id: String,
    /// Snapshot the candidate expects to supersede, if any.
    pub base_snapshot_id: Option<String>,
    /// Candidate snapshot shown for review.
    pub candidate: PersonalModelSnapshot,
    /// Response observations explicitly allowed to support learning.
    pub evidence_response_ids: Vec<String>,
    /// Grant selected when the proposal was created.
    pub consent_grant_id: String,
    /// Current proposal state.
    pub state: ModelUpdateState,
}

/// Explicit privacy-reviewed authority to share an export.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExportApproval {
    /// Export-approval identifier.
    pub id: String,
    /// Grant that authorizes research export.
    pub consent_grant_id: String,
    /// Approval time.
    pub approved_at: String,
    /// Manifest hash after the approved export is actually shared.
    pub shared_manifest_sha256: Option<String>,
}

/// Commands accepted by the authoritative session aggregate.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(tag = "type", content = "payload", rename_all = "snake_case")]
pub enum SessionCommand {
    /// Start one session and optionally load a prior model snapshot.
    StartSession {
        /// Prior inspectable snapshot available for this session.
        prior_model_snapshot: Option<PersonalModelSnapshot>,
    },
    /// Record one canonical consent grant.
    GrantConsent { grant: ConsentGrant },
    /// Revoke a previously recorded grant.
    RevokeConsent { consent_grant_id: String },
    /// Accept one fully reviewed, consent-scoped working projection.
    AcceptWorkingProjection {
        projection: WorkingContextProjection,
    },
    /// Record one present-moment context.
    RecordMoment { moment: MomentContext },
    /// Record one editable draft journey.
    ProposeJourney { plan: JourneyPlan },
    /// Explicitly approve the current draft journey.
    ApproveJourney {
        plan_id: String,
        consent: ConsentSelection,
    },
    /// Record an immutable generation specification without invoking a worker.
    RequestGeneration { specification: GenerationSpec },
    /// Explicitly approve the current generation request.
    ApproveGeneration { consent: ConsentSelection },
    /// Mark the approved job as running before worker invocation.
    StartGeneration,
    /// Record one terminal or partial worker result.
    RecordGenerationResult { result: GenerationResult },
    /// Cancel a requested, approved, or running generation job.
    CancelGeneration,
    /// Explicitly approve playback of one generated artifact hash.
    ApprovePlayback { artifact_sha256: String },
    /// Begin actual playback using an unconsumed approval.
    StartExposure { approval_id: String },
    /// Stop actual playback with an explicit reason.
    StopExposure {
        exposure_id: String,
        reason: ExposureStopReason,
    },
    /// Record a felt response separately from intended or measured acoustics.
    RecordResponse {
        response: ResponseObservation,
        consent: ConsentSelection,
    },
    /// Record an explicit safety event and halt continuation.
    RecordSafetyEvent {
        kind: SafetyEventKind,
        description: String,
    },
    /// Explicitly acknowledge the current safety halt before any continuation.
    AcknowledgeSafetyEvent { safety_event_id: String },
    /// Propose, but do not apply, a personal-model update.
    ProposeModelUpdate {
        consent: ConsentSelection,
        candidate: PersonalModelSnapshot,
        evidence_response_ids: Vec<String>,
    },
    /// Explicitly accept the pending personal-model update.
    AcceptModelUpdate {
        proposal_id: String,
        consent: ConsentSelection,
    },
    /// Reject the pending update while preserving the current snapshot.
    RejectModelUpdate { proposal_id: String },
    /// Mark the pending update failed while preserving the current snapshot.
    FailModelUpdate { proposal_id: String },
    /// Explicitly approve a privacy-reviewed research export.
    ApproveExport { consent: ConsentSelection },
    /// Record that an approved export was shared with this manifest hash.
    RecordExportShared {
        approval_id: String,
        manifest_sha256: String,
    },
    /// Close the session.
    CloseSession,
}

/// Immutable facts emitted by valid commands.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(tag = "type", content = "payload", rename_all = "snake_case")]
pub enum SessionEvent {
    /// Session start and optional prior snapshot.
    SessionStarted {
        prior_model_snapshot: Option<PersonalModelSnapshot>,
    },
    /// Consent grant recorded.
    ConsentGranted { grant: ConsentGrant },
    /// Consent grant revoked.
    ConsentRevoked { consent_grant_id: String },
    /// Working projection accepted after review.
    WorkingProjectionAccepted {
        projection: WorkingContextProjection,
    },
    /// Moment context recorded.
    MomentRecorded { moment: MomentContext },
    /// Draft journey recorded.
    JourneyProposed { plan: JourneyPlan },
    /// Journey received explicit approval.
    JourneyApproved {
        plan_id: String,
        consent_grant_id: String,
    },
    /// Generation specification recorded without invocation.
    GenerationRequested { specification: GenerationSpec },
    /// Generation received explicit approval.
    GenerationApproved { consent_grant_id: String },
    /// Worker invocation started.
    GenerationStarted,
    /// Worker result recorded.
    GenerationResultRecorded { result: GenerationResult },
    /// Generation cancelled.
    GenerationCancelled,
    /// Playback approved for one artifact.
    PlaybackApproved { approval: PlaybackApproval },
    /// Actual exposure started.
    ExposureStarted { exposure: Exposure },
    /// Actual exposure stopped.
    ExposureStopped {
        exposure_id: String,
        reason: ExposureStopReason,
    },
    /// Felt response recorded.
    ResponseRecorded {
        response: ResponseObservation,
        consent_grant_id: String,
    },
    /// Safety event recorded and continuation halted.
    SafetyEventRecorded { safety_event: SafetyEvent },
    /// Safety halt explicitly acknowledged.
    SafetyEventAcknowledged { safety_event_id: String },
    /// Personal-model update proposed for review.
    ModelUpdateProposed { proposal: ModelUpdateProposal },
    /// Pending proposal explicitly accepted.
    ModelUpdateAccepted { proposal_id: String },
    /// Pending proposal explicitly rejected.
    ModelUpdateRejected { proposal_id: String },
    /// Pending proposal failed without replacing the current snapshot.
    ModelUpdateFailed { proposal_id: String },
    /// Research export explicitly approved.
    ExportApproved { approval: ExportApproval },
    /// Approved export recorded as shared.
    ExportShared {
        approval_id: String,
        manifest_sha256: String,
    },
    /// Session closed.
    SessionClosed,
}

/// Versioned immutable event envelope used by persistence adapters.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct RecordedEvent {
    /// Envelope schema version.
    pub schema_version: String,
    /// Event identifier.
    pub id: String,
    /// Owning session identifier.
    pub session_id: String,
    /// One-based sequence within the session stream.
    pub sequence: u64,
    /// RFC 3339 decision time supplied by the clock port.
    pub occurred_at: String,
    /// Immutable domain fact.
    pub event: SessionEvent,
}

/// Authoritative state rebuilt entirely from immutable events.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Session {
    id: String,
    version: u64,
    started_at: Option<String>,
    closed_at: Option<String>,
    consent_grants: BTreeMap<String, ConsentGrant>,
    working_projection: Option<WorkingContextProjection>,
    moment: Option<MomentContext>,
    journey: Option<JourneyState>,
    generation: Option<GenerationJob>,
    playback_approval: Option<PlaybackApproval>,
    exposure: Option<Exposure>,
    responses: BTreeMap<String, ResponseObservation>,
    safety_events: Vec<SafetyEvent>,
    safety_halt_id: Option<String>,
    personal_model_snapshot: Option<PersonalModelSnapshot>,
    model_update_proposal: Option<ModelUpdateProposal>,
    export_approval: Option<ExportApproval>,
}

impl Session {
    /// Create an empty aggregate ready to replay or start one named session.
    ///
    /// # Errors
    ///
    /// Returns [`DomainError::EmptyIdentifier`] for a blank session identifier.
    pub fn empty(session_id: impl Into<String>) -> Result<Self, DomainError> {
        let id = session_id.into();
        require_identifier(&id)?;
        Ok(Self {
            id,
            version: 0,
            started_at: None,
            closed_at: None,
            consent_grants: BTreeMap::new(),
            working_projection: None,
            moment: None,
            journey: None,
            generation: None,
            playback_approval: None,
            exposure: None,
            responses: BTreeMap::new(),
            safety_events: Vec::new(),
            safety_halt_id: None,
            personal_model_snapshot: None,
            model_update_proposal: None,
            export_approval: None,
        })
    }

    /// Rebuild authoritative state from one ordered event stream.
    ///
    /// # Errors
    ///
    /// Fails closed on an invalid identifier, wrong session, invalid timestamp,
    /// non-contiguous sequence, or event that cannot apply to the replay state.
    pub fn rehydrate(
        session_id: impl Into<String>,
        events: &[RecordedEvent],
    ) -> Result<Self, DomainError> {
        let mut session = Self::empty(session_id)?;
        for event in events {
            session.apply_recorded(event)?;
        }
        Ok(session)
    }

    /// Return the owning session identifier.
    #[must_use]
    pub fn id(&self) -> &str {
        &self.id
    }

    /// Return the current event-stream version.
    #[must_use]
    pub const fn version(&self) -> u64 {
        self.version
    }

    /// Report whether the session has started.
    #[must_use]
    pub const fn is_started(&self) -> bool {
        self.started_at.is_some()
    }

    /// Report whether the session is closed.
    #[must_use]
    pub const fn is_closed(&self) -> bool {
        self.closed_at.is_some()
    }

    /// Return the currently accepted working projection, if any.
    #[must_use]
    pub const fn working_projection(&self) -> Option<&WorkingContextProjection> {
        self.working_projection.as_ref()
    }

    /// Return the current moment context, if any.
    #[must_use]
    pub const fn moment(&self) -> Option<&MomentContext> {
        self.moment.as_ref()
    }

    /// Return the current journey and separate approval state.
    #[must_use]
    pub const fn journey(&self) -> Option<&JourneyState> {
        self.journey.as_ref()
    }

    /// Return the current generation job.
    #[must_use]
    pub const fn generation(&self) -> Option<&GenerationJob> {
        self.generation.as_ref()
    }

    /// Return the latest actual exposure.
    #[must_use]
    pub const fn exposure(&self) -> Option<&Exposure> {
        self.exposure.as_ref()
    }

    /// Return the active safety halt identifier, if continuation is blocked.
    #[must_use]
    pub fn safety_halt_id(&self) -> Option<&str> {
        self.safety_halt_id.as_deref()
    }

    /// Return the current accepted personal-model snapshot.
    #[must_use]
    pub const fn personal_model_snapshot(&self) -> Option<&PersonalModelSnapshot> {
        self.personal_model_snapshot.as_ref()
    }

    /// Return the latest personal-model update proposal.
    #[must_use]
    pub const fn model_update_proposal(&self) -> Option<&ModelUpdateProposal> {
        self.model_update_proposal.as_ref()
    }

    /// Return the current export approval.
    #[must_use]
    pub const fn export_approval(&self) -> Option<&ExportApproval> {
        self.export_approval.as_ref()
    }

    /// Return one recorded response by canonical identifier.
    #[must_use]
    pub fn response(&self, response_id: &str) -> Option<&ResponseObservation> {
        self.responses.get(response_id)
    }

    #[allow(clippy::too_many_lines)]
    pub(crate) fn decide<I: IdentifierSource>(
        &self,
        command: SessionCommand,
        now: &str,
        identifiers: &mut I,
    ) -> Result<Vec<SessionEvent>, ApplicationError> {
        parse_timestamp(now)?;
        if !matches!(&command, SessionCommand::StartSession { .. }) {
            self.require_open()?;
        }

        let events = match command {
            SessionCommand::StartSession {
                prior_model_snapshot,
            } => self.decide_start(prior_model_snapshot)?,
            SessionCommand::GrantConsent { grant } => self.decide_grant(grant, now)?,
            SessionCommand::RevokeConsent { consent_grant_id } => {
                self.decide_revoke(consent_grant_id)?
            }
            SessionCommand::AcceptWorkingProjection { projection } => {
                self.require_no_safety_halt()?;
                self.decide_projection(projection, now)?
            }
            SessionCommand::RecordMoment { moment } => {
                self.require_no_safety_halt()?;
                self.decide_moment(moment, now)?
            }
            SessionCommand::ProposeJourney { plan } => {
                self.require_no_safety_halt()?;
                self.decide_journey(plan)?
            }
            SessionCommand::ApproveJourney { plan_id, consent } => {
                self.require_no_safety_halt()?;
                self.decide_journey_approval(plan_id, &consent, now)?
            }
            SessionCommand::RequestGeneration { specification } => {
                self.require_no_safety_halt()?;
                self.decide_generation_request(specification)?
            }
            SessionCommand::ApproveGeneration { consent } => {
                self.require_no_safety_halt()?;
                self.decide_generation_approval(&consent, now)?
            }
            SessionCommand::StartGeneration => {
                self.require_no_safety_halt()?;
                self.decide_generation_start(now)?
            }
            SessionCommand::RecordGenerationResult { result } => {
                self.decide_generation_result(result)?
            }
            SessionCommand::CancelGeneration => self.decide_generation_cancel()?,
            SessionCommand::ApprovePlayback { artifact_sha256 } => {
                self.require_no_safety_halt()?;
                let approval_id = next_identifier(identifiers, IdentifierKind::PlaybackApproval)?;
                self.decide_playback_approval(approval_id, artifact_sha256, now)?
            }
            SessionCommand::StartExposure { approval_id } => {
                self.require_no_safety_halt()?;
                let exposure_id = next_identifier(identifiers, IdentifierKind::Exposure)?;
                self.decide_exposure_start(exposure_id, approval_id, now)?
            }
            SessionCommand::StopExposure {
                exposure_id,
                reason,
            } => {
                let safety_id = if reason == ExposureStopReason::AdverseResponse {
                    Some(next_identifier(identifiers, IdentifierKind::SafetyEvent)?)
                } else {
                    None
                };
                self.decide_exposure_stop(exposure_id, reason, safety_id, now)?
            }
            SessionCommand::RecordResponse { response, consent } => {
                let needs_safety_event =
                    response.harm.unwrap_or(0.0) > 0.0 || response.stopped_early.unwrap_or(false);
                let safety_id = if needs_safety_event {
                    Some(next_identifier(identifiers, IdentifierKind::SafetyEvent)?)
                } else {
                    None
                };
                self.decide_response(response, &consent, safety_id, now)?
            }
            SessionCommand::RecordSafetyEvent { kind, description } => {
                let safety_id = next_identifier(identifiers, IdentifierKind::SafetyEvent)?;
                Self::decide_safety_event(safety_id, kind, description, now)?
            }
            SessionCommand::AcknowledgeSafetyEvent { safety_event_id } => {
                self.decide_safety_acknowledgement(safety_event_id)?
            }
            SessionCommand::ProposeModelUpdate {
                consent,
                candidate,
                evidence_response_ids,
            } => {
                self.require_no_safety_halt()?;
                let proposal_id =
                    next_identifier(identifiers, IdentifierKind::ModelUpdateProposal)?;
                self.decide_model_update_proposal(
                    proposal_id,
                    &consent,
                    candidate,
                    evidence_response_ids,
                    now,
                )?
            }
            SessionCommand::AcceptModelUpdate {
                proposal_id,
                consent,
            } => {
                self.require_no_safety_halt()?;
                self.decide_model_update_acceptance(proposal_id, &consent, now)?
            }
            SessionCommand::RejectModelUpdate { proposal_id } => {
                self.decide_model_update_rejection(proposal_id)?
            }
            SessionCommand::FailModelUpdate { proposal_id } => {
                self.decide_model_update_failure(proposal_id)?
            }
            SessionCommand::ApproveExport { consent } => {
                self.require_no_safety_halt()?;
                let approval_id = next_identifier(identifiers, IdentifierKind::ExportApproval)?;
                self.decide_export_approval(approval_id, &consent, now)?
            }
            SessionCommand::RecordExportShared {
                approval_id,
                manifest_sha256,
            } => self.decide_export_shared(approval_id, manifest_sha256, now)?,
            SessionCommand::CloseSession => vec![SessionEvent::SessionClosed],
        };
        Ok(events)
    }

    fn require_open(&self) -> Result<(), DomainError> {
        if !self.is_started() {
            return Err(DomainError::SessionNotStarted);
        }
        if self.is_closed() {
            return Err(DomainError::SessionClosed);
        }
        Ok(())
    }

    fn require_no_safety_halt(&self) -> Result<(), DomainError> {
        if self.safety_halt_id.is_some() {
            return Err(DomainError::SafetyHaltActive);
        }
        Ok(())
    }

    fn decide_start(
        &self,
        prior_model_snapshot: Option<PersonalModelSnapshot>,
    ) -> Result<Vec<SessionEvent>, DomainError> {
        if self.is_started() {
            return Err(DomainError::SessionAlreadyStarted);
        }
        if let Some(snapshot) = prior_model_snapshot.as_ref() {
            validate_snapshot(snapshot)?;
        }
        Ok(vec![SessionEvent::SessionStarted {
            prior_model_snapshot,
        }])
    }

    fn decide_grant(
        &self,
        grant: ConsentGrant,
        now: &str,
    ) -> Result<Vec<SessionEvent>, DomainError> {
        validate_typed_contract("consent-grant", &grant)?;
        self.require_same_session(&grant.session_id)?;
        if self.consent_grants.contains_key(&grant.id) {
            return Err(DomainError::ConsentAlreadyExists);
        }
        let created_at = parse_timestamp(&grant.created_at)?;
        let now = parse_timestamp(now)?;
        if created_at > now {
            return Err(DomainError::InvalidTimestamp);
        }
        if let Some(expires_at) = grant.expires_at.as_deref()
            && parse_timestamp(expires_at)? <= created_at
        {
            return Err(DomainError::InvalidTimestamp);
        }
        Ok(vec![SessionEvent::ConsentGranted { grant }])
    }

    fn decide_revoke(&self, consent_grant_id: String) -> Result<Vec<SessionEvent>, DomainError> {
        require_identifier(&consent_grant_id)?;
        let grant = self
            .consent_grants
            .get(&consent_grant_id)
            .ok_or(DomainError::ConsentMissing)?;
        if grant.status == ConsentGrantStatus::Revoked {
            return Err(DomainError::ConsentRevoked);
        }
        Ok(vec![SessionEvent::ConsentRevoked { consent_grant_id }])
    }

    fn decide_projection(
        &self,
        projection: WorkingContextProjection,
        now: &str,
    ) -> Result<Vec<SessionEvent>, DomainError> {
        validate_typed_contract("working-context-projection", &projection)?;
        self.require_same_session(&projection.session_id)?;
        if projection
            .semantic_items
            .iter()
            .any(|item| item.user_review == WorkingContextProjectionSemanticItemUserReview::Pending)
        {
            return Err(DomainError::ProjectionReviewPending);
        }
        if let Some(expires_at) = projection.expires_at.as_deref()
            && parse_timestamp(expires_at)? <= parse_timestamp(now)?
        {
            return Err(DomainError::ProjectionExpired);
        }
        for consent_grant_id in &projection.consent_grant_ids {
            let grant = self.validate_named_consent(
                consent_grant_id,
                &ConsentGrantPurpose::JourneyPlanning,
                &ConsentGrantAction::Project,
                now,
            )?;
            if grant.retention.allow_derived_projection != Some(true) {
                return Err(DomainError::ConsentProjectionNotAllowed);
            }
        }
        Ok(vec![SessionEvent::WorkingProjectionAccepted { projection }])
    }

    fn decide_moment(
        &self,
        moment: MomentContext,
        now: &str,
    ) -> Result<Vec<SessionEvent>, DomainError> {
        if self.moment.is_some() {
            return Err(DomainError::MomentAlreadyRecorded);
        }
        validate_typed_contract("moment-context", &moment)?;
        self.require_same_session(&moment.session_id)?;
        parse_timestamp(&moment.observed_at)?;
        if let Some(projection_id) = moment.working_projection_id.as_deref() {
            let projection = self
                .working_projection
                .as_ref()
                .filter(|projection| projection.id == projection_id)
                .ok_or(DomainError::ProjectionMissing)?;
            if let Some(expires_at) = projection.expires_at.as_deref()
                && parse_timestamp(expires_at)? <= parse_timestamp(now)?
            {
                return Err(DomainError::ProjectionExpired);
            }
        }
        Ok(vec![SessionEvent::MomentRecorded { moment }])
    }

    fn decide_journey(&self, plan: JourneyPlan) -> Result<Vec<SessionEvent>, DomainError> {
        if self.journey.is_some() {
            return Err(DomainError::JourneyAlreadyExists);
        }
        validate_typed_contract("journey-plan", &plan)?;
        self.require_same_session(&plan.session_id)?;
        let moment = self.moment.as_ref().ok_or(DomainError::MomentMissing)?;
        if plan.status != JourneyPlanStatus::Draft
            || plan.moment_context_id != moment.id
            || plan.working_projection_id != moment.working_projection_id
        {
            return Err(DomainError::JourneyInvalid);
        }
        validate_journey_stages(&plan)?;
        Ok(vec![SessionEvent::JourneyProposed { plan }])
    }

    fn decide_journey_approval(
        &self,
        plan_id: String,
        selection: &ConsentSelection,
        now: &str,
    ) -> Result<Vec<SessionEvent>, DomainError> {
        let journey = self.journey.as_ref().ok_or(DomainError::JourneyMissing)?;
        if journey.plan.id != plan_id {
            return Err(DomainError::JourneyMissing);
        }
        if journey.approval != JourneyApprovalState::Draft {
            return Err(DomainError::JourneyNotDraft);
        }
        let grant = self.resolve_consent(
            selection,
            &ConsentGrantPurpose::JourneyPlanning,
            &ConsentGrantAction::Project,
            now,
        )?;
        Ok(vec![SessionEvent::JourneyApproved {
            plan_id,
            consent_grant_id: grant.id.clone(),
        }])
    }

    fn decide_generation_request(
        &self,
        specification: GenerationSpec,
    ) -> Result<Vec<SessionEvent>, DomainError> {
        if self.generation.is_some() {
            return Err(DomainError::GenerationAlreadyActive);
        }
        validate_typed_contract("generation-spec", &specification)?;
        self.require_same_session(&specification.session_id)?;
        let journey = self.journey.as_ref().ok_or(DomainError::JourneyMissing)?;
        if !matches!(&journey.approval, JourneyApprovalState::Approved { .. }) {
            return Err(DomainError::JourneyNotApproved);
        }
        let plan_hash = journey
            .plan
            .plan_hash
            .as_deref()
            .ok_or(DomainError::JourneyInvalid)?;
        if specification.journey_plan_id != journey.plan.id
            || specification.journey_plan_hash != plan_hash
            || specification.duration_seconds != journey.plan.total_duration_seconds
        {
            return Err(DomainError::GenerationMismatch);
        }
        Ok(vec![SessionEvent::GenerationRequested { specification }])
    }

    fn decide_generation_approval(
        &self,
        selection: &ConsentSelection,
        now: &str,
    ) -> Result<Vec<SessionEvent>, DomainError> {
        let generation = self
            .generation
            .as_ref()
            .ok_or(DomainError::GenerationMissing)?;
        if generation.state != GenerationJobState::Requested {
            return if generation.state.is_terminal() {
                Err(DomainError::GenerationTerminal)
            } else {
                Err(DomainError::GenerationNotApproved)
            };
        }
        let grant = self.resolve_consent(
            selection,
            &ConsentGrantPurpose::Generation,
            &ConsentGrantAction::Generate,
            now,
        )?;
        Ok(vec![SessionEvent::GenerationApproved {
            consent_grant_id: grant.id.clone(),
        }])
    }

    fn decide_generation_start(&self, now: &str) -> Result<Vec<SessionEvent>, DomainError> {
        let generation = self
            .generation
            .as_ref()
            .ok_or(DomainError::GenerationMissing)?;
        if generation.state != GenerationJobState::Approved {
            return if generation.state.is_terminal() {
                Err(DomainError::GenerationTerminal)
            } else {
                Err(DomainError::GenerationNotApproved)
            };
        }
        let grant_id = generation
            .consent_grant_id
            .as_deref()
            .ok_or(DomainError::ConsentMissing)?;
        self.validate_named_consent(
            grant_id,
            &ConsentGrantPurpose::Generation,
            &ConsentGrantAction::Generate,
            now,
        )?;
        Ok(vec![SessionEvent::GenerationStarted])
    }

    fn decide_generation_result(
        &self,
        result: GenerationResult,
    ) -> Result<Vec<SessionEvent>, DomainError> {
        let generation = self
            .generation
            .as_ref()
            .ok_or(DomainError::GenerationMissing)?;
        if generation.state != GenerationJobState::Running {
            return Err(DomainError::GenerationNotRunning);
        }
        validate_typed_contract("generation-result", &result)?;
        if result.generation_spec_id != generation.specification.id {
            return Err(DomainError::GenerationMismatch);
        }
        if result.status == GenerationResultStatus::Generated
            && !result.artifacts.iter().any(|artifact| {
                artifact.kind == GenerationResultArtifactKind::Audio && artifact.size_bytes > 0
            })
        {
            return Err(DomainError::GeneratedAudioMissing);
        }
        Ok(vec![SessionEvent::GenerationResultRecorded { result }])
    }

    fn decide_generation_cancel(&self) -> Result<Vec<SessionEvent>, DomainError> {
        let generation = self
            .generation
            .as_ref()
            .ok_or(DomainError::GenerationMissing)?;
        if generation.state.is_terminal() {
            return Err(DomainError::GenerationTerminal);
        }
        Ok(vec![SessionEvent::GenerationCancelled])
    }

    fn decide_playback_approval(
        &self,
        approval_id: String,
        artifact_sha256: String,
        now: &str,
    ) -> Result<Vec<SessionEvent>, DomainError> {
        require_sha256(&artifact_sha256)?;
        let generation = self
            .generation
            .as_ref()
            .ok_or(DomainError::GenerationMissing)?;
        if generation.state != GenerationJobState::Generated {
            return Err(DomainError::GenerationTerminal);
        }
        if !generation_has_audio_hash(generation, &artifact_sha256) {
            return Err(DomainError::ArtifactMismatch);
        }
        Ok(vec![SessionEvent::PlaybackApproved {
            approval: PlaybackApproval {
                id: approval_id,
                artifact_sha256,
                approved_at: now.to_owned(),
                consumed: false,
            },
        }])
    }

    fn decide_exposure_start(
        &self,
        exposure_id: String,
        approval_id: String,
        now: &str,
    ) -> Result<Vec<SessionEvent>, DomainError> {
        if self
            .exposure
            .as_ref()
            .is_some_and(|exposure| exposure.state == ExposureState::Playing)
        {
            return Err(DomainError::ExposureAlreadyActive);
        }
        let approval = self
            .playback_approval
            .as_ref()
            .filter(|approval| approval.id == approval_id && !approval.consumed)
            .ok_or(DomainError::PlaybackNotApproved)?;
        let generation = self
            .generation
            .as_ref()
            .ok_or(DomainError::GenerationMissing)?;
        if generation.state != GenerationJobState::Generated
            || !generation_has_audio_hash(generation, &approval.artifact_sha256)
        {
            return Err(DomainError::ArtifactMismatch);
        }
        Ok(vec![SessionEvent::ExposureStarted {
            exposure: Exposure {
                id: exposure_id,
                approval_id,
                artifact_sha256: approval.artifact_sha256.clone(),
                started_at: now.to_owned(),
                state: ExposureState::Playing,
            },
        }])
    }

    fn decide_exposure_stop(
        &self,
        exposure_id: String,
        reason: ExposureStopReason,
        safety_id: Option<String>,
        now: &str,
    ) -> Result<Vec<SessionEvent>, DomainError> {
        let exposure = self
            .exposure
            .as_ref()
            .filter(|exposure| exposure.id == exposure_id)
            .ok_or(DomainError::ExposureMissing)?;
        if exposure.state != ExposureState::Playing {
            return Err(DomainError::ExposureNotActive);
        }
        let mut events = vec![SessionEvent::ExposureStopped {
            exposure_id,
            reason,
        }];
        if reason == ExposureStopReason::AdverseResponse {
            events.push(SessionEvent::SafetyEventRecorded {
                safety_event: SafetyEvent {
                    id: safety_id.ok_or(DomainError::EmptyIdentifier)?,
                    kind: SafetyEventKind::PlaybackStop,
                    description: "playback stopped after an adverse response".to_owned(),
                    observed_at: now.to_owned(),
                },
            });
        }
        Ok(events)
    }

    fn decide_response(
        &self,
        response: ResponseObservation,
        selection: &ConsentSelection,
        safety_id: Option<String>,
        now: &str,
    ) -> Result<Vec<SessionEvent>, DomainError> {
        validate_typed_contract("response-observation", &response)?;
        self.require_same_session(&response.session_id)?;
        if self.responses.contains_key(&response.id) {
            return Err(DomainError::InvalidContract {
                contract: "response-observation",
            });
        }
        let exposure = self
            .exposure
            .as_ref()
            .filter(|exposure| exposure.id == response.exposure_id)
            .ok_or(DomainError::ExposureMissing)?;
        validate_response_window(exposure, &response.window)?;
        let grant = self.resolve_consent(
            selection,
            &ConsentGrantPurpose::ResponseCapture,
            &ConsentGrantAction::Retain,
            now,
        )?;
        let harmed = response.harm.unwrap_or(0.0) > 0.0;
        let stopped_early = response.stopped_early.unwrap_or(false);
        let mut events = vec![SessionEvent::ResponseRecorded {
            response,
            consent_grant_id: grant.id.clone(),
        }];
        if harmed || stopped_early {
            events.push(SessionEvent::SafetyEventRecorded {
                safety_event: SafetyEvent {
                    id: safety_id.ok_or(DomainError::EmptyIdentifier)?,
                    kind: if harmed {
                        SafetyEventKind::AdverseResponse
                    } else {
                        SafetyEventKind::PlaybackStop
                    },
                    description: if harmed {
                        "response observation reported possible harm".to_owned()
                    } else {
                        "response observation recorded an early stop".to_owned()
                    },
                    observed_at: now.to_owned(),
                },
            });
        }
        Ok(events)
    }

    fn decide_safety_event(
        safety_id: String,
        kind: SafetyEventKind,
        description: String,
        now: &str,
    ) -> Result<Vec<SessionEvent>, DomainError> {
        require_identifier(&description)?;
        Ok(vec![SessionEvent::SafetyEventRecorded {
            safety_event: SafetyEvent {
                id: safety_id,
                kind,
                description,
                observed_at: now.to_owned(),
            },
        }])
    }

    fn decide_safety_acknowledgement(
        &self,
        safety_event_id: String,
    ) -> Result<Vec<SessionEvent>, DomainError> {
        if self.safety_halt_id.as_deref() != Some(safety_event_id.as_str()) {
            return Err(DomainError::SafetyHaltMissing);
        }
        Ok(vec![SessionEvent::SafetyEventAcknowledged {
            safety_event_id,
        }])
    }

    fn decide_model_update_proposal(
        &self,
        proposal_id: String,
        selection: &ConsentSelection,
        candidate: PersonalModelSnapshot,
        evidence_response_ids: Vec<String>,
        now: &str,
    ) -> Result<Vec<SessionEvent>, DomainError> {
        if self
            .model_update_proposal
            .as_ref()
            .is_some_and(|proposal| proposal.state == ModelUpdateState::Pending)
        {
            return Err(DomainError::ModelUpdateAlreadyPending);
        }
        validate_snapshot(&candidate)?;
        validate_model_base(self.personal_model_snapshot.as_ref(), &candidate)?;
        if evidence_response_ids.is_empty()
            || evidence_response_ids != candidate.evidence_response_ids
        {
            return Err(DomainError::ModelEvidenceInvalid);
        }
        for response_id in &evidence_response_ids {
            let response = self
                .responses
                .get(response_id)
                .ok_or(DomainError::ResponseMissing)?;
            if response.allow_personal_model_update != Some(true) {
                return Err(DomainError::ModelEvidenceInvalid);
            }
        }
        let grant = self.resolve_consent(
            selection,
            &ConsentGrantPurpose::PersonalLearning,
            &ConsentGrantAction::Learn,
            now,
        )?;
        if grant.retention.allow_personal_model_update != Some(true) {
            return Err(DomainError::ConsentLearningNotAllowed);
        }
        Ok(vec![SessionEvent::ModelUpdateProposed {
            proposal: ModelUpdateProposal {
                id: proposal_id,
                base_snapshot_id: self
                    .personal_model_snapshot
                    .as_ref()
                    .map(|snapshot| snapshot.id.clone()),
                candidate,
                evidence_response_ids,
                consent_grant_id: grant.id.clone(),
                state: ModelUpdateState::Pending,
            },
        }])
    }

    fn decide_model_update_acceptance(
        &self,
        proposal_id: String,
        selection: &ConsentSelection,
        now: &str,
    ) -> Result<Vec<SessionEvent>, DomainError> {
        let proposal = self.pending_model_update(&proposal_id)?;
        validate_model_base(self.personal_model_snapshot.as_ref(), &proposal.candidate)?;
        let grant = self.resolve_consent(
            selection,
            &ConsentGrantPurpose::PersonalLearning,
            &ConsentGrantAction::Learn,
            now,
        )?;
        if grant.id != proposal.consent_grant_id
            || grant.retention.allow_personal_model_update != Some(true)
        {
            return Err(DomainError::ConsentLearningNotAllowed);
        }
        Ok(vec![SessionEvent::ModelUpdateAccepted { proposal_id }])
    }

    fn decide_model_update_rejection(
        &self,
        proposal_id: String,
    ) -> Result<Vec<SessionEvent>, DomainError> {
        self.pending_model_update(&proposal_id)?;
        Ok(vec![SessionEvent::ModelUpdateRejected { proposal_id }])
    }

    fn decide_model_update_failure(
        &self,
        proposal_id: String,
    ) -> Result<Vec<SessionEvent>, DomainError> {
        self.pending_model_update(&proposal_id)?;
        Ok(vec![SessionEvent::ModelUpdateFailed { proposal_id }])
    }

    fn decide_export_approval(
        &self,
        approval_id: String,
        selection: &ConsentSelection,
        now: &str,
    ) -> Result<Vec<SessionEvent>, DomainError> {
        let grant = self.resolve_consent(
            selection,
            &ConsentGrantPurpose::ResearchExport,
            &ConsentGrantAction::Export,
            now,
        )?;
        Ok(vec![SessionEvent::ExportApproved {
            approval: ExportApproval {
                id: approval_id,
                consent_grant_id: grant.id.clone(),
                approved_at: now.to_owned(),
                shared_manifest_sha256: None,
            },
        }])
    }

    fn decide_export_shared(
        &self,
        approval_id: String,
        manifest_sha256: String,
        now: &str,
    ) -> Result<Vec<SessionEvent>, DomainError> {
        require_sha256(&manifest_sha256)?;
        let approval = self
            .export_approval
            .as_ref()
            .filter(|approval| approval.id == approval_id)
            .ok_or(DomainError::ExportApprovalMissing)?;
        if approval.shared_manifest_sha256.is_some() {
            return Err(DomainError::ExportAlreadyShared);
        }
        self.validate_named_consent(
            &approval.consent_grant_id,
            &ConsentGrantPurpose::ResearchExport,
            &ConsentGrantAction::Export,
            now,
        )?;
        Ok(vec![SessionEvent::ExportShared {
            approval_id,
            manifest_sha256,
        }])
    }

    fn pending_model_update(&self, proposal_id: &str) -> Result<&ModelUpdateProposal, DomainError> {
        let proposal = self
            .model_update_proposal
            .as_ref()
            .filter(|proposal| proposal.id == proposal_id)
            .ok_or(DomainError::ModelUpdateMissing)?;
        if proposal.state != ModelUpdateState::Pending {
            return Err(DomainError::ModelUpdateNotPending);
        }
        Ok(proposal)
    }

    fn require_same_session(&self, session_id: &str) -> Result<(), DomainError> {
        if session_id != self.id {
            return Err(DomainError::WrongSession);
        }
        Ok(())
    }

    fn resolve_consent(
        &self,
        selection: &ConsentSelection,
        purpose: &ConsentGrantPurpose,
        action: &ConsentGrantAction,
        now: &str,
    ) -> Result<&ConsentGrant, DomainError> {
        match selection.grant_ids.as_slice() {
            [grant_id] => self.validate_named_consent(grant_id, purpose, action, now),
            [] => {
                let matching = self
                    .consent_grants
                    .values()
                    .filter(|grant| self.validate_grant(grant, purpose, action, now).is_ok())
                    .collect::<Vec<_>>();
                match matching.as_slice() {
                    [grant] => Ok(*grant),
                    [] => Err(DomainError::ConsentMissing),
                    _ => Err(DomainError::ConsentAmbiguous),
                }
            }
            _ => Err(DomainError::ConsentAmbiguous),
        }
    }

    fn validate_named_consent(
        &self,
        grant_id: &str,
        purpose: &ConsentGrantPurpose,
        action: &ConsentGrantAction,
        now: &str,
    ) -> Result<&ConsentGrant, DomainError> {
        let grant = self
            .consent_grants
            .get(grant_id)
            .ok_or(DomainError::ConsentMissing)?;
        self.validate_grant(grant, purpose, action, now)?;
        Ok(grant)
    }

    fn validate_grant(
        &self,
        grant: &ConsentGrant,
        purpose: &ConsentGrantPurpose,
        action: &ConsentGrantAction,
        now: &str,
    ) -> Result<(), DomainError> {
        self.require_same_session(&grant.session_id)?;
        match &grant.status {
            ConsentGrantStatus::Revoked => return Err(DomainError::ConsentRevoked),
            ConsentGrantStatus::Expired => return Err(DomainError::ConsentExpired),
            ConsentGrantStatus::Active => {}
        }
        if let Some(expires_at) = grant.expires_at.as_deref()
            && parse_timestamp(expires_at)? <= parse_timestamp(now)?
        {
            return Err(DomainError::ConsentExpired);
        }
        if !grant.purposes.contains(purpose) {
            return Err(DomainError::ConsentWrongPurpose);
        }
        if !grant.actions.contains(action) {
            return Err(DomainError::ConsentWrongAction);
        }
        Ok(())
    }

    fn apply_recorded(&mut self, recorded: &RecordedEvent) -> Result<(), DomainError> {
        require_identifier(&recorded.id)?;
        self.require_same_session(&recorded.session_id)?;
        parse_timestamp(&recorded.occurred_at)?;
        if recorded.schema_version != SESSION_EVENT_SCHEMA_VERSION
            || recorded.sequence != self.version + 1
        {
            return Err(DomainError::InvalidEventSequence);
        }
        self.apply(recorded.event.clone(), &recorded.occurred_at)?;
        self.version = recorded.sequence;
        Ok(())
    }

    #[allow(clippy::too_many_lines)]
    fn apply(&mut self, event: SessionEvent, occurred_at: &str) -> Result<(), DomainError> {
        if !matches!(&event, SessionEvent::SessionStarted { .. }) {
            self.require_open()?;
        }
        if self.safety_halt_id.is_some() && event_requires_clear_safety(&event) {
            return Err(DomainError::SafetyHaltActive);
        }
        match event {
            SessionEvent::SessionStarted {
                prior_model_snapshot,
            } => {
                if self.is_started() {
                    return Err(DomainError::SessionAlreadyStarted);
                }
                if let Some(snapshot) = prior_model_snapshot.as_ref() {
                    validate_snapshot(snapshot)?;
                }
                self.started_at = Some(occurred_at.to_owned());
                self.personal_model_snapshot = prior_model_snapshot;
            }
            SessionEvent::ConsentGranted { grant } => {
                drop(self.decide_grant(grant.clone(), occurred_at)?);
                self.consent_grants.insert(grant.id.clone(), grant);
            }
            SessionEvent::ConsentRevoked { consent_grant_id } => {
                drop(self.decide_revoke(consent_grant_id.clone())?);
                let grant = self
                    .consent_grants
                    .get_mut(&consent_grant_id)
                    .ok_or(DomainError::ConsentMissing)?;
                grant.status = ConsentGrantStatus::Revoked;
            }
            SessionEvent::WorkingProjectionAccepted { projection } => {
                drop(self.decide_projection(projection.clone(), occurred_at)?);
                self.working_projection = Some(projection);
            }
            SessionEvent::MomentRecorded { moment } => {
                drop(self.decide_moment(moment.clone(), occurred_at)?);
                self.moment = Some(moment);
            }
            SessionEvent::JourneyProposed { plan } => {
                drop(self.decide_journey(plan.clone())?);
                self.journey = Some(JourneyState {
                    plan,
                    approval: JourneyApprovalState::Draft,
                });
            }
            SessionEvent::JourneyApproved {
                plan_id,
                consent_grant_id,
            } => {
                drop(self.decide_journey_approval(
                    plan_id.clone(),
                    &ConsentSelection::explicit(consent_grant_id.clone()),
                    occurred_at,
                )?);
                let journey = self.journey.as_mut().ok_or(DomainError::JourneyMissing)?;
                journey.approval = JourneyApprovalState::Approved {
                    consent_grant_id,
                    approved_at: occurred_at.to_owned(),
                };
            }
            SessionEvent::GenerationRequested { specification } => {
                drop(self.decide_generation_request(specification.clone())?);
                self.generation = Some(GenerationJob {
                    specification,
                    state: GenerationJobState::Requested,
                    consent_grant_id: None,
                    result: None,
                });
            }
            SessionEvent::GenerationApproved { consent_grant_id } => {
                drop(self.decide_generation_approval(
                    &ConsentSelection::explicit(consent_grant_id.clone()),
                    occurred_at,
                )?);
                let generation = self
                    .generation
                    .as_mut()
                    .ok_or(DomainError::GenerationMissing)?;
                generation.state = GenerationJobState::Approved;
                generation.consent_grant_id = Some(consent_grant_id);
            }
            SessionEvent::GenerationStarted => {
                drop(self.decide_generation_start(occurred_at)?);
                let generation = self
                    .generation
                    .as_mut()
                    .ok_or(DomainError::GenerationMissing)?;
                generation.state = GenerationJobState::Running;
            }
            SessionEvent::GenerationResultRecorded { result } => {
                drop(self.decide_generation_result(result.clone())?);
                let generation = self
                    .generation
                    .as_mut()
                    .ok_or(DomainError::GenerationMissing)?;
                generation.state = match &result.status {
                    GenerationResultStatus::Generated => GenerationJobState::Generated,
                    GenerationResultStatus::Partial => GenerationJobState::Partial,
                    GenerationResultStatus::Cancelled => GenerationJobState::Cancelled,
                    GenerationResultStatus::Failed => GenerationJobState::Failed,
                };
                generation.result = Some(result);
            }
            SessionEvent::GenerationCancelled => {
                drop(self.decide_generation_cancel()?);
                let generation = self
                    .generation
                    .as_mut()
                    .ok_or(DomainError::GenerationMissing)?;
                generation.state = GenerationJobState::Cancelled;
            }
            SessionEvent::PlaybackApproved { approval } => {
                require_identifier(&approval.id)?;
                require_sha256(&approval.artifact_sha256)?;
                if approval.consumed || approval.approved_at != occurred_at {
                    return Err(DomainError::PlaybackNotApproved);
                }
                drop(self.decide_playback_approval(
                    approval.id.clone(),
                    approval.artifact_sha256.clone(),
                    occurred_at,
                )?);
                self.playback_approval = Some(approval);
            }
            SessionEvent::ExposureStarted { exposure } => {
                require_identifier(&exposure.id)?;
                require_sha256(&exposure.artifact_sha256)?;
                if exposure.state != ExposureState::Playing || exposure.started_at != occurred_at {
                    return Err(DomainError::ExposureNotActive);
                }
                drop(self.decide_exposure_start(
                    exposure.id.clone(),
                    exposure.approval_id.clone(),
                    occurred_at,
                )?);
                let approval = self
                    .playback_approval
                    .as_mut()
                    .filter(|approval| {
                        approval.id == exposure.approval_id
                            && approval.artifact_sha256 == exposure.artifact_sha256
                            && !approval.consumed
                    })
                    .ok_or(DomainError::PlaybackNotApproved)?;
                approval.consumed = true;
                self.exposure = Some(exposure);
            }
            SessionEvent::ExposureStopped {
                exposure_id,
                reason,
            } => {
                let exposure = self
                    .exposure
                    .as_mut()
                    .filter(|exposure| exposure.id == exposure_id)
                    .ok_or(DomainError::ExposureMissing)?;
                if exposure.state != ExposureState::Playing {
                    return Err(DomainError::ExposureNotActive);
                }
                exposure.state = ExposureState::Stopped {
                    stopped_at: occurred_at.to_owned(),
                    reason,
                };
            }
            SessionEvent::ResponseRecorded {
                response,
                consent_grant_id,
            } => {
                let safety_id = (response.harm.unwrap_or(0.0) > 0.0
                    || response.stopped_early.unwrap_or(false))
                .then(|| "replay-safety-validation".to_owned());
                drop(self.decide_response(
                    response.clone(),
                    &ConsentSelection::explicit(consent_grant_id),
                    safety_id,
                    occurred_at,
                )?);
                self.responses.insert(response.id.clone(), response);
            }
            SessionEvent::SafetyEventRecorded { safety_event } => {
                require_identifier(&safety_event.id)?;
                require_identifier(&safety_event.description)?;
                parse_timestamp(&safety_event.observed_at)?;
                self.safety_halt_id = Some(safety_event.id.clone());
                self.safety_events.push(safety_event);
            }
            SessionEvent::SafetyEventAcknowledged { safety_event_id } => {
                if self.safety_halt_id.as_deref() != Some(safety_event_id.as_str()) {
                    return Err(DomainError::SafetyHaltMissing);
                }
                self.safety_halt_id = None;
            }
            SessionEvent::ModelUpdateProposed { proposal } => {
                drop(self.decide_model_update_proposal(
                    proposal.id.clone(),
                    &ConsentSelection::explicit(proposal.consent_grant_id.clone()),
                    proposal.candidate.clone(),
                    proposal.evidence_response_ids.clone(),
                    occurred_at,
                )?);
                self.model_update_proposal = Some(proposal);
            }
            SessionEvent::ModelUpdateAccepted { proposal_id } => {
                let consent_grant_id = self
                    .pending_model_update(&proposal_id)?
                    .consent_grant_id
                    .clone();
                drop(self.decide_model_update_acceptance(
                    proposal_id.clone(),
                    &ConsentSelection::explicit(consent_grant_id),
                    occurred_at,
                )?);
                let proposal = self
                    .model_update_proposal
                    .as_mut()
                    .filter(|proposal| proposal.id == proposal_id)
                    .ok_or(DomainError::ModelUpdateMissing)?;
                if proposal.state != ModelUpdateState::Pending {
                    return Err(DomainError::ModelUpdateNotPending);
                }
                proposal.state = ModelUpdateState::Accepted;
                self.personal_model_snapshot = Some(proposal.candidate.clone());
            }
            SessionEvent::ModelUpdateRejected { proposal_id } => {
                drop(self.decide_model_update_rejection(proposal_id.clone())?);
                set_model_update_state(
                    self.model_update_proposal.as_mut(),
                    &proposal_id,
                    ModelUpdateState::Rejected,
                )?;
            }
            SessionEvent::ModelUpdateFailed { proposal_id } => {
                drop(self.decide_model_update_failure(proposal_id.clone())?);
                set_model_update_state(
                    self.model_update_proposal.as_mut(),
                    &proposal_id,
                    ModelUpdateState::Failed,
                )?;
            }
            SessionEvent::ExportApproved { approval } => {
                require_identifier(&approval.id)?;
                if approval.shared_manifest_sha256.is_some() || approval.approved_at != occurred_at
                {
                    return Err(DomainError::ExportAlreadyShared);
                }
                drop(self.decide_export_approval(
                    approval.id.clone(),
                    &ConsentSelection::explicit(approval.consent_grant_id.clone()),
                    occurred_at,
                )?);
                self.export_approval = Some(approval);
            }
            SessionEvent::ExportShared {
                approval_id,
                manifest_sha256,
            } => {
                drop(self.decide_export_shared(
                    approval_id.clone(),
                    manifest_sha256.clone(),
                    occurred_at,
                )?);
                let approval = self
                    .export_approval
                    .as_mut()
                    .filter(|approval| approval.id == approval_id)
                    .ok_or(DomainError::ExportApprovalMissing)?;
                if approval.shared_manifest_sha256.is_some() {
                    return Err(DomainError::ExportAlreadyShared);
                }
                approval.shared_manifest_sha256 = Some(manifest_sha256);
            }
            SessionEvent::SessionClosed => {
                self.closed_at = Some(occurred_at.to_owned());
            }
        }
        Ok(())
    }
}

fn parse_timestamp(value: &str) -> Result<OffsetDateTime, DomainError> {
    OffsetDateTime::parse(value, &Rfc3339).map_err(|_| DomainError::InvalidTimestamp)
}

fn event_requires_clear_safety(event: &SessionEvent) -> bool {
    matches!(
        event,
        SessionEvent::WorkingProjectionAccepted { .. }
            | SessionEvent::MomentRecorded { .. }
            | SessionEvent::JourneyProposed { .. }
            | SessionEvent::JourneyApproved { .. }
            | SessionEvent::GenerationRequested { .. }
            | SessionEvent::GenerationApproved { .. }
            | SessionEvent::GenerationStarted
            | SessionEvent::PlaybackApproved { .. }
            | SessionEvent::ExposureStarted { .. }
            | SessionEvent::ModelUpdateProposed { .. }
            | SessionEvent::ModelUpdateAccepted { .. }
            | SessionEvent::ExportApproved { .. }
            | SessionEvent::ExportShared { .. }
    )
}

pub(crate) fn require_identifier(value: &str) -> Result<(), DomainError> {
    if value.trim().is_empty() {
        Err(DomainError::EmptyIdentifier)
    } else {
        Ok(())
    }
}

fn require_sha256(value: &str) -> Result<(), DomainError> {
    if value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        Ok(())
    } else {
        Err(DomainError::InvalidSha256)
    }
}

fn validate_typed_contract<T: Serialize>(name: &'static str, value: &T) -> Result<(), DomainError> {
    let value =
        serde_json::to_value(value).map_err(|_| DomainError::InvalidContract { contract: name })?;
    validate_contract(name, &value).map_err(|_| DomainError::InvalidContract { contract: name })
}

fn validate_snapshot(snapshot: &PersonalModelSnapshot) -> Result<(), DomainError> {
    require_identifier(&snapshot.id)?;
    require_identifier(&snapshot.summary)?;
    if snapshot.version == 0 || snapshot.evidence_response_ids.is_empty() {
        return Err(DomainError::ModelEvidenceInvalid);
    }
    let mut evidence = snapshot.evidence_response_ids.clone();
    if evidence
        .iter()
        .any(|identifier| require_identifier(identifier).is_err())
    {
        return Err(DomainError::ModelEvidenceInvalid);
    }
    evidence.sort_unstable();
    evidence.dedup();
    if evidence.len() != snapshot.evidence_response_ids.len() {
        return Err(DomainError::ModelEvidenceInvalid);
    }
    Ok(())
}

fn validate_model_base(
    current: Option<&PersonalModelSnapshot>,
    candidate: &PersonalModelSnapshot,
) -> Result<(), DomainError> {
    match current {
        Some(current) => {
            if candidate.id == current.id
                || current.version.checked_add(1) != Some(candidate.version)
            {
                return Err(DomainError::ModelSnapshotMismatch);
            }
        }
        None if candidate.version != 1 => return Err(DomainError::ModelSnapshotMismatch),
        None => {}
    }
    Ok(())
}

fn validate_journey_stages(plan: &JourneyPlan) -> Result<(), DomainError> {
    let mut duration = 0_i64;
    let mut identifiers = Vec::with_capacity(plan.stages.len());
    for (expected_order, stage) in plan.stages.iter().enumerate() {
        let expected_order =
            i64::try_from(expected_order).map_err(|_| DomainError::JourneyInvalid)?;
        if stage.order != expected_order {
            return Err(DomainError::JourneyInvalid);
        }
        require_identifier(&stage.id)?;
        duration = duration
            .checked_add(stage.duration_seconds)
            .ok_or(DomainError::JourneyInvalid)?;
        identifiers.push(stage.id.as_str());
    }
    identifiers.sort_unstable();
    identifiers.dedup();
    if duration != plan.total_duration_seconds || identifiers.len() != plan.stages.len() {
        return Err(DomainError::JourneyInvalid);
    }
    Ok(())
}

fn generation_has_audio_hash(generation: &GenerationJob, artifact_sha256: &str) -> bool {
    generation.result.as_ref().is_some_and(|result| {
        result.status == GenerationResultStatus::Generated
            && result.artifacts.iter().any(|artifact| {
                artifact.kind == GenerationResultArtifactKind::Audio
                    && artifact.size_bytes > 0
                    && artifact.sha256 == artifact_sha256
            })
    })
}

fn validate_response_window(
    exposure: &Exposure,
    window: &ResponseObservationWindow,
) -> Result<(), DomainError> {
    let valid = matches!(
        (&exposure.state, window),
        (ExposureState::Playing, ResponseObservationWindow::During)
            | (
                ExposureState::Stopped { .. },
                ResponseObservationWindow::Immediate | ResponseObservationWindow::Later
            )
    );
    if valid {
        Ok(())
    } else {
        Err(DomainError::ResponseWindowInvalid)
    }
}

fn set_model_update_state(
    proposal: Option<&mut ModelUpdateProposal>,
    proposal_id: &str,
    state: ModelUpdateState,
) -> Result<(), DomainError> {
    let proposal = proposal
        .filter(|proposal| proposal.id == proposal_id)
        .ok_or(DomainError::ModelUpdateMissing)?;
    if proposal.state != ModelUpdateState::Pending {
        return Err(DomainError::ModelUpdateNotPending);
    }
    proposal.state = state;
    Ok(())
}

fn next_identifier<I: IdentifierSource>(
    identifiers: &mut I,
    kind: IdentifierKind,
) -> Result<String, ApplicationError> {
    let identifier = identifiers.next_id(kind)?;
    require_identifier(&identifier)?;
    Ok(identifier)
}
