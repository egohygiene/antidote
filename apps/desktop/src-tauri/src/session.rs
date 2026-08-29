//! Recoverable Tauri application boundary for one local mock session.

use std::collections::BTreeMap;
use std::ffi::OsString;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use antidote_core::contracts::{
    ConsentGrant, ConsentGrantAction, ConsentGrantPurpose, ConsentGrantRetention,
    ConsentGrantRetentionMode, ConsentGrantSource, ConsentGrantSourceSourceType,
    ConsentGrantStatus, GenerationResult, GenerationResultAdapter, GenerationResultFailure,
    GenerationResultModel, GenerationResultStatus, GenerationSpec, GenerationSpecAdapter,
    GenerationSpecModel, GenerationSpecOutput, GenerationSpecOutputFormat,
    MomentContext, MomentContextDesiredTransition, MomentContextDesiredTransitionDirection,
    MomentContextState, ResponseObservation, ResponseObservationFeltState,
    ResponseObservationWindow, WorkingContextProjection, WorkingContextProjectionSemanticItem,
    WorkingContextProjectionSemanticItemKind, WorkingContextProjectionSemanticItemUserReview,
};
use antidote_core::{
    ApplicationError, Clock, ConsentSelection, ExposureState, ExposureStopReason,
    GenerationJobState, IdentifierKind, IdentifierSource, JourneyApprovalState, JourneyEdit,
    PlanningError, PortFailure, RuleGuidedPlanner, Session, SessionCommand, SessionService,
};
use antidote_store::{SqliteEventStore, StoreError};
use antidote_worker::{
    DEFAULT_MAX_ARTIFACT_BYTES, MockSimulation, MockSimulationMode, ProgressDecision,
    WorkerModelIdentity, WorkerProgress, WorkerSupervisor, WorkerSupervisorConfig,
};
use serde::{Deserialize, Serialize};
use serde_json::json;
use time::{OffsetDateTime, format_description::well_known::Rfc3339};

const DATABASE_FILENAME: &str = "antidote-session.sqlite3";
const ACTIVE_SESSION_FILENAME: &str = "active-session";
const MOCK_MODEL_HASH: &str =
    "9d994d01452850f4f539b420486247d262b8a4a5afffefa85f333e334daa1c2e";
const MOCK_MAX_DURATION_SECONDS: i64 = 30;
static IDENTIFIER_SEQUENCE: AtomicU64 = AtomicU64::new(0);

/// Stable, source-text-free error returned through the Tauri boundary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct DesktopCommandError {
    /// Machine-readable failure class.
    pub code: &'static str,
    /// Plain-language recovery guidance.
    pub message: &'static str,
    /// Whether retrying or changing the current input may succeed.
    pub recoverable: bool,
}

#[derive(Debug)]
enum DesktopError {
    ConsentRequired,
    InvalidInput,
    NoActiveSession,
    SessionInProgress,
    GenerationStillActive,
    Application,
    Planning,
    Storage,
    WorkerUnavailable,
}

impl From<ApplicationError> for DesktopError {
    fn from(_error: ApplicationError) -> Self {
        Self::Application
    }
}

impl From<PlanningError> for DesktopError {
    fn from(_error: PlanningError) -> Self {
        Self::Planning
    }
}

impl From<StoreError> for DesktopError {
    fn from(_error: StoreError) -> Self {
        Self::Storage
    }
}

impl From<DesktopError> for DesktopCommandError {
    fn from(error: DesktopError) -> Self {
        match error {
            DesktopError::ConsentRequired => Self {
                code: "consent_required",
                message: "Review and confirm the visible session permissions before continuing.",
                recoverable: true,
            },
            DesktopError::InvalidInput => Self {
                code: "invalid_input",
                message: "Review the highlighted session values and try again.",
                recoverable: true,
            },
            DesktopError::NoActiveSession => Self {
                code: "session_missing",
                message: "Start a local session before using this action.",
                recoverable: true,
            },
            DesktopError::SessionInProgress => Self {
                code: "session_in_progress",
                message: "Finish the current session before starting another one.",
                recoverable: true,
            },
            DesktopError::GenerationStillActive => Self {
                code: "generation_active",
                message: "Wait for generation to stop before recovering it.",
                recoverable: true,
            },
            DesktopError::Application => Self {
                code: "session_transition_rejected",
                message: "The Rust session authority rejected this transition. Refresh the canonical state and review the required approval.",
                recoverable: true,
            },
            DesktopError::Planning => Self {
                code: "journey_rejected",
                message: "The journey violates a visible duration, exclusion, or control boundary.",
                recoverable: true,
            },
            DesktopError::Storage => Self {
                code: "local_state_unavailable",
                message: "Antidote could not verify its local session record.",
                recoverable: false,
            },
            DesktopError::WorkerUnavailable => Self {
                code: "worker_unavailable",
                message: "The local synthetic worker could not be started. No real model or network fallback was used.",
                recoverable: true,
            },
        }
    }
}

type DesktopResult<T> = Result<T, DesktopCommandError>;
type InternalResult<T> = Result<T, DesktopError>;

/// Coarse screen selected from canonical Rust state.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum DesktopPhase {
    CheckIn,
    ContextReview,
    JourneyReview,
    GenerationReview,
    Generating,
    GenerationFailed,
    ReadyToListen,
    Listening,
    Response,
    Complete,
}

