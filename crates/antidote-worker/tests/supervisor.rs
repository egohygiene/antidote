#![allow(clippy::too_many_lines)]

use std::collections::BTreeMap;
use std::ffi::OsString;
use std::path::{Path, PathBuf};
use std::time::Duration;

use antidote_contracts::{
    ConsentGrant, ConsentGrantAction, ConsentGrantPurpose, GenerationResultStatus, GenerationSpec,
    MomentContext, WorkingContextProjection,
};
use antidote_core::{
    Clock, ConsentSelection, EventRepository, GenerationJobState, GenerationOrchestrator,
    IdentifierKind, IdentifierSource, PortFailure, RecordedEvent, RuleGuidedPlanner,
    SessionCommand, SessionService,
};
use antidote_worker::{
    DEFAULT_MAX_ARTIFACT_BYTES, MockSimulation, MockSimulationMode, ProgressDecision,
    WorkerErrorKind, WorkerModelIdentity, WorkerSupervisor, WorkerSupervisorConfig,
};
use serde::Deserialize;
use serde_json::Value;
use tempfile::TempDir;

const MODEL_HASH: &str = "9d994d01452850f4f539b420486247d262b8a4a5afffefa85f333e334daa1c2e";

#[derive(Debug, Deserialize)]
struct FixtureSuite {
    cases: Vec<FixtureCase>,
}

#[derive(Debug, Deserialize)]
struct FixtureCase {
    name: String,
    data: Value,
}

fn repository_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("worker crate must be nested under repository crates")
        .to_path_buf()
}

fn find_executable(name: &str) -> PathBuf {
    std::env::var_os("PATH")
        .and_then(|paths| {
            std::env::split_paths(&paths)
                .map(|directory| directory.join(name))
                .find(|candidate| candidate.is_file())
        })
        .and_then(|path| path.canonicalize().ok())
        .unwrap_or_else(|| panic!("{name} must be available after MVP bootstrap"))
}

fn identity() -> WorkerModelIdentity {
    WorkerModelIdentity {
        adapter_id: "antidote.mock".to_owned(),
        adapter_version: "1.0.0".to_owned(),
        model_id: "synthetic-triangle".to_owned(),
        model_revision: "1".to_owned(),
        model_artifact_hash: Some(MODEL_HASH.to_owned()),
    }
}

fn generation_spec() -> GenerationSpec {
    let suite: FixtureSuite =
        serde_json::from_str(include_str!("../../../contracts/fixtures/cases.json"))
            .expect("contract fixtures must parse");
    let value = suite
        .cases
        .into_iter()
        .find(|case| case.name == "generation-spec-valid")
        .expect("generation fixture must exist")
        .data;
    let mut specification: GenerationSpec =
        serde_json::from_value(value).expect("generation fixture must be typed");
    "antidote.mock".clone_into(&mut specification.adapter.id);
    "1.0.0".clone_into(&mut specification.adapter.version);
    "synthetic-triangle".clone_into(&mut specification.model.id);
    "1".clone_into(&mut specification.model.revision);
    specification.model.artifact_hash = Some(MODEL_HASH.to_owned());
    specification.duration_seconds = 10;
    specification.output.sample_rate_hz = 8_000;
    specification.output.channels = 1;
    specification.required_capabilities = Some(vec!["deterministic_seed".to_owned()]);
    specification
}

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
            return Err(PortFailure::new("memory_append"));
        }
        stream.extend_from_slice(events);
        Ok(())
    }
}

#[derive(Debug, Clone, Copy)]
struct FixedClock;

impl Clock for FixedClock {
    fn now_rfc3339(&self) -> Result<String, PortFailure> {
        Ok("2026-08-29T12:00:00Z".to_owned())
    }
}

#[derive(Debug, Default)]
struct Identifiers(u64);

impl IdentifierSource for Identifiers {
    fn next_id(&mut self, _kind: IdentifierKind) -> Result<String, PortFailure> {
        self.0 += 1;
        Ok(format!("integration-event-{}", self.0))
    }
}

