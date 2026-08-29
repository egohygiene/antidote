#![allow(clippy::too_many_lines)]

use std::collections::BTreeMap;

use antidote_core::contracts::{
    ConsentGrant, ConsentGrantAction, ConsentGrantPurpose, GenerationResult, GenerationSpec,
    JourneyPlan, JourneyPlanStatus, MomentContext, ResponseObservation, WorkingContextProjection,
};
use antidote_core::{
    ApplicationError, Clock, ConsentSelection, DomainError, EventRepository, ExposureStopReason,
    GenerationJobState, GenerationOrchestrator, IdentifierKind, IdentifierSource, ModelUpdateState,
    PersonalModelSnapshot, PortFailure, RecordedEvent, SafetyEventKind, SessionCommand,
    SessionService, WorkerInvocationPort,
};
use serde::de::DeserializeOwned;
use serde_json::Value;

const SESSION_ID: &str = "session-synthetic-1";
const NOW: &str = "2026-08-27T12:10:00Z";
const AUDIO_HASH: &str = "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd";
const MANIFEST_HASH: &str = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee";

#[derive(Debug, Default)]
struct MemoryRepository {
    streams: BTreeMap<String, Vec<RecordedEvent>>,
}

impl EventRepository for MemoryRepository {
    fn load(&self, session_id: &str) -> Result<Vec<RecordedEvent>, PortFailure> {
        Ok(self.streams.get(session_id).cloned().unwrap_or_default())
    }

    fn append(
        &mut self,
        session_id: &str,
        expected_version: u64,
        events: &[RecordedEvent],
    ) -> Result<(), PortFailure> {
        let stream = self.streams.entry(session_id.to_owned()).or_default();
        if u64::try_from(stream.len()).ok() != Some(expected_version) {
            return Err(PortFailure::new("append_conflict"));
        }
        stream.extend_from_slice(events);
        Ok(())
    }
}

#[derive(Debug, Clone, Copy)]
struct FixedClock;

impl Clock for FixedClock {
    fn now_rfc3339(&self) -> Result<String, PortFailure> {
        Ok(NOW.to_owned())
    }
}

#[derive(Debug, Default)]
struct DeterministicIdentifiers {
    event: u64,
    playback: u64,
    exposure: u64,
    safety: u64,
    model_update: u64,
    export: u64,
}

impl IdentifierSource for DeterministicIdentifiers {
    fn next_id(&mut self, kind: IdentifierKind) -> Result<String, PortFailure> {
        let (prefix, counter) = match kind {
            IdentifierKind::Event => ("event", &mut self.event),
            IdentifierKind::PlaybackApproval => ("playback", &mut self.playback),
            IdentifierKind::Exposure => ("exposure", &mut self.exposure),
            IdentifierKind::SafetyEvent => ("safety", &mut self.safety),
            IdentifierKind::ModelUpdateProposal => ("model-update", &mut self.model_update),
            IdentifierKind::ExportApproval => ("export", &mut self.export),
        };
        *counter += 1;
        Ok(format!("{prefix}-{counter}"))
    }
}

type TestService = SessionService<MemoryRepository, FixedClock, DeterministicIdentifiers>;

fn service() -> TestService {
    SessionService::new(
        MemoryRepository::default(),
        FixedClock,
        DeterministicIdentifiers::default(),
    )
}

fn fixture<T: DeserializeOwned>(name: &str) -> T {
    let suite: Value = serde_json::from_str(include_str!("../../../contracts/fixtures/cases.json"))
        .expect("canonical fixture suite must parse");
    let data = suite["cases"]
        .as_array()
        .expect("fixture cases must be an array")
        .iter()
        .find(|case| case["name"] == name)
        .expect("named fixture must exist")["data"]
        .clone();
    serde_json::from_value(data).expect("valid fixture must match generated type")
}

fn broad_grant(id: &str) -> ConsentGrant {
    let mut grant: ConsentGrant = fixture("consent-grant-valid");
    id.clone_into(&mut grant.id);
    grant.purposes = vec![
        ConsentGrantPurpose::JourneyPlanning,
        ConsentGrantPurpose::Generation,
        ConsentGrantPurpose::ResponseCapture,
        ConsentGrantPurpose::PersonalLearning,
        ConsentGrantPurpose::ResearchExport,
    ];
    grant.actions = vec![
        ConsentGrantAction::Inspect,
        ConsentGrantAction::Project,
        ConsentGrantAction::Generate,
        ConsentGrantAction::Retain,
        ConsentGrantAction::Learn,
        ConsentGrantAction::Export,
    ];
    grant.retention.allow_derived_projection = Some(true);
    grant.retention.allow_personal_model_update = Some(true);
    grant
}