/// Public capability declaration for the deterministic worker.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct WorkerCard {
    pub adapter_id: &'static str,
    pub adapter_version: &'static str,
    pub model_id: &'static str,
    pub model_revision: &'static str,
    pub license: &'static str,
    pub device_class: &'static str,
    pub network_access: bool,
    pub duration_seconds_min: i64,
    pub duration_seconds_max: i64,
    pub controls: Vec<&'static str>,
    pub restrictions: Vec<&'static str>,
    pub visible_downgrades: Vec<&'static str>,
}

/// Latest bounded progress observation kept outside canonical session truth.
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct GenerationProgressView {
    pub stage: String,
    pub fraction: f64,
    pub elapsed_ms: u64,
}

impl Default for GenerationProgressView {
    fn default() -> Self {
        Self {
            stage: "waiting".to_owned(),
            fraction: 0.0,
            elapsed_ms: 0,
        }
    }
}

/// Complete recoverable projection returned to React.
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct DesktopSnapshot {
    pub session_id: Option<String>,
    pub phase: DesktopPhase,
    pub canonical_session: Option<Session>,
    pub worker: WorkerCard,
    pub progress: GenerationProgressView,
    pub generation_active: bool,
    pub cancellation_requested: bool,
    pub recovery_required: bool,
}

/// Person-entered check-in. The browser never grants authority by itself.
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct CheckInInput {
    pub current_state: String,
    pub desired_direction: String,
    pub desired_transition: String,
    pub horizon_seconds: i64,
    #[serde(default)]
    pub inclusions: Vec<String>,
    #[serde(default)]
    pub exclusions: Vec<String>,
    pub optional_context: Option<String>,
    pub notes: Option<String>,
    pub consent_confirmed: bool,
}

/// Editable portion of one journey stage.
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct JourneyStageEditInput {
    pub semantic_intent: Vec<String>,
    pub tempo_bpm: Option<f64>,
    pub density: Option<f64>,
}

/// Person-authored replacement values for an immutable journey revision.
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct JourneyRevisionInput {
    pub strategy: String,
    pub stages: Vec<JourneyStageEditInput>,
}

/// Explicitly testable mock terminal behavior.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum GenerationSimulation {
    Normal,
    Crash,
}

/// Felt response remains separate from the journey and acoustic output.
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct ResponseInput {
    pub felt_state: String,
    pub wanted_intensity: Option<bool>,
    pub helpfulness: Option<f64>,
    pub resonance: Option<f64>,
    pub mismatch: Option<f64>,
    pub harm: Option<f64>,
    pub stopped_early: bool,
    pub notes: Option<String>,
    pub later_aftereffect_requested: bool,
}

#[derive(Debug)]
struct DesktopRuntimeInner {
    data_root: PathBuf,
    progress: Mutex<GenerationProgressView>,
    generation_active: AtomicBool,
    cancellation_requested: AtomicBool,
}

/// Cloneable Tauri state whose durable authority remains the SQLite event log.
#[derive(Debug, Clone)]
pub struct DesktopRuntime {
    inner: Arc<DesktopRuntimeInner>,
}

impl DesktopRuntime {
    /// Open the local runtime at one application-owned data root.
    ///
    /// # Errors
    ///
    /// Returns a redacted storage error if the directory or database cannot be opened.
    pub fn open(data_root: PathBuf) -> DesktopResult<Self> {
        std::fs::create_dir_all(data_root.join("artifacts"))
            .map_err(|_| DesktopCommandError::from(DesktopError::Storage))?;
        SqliteEventStore::open(data_root.join(DATABASE_FILENAME))
            .map_err(|_| DesktopCommandError::from(DesktopError::Storage))?;
        Ok(Self {
            inner: Arc::new(DesktopRuntimeInner {
                data_root,
                progress: Mutex::new(GenerationProgressView::default()),
                generation_active: AtomicBool::new(false),
                cancellation_requested: AtomicBool::new(false),
            }),
        })
    }

    fn database_path(&self) -> PathBuf {
        self.inner.data_root.join(DATABASE_FILENAME)
    }

    fn active_session_path(&self) -> PathBuf {
        self.inner.data_root.join(ACTIVE_SESSION_FILENAME)
    }

    fn service(
        &self,
    ) -> InternalResult<SessionService<SqliteEventStore, SystemClock, SystemIdentifiers>> {
        let store = SqliteEventStore::open(self.database_path())?;
        Ok(SessionService::new(store, SystemClock, SystemIdentifiers))
    }

    fn active_session_id(&self) -> InternalResult<Option<String>> {
        match std::fs::read_to_string(self.active_session_path()) {
            Ok(identifier) if !identifier.trim().is_empty() => Ok(Some(identifier.trim().to_owned())),
            Ok(_) => Ok(None),
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(None),
            Err(_) => Err(DesktopError::Storage),
        }
    }

    fn set_active_session_id(&self, session_id: &str) -> InternalResult<()> {
        let temporary = self.inner.data_root.join("active-session.next");
        std::fs::write(&temporary, session_id).map_err(|_| DesktopError::Storage)?;
        std::fs::rename(temporary, self.active_session_path())
            .map_err(|_| DesktopError::Storage)
    }

