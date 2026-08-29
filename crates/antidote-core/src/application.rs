use crate::{
    ApplicationError, Clock, EventRepository, GenerationJobState, IdentifierKind, IdentifierSource,
    PortFailure, RecordedEvent, SESSION_EVENT_SCHEMA_VERSION, Session, SessionCommand,
    WorkerInvocationPort, require_identifier,
};
use antidote_contracts::{
    GenerationResult, GenerationResultAdapter, GenerationResultFailure, GenerationResultModel,
    GenerationResultStatus,
};

/// Framework-independent command boundary for one immutable event repository.
#[derive(Debug)]
pub struct SessionService<R, C, I> {
    repository: R,
    clock: C,
    identifiers: I,
}

/// Immutable event batches produced by one supervised generation attempt.
#[derive(Debug)]
pub struct GenerationOrchestrationOutcome {
    /// Events that moved the approved job to running before process invocation.
    pub started: Vec<RecordedEvent>,
    /// Events that classified the terminal worker outcome.
    pub terminal: Vec<RecordedEvent>,
    /// Redacted adapter failure, when the worker did not return a trusted result.
    pub worker_failure: Option<PortFailure>,
}

/// Framework-independent authority boundary around worker invocation.
#[derive(Debug)]
pub struct GenerationOrchestrator<R, C, I, W> {
    sessions: SessionService<R, C, I>,
    worker: W,
}

impl<R, C, I, W> GenerationOrchestrator<R, C, I, W>
where
    R: EventRepository,
    C: Clock,
    I: IdentifierSource,
    W: WorkerInvocationPort,
{
    /// Compose the authoritative session service with one replaceable worker adapter.
    #[must_use]
    pub const fn new(sessions: SessionService<R, C, I>, worker: W) -> Self {
        Self { sessions, worker }
    }

    /// Start an approved job, invoke the worker, and record exactly one terminal result.
    ///
    /// A process, protocol, timeout, or integrity failure is converted into a canonical
    /// failed generation result. It can never be interpreted as completed generation.
    ///
    /// # Errors
    ///
    /// Returns an application error when the session transition or event append fails.
    pub fn generate(
        &mut self,
        session_id: &str,
    ) -> Result<GenerationOrchestrationOutcome, ApplicationError> {
        let session = self.sessions.load_session(session_id)?;
        let job = session
            .generation()
            .ok_or(crate::DomainError::GenerationMissing)?;
        if job.state != GenerationJobState::Approved {
            return Err(crate::DomainError::GenerationNotApproved.into());
        }
        let specification = job.specification.clone();
        let started = self
            .sessions
            .execute(session_id, SessionCommand::StartGeneration)?;

        let (result, worker_failure) = match self.worker.generate(&specification) {
            Ok(result) => (result, None),
            Err(failure) => (failed_worker_result(&specification), Some(failure)),
        };
        let terminal = self.sessions.execute(
            session_id,
            SessionCommand::RecordGenerationResult { result },
        )?;
        Ok(GenerationOrchestrationOutcome {
            started,
            terminal,
            worker_failure,
        })
    }

    /// Record a person's cancellation even if cooperative delivery to the worker fails.
    ///
    /// # Errors
    ///
    /// Returns an application error when the job is absent, terminal, or cannot be appended.
    pub fn cancel(
        &mut self,
        session_id: &str,
    ) -> Result<(Vec<RecordedEvent>, Option<PortFailure>), ApplicationError> {
        let session = self.sessions.load_session(session_id)?;
        let job = session
            .generation()
            .ok_or(crate::DomainError::GenerationMissing)?;
        let delivery_failure = self.worker.cancel(&job.specification.id).err();
        let events = self
            .sessions
            .execute(session_id, SessionCommand::CancelGeneration)?;
        Ok((events, delivery_failure))
    }

    /// Recover the owned session service and worker adapter.
    #[must_use]
    pub fn into_parts(self) -> (SessionService<R, C, I>, W) {
        (self.sessions, self.worker)
    }
}

fn failed_worker_result(specification: &antidote_contracts::GenerationSpec) -> GenerationResult {
    GenerationResult {
        schema_version: "1.0.0".to_owned(),
        id: format!("worker-failure-{}", specification.id),
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
        warnings: vec!["worker did not return a trusted terminal result".to_owned()],
        failure: Some(GenerationResultFailure {
            code: Some("worker_unavailable".to_owned()),
            message: Some("worker invocation failed".to_owned()),
            retryable: Some(true),
        }),
    }
}

impl<R, C, I> SessionService<R, C, I>
where
    R: EventRepository,
    C: Clock,
    I: IdentifierSource,
{
    /// Construct the service from explicit persistence, time, and identifier ports.
    #[must_use]
    pub const fn new(repository: R, clock: C, identifiers: I) -> Self {
        Self {
            repository,
            clock,
            identifiers,
        }
    }

    /// Load and replay one session without changing its event stream.
    ///
    /// # Errors
    ///
    /// Returns a domain error for an invalid stream or a redacted port error
    /// when persistence is unavailable.
    pub fn load_session(&self, session_id: &str) -> Result<Session, ApplicationError> {
        require_identifier(session_id)?;
        let events = self.repository.load(session_id)?;
        Ok(Session::rehydrate(session_id, &events)?)
    }

    /// Decide one command and atomically append its immutable facts.
    ///
    /// The repository's expected-version check is the concurrency boundary.
    /// The clock and identifier ports make all tests deterministic.
    ///
    /// # Errors
    ///
    /// Returns a fail-closed domain error for invalid commands or streams and
    /// a redacted port error for clock, identifier, or persistence failures.
    pub fn execute(
        &mut self,
        session_id: &str,
        command: SessionCommand,
    ) -> Result<Vec<RecordedEvent>, ApplicationError> {
        let session = self.load_session(session_id)?;
        let now = self.clock.now_rfc3339()?;
        let facts = session.decide(command, &now, &mut self.identifiers)?;
        let mut recorded = Vec::with_capacity(facts.len());
        for (offset, event) in facts.into_iter().enumerate() {
            let id = self.identifiers.next_id(IdentifierKind::Event)?;
            require_identifier(&id)?;
            let offset =
                u64::try_from(offset).map_err(|_| crate::DomainError::InvalidEventSequence)?;
            let increment = offset
                .checked_add(1)
                .ok_or(crate::DomainError::InvalidEventSequence)?;
            let sequence = session
                .version()
                .checked_add(increment)
                .ok_or(crate::DomainError::InvalidEventSequence)?;
            recorded.push(RecordedEvent {
                schema_version: SESSION_EVENT_SCHEMA_VERSION.to_owned(),
                id,
                session_id: session_id.to_owned(),
                sequence,
                occurred_at: now.clone(),
                event,
            });
        }
        self.repository
            .append(session_id, session.version(), &recorded)?;
        Ok(recorded)
    }

    /// Recover the owned adapters, for example after a deterministic test.
    #[must_use]
    pub fn into_parts(self) -> (R, C, I) {
        (self.repository, self.clock, self.identifiers)
    }
}