fn prior_snapshot() -> PersonalModelSnapshot {
    PersonalModelSnapshot {
        id: "snapshot-1".to_owned(),
        version: 1,
        summary: "A provisional, correctable prior-session preference.".to_owned(),
        evidence_response_ids: vec!["response-prior-1".to_owned()],
    }
}

fn assert_domain(error: ApplicationError, expected: &DomainError) {
    match error {
        ApplicationError::Domain(actual) => assert_eq!(&actual, expected),
        ApplicationError::Port(actual) => panic!("expected domain error, got {actual}"),
    }
}

fn execute(service: &mut TestService, command: SessionCommand) {
    service
        .execute(SESSION_ID, command)
        .expect("authorized transition must append");
}

fn service_through_generation_request() -> TestService {
    let mut service = service();
    execute(
        &mut service,
        SessionCommand::StartSession {
            prior_model_snapshot: Some(prior_snapshot()),
        },
    );
    execute(
        &mut service,
        SessionCommand::GrantConsent {
            grant: broad_grant("consent-all"),
        },
    );

    let mut projection: WorkingContextProjection = fixture("working-context-projection-valid");
    projection.consent_grant_ids = vec!["consent-all".to_owned()];
    execute(
        &mut service,
        SessionCommand::AcceptWorkingProjection { projection },
    );
    let moment: MomentContext = fixture("moment-context-valid");
    execute(&mut service, SessionCommand::RecordMoment { moment });

    let mut plan: JourneyPlan = fixture("journey-plan-valid");
    plan.status = JourneyPlanStatus::Draft;
    plan.approved_at = None;
    execute(&mut service, SessionCommand::ProposeJourney { plan });
    execute(
        &mut service,
        SessionCommand::ApproveJourney {
            plan_id: "journey-synthetic-1".to_owned(),
            consent: ConsentSelection::explicit("consent-all"),
        },
    );

    let specification: GenerationSpec = fixture("generation-spec-valid");
    execute(
        &mut service,
        SessionCommand::RequestGeneration { specification },
    );
    service
}

#[derive(Debug)]
struct StubWorker {
    result: Option<Result<GenerationResult, PortFailure>>,
}

impl WorkerInvocationPort for StubWorker {
    fn generate(
        &mut self,
        _specification: &GenerationSpec,
    ) -> Result<GenerationResult, PortFailure> {
        self.result
            .take()
            .expect("stub generation must be invoked exactly once")
    }

    fn cancel(&mut self, _generation_spec_id: &str) -> Result<(), PortFailure> {
        Ok(())
    }
}

#[test]
fn orchestrator_records_only_rust_owned_start_and_terminal_events() {
    let mut service = service_through_generation_request();
    execute(
        &mut service,
        SessionCommand::ApproveGeneration {
            consent: ConsentSelection::explicit("consent-all"),
        },
    );
    let worker = StubWorker {
        result: Some(Ok(fixture("generation-result-valid"))),
    };
    let mut orchestrator = GenerationOrchestrator::new(service, worker);
    let outcome = orchestrator
        .generate(SESSION_ID)
        .expect("trusted result must append through commands");
    assert_eq!(outcome.started.len(), 1);
    assert_eq!(outcome.terminal.len(), 1);
    assert!(outcome.worker_failure.is_none());

    let (service, _worker) = orchestrator.into_parts();
    let session = service
        .load_session(SESSION_ID)
        .expect("stream must replay");
    assert_eq!(
        session.generation().map(|generation| generation.state),
        Some(GenerationJobState::Generated)
    );
}