    fn load_session(&self) -> InternalResult<Session> {
        let session_id = self
            .active_session_id()?
            .ok_or(DesktopError::NoActiveSession)?;
        Ok(self.service()?.load_session(&session_id)?)
    }

    fn snapshot_internal(&self) -> InternalResult<DesktopSnapshot> {
        let session_id = self.active_session_id()?;
        let session = session_id
            .as_deref()
            .map(|identifier| self.service()?.load_session(identifier))
            .transpose()?;
        let generation_active = self.inner.generation_active.load(Ordering::Acquire);
        let cancellation_requested = self
            .inner
            .cancellation_requested
            .load(Ordering::Acquire);
        let recovery_required = session.as_ref().is_some_and(|current| {
            current
                .generation()
                .is_some_and(|job| job.state == GenerationJobState::Running)
                && !generation_active
        });
        let progress = self
            .inner
            .progress
            .lock()
            .map_err(|_| DesktopError::Storage)?
            .clone();
        Ok(DesktopSnapshot {
            phase: session.as_ref().map_or(DesktopPhase::CheckIn, phase_for),
            session_id,
            canonical_session: session,
            worker: worker_card(),
            progress,
            generation_active,
            cancellation_requested,
            recovery_required,
        })
    }

    /// Load the current canonical projection without mutating the event stream.
    pub fn snapshot(&self) -> DesktopResult<DesktopSnapshot> {
        self.snapshot_internal().map_err(DesktopCommandError::from)
    }

    /// Start and record one consented check-in and its exact optional projection.
    pub fn record_check_in(&self, input: CheckInInput) -> DesktopResult<DesktopSnapshot> {
        self.record_check_in_internal(input)
            .and_then(|()| self.snapshot_internal())
            .map_err(DesktopCommandError::from)
    }

    fn record_check_in_internal(&self, input: CheckInInput) -> InternalResult<()> {
        validate_check_in(&input)?;
        if !input.consent_confirmed {
            return Err(DesktopError::ConsentRequired);
        }
        if self
            .active_session_id()?
            .map(|_| self.load_session())
            .transpose()?
            .is_some_and(|session| !session.is_closed())
        {
            return Err(DesktopError::SessionInProgress);
        }

        let session_id = next_local_identifier("session");
        let consent_id = consent_id(&session_id);
        let now = current_timestamp()?;
        let context = optional_trimmed(input.optional_context);
        let mut service = self.service()?;
        service.execute(
            &session_id,
            SessionCommand::StartSession {
                prior_model_snapshot: None,
            },
        )?;
        let sources = context.as_ref().map_or_else(Vec::new, |_| {
            vec![ConsentGrantSource {
                source_id: format!("manual-context-{session_id}"),
                source_type: ConsentGrantSourceSourceType::ManualEntry,
                content_hash: None,
            }]
        });
        service.execute(
            &session_id,
            SessionCommand::GrantConsent {
                grant: ConsentGrant {
                    schema_version: "1.0.0".to_owned(),
                    id: consent_id.clone(),
                    session_id: session_id.clone(),
                    status: ConsentGrantStatus::Active,
                    created_at: now.clone(),
                    expires_at: None,
                    purposes: vec![
                        ConsentGrantPurpose::JourneyPlanning,
                        ConsentGrantPurpose::Generation,
                        ConsentGrantPurpose::ResponseCapture,
                    ],
                    actions: vec![
                        ConsentGrantAction::Project,
                        ConsentGrantAction::Generate,
                        ConsentGrantAction::Retain,
                    ],
                    sources,
                    retention: ConsentGrantRetention {
                        mode: ConsentGrantRetentionMode::SessionOnly,
                        allow_derived_projection: Some(true),
                        allow_personal_model_update: Some(false),
                    },
                },
            },
        )?;

        let projection_id = if let Some(context) = context {
            let identifier = format!("projection-{session_id}");
            service.execute(
                &session_id,
                SessionCommand::AcceptWorkingProjection {
                    projection: WorkingContextProjection {
                        schema_version: "1.0.0".to_owned(),
                        id: identifier.clone(),
                        session_id: session_id.clone(),
                        consent_grant_ids: vec![consent_id],
                        created_at: now.clone(),
                        expires_at: None,
                        derivation_version: "manual-review-v1".to_owned(),
                        source_event_ids: Vec::new(),
                        semantic_items: vec![WorkingContextProjectionSemanticItem {
                            id: format!("context-item-{session_id}"),
                            kind: WorkingContextProjectionSemanticItemKind::Meaning,
                            text: context,
                            source_event_ids: Vec::new(),
                            user_review:
                                WorkingContextProjectionSemanticItemUserReview::Approved,
                        }],
                        projection_hash: None,
                    },
                },
            )?;
            Some(identifier)
        } else {
            None
        };

        service.execute(
            &session_id,
            SessionCommand::RecordMoment {
                moment: MomentContext {
                    schema_version: "1.0.0".to_owned(),
                    id: format!("moment-{session_id}"),
                    session_id: session_id.clone(),
                    observed_at: now,
                    working_projection_id: projection_id,
                    current_state: MomentContextState {
                        description: input.current_state.trim().to_owned(),
                        valence: None,
                        arousal: None,
                        intensity: None,
                        confidence: None,
                    },
                    desired_transition: MomentContextDesiredTransition {
                        direction: parse_direction(&input.desired_direction)?,
                        description: input.desired_transition.trim().to_owned(),
                        target_state: None,
                    },
                    time_horizon_seconds: input.horizon_seconds,
                    inclusions: clean_list(input.inclusions),
                    exclusions: clean_list(input.exclusions),
                    notes: optional_trimmed(input.notes),
                },
            },
        )?;
        self.set_active_session_id(&session_id)
    }