fn fixture<T: for<'de> Deserialize<'de>>(name: &str) -> T {
    let suite: FixtureSuite =
        serde_json::from_str(include_str!("../../../contracts/fixtures/cases.json"))
            .expect("contract fixtures must parse");
    let value = suite
        .cases
        .into_iter()
        .find(|case| case.name == name)
        .unwrap_or_else(|| panic!("fixture {name} must exist"))
        .data;
    serde_json::from_value(value).expect("valid fixture must match its generated type")
}

fn approved_generation_service() -> SessionService<MemoryRepository, FixedClock, Identifiers> {
    let mut service = SessionService::new(MemoryRepository::default(), FixedClock, Identifiers(0));
    let session_id = "session-synthetic-1";
    service
        .execute(
            session_id,
            SessionCommand::StartSession {
                prior_model_snapshot: None,
            },
        )
        .expect("session must start");
    let mut grant: ConsentGrant = fixture("consent-grant-valid");
    "consent-worker-integration".clone_into(&mut grant.id);
    grant.purposes = vec![
        ConsentGrantPurpose::JourneyPlanning,
        ConsentGrantPurpose::Generation,
    ];
    grant.actions = vec![
        ConsentGrantAction::Inspect,
        ConsentGrantAction::Project,
        ConsentGrantAction::Generate,
    ];
    grant.retention.allow_derived_projection = Some(true);
    service
        .execute(session_id, SessionCommand::GrantConsent { grant })
        .expect("consent must append");
    let mut projection: WorkingContextProjection = fixture("working-context-projection-valid");
    projection.consent_grant_ids = vec!["consent-worker-integration".to_owned()];
    service
        .execute(
            session_id,
            SessionCommand::AcceptWorkingProjection { projection },
        )
        .expect("projection must append");
    let moment = fixture::<MomentContext>("moment-context-valid");
    service
        .execute(
            session_id,
            SessionCommand::RecordMoment {
                moment: moment.clone(),
            },
        )
        .expect("moment must append");
    let plan = RuleGuidedPlanner::default()
        .propose("journey-synthetic-1", &moment)
        .expect("synthetic moment must produce an inspectable plan");
    let plan_hash = plan
        .plan_hash
        .clone()
        .expect("planner must seal the proposal");
    service
        .execute(session_id, SessionCommand::ProposeJourney { plan })
        .expect("journey must append");
    service
        .execute(
            session_id,
            SessionCommand::ApproveJourney {
                plan_id: "journey-synthetic-1".to_owned(),
                consent: ConsentSelection::explicit("consent-worker-integration"),
            },
        )
        .expect("journey approval must append");
    let mut specification = generation_spec();
    specification.journey_plan_hash = plan_hash;
    service
        .execute(
            session_id,
            SessionCommand::RequestGeneration { specification },
        )
        .expect("generation request must append");
    service
        .execute(
            session_id,
            SessionCommand::ApproveGeneration {
                consent: ConsentSelection::explicit("consent-worker-integration"),
            },
        )
        .expect("generation approval must append");
    service
}

fn real_worker_config(temporary: &TempDir, timeout: Duration) -> WorkerSupervisorConfig {
    let root = repository_root();
    let output = temporary.path().join("approved-output");
    std::fs::create_dir(&output).expect("approved output root must be created");
    WorkerSupervisorConfig {
        executable: find_executable("uv"),
        arguments: vec![
            OsString::from("run"),
            OsString::from("--project"),
            root.join("workers/generation").into_os_string(),
            OsString::from("--locked"),
            OsString::from("--no-sync"),
            OsString::from("antidote-generation-worker"),
        ],
        environment: BTreeMap::from([
            (OsString::from("UV_OFFLINE"), OsString::from("true")),
            (OsString::from("UV_NO_PROGRESS"), OsString::from("true")),
        ]),
        working_directory: root,
        approved_output_root: output,
        request_timeout: timeout,
        shutdown_timeout: Duration::from_secs(2),
        max_artifact_bytes: DEFAULT_MAX_ARTIFACT_BYTES,
        allow_mock_simulation: true,
    }
}