#[test]
fn orchestrator_translates_worker_failure_without_completing_generation() {
    let mut service = service_through_generation_request();
    execute(
        &mut service,
        SessionCommand::ApproveGeneration {
            consent: ConsentSelection::explicit("consent-all"),
        },
    );
    let worker = StubWorker {
        result: Some(Err(PortFailure::new("worker_crash"))),
    };
    let mut orchestrator = GenerationOrchestrator::new(service, worker);
    let outcome = orchestrator
        .generate(SESSION_ID)
        .expect("worker failure classification must append");
    assert_eq!(
        outcome.worker_failure.as_ref().map(PortFailure::operation),
        Some("worker_crash")
    );

    let (service, _worker) = orchestrator.into_parts();
    let session = service
        .load_session(SESSION_ID)
        .expect("stream must replay");
    let generation = session.generation().expect("generation must exist");
    assert_eq!(generation.state, GenerationJobState::Failed);
    assert_eq!(
        generation.result.as_ref().map(|result| &result.status),
        Some(&antidote_core::contracts::GenerationResultStatus::Failed)
    );
    assert!(
        generation
            .result
            .as_ref()
            .is_some_and(|result| result.artifacts.is_empty())
    );
}

fn service_through_response() -> TestService {
    let mut service = service_through_generation_request();
    execute(
        &mut service,
        SessionCommand::ApproveGeneration {
            consent: ConsentSelection::explicit("consent-all"),
        },
    );
    execute(&mut service, SessionCommand::StartGeneration);
    let result: GenerationResult = fixture("generation-result-valid");
    execute(
        &mut service,
        SessionCommand::RecordGenerationResult { result },
    );
    execute(
        &mut service,
        SessionCommand::ApprovePlayback {
            artifact_sha256: AUDIO_HASH.to_owned(),
        },
    );
    execute(
        &mut service,
        SessionCommand::StartExposure {
            approval_id: "playback-1".to_owned(),
        },
    );
    execute(
        &mut service,
        SessionCommand::StopExposure {
            exposure_id: "exposure-1".to_owned(),
            reason: ExposureStopReason::Completed,
        },
    );

    let mut response: ResponseObservation = fixture("response-observation-valid");
    "exposure-1".clone_into(&mut response.exposure_id);
    response.allow_personal_model_update = Some(true);
    execute(
        &mut service,
        SessionCommand::RecordResponse {
            response,
            consent: ConsentSelection::explicit("consent-all"),
        },
    );
    service
}

#[test]
fn cancellation_is_terminal_and_does_not_invoke_generation() {
    let mut service = service_through_generation_request();
    execute(&mut service, SessionCommand::CancelGeneration);
    let session = service
        .load_session(SESSION_ID)
        .expect("stream must replay");
    assert_eq!(
        session.generation().map(|generation| generation.state),
        Some(GenerationJobState::Cancelled)
    );
    let error = service
        .execute(SESSION_ID, SessionCommand::StartGeneration)
        .expect_err("a cancelled generation cannot start");
    assert_domain(error, &DomainError::GenerationTerminal);
}

#[test]
fn authorized_path_requires_each_human_gate_and_replays() {
    let mut service = service();
    execute(
        &mut service,
        SessionCommand::StartSession {
            prior_model_snapshot: None,
        },
    );
    execute(
        &mut service,
        SessionCommand::GrantConsent {
            grant: broad_grant("consent-all"),
        },
    );
    let error = service
        .execute(
            SESSION_ID,
            SessionCommand::RequestGeneration {
                specification: fixture("generation-spec-valid"),
            },
        )
        .expect_err("generation without a journey must fail closed");
    assert_domain(error, &DomainError::JourneyMissing);

    let mut service = service_through_response();
    let candidate = PersonalModelSnapshot {
        id: "snapshot-2".to_owned(),
        version: 2,
        summary: "The current observation may favor gentle continuity.".to_owned(),
        evidence_response_ids: vec!["response-synthetic-1".to_owned()],
    };
    execute(
        &mut service,
        SessionCommand::ProposeModelUpdate {
            consent: ConsentSelection::explicit("consent-all"),
            candidate,
            evidence_response_ids: vec!["response-synthetic-1".to_owned()],
        },
    );
    let pending = service
        .load_session(SESSION_ID)
        .expect("stream must replay")
        .model_update_proposal()
        .expect("proposal must exist")
        .state
        .clone();
    assert_eq!(pending, ModelUpdateState::Pending);
    execute(
        &mut service,
        SessionCommand::AcceptModelUpdate {
            proposal_id: "model-update-1".to_owned(),
            consent: ConsentSelection::explicit("consent-all"),
        },
    );
    execute(
        &mut service,
        SessionCommand::ApproveExport {
            consent: ConsentSelection::explicit("consent-all"),
        },
    );
    execute(
        &mut service,
        SessionCommand::RecordExportShared {
            approval_id: "export-1".to_owned(),
            manifest_sha256: MANIFEST_HASH.to_owned(),
        },
    );
    execute(&mut service, SessionCommand::CloseSession);

    let session = service
        .load_session(SESSION_ID)
        .expect("stream must replay");
    assert!(session.is_closed());
    assert_eq!(
        session
            .personal_model_snapshot()
            .map(|snapshot| snapshot.id.as_str()),
        Some("snapshot-2")
    );
    assert_eq!(
        session
            .export_approval()
            .and_then(|approval| { approval.shared_manifest_sha256.as_deref() }),
        Some(MANIFEST_HASH)
    );
}