    /// Produce the first inspectable Level-1 plan from the recorded moment.
    pub fn propose_journey(&self) -> DesktopResult<DesktopSnapshot> {
        self.propose_journey_internal()
            .and_then(|()| self.snapshot_internal())
            .map_err(DesktopCommandError::from)
    }

    fn propose_journey_internal(&self) -> InternalResult<()> {
        let session = self.load_session()?;
        let moment = session.moment().ok_or(DesktopError::InvalidInput)?;
        let plan = RuleGuidedPlanner::default()
            .propose(&next_local_identifier("journey"), moment)?;
        self.service()?.execute(
            session.id(),
            SessionCommand::ProposeJourney { plan },
        )?;
        Ok(())
    }

    /// Create an immutable replacement plan from person-edited storyboard values.
    pub fn revise_journey(
        &self,
        input: JourneyRevisionInput,
    ) -> DesktopResult<DesktopSnapshot> {
        self.revise_journey_internal(input)
            .and_then(|()| self.snapshot_internal())
            .map_err(DesktopCommandError::from)
    }

    fn revise_journey_internal(&self, input: JourneyRevisionInput) -> InternalResult<()> {
        if input.strategy.trim().is_empty() {
            return Err(DesktopError::InvalidInput);
        }
        let session = self.load_session()?;
        let moment = session.moment().ok_or(DesktopError::InvalidInput)?;
        let current = session.journey().ok_or(DesktopError::InvalidInput)?;
        if input.stages.len() != current.plan.stages.len() {
            return Err(DesktopError::InvalidInput);
        }
        let mut edits = vec![JourneyEdit::Strategy(input.strategy.trim().to_owned())];
        for (stage_index, (stage, replacement)) in current
            .plan
            .stages
            .iter()
            .zip(input.stages)
            .enumerate()
        {
            let semantic_intent = clean_list(replacement.semantic_intent);
            if semantic_intent.is_empty() {
                return Err(DesktopError::InvalidInput);
            }
            let mut controls = stage.acoustic_controls.clone();
            controls.tempo_bpm = replacement.tempo_bpm;
            controls.density = replacement.density;
            edits.push(JourneyEdit::StageSemanticIntent {
                stage_index,
                semantic_intent,
            });
            edits.push(JourneyEdit::StageAcousticControls {
                stage_index,
                acoustic_controls: controls,
            });
        }
        let replacement = RuleGuidedPlanner::default().revise(
            &current.plan,
            &next_local_identifier("journey"),
            moment,
            &edits,
        )?;
        let current_id = current.plan.id.clone();
        self.service()?.execute(
            session.id(),
            SessionCommand::ReviseJourney {
                plan: replacement,
                supersedes_plan_id: current_id,
            },
        )?;
        Ok(())
    }

    /// Approve the exact current plan and record, but do not invoke, its generation spec.
    pub fn approve_journey(&self) -> DesktopResult<DesktopSnapshot> {
        self.approve_journey_internal()
            .and_then(|()| self.snapshot_internal())
            .map_err(DesktopCommandError::from)
    }

    fn approve_journey_internal(&self) -> InternalResult<()> {
        let session = self.load_session()?;
        let journey = session.journey().ok_or(DesktopError::InvalidInput)?;
        let plan = journey.plan.clone();
        let plan_hash = plan.plan_hash.clone().ok_or(DesktopError::InvalidInput)?;
        let moment = session.moment().ok_or(DesktopError::InvalidInput)?;
        let now = current_timestamp()?;
        let mut service = self.service()?;
        service.execute(
            session.id(),
            SessionCommand::ApproveJourney {
                plan_id: plan.id.clone(),
                consent: ConsentSelection::explicit(consent_id(session.id())),
            },
        )?;
        let prompt = plan
            .stages
            .iter()
            .flat_map(|stage| stage.semantic_intent.iter())
            .cloned()
            .collect::<Vec<_>>()
            .join("; ");
        let negative_prompt = (!moment.exclusions.is_empty()).then(|| moment.exclusions.join("; "));
        service.execute(
            session.id(),
            SessionCommand::RequestGeneration {
                specification: GenerationSpec {
                    schema_version: "1.0.0".to_owned(),
                    id: next_local_identifier("generation-spec"),
                    session_id: session.id().to_owned(),
                    journey_plan_id: plan.id,
                    journey_plan_hash: plan_hash,
                    adapter: GenerationSpecAdapter {
                        id: "antidote.mock".to_owned(),
                        version: "1.0.0".to_owned(),
                    },
                    model: GenerationSpecModel {
                        id: "synthetic-triangle".to_owned(),
                        revision: "1".to_owned(),
                        artifact_hash: Some(MOCK_MODEL_HASH.to_owned()),
                    },
                    duration_seconds: plan.total_duration_seconds,
                    seed: Some(42),
                    prompt: Some(prompt),
                    negative_prompt,
                    parameters: Some(json!({"journey_stages": plan.stages})),
                    required_capabilities: Some(vec![
                        "deterministic_seed".to_owned(),
                        "duration".to_owned(),
                        "sample_rate".to_owned(),
                        "channels".to_owned(),
                    ]),
                    output: GenerationSpecOutput {
                        format: GenerationSpecOutputFormat::Wav,
                        sample_rate_hz: 8_000,
                        channels: 1,
                    },
                    created_at: now,
                },
            },
        )?;
        Ok(())
    }

