use crate::{
    ApplicationError, Clock, EventRepository, IdentifierKind, IdentifierSource, RecordedEvent,
    SESSION_EVENT_SCHEMA_VERSION, Session, SessionCommand, require_identifier,
};

/// Framework-independent command boundary for one immutable event repository.
#[derive(Debug)]
pub struct SessionService<R, C, I> {
    repository: R,
    clock: C,
    identifiers: I,
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