#[test]
fn expired_revoked_wrong_scope_and_ambiguous_consent_fail_closed() {
    let mut service = service();
    execute(
        &mut service,
        SessionCommand::StartSession {
            prior_model_snapshot: None,
        },
    );
    let mut expired = broad_grant("expired");
    expired.expires_at = Some("2026-08-27T12:05:00Z".to_owned());
    execute(
        &mut service,
        SessionCommand::GrantConsent { grant: expired },
    );
    let error = service
        .execute(
            SESSION_ID,
            SessionCommand::ApproveExport {
                consent: ConsentSelection::explicit("expired"),
            },
        )
        .expect_err("expired consent cannot authorize export");
    assert_domain(error, &DomainError::ConsentExpired);

    let revoked_session = "session-revoked";
    service
        .execute(
            revoked_session,
            SessionCommand::StartSession {
                prior_model_snapshot: None,
            },
        )
        .expect("session starts");
    let mut revoked = broad_grant("revoked");
    revoked.session_id = revoked_session.to_owned();
    service
        .execute(
            revoked_session,
            SessionCommand::GrantConsent { grant: revoked },
        )
        .expect("grant records");
    service
        .execute(
            revoked_session,
            SessionCommand::RevokeConsent {
                consent_grant_id: "revoked".to_owned(),
            },
        )
        .expect("grant revokes");
    let error = service
        .execute(
            revoked_session,
            SessionCommand::ApproveExport {
                consent: ConsentSelection::explicit("revoked"),
            },
        )
        .expect_err("revoked consent cannot authorize export");
    assert_domain(error, &DomainError::ConsentRevoked);

    let wrong_session = "session-wrong-scope";
    service
        .execute(
            wrong_session,
            SessionCommand::StartSession {
                prior_model_snapshot: None,
            },
        )
        .expect("session starts");
    let mut wrong = broad_grant("wrong");
    wrong.session_id = wrong_session.to_owned();
    wrong.purposes = vec![ConsentGrantPurpose::JourneyPlanning];
    wrong.actions = vec![ConsentGrantAction::Project];
    service
        .execute(wrong_session, SessionCommand::GrantConsent { grant: wrong })
        .expect("grant records");
    let error = service
        .execute(
            wrong_session,
            SessionCommand::ApproveExport {
                consent: ConsentSelection::explicit("wrong"),
            },
        )
        .expect_err("wrong-purpose consent cannot authorize export");
    assert_domain(error, &DomainError::ConsentWrongPurpose);

    let ambiguous_session = "session-ambiguous";
    service
        .execute(
            ambiguous_session,
            SessionCommand::StartSession {
                prior_model_snapshot: None,
            },
        )
        .expect("session starts");
    for id in ["export-a", "export-b"] {
        let mut grant = broad_grant(id);
        grant.session_id = ambiguous_session.to_owned();
        service
            .execute(ambiguous_session, SessionCommand::GrantConsent { grant })
            .expect("grant records");
    }
    let error = service
        .execute(
            ambiguous_session,
            SessionCommand::ApproveExport {
                consent: ConsentSelection::automatic(),
            },
        )
        .expect_err("implicit selection with two grants must be ambiguous");
    assert_domain(error, &DomainError::ConsentAmbiguous);
}