    /// Apply the separate generation-consent gate without starting the worker.
    pub fn approve_generation(&self) -> DesktopResult<DesktopSnapshot> {
        let result = (|| -> InternalResult<()> {
            let session = self.load_session()?;
            self.service()?.execute(
                session.id(),
                SessionCommand::ApproveGeneration {
                    consent: ConsentSelection::explicit(consent_id(session.id())),
                },
            )?;
            Ok(())
        })();
        result
            .and_then(|()| self.snapshot_internal())
            .map_err(DesktopCommandError::from)
    }

    /// Invoke the isolated Python mock worker and record exactly one terminal result.
    pub fn run_generation(
        &self,
        simulation: GenerationSimulation,
    ) -> DesktopResult<DesktopSnapshot> {
        self.run_generation_internal(simulation)
            .and_then(|()| self.snapshot_internal())
            .map_err(DesktopCommandError::from)
    }

    fn run_generation_internal(&self, simulation: GenerationSimulation) -> InternalResult<()> {
        if self
            .inner
            .generation_active
            .swap(true, Ordering::AcqRel)
        {
            return Err(DesktopError::GenerationStillActive);
        }
        let _active_guard = GenerationActiveGuard(&self.inner);
        self.inner
            .cancellation_requested
            .store(false, Ordering::Release);
        *self
            .inner
            .progress
            .lock()
            .map_err(|_| DesktopError::Storage)? = GenerationProgressView::default();

        let session = self.load_session()?;
        let specification = session
            .generation()
            .ok_or(DesktopError::InvalidInput)?
            .specification
            .clone();
        let mut service = self.service()?;
        service.execute(session.id(), SessionCommand::StartGeneration)?;
        let result = match self.connect_worker() {
            Ok(mut worker) => worker
                .generate_with_progress(
                    &specification,
                    Some(MockSimulation {
                        mode: match simulation {
                            GenerationSimulation::Normal => MockSimulationMode::Normal,
                            GenerationSimulation::Crash => MockSimulationMode::Crash,
                        },
                        step_delay_ms: 80,
                    }),
                    |progress| self.observe_progress(progress),
                )
                .unwrap_or_else(|_| failed_result(&specification, "worker_failed")),
            Err(_) => failed_result(&specification, "worker_unavailable"),
        };
        service.execute(
            session.id(),
            SessionCommand::RecordGenerationResult { result },
        )?;
        Ok(())
    }

    fn observe_progress(&self, progress: WorkerProgress) -> ProgressDecision {
        if let Ok(mut current) = self.inner.progress.lock() {
            *current = GenerationProgressView {
                stage: progress.stage,
                fraction: progress.fraction,
                elapsed_ms: progress.elapsed_ms,
            };
        }
        if self
            .inner
            .cancellation_requested
            .load(Ordering::Acquire)
        {
            ProgressDecision::Cancel
        } else {
            ProgressDecision::Continue
        }
    }

    fn connect_worker(&self) -> InternalResult<WorkerSupervisor> {
        let root = repository_root();
        let executable = find_executable("uv").ok_or(DesktopError::WorkerUnavailable)?;
        WorkerSupervisor::connect(
            WorkerSupervisorConfig {
                executable,
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
                approved_output_root: self.inner.data_root.join("artifacts"),
                request_timeout: Duration::from_secs(20),
                shutdown_timeout: Duration::from_secs(2),
                max_artifact_bytes: DEFAULT_MAX_ARTIFACT_BYTES,
                allow_mock_simulation: true,
            },
            WorkerModelIdentity {
                adapter_id: "antidote.mock".to_owned(),
                adapter_version: "1.0.0".to_owned(),
                model_id: "synthetic-triangle".to_owned(),
                model_revision: "1".to_owned(),
                model_artifact_hash: Some(MOCK_MODEL_HASH.to_owned()),
            },
        )
        .map_err(|_| DesktopError::WorkerUnavailable)
    }

    /// Request cooperative cancellation or cancel a job that has not started.
    pub fn cancel_generation(&self) -> DesktopResult<DesktopSnapshot> {
        let result = (|| -> InternalResult<()> {
            let session = self.load_session()?;
            let state = session
                .generation()
                .ok_or(DesktopError::InvalidInput)?
                .state;
            if state == GenerationJobState::Running {
                self.inner
                    .cancellation_requested
                    .store(true, Ordering::Release);
            } else if matches!(state, GenerationJobState::Requested | GenerationJobState::Approved)
            {
                self.service()?
                    .execute(session.id(), SessionCommand::CancelGeneration)?;
            } else {
                return Err(DesktopError::InvalidInput);
            }
            Ok(())
        })();
        result
            .and_then(|()| self.snapshot_internal())
            .map_err(DesktopCommandError::from)
    }