fn fault_worker_config(temporary: &TempDir, mode: &str) -> WorkerSupervisorConfig {
    let root = repository_root();
    let output = temporary.path().join("approved-output");
    std::fs::create_dir(&output).expect("approved output root must be created");
    let python = root.join("workers/generation/.venv/bin/python");
    WorkerSupervisorConfig {
        executable: python
            .canonicalize()
            .expect("MVP bootstrap must create the worker virtual environment"),
        arguments: vec![
            root.join("crates/antidote-worker/tests/fixtures/fault_worker.py")
                .into_os_string(),
        ],
        environment: BTreeMap::from([(
            OsString::from("ANTIDOTE_FAULT_MODE"),
            OsString::from(mode),
        )]),
        working_directory: root,
        approved_output_root: output,
        request_timeout: Duration::from_secs(5),
        shutdown_timeout: Duration::from_secs(1),
        max_artifact_bytes: DEFAULT_MAX_ARTIFACT_BYTES,
        allow_mock_simulation: false,
    }
}

#[test]
fn success_delivers_progress_and_accepts_only_verified_artifacts() {
    let temporary = TempDir::new().expect("temporary root must exist");
    let mut supervisor = WorkerSupervisor::connect(
        real_worker_config(&temporary, Duration::from_secs(10)),
        identity(),
    )
    .expect("real mock worker must negotiate");
    assert!(supervisor.health().expect("loaded worker must be healthy"));
    let mut progress = Vec::new();
    let result = supervisor
        .generate_with_progress(&generation_spec(), None, |update| {
            progress.push(update);
            ProgressDecision::Continue
        })
        .expect("mock generation must succeed");
    assert_eq!(result.status, GenerationResultStatus::Generated);
    assert!(!progress.is_empty());
    assert_eq!(result.artifacts.len(), 1);
    let artifact = Path::new(&result.artifacts[0].path)
        .canonicalize()
        .expect("artifact must exist");
    assert!(artifact.starts_with(temporary.path().join("approved-output")));
    assert!(supervisor.health().expect("worker remains healthy"));
}

#[test]
fn real_supervisor_composes_with_the_rust_event_orchestrator() {
    let temporary = TempDir::new().expect("temporary root must exist");
    let supervisor = WorkerSupervisor::connect(
        real_worker_config(&temporary, Duration::from_secs(10)),
        identity(),
    )
    .expect("real mock worker must negotiate");
    let mut orchestrator = GenerationOrchestrator::new(approved_generation_service(), supervisor);
    let outcome = orchestrator
        .generate("session-synthetic-1")
        .expect("approved generation must flow through the Rust authority boundary");
    assert_eq!(outcome.started.len(), 1);
    assert_eq!(outcome.terminal.len(), 1);
    assert!(outcome.worker_failure.is_none());
    let (service, _supervisor) = orchestrator.into_parts();
    let session = service
        .load_session("session-synthetic-1")
        .expect("orchestrated stream must replay");
    assert_eq!(
        session.generation().map(|generation| generation.state),
        Some(GenerationJobState::Generated)
    );
}

#[test]
fn cancellation_is_correlated_and_leaves_no_partial_artifact() {
    let temporary = TempDir::new().expect("temporary root must exist");
    let mut supervisor = WorkerSupervisor::connect(
        real_worker_config(&temporary, Duration::from_secs(10)),
        identity(),
    )
    .expect("real mock worker must negotiate");
    let result = supervisor
        .generate_with_progress(
            &generation_spec(),
            Some(MockSimulation {
                mode: MockSimulationMode::Normal,
                step_delay_ms: 50,
            }),
            |_| ProgressDecision::Cancel,
        )
        .expect("cooperative cancellation returns a canonical result");
    assert_eq!(result.status, GenerationResultStatus::Cancelled);
    assert!(result.artifacts.is_empty());
    assert!(
        supervisor
            .health()
            .expect("cancel response is fully drained")
    );
    let leftovers = std::fs::read_dir(temporary.path().join("approved-output"))
        .expect("output root must remain readable")
        .filter_map(std::result::Result::ok)
        .flat_map(|entry| std::fs::read_dir(entry.path()).into_iter().flatten())
        .filter_map(std::result::Result::ok)
        .collect::<Vec<_>>();
    assert!(leftovers.is_empty());
}