#[test]
fn safety_halt_blocks_continuation_until_matching_acknowledgement() {
    let mut service = service();
    execute(
        &mut service,
        SessionCommand::StartSession {
            prior_model_snapshot: None,
        },
    );
    execute(
        &mut service,
        SessionCommand::GrantConsent {
            grant: broad_grant("consent-all"),
        },
    );
    execute(
        &mut service,
        SessionCommand::RecordSafetyEvent {
            kind: SafetyEventKind::Distress,
            description: "The person requested a pause.".to_owned(),
        },
    );
    let error = service
        .execute(
            SESSION_ID,
            SessionCommand::ApproveExport {
                consent: ConsentSelection::explicit("consent-all"),
            },
        )
        .expect_err("safety halt must block continuation");
    assert_domain(error, &DomainError::SafetyHaltActive);
    let error = service
        .execute(
            SESSION_ID,
            SessionCommand::AcknowledgeSafetyEvent {
                safety_event_id: "safety-other".to_owned(),
            },
        )
        .expect_err("wrong acknowledgement must fail");
    assert_domain(error, &DomainError::SafetyHaltMissing);
    execute(
        &mut service,
        SessionCommand::AcknowledgeSafetyEvent {
            safety_event_id: "safety-1".to_owned(),
        },
    );
    execute(
        &mut service,
        SessionCommand::ApproveExport {
            consent: ConsentSelection::explicit("consent-all"),
        },
    );
}

#[test]
fn failed_model_update_preserves_the_prior_snapshot() {
    let mut service = service_through_response();
    let prior = service
        .load_session(SESSION_ID)
        .expect("stream must replay")
        .personal_model_snapshot()
        .expect("prior snapshot must exist")
        .clone();
    execute(
        &mut service,
        SessionCommand::ProposeModelUpdate {
            consent: ConsentSelection::explicit("consent-all"),
            candidate: PersonalModelSnapshot {
                id: "snapshot-2".to_owned(),
                version: 2,
                summary: "A proposed but unapplied preference.".to_owned(),
                evidence_response_ids: vec!["response-synthetic-1".to_owned()],
            },
            evidence_response_ids: vec!["response-synthetic-1".to_owned()],
        },
    );
    execute(
        &mut service,
        SessionCommand::FailModelUpdate {
            proposal_id: "model-update-1".to_owned(),
        },
    );
    let session = service
        .load_session(SESSION_ID)
        .expect("stream must replay");
    assert_eq!(session.personal_model_snapshot(), Some(&prior));
    assert_eq!(
        session
            .model_update_proposal()
            .map(|proposal| &proposal.state),
        Some(&ModelUpdateState::Failed)
    );
}

#[test]
fn replay_rejects_non_contiguous_sequences() {
    let event = RecordedEvent {
        schema_version: antidote_core::SESSION_EVENT_SCHEMA_VERSION.to_owned(),
        id: "event-1".to_owned(),
        session_id: SESSION_ID.to_owned(),
        sequence: 2,
        occurred_at: NOW.to_owned(),
        event: antidote_core::SessionEvent::SessionStarted {
            prior_model_snapshot: None,
        },
    };
    let error = antidote_core::Session::rehydrate(SESSION_ID, &[event])
        .expect_err("a stream gap must fail replay");
    assert_eq!(error, DomainError::InvalidEventSequence);
}

#[test]
fn replay_cannot_bypass_the_journey_approval_gate() {
    let events = vec![
        RecordedEvent {
            schema_version: antidote_core::SESSION_EVENT_SCHEMA_VERSION.to_owned(),
            id: "event-1".to_owned(),
            session_id: SESSION_ID.to_owned(),
            sequence: 1,
            occurred_at: NOW.to_owned(),
            event: antidote_core::SessionEvent::SessionStarted {
                prior_model_snapshot: None,
            },
        },
        RecordedEvent {
            schema_version: antidote_core::SESSION_EVENT_SCHEMA_VERSION.to_owned(),
            id: "event-2".to_owned(),
            session_id: SESSION_ID.to_owned(),
            sequence: 2,
            occurred_at: NOW.to_owned(),
            event: antidote_core::SessionEvent::GenerationRequested {
                specification: fixture("generation-spec-valid"),
            },
        },
    ];
    let error = antidote_core::Session::rehydrate(SESSION_ID, &events)
        .expect_err("replay cannot inject generation without an approved journey");
    assert_eq!(error, DomainError::JourneyMissing);
}