    /// Classify an orphaned running job after a desktop restart.
    pub fn recover_interrupted_generation(&self) -> DesktopResult<DesktopSnapshot> {
        let result = (|| -> InternalResult<()> {
            if self.inner.generation_active.load(Ordering::Acquire) {
                return Err(DesktopError::GenerationStillActive);
            }
            let session = self.load_session()?;
            let job = session.generation().ok_or(DesktopError::InvalidInput)?;
            if job.state != GenerationJobState::Running {
                return Err(DesktopError::InvalidInput);
            }
            self.service()?.execute(
                session.id(),
                SessionCommand::RecordGenerationResult {
                    result: failed_result(&job.specification, "host_restarted"),
                },
            )?;
            Ok(())
        })();
        result
            .and_then(|()| self.snapshot_internal())
            .map_err(DesktopCommandError::from)
    }

    /// Approve and begin deliberate playback of the generated audio artifact.
    pub fn start_playback(&self) -> DesktopResult<DesktopSnapshot> {
        let result = (|| -> InternalResult<()> {
            let session = self.load_session()?;
            let artifact = session
                .generation()
                .and_then(|job| job.result.as_ref())
                .and_then(|result| {
                    result.artifacts.iter().find(|artifact| {
                        artifact.kind
                            == antidote_core::contracts::GenerationResultArtifactKind::Audio
                    })
                })
                .ok_or(DesktopError::InvalidInput)?;
            let mut service = self.service()?;
            let events = service.execute(
                session.id(),
                SessionCommand::ApprovePlayback {
                    artifact_sha256: artifact.sha256.clone(),
                },
            )?;
            let approval_id = events
                .iter()
                .find_map(|event| match &event.event {
                    antidote_core::SessionEvent::PlaybackApproved { approval } => {
                        Some(approval.id.clone())
                    }
                    _ => None,
                })
                .ok_or(DesktopError::InvalidInput)?;
            service.execute(
                session.id(),
                SessionCommand::StartExposure { approval_id },
            )?;
            Ok(())
        })();
        result
            .and_then(|()| self.snapshot_internal())
            .map_err(DesktopCommandError::from)
    }

    /// Stop playback immediately with one visible classification.
    pub fn stop_playback(&self, reason: ExposureStopReason) -> DesktopResult<DesktopSnapshot> {
        let result = (|| -> InternalResult<()> {
            let session = self.load_session()?;
            let exposure = session.exposure().ok_or(DesktopError::InvalidInput)?;
            self.service()?.execute(
                session.id(),
                SessionCommand::StopExposure {
                    exposure_id: exposure.id.clone(),
                    reason,
                },
            )?;
            Ok(())
        })();
        result
            .and_then(|()| self.snapshot_internal())
            .map_err(DesktopCommandError::from)
    }

    /// Record an immediate response without treating intensity as success.
    pub fn record_response(&self, input: ResponseInput) -> DesktopResult<DesktopSnapshot> {
        let result = (|| -> InternalResult<()> {
            if input.felt_state.trim().is_empty() {
                return Err(DesktopError::InvalidInput);
            }
            let session = self.load_session()?;
            let exposure = session.exposure().ok_or(DesktopError::InvalidInput)?;
            let now = current_timestamp()?;
            self.service()?.execute(
                session.id(),
                SessionCommand::RecordResponse {
                    response: ResponseObservation {
                        schema_version: "1.0.0".to_owned(),
                        id: next_local_identifier("response"),
                        session_id: session.id().to_owned(),
                        exposure_id: exposure.id.clone(),
                        observed_at: now,
                        window: ResponseObservationWindow::Immediate,
                        felt_state: ResponseObservationFeltState {
                            description: input.felt_state.trim().to_owned(),
                            valence: None,
                            arousal: None,
                            intensity: None,
                        },
                        wanted_intensity: input.wanted_intensity,
                        helpfulness: bounded_score(input.helpfulness)?,
                        resonance: bounded_score(input.resonance)?,
                        mismatch: bounded_score(input.mismatch)?,
                        harm: bounded_score(input.harm)?,
                        stopped_early: Some(input.stopped_early),
                        notes: optional_trimmed(input.notes),
                        later_aftereffect_requested: Some(
                            input.later_aftereffect_requested,
                        ),
                        allow_personal_model_update: Some(false),
                    },
                    consent: ConsentSelection::explicit(consent_id(session.id())),
                },
            )?;
            Ok(())
        })();
        result
            .and_then(|()| self.snapshot_internal())
            .map_err(DesktopCommandError::from)
    }

    /// Acknowledge the exact active safety event without reclassifying it.
    pub fn acknowledge_safety_event(&self) -> DesktopResult<DesktopSnapshot> {
        let result = (|| -> InternalResult<()> {
            let session = self.load_session()?;
            let identifier = session
                .safety_halt_id()
                .ok_or(DesktopError::InvalidInput)?
                .to_owned();
            self.service()?.execute(
                session.id(),
                SessionCommand::AcknowledgeSafetyEvent {
                    safety_event_id: identifier,
                },
            )?;
            Ok(())
        })();
        result
            .and_then(|()| self.snapshot_internal())
            .map_err(DesktopCommandError::from)
    }