#[test]
fn classified_timeout_partial_and_crash_results_remain_non_success() {
    for (mode, expected) in [
        (MockSimulationMode::Timeout, GenerationResultStatus::Failed),
        (MockSimulationMode::Partial, GenerationResultStatus::Partial),
        (MockSimulationMode::Crash, GenerationResultStatus::Failed),
    ] {
        let temporary = TempDir::new().expect("temporary root must exist");
        let mut supervisor = WorkerSupervisor::connect(
            real_worker_config(&temporary, Duration::from_secs(10)),
            identity(),
        )
        .expect("real mock worker must negotiate");
        let result = supervisor
            .generate_with_progress(
                &generation_spec(),
                Some(MockSimulation {
                    mode,
                    step_delay_ms: 0,
                }),
                |_| ProgressDecision::Continue,
            )
            .expect("classified mock outcome must be a trusted result");
        assert_eq!(result.status, expected);
        assert_ne!(result.status, GenerationResultStatus::Generated);
    }
}

#[test]
fn host_timeout_kills_cleans_and_restarts_the_worker() {
    let temporary = TempDir::new().expect("temporary root must exist");
    let mut supervisor = WorkerSupervisor::connect(
        real_worker_config(&temporary, Duration::from_secs(2)),
        identity(),
    )
    .expect("real mock worker must negotiate");
    let error = supervisor
        .generate_with_progress(
            &generation_spec(),
            Some(MockSimulation {
                mode: MockSimulationMode::Normal,
                step_delay_ms: 250,
            }),
            |_| ProgressDecision::Continue,
        )
        .expect_err("host deadline must terminate delayed generation");
    assert_eq!(error.kind(), WorkerErrorKind::Timeout);
    assert!(
        std::fs::read_dir(temporary.path().join("approved-output"))
            .expect("output root remains")
            .next()
            .is_none()
    );
    supervisor.restart().expect("worker must restart cleanly");
    assert!(
        supervisor
            .health()
            .expect("restarted worker must be healthy")
    );
}

#[test]
fn unsupported_capability_fails_before_generation_mutation() {
    let temporary = TempDir::new().expect("temporary root must exist");
    let mut supervisor = WorkerSupervisor::connect(
        real_worker_config(&temporary, Duration::from_secs(10)),
        identity(),
    )
    .expect("real mock worker must negotiate");
    let mut unsupported = generation_spec();
    unsupported.required_capabilities = Some(vec!["unavailable-control".to_owned()]);
    let error = supervisor
        .generate_with_progress(&unsupported, None, |_| ProgressDecision::Continue)
        .expect_err("missing capability must fail before generation");
    assert_eq!(error.kind(), WorkerErrorKind::UnsupportedCapability);
    assert!(
        std::fs::read_dir(temporary.path().join("approved-output"))
            .expect("output root remains")
            .next()
            .is_none()
    );
}

#[test]
fn process_crash_and_malformed_output_are_redacted_and_fail_closed() {
    for (mode, expected) in [
        ("crash", WorkerErrorKind::Crash),
        ("malformed", WorkerErrorKind::Protocol),
    ] {
        let temporary = TempDir::new().expect("temporary root must exist");
        let mut supervisor =
            WorkerSupervisor::connect(fault_worker_config(&temporary, mode), identity())
                .expect("fault fixture must negotiate");
        let error = supervisor
            .generate_with_progress(&generation_spec(), None, |_| ProgressDecision::Continue)
            .expect_err("fault must not produce a trusted result");
        assert_eq!(error.kind(), expected);
        assert!(!error.to_string().contains("SYNTHETIC-DIAGNOSTIC"));
        let stderr = supervisor.stderr_summary();
        assert!(stderr.bytes_observed > 0);
    }
}

#[test]
fn artifact_outside_the_per_run_grant_is_rejected() {
    let temporary = TempDir::new().expect("temporary root must exist");
    let mut supervisor =
        WorkerSupervisor::connect(fault_worker_config(&temporary, "escape"), identity())
            .expect("fault fixture must negotiate");
    let error = supervisor
        .generate_with_progress(&generation_spec(), None, |_| ProgressDecision::Continue)
        .expect_err("artifact outside the exact run grant must fail closed");
    assert_eq!(error.kind(), WorkerErrorKind::ArtifactIntegrity);
}