    /// Close the current immutable session after response review.
    pub fn close_session(&self) -> DesktopResult<DesktopSnapshot> {
        let result = (|| -> InternalResult<()> {
            let session = self.load_session()?;
            self.service()?
                .execute(session.id(), SessionCommand::CloseSession)?;
            std::fs::remove_file(self.active_session_path())
                .map_err(|_| DesktopError::Storage)?;
            Ok(())
        })();
        result
            .and_then(|()| self.snapshot_internal())
            .map_err(DesktopCommandError::from)
    }
}

struct GenerationActiveGuard<'a>(&'a DesktopRuntimeInner);

impl Drop for GenerationActiveGuard<'_> {
    fn drop(&mut self) {
        self.0.generation_active.store(false, Ordering::Release);
    }
}

#[derive(Debug, Clone, Copy)]
struct SystemClock;

impl Clock for SystemClock {
    fn now_rfc3339(&self) -> Result<String, PortFailure> {
        current_timestamp().map_err(|_| PortFailure::new("system_clock"))
    }
}

#[derive(Debug, Clone, Copy)]
struct SystemIdentifiers;

impl IdentifierSource for SystemIdentifiers {
    fn next_id(&mut self, kind: IdentifierKind) -> Result<String, PortFailure> {
        let prefix = match kind {
            IdentifierKind::Event => "event",
            IdentifierKind::PlaybackApproval => "playback-approval",
            IdentifierKind::Exposure => "exposure",
            IdentifierKind::SafetyEvent => "safety-event",
            IdentifierKind::ModelUpdateProposal => "model-update",
            IdentifierKind::ExportApproval => "export-approval",
        };
        Ok(next_local_identifier(prefix))
    }
}

fn phase_for(session: &Session) -> DesktopPhase {
    if session.moment().is_none() {
        return DesktopPhase::CheckIn;
    }
    let Some(journey) = session.journey() else {
        return DesktopPhase::ContextReview;
    };
    if !matches!(journey.approval, JourneyApprovalState::Approved { .. }) {
        return DesktopPhase::JourneyReview;
    }
    let Some(generation) = session.generation() else {
        return DesktopPhase::JourneyReview;
    };
    match generation.state {
        GenerationJobState::Requested => DesktopPhase::GenerationReview,
        GenerationJobState::Approved | GenerationJobState::Running => DesktopPhase::Generating,
        GenerationJobState::Cancelled
        | GenerationJobState::Partial
        | GenerationJobState::Failed => DesktopPhase::GenerationFailed,
        GenerationJobState::Generated => match session.exposure() {
            None => DesktopPhase::ReadyToListen,
            Some(exposure) if exposure.state == ExposureState::Playing => DesktopPhase::Listening,
            Some(_) if session.response_count() == 0 => DesktopPhase::Response,
            Some(_) => DesktopPhase::Complete,
        },
    }
}

fn validate_check_in(input: &CheckInInput) -> InternalResult<()> {
    if input.current_state.trim().is_empty()
        || input.desired_transition.trim().is_empty()
        || !(10..=MOCK_MAX_DURATION_SECONDS).contains(&input.horizon_seconds)
    {
        return Err(DesktopError::InvalidInput);
    }
    parse_direction(&input.desired_direction)?;
    let inclusions = clean_list(input.inclusions.clone());
    let exclusions = clean_list(input.exclusions.clone());
    if inclusions.iter().any(|inclusion| {
        exclusions
            .iter()
            .any(|exclusion| inclusion.eq_ignore_ascii_case(exclusion))
    }) {
        return Err(DesktopError::InvalidInput);
    }
    Ok(())
}

fn parse_direction(value: &str) -> InternalResult<MomentContextDesiredTransitionDirection> {
    match value {
        "stay_with" => Ok(MomentContextDesiredTransitionDirection::StayWith),
        "soften" => Ok(MomentContextDesiredTransitionDirection::Soften),
        "regulate" => Ok(MomentContextDesiredTransitionDirection::Regulate),
        "uplift" => Ok(MomentContextDesiredTransitionDirection::Uplift),
        "focus" => Ok(MomentContextDesiredTransitionDirection::Focus),
        "release" => Ok(MomentContextDesiredTransitionDirection::Release),
        "explore" => Ok(MomentContextDesiredTransitionDirection::Explore),
        "other" => Ok(MomentContextDesiredTransitionDirection::Other),
        _ => Err(DesktopError::InvalidInput),
    }
}

fn clean_list(values: Vec<String>) -> Vec<String> {
    values
        .into_iter()
        .map(|value| value.trim().to_owned())
        .filter(|value| !value.is_empty())
        .collect()
}

fn optional_trimmed(value: Option<String>) -> Option<String> {
    value
        .map(|text| text.trim().to_owned())
        .filter(|text| !text.is_empty())
}

fn bounded_score(value: Option<f64>) -> InternalResult<Option<f64>> {
    if value.is_some_and(|score| !score.is_finite() || !(0.0..=1.0).contains(&score)) {
        return Err(DesktopError::InvalidInput);
    }
    Ok(value)
}

fn current_timestamp() -> InternalResult<String> {
    OffsetDateTime::now_utc()
        .format(&Rfc3339)
        .map_err(|_| DesktopError::Storage)
}

fn next_local_identifier(prefix: &str) -> String {
    let elapsed = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos();
    let sequence = IDENTIFIER_SEQUENCE.fetch_add(1, Ordering::Relaxed);
    format!("{prefix}-{elapsed:032x}-{sequence:016x}")
}

fn consent_id(session_id: &str) -> String {
    format!("consent-{session_id}")
}

fn worker_card() -> WorkerCard {
    WorkerCard {
        adapter_id: "antidote.mock",
        adapter_version: "1.0.0",
        model_id: "synthetic-triangle",
        model_revision: "1",
        license: "MIT",
        device_class: "synthetic-cpu",
        network_access: false,
        duration_seconds_min: 10,
        duration_seconds_max: MOCK_MAX_DURATION_SECONDS,
        controls: vec![
            "deterministic_seed",
            "duration",
            "sample_rate",
            "channels",
        ],
        restrictions: vec![
            "synthetic-test-output-only",
            "no-model-weights",
            "no-network-access",
        ],
        visible_downgrades: vec![
            "The mock worker preserves the storyboard but does not claim to realize timbre, harmony, density, spatiality, or felt-state intent.",
            "Synthetic analysis values are test evidence, not proof of acoustic-plan adherence or benefit.",
        ],
    }
}

fn failed_result(specification: &GenerationSpec, code: &str) -> GenerationResult {
    GenerationResult {
        schema_version: "1.0.0".to_owned(),
        id: next_local_identifier("generation-result"),
        generation_spec_id: specification.id.clone(),
        status: GenerationResultStatus::Failed,
        adapter: GenerationResultAdapter {
            id: specification.adapter.id.clone(),
            version: specification.adapter.version.clone(),
        },
        model: GenerationResultModel {
            id: specification.model.id.clone(),
            revision: specification.model.revision.clone(),
        },
        code_revision: "unavailable".to_owned(),
        device_class: "unavailable".to_owned(),
        elapsed_ms: 0,
        effective_parameters: None,
        artifacts: Vec::new(),
        feature_report: None,
        warnings: vec!["No complete playable artifact was recorded.".to_owned()],
        failure: Some(GenerationResultFailure {
            code: Some(code.to_owned()),
            message: Some("The local synthetic generation attempt did not complete.".to_owned()),
            retryable: Some(true),
        }),
    }
}

fn repository_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .and_then(Path::parent)
        .expect("desktop crate must remain nested under apps/desktop")
        .to_path_buf()
}

fn find_executable(name: &str) -> Option<PathBuf> {
    std::env::var_os("PATH").and_then(|paths| {
        std::env::split_paths(&paths)
            .map(|directory| directory.join(name))
            .find(|candidate| candidate.is_file())
            .and_then(|candidate| candidate.canonicalize().ok())
    })
}

#[cfg(test)]
mod tests {
    use tempfile::TempDir;

    use super::*;

    fn check_in(consent_confirmed: bool) -> CheckInInput {
        CheckInInput {
            current_state: "synthetic unsettled baseline".to_owned(),
            desired_direction: "regulate".to_owned(),
            desired_transition: "move toward a steadier synthetic state".to_owned(),
            horizon_seconds: 10,
            inclusions: vec!["soft continuity".to_owned()],
            exclusions: vec!["sudden level changes".to_owned()],
            optional_context: Some("A synthetic manual context item.".to_owned()),
            notes: None,
            consent_confirmed,
        }
    }

    #[test]
    fn consent_is_required_before_any_session_event_is_written() {
        let temporary = TempDir::new().expect("temporary root must exist");
        let runtime = DesktopRuntime::open(temporary.path().to_path_buf())
            .expect("runtime must open");
        let error = runtime
            .record_check_in(check_in(false))
            .expect_err("missing consent must fail closed");

        assert_eq!(error.code, "consent_required");
        assert_eq!(
            runtime.snapshot().expect("snapshot must load").phase,
            DesktopPhase::CheckIn
        );
    }

    #[test]
    fn canonical_state_recovers_after_runtime_reconstruction() {
        let temporary = TempDir::new().expect("temporary root must exist");
        let runtime = DesktopRuntime::open(temporary.path().to_path_buf())
            .expect("runtime must open");
        let reviewed = runtime
            .record_check_in(check_in(true))
            .expect("check-in must append");
        assert_eq!(reviewed.phase, DesktopPhase::ContextReview);
        runtime
            .propose_journey()
            .expect("planner must append a journey");

        let recovered = DesktopRuntime::open(temporary.path().to_path_buf())
            .expect("runtime must reopen")
            .snapshot()
            .expect("canonical state must replay");
        assert_eq!(recovered.phase, DesktopPhase::JourneyReview);
        assert!(
            recovered
                .canonical_session
                .as_ref()
                .is_some_and(|session| session.version() >= 5)
        );
    }

    #[test]
    fn generation_cannot_be_approved_before_journey_approval() {
        let temporary = TempDir::new().expect("temporary root must exist");
        let runtime = DesktopRuntime::open(temporary.path().to_path_buf())
            .expect("runtime must open");
        runtime
            .record_check_in(check_in(true))
            .expect("check-in must append");
        runtime
            .propose_journey()
            .expect("planner must append a journey");

        let error = runtime
            .approve_generation()
            .expect_err("generation approval must remain gated");
        assert_eq!(error.code, "session_transition_rejected");
    }
}
