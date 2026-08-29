//! Bounded process supervision for the Antidote model-worker protocol.
//!
//! The supervisor validates both directions of the NDJSON boundary, grants one
//! host-created output directory per request, and returns only verified contract
//! results to the framework-independent Rust core.

use std::collections::{BTreeMap, BTreeSet};
use std::ffi::OsString;
use std::fmt::{Debug, Formatter};
use std::fs::{self, File};
use std::io::{BufRead, BufReader, Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdin, Command, Stdio};
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::mpsc::{self, Receiver, RecvTimeoutError};
use std::thread::{self, JoinHandle};
use std::time::{Duration, Instant};

use antidote_contracts::{
    GenerationResult, GenerationResultStatus, GenerationSpec, GenerationSpecOutputFormat,
    validate_contract,
};
use antidote_core::{PortFailure, WorkerInvocationPort};
use serde::{Deserialize, Serialize};
use serde_json::value::RawValue;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

/// Model-worker protocol version supported by this host.
pub const PROTOCOL_VERSION: &str = "1.0.0";
/// Maximum request or response line, including its newline delimiter.
pub const MAX_MESSAGE_BYTES: usize = 65_536;
/// Default maximum artifact size accepted from a worker.
pub const DEFAULT_MAX_ARTIFACT_BYTES: u64 = 64 * 1024 * 1024;

const STDERR_ACCOUNTING_LIMIT: u64 = 64 * 1024;
const MAX_REPORTED_MEMORY_BYTES: u64 = 1 << 50;

/// Stable, source-text-free supervisor failure classification.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub enum WorkerErrorKind {
    /// Executable, path, or process startup policy failed.
    Configuration,
    /// The child process could not be started or contacted.
    Process,
    /// The child exited before returning a terminal response.
    Crash,
    /// An envelope or operation payload was malformed or mismatched.
    Protocol,
    /// The operation exceeded its bounded deadline.
    Timeout,
    /// The worker did not advertise a required immutable capability.
    UnsupportedCapability,
    /// A returned artifact escaped its grant or failed size/hash checks.
    ArtifactIntegrity,
    /// The worker returned a classified operation error.
    WorkerRejected,
}

/// Redacted supervisor error safe to cross the application boundary.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WorkerError {
    kind: WorkerErrorKind,
    operation: &'static str,
}

impl WorkerError {
    fn new(kind: WorkerErrorKind, operation: &'static str) -> Self {
        Self { kind, operation }
    }

    /// Return the stable failure class without exposing submitted content.
    #[must_use]
    pub const fn kind(&self) -> WorkerErrorKind {
        self.kind
    }

    /// Return the bounded operation that failed.
    #[must_use]
    pub const fn operation(&self) -> &'static str {
        self.operation
    }
}

impl std::fmt::Display for WorkerError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        write!(
            formatter,
            "worker {} operation failed ({:?})",
            self.operation, self.kind
        )
    }
}

impl std::error::Error for WorkerError {}

/// Immutable model identity negotiated and loaded at process startup.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WorkerModelIdentity {
    /// Adapter identifier.
    pub adapter_id: String,
    /// Adapter implementation version.
    pub adapter_version: String,
    /// Model identifier.
    pub model_id: String,
    /// Immutable model revision.
    pub model_revision: String,
    /// Optional expected model artifact digest.
    pub model_artifact_hash: Option<String>,
}

/// Explicit child-process and filesystem policy.
#[derive(Clone)]
pub struct WorkerSupervisorConfig {
    /// Absolute worker launcher executable; never interpreted by a shell.
    pub executable: PathBuf,
    /// Exact ordered argument vector.
    pub arguments: Vec<OsString>,
    /// Exact environment after the inherited environment is cleared.
    pub environment: BTreeMap<OsString, OsString>,
    /// Existing working directory used for process launch.
    pub working_directory: PathBuf,
    /// Existing directory under which per-run grants are created.
    pub approved_output_root: PathBuf,
    /// Deadline applied independently to each operation.
    pub request_timeout: Duration,
    /// Grace period for EOF shutdown before forced termination.
    pub shutdown_timeout: Duration,
    /// Maximum trusted artifact length.
    pub max_artifact_bytes: u64,
    /// Permit the protocol's mock-only simulation field in test configurations.
    pub allow_mock_simulation: bool,
}

impl Debug for WorkerSupervisorConfig {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("WorkerSupervisorConfig")
            .field("executable", &self.executable)
            .field("argument_count", &self.arguments.len())
            .field(
                "environment_keys",
                &self.environment.keys().collect::<Vec<_>>(),
            )
            .field("working_directory", &self.working_directory)
            .field("approved_output_root", &self.approved_output_root)
            .field("request_timeout", &self.request_timeout)
            .field("shutdown_timeout", &self.shutdown_timeout)
            .field("max_artifact_bytes", &self.max_artifact_bytes)
            .field("allow_mock_simulation", &self.allow_mock_simulation)
            .finish()
    }
}

/// One non-sensitive progress observation delivered by the worker.
#[derive(Debug, Clone, PartialEq)]
pub struct WorkerProgress {
    /// Worker-declared stage label.
    pub stage: String,
    /// Fraction in the inclusive range zero through one.
    pub fraction: f64,
    /// Worker-declared elapsed milliseconds.
    pub elapsed_ms: u64,
}

/// Host decision after receiving a progress observation.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProgressDecision {
    /// Continue waiting for the generation result.
    Continue,
    /// Send one cooperative cancellation request.
    Cancel,
}

/// Mock-only failure mode used by integration evidence.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MockSimulationMode {
    /// Complete normally.
    Normal,
    /// Return a classified timeout result from the worker.
    Timeout,
    /// Return a classified partial artifact.
    Partial,
    /// Return a classified simulated worker crash result.
    Crash,
}

impl MockSimulationMode {
    const fn as_str(self) -> &'static str {
        match self {
            Self::Normal => "normal",
            Self::Timeout => "timeout",
            Self::Partial => "partial",
            Self::Crash => "crash",
        }
    }
}

/// Optional mock-only generation controls, rejected by production configurations.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct MockSimulation {
    /// Synthetic terminal class.
    pub mode: MockSimulationMode,
    /// Bounded delay after each synthetic chunk.
    pub step_delay_ms: u16,
}

/// Redacted standard-error accounting; child text is never retained.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct StderrSummary {
    /// Number of diagnostic bytes observed, capped at the accounting limit.
    pub bytes_observed: u64,
    /// Whether the child wrote beyond the accounting limit.
    pub truncated: bool,
}

#[derive(Debug)]
enum ReaderEvent {
    Line(Vec<u8>),
    Eof,
    Failed,
}

#[derive(Debug)]
struct ChildProcess {
    child: Child,
    stdin: Option<ChildStdin>,
    receiver: Receiver<ReaderEvent>,
    stdout_thread: Option<JoinHandle<()>>,
    stderr_thread: Option<JoinHandle<()>>,
    stderr_bytes: Arc<AtomicU64>,
    stderr_truncated: Arc<AtomicBool>,
}

/// Stateful supervisor for one negotiated local worker process.
#[derive(Debug)]
pub struct WorkerSupervisor {
    config: WorkerSupervisorConfig,
    identity: WorkerModelIdentity,
    process: Option<ChildProcess>,
    capabilities: CapabilitySet,
    request_sequence: u64,
    active_generation: Option<(String, String, PathBuf)>,
    last_stderr_summary: StderrSummary,
}

impl WorkerSupervisor {
    /// Spawn, negotiate, discover capabilities, and load one immutable model identity.
    ///
    /// # Errors
    ///
    /// Fails closed for invalid paths, startup failure, incompatible protocol,
    /// missing capability, malformed output, timeout, or model-load rejection.
    pub fn connect(
        mut config: WorkerSupervisorConfig,
        identity: WorkerModelIdentity,
    ) -> Result<Self, WorkerError> {
        validate_config(&mut config)?;
        validate_identity(&identity)?;
        let mut supervisor = Self {
            config,
            identity,
            process: None,
            capabilities: CapabilitySet::default(),
            request_sequence: 0,
            active_generation: None,
            last_stderr_summary: StderrSummary {
                bytes_observed: 0,
                truncated: false,
            },
        };
        supervisor.spawn_and_negotiate()?;
        Ok(supervisor)
    }

    /// Return the latest redacted standard-error accounting.
    #[must_use]
    pub fn stderr_summary(&self) -> StderrSummary {
        self.process
            .as_ref()
            .map_or(self.last_stderr_summary, |process| StderrSummary {
                bytes_observed: process.stderr_bytes.load(Ordering::Relaxed),
                truncated: process.stderr_truncated.load(Ordering::Relaxed),
            })
    }

    /// Request a source-text-free readiness report.
    ///
    /// # Errors
    ///
    /// Returns a redacted process or protocol failure.
    pub fn health(&mut self) -> Result<bool, WorkerError> {
        let request_id = self.send_request("health", json!({}))?;
        let response = self.await_terminal(&request_id, "health")?;
        let health: HealthPayload = parse_payload(&response, "health")?;
        if health.device_class.is_empty()
            || health.resources.network
            || health.resources.model_memory_bytes > MAX_REPORTED_MEMORY_BYTES
        {
            return Err(WorkerError::new(WorkerErrorKind::Protocol, "health"));
        }
        Ok(health.ready && health.model_loaded && health.active_jobs == 0)
    }

    /// Terminate any prior process and repeat negotiation with the same explicit policy.
    ///
    /// # Errors
    ///
    /// Returns a redacted startup or negotiation failure.
    pub fn restart(&mut self) -> Result<(), WorkerError> {
        self.terminate_process();
        self.active_generation = None;
        self.capabilities = CapabilitySet::default();
        self.spawn_and_negotiate()
    }

    /// Generate with progress delivery and optional integration-test simulation.
    ///
    /// # Errors
    ///
    /// Fails before generation for unsupported controls or unsafe paths, and
    /// fails closed for timeout, crash, malformed output, or artifact mismatch.
    #[allow(clippy::too_many_lines)]
    pub fn generate_with_progress<F>(
        &mut self,
        specification: &GenerationSpec,
        simulation: Option<MockSimulation>,
        mut on_progress: F,
    ) -> Result<GenerationResult, WorkerError>
    where
        F: FnMut(WorkerProgress) -> ProgressDecision,
    {
        self.require_capabilities(specification)?;
        if simulation.is_some() && !self.config.allow_mock_simulation {
            return Err(WorkerError::new(
                WorkerErrorKind::Configuration,
                "mock_simulation",
            ));
        }
        let request_id = self.next_request_id("generate")?;
        let output_directory = self.create_output_grant(specification, &request_id)?;
        let mut payload = json!({
            "spec": specification,
            "output_directory": output_directory,
        });
        if let Some(simulation) = simulation {
            payload["simulation"] = json!({
                "mode": simulation.mode.as_str(),
                "step_delay_ms": simulation.step_delay_ms,
            });
        }
        self.write_request(&request_id, "generate", payload)?;
        self.active_generation = Some((
            specification.id.clone(),
            request_id.clone(),
            output_directory.clone(),
        ));

        let deadline = Instant::now() + self.config.request_timeout;
        let mut cancellation_request = None;
        let mut cancellation_acknowledged = false;
        let mut generation_result = None;
        let result = (|| -> Result<GenerationResult, WorkerError> {
            loop {
                let response = self.receive_until(deadline)?;
                let response_id = response
                    .request_id
                    .as_deref()
                    .ok_or_else(|| WorkerError::new(WorkerErrorKind::Protocol, "generate"))?;
                if response_id == request_id {
                    Self::require_response_identity(&response, &request_id, "generate")?;
                    match response.kind {
                        ResponseKind::Progress => {
                            let progress: ProgressPayload = parse_payload(&response, "progress")?;
                            let elapsed_ms = u64::try_from(progress.elapsed_ms).map_err(|_| {
                                WorkerError::new(WorkerErrorKind::Protocol, "progress")
                            })?;
                            if !(0.0..=1.0).contains(&progress.fraction)
                                || !progress.fraction.is_finite()
                                || progress.stage.is_empty()
                                || progress.stage.len() > 128
                                || !progress.stage.bytes().all(|byte| {
                                    byte.is_ascii_alphanumeric() || b"._:-".contains(&byte)
                                })
                            {
                                return Err(WorkerError::new(
                                    WorkerErrorKind::Protocol,
                                    "progress",
                                ));
                            }
                            if on_progress(WorkerProgress {
                                stage: progress.stage,
                                fraction: progress.fraction,
                                elapsed_ms,
                            }) == ProgressDecision::Cancel
                                && cancellation_request.is_none()
                            {
                                let cancel_id = self.next_request_id("cancel")?;
                                self.write_request(
                                    &cancel_id,
                                    "cancel",
                                    json!({"target_request_id": request_id}),
                                )?;
                                cancellation_request = Some(cancel_id);
                            }
                        }
                        ResponseKind::Result => {
                            let generation: GenerationResult =
                                parse_payload(&response, "generate")?;
                            self.verify_generation_result(
                                specification,
                                &output_directory,
                                &generation,
                            )?;
                            if cancellation_request.is_none() || cancellation_acknowledged {
                                break Ok(generation);
                            }
                            generation_result = Some(generation);
                        }
                        ResponseKind::Error => {
                            break Err(parse_worker_error(&response, "generate")?);
                        }
                    }
                } else if cancellation_request.as_deref() == Some(response_id) {
                    let Some(cancel_id) = cancellation_request.as_deref() else {
                        break Err(WorkerError::new(WorkerErrorKind::Protocol, "cancel"));
                    };
                    Self::require_response_identity(&response, cancel_id, "cancel")?;
                    if response.kind != ResponseKind::Result {
                        break Err(WorkerError::new(WorkerErrorKind::WorkerRejected, "cancel"));
                    }
                    let cancellation: CancelPayload = parse_payload(&response, "cancel")?;
                    if cancellation.target_request_id != request_id
                        || cancellation.status != CancelStatus::Accepted
                    {
                        break Err(WorkerError::new(WorkerErrorKind::WorkerRejected, "cancel"));
                    }
                    cancellation_acknowledged = true;
                    if let Some(generation) = generation_result.take() {
                        break Ok(generation);
                    }
                } else {
                    break Err(WorkerError::new(WorkerErrorKind::Protocol, "correlation"));
                }
            }
        })();
        self.active_generation = None;
        if result.is_err() {
            self.fail_active_generation(&output_directory);
        }
        result
    }

    fn spawn_and_negotiate(&mut self) -> Result<(), WorkerError> {
        self.process = Some(spawn_process(&self.config)?);
        let hello_id = self.send_request(
            "hello",
            json!({
                "host": {"name": "antidote-rust", "version": env!("CARGO_PKG_VERSION")},
                "supported_protocol_versions": [PROTOCOL_VERSION],
            }),
        )?;
        let hello_response = self.await_terminal(&hello_id, "hello")?;
        let hello: HelloPayload = parse_payload(&hello_response, "hello")?;
        if hello.selected_protocol_version != PROTOCOL_VERSION
            || !hello
                .compatible_protocol_versions
                .iter()
                .any(|version| version == PROTOCOL_VERSION)
            || hello.worker.id.is_empty()
            || hello.worker.version.is_empty()
            || hello.worker.code_revision.is_empty()
        {
            return Err(WorkerError::new(WorkerErrorKind::Protocol, "hello"));
        }

        let capability_id = self.send_request(
            "capabilities",
            json!({"adapter_id": self.identity.adapter_id}),
        )?;
        let capability_response = self.await_terminal(&capability_id, "capabilities")?;
        let capabilities: CapabilitiesPayload =
            parse_payload(&capability_response, "capabilities")?;
        self.capabilities = CapabilitySet::select(&capabilities, &self.identity)?;

        let mut model = json!({
            "id": self.identity.model_id,
            "revision": self.identity.model_revision,
        });
        if let Some(hash) = &self.identity.model_artifact_hash {
            model["artifact_hash"] = Value::String(hash.clone());
        }
        let load_id = self.send_request(
            "load_model",
            json!({
                "adapter": {
                    "id": self.identity.adapter_id,
                    "version": self.identity.adapter_version,
                },
                "model": model,
            }),
        )?;
        let load_response = self.await_terminal(&load_id, "load_model")?;
        let loaded: LoadModelPayload = parse_payload(&load_response, "load_model")?;
        if loaded.adapter.id != self.identity.adapter_id
            || loaded.adapter.version != self.identity.adapter_version
            || loaded.model.id != self.identity.model_id
            || loaded.model.revision != self.identity.model_revision
            || self
                .identity
                .model_artifact_hash
                .as_ref()
                .is_some_and(|expected| &loaded.model.artifact_hash != expected)
            || loaded.device_class.is_empty()
            || loaded.memory_bytes > MAX_REPORTED_MEMORY_BYTES
            || loaded.warnings.iter().any(|warning| warning.len() > 2_000)
        {
            return Err(WorkerError::new(WorkerErrorKind::Protocol, "load_model"));
        }
        Ok(())
    }

    fn send_request(
        &mut self,
        operation: &'static str,
        payload: Value,
    ) -> Result<String, WorkerError> {
        let request_id = self.next_request_id(operation)?;
        self.write_request(&request_id, operation, payload)?;
        Ok(request_id)
    }

    fn next_request_id(&mut self, operation: &'static str) -> Result<String, WorkerError> {
        self.request_sequence = self
            .request_sequence
            .checked_add(1)
            .ok_or_else(|| WorkerError::new(WorkerErrorKind::Protocol, "request_identifier"))?;
        Ok(format!("host-{operation}-{:08}", self.request_sequence))
    }

    fn write_request(
        &mut self,
        request_id: &str,
        operation: &'static str,
        payload: Value,
    ) -> Result<(), WorkerError> {
        let request = RequestEnvelope {
            protocol_version: PROTOCOL_VERSION,
            request_id,
            operation,
            payload,
        };
        let mut encoded = serde_json::to_vec(&request)
            .map_err(|_| WorkerError::new(WorkerErrorKind::Protocol, operation))?;
        encoded.push(b'\n');
        if encoded.len() > MAX_MESSAGE_BYTES {
            return Err(WorkerError::new(WorkerErrorKind::Protocol, operation));
        }
        let stdin = self
            .process
            .as_mut()
            .and_then(|process| process.stdin.as_mut())
            .ok_or_else(|| WorkerError::new(WorkerErrorKind::Crash, operation))?;
        stdin
            .write_all(&encoded)
            .and_then(|()| stdin.flush())
            .map_err(|_| WorkerError::new(WorkerErrorKind::Crash, operation))
    }

    fn await_terminal(
        &mut self,
        request_id: &str,
        operation: &'static str,
    ) -> Result<ResponseEnvelope, WorkerError> {
        let deadline = Instant::now() + self.config.request_timeout;
        let response = self.receive_until(deadline)?;
        Self::require_response_identity(&response, request_id, operation)?;
        match response.kind {
            ResponseKind::Result => Ok(response),
            ResponseKind::Error => Err(parse_worker_error(&response, operation)?),
            ResponseKind::Progress => Err(WorkerError::new(WorkerErrorKind::Protocol, operation)),
        }
    }

    fn receive_until(&mut self, deadline: Instant) -> Result<ResponseEnvelope, WorkerError> {
        let remaining = deadline.saturating_duration_since(Instant::now());
        if remaining.is_zero() {
            self.terminate_process();
            return Err(WorkerError::new(WorkerErrorKind::Timeout, "response"));
        }
        let event = self
            .process
            .as_ref()
            .ok_or_else(|| WorkerError::new(WorkerErrorKind::Crash, "response"))?
            .receiver
            .recv_timeout(remaining);
        match event {
            Ok(ReaderEvent::Line(line)) => parse_response(&line),
            Ok(ReaderEvent::Eof) => {
                self.terminate_process();
                Err(WorkerError::new(WorkerErrorKind::Crash, "response"))
            }
            Ok(ReaderEvent::Failed) | Err(RecvTimeoutError::Disconnected) => {
                self.terminate_process();
                Err(WorkerError::new(WorkerErrorKind::Process, "response"))
            }
            Err(RecvTimeoutError::Timeout) => {
                self.terminate_process();
                Err(WorkerError::new(WorkerErrorKind::Timeout, "response"))
            }
        }
    }

    fn require_response_identity(
        response: &ResponseEnvelope,
        request_id: &str,
        operation: &'static str,
    ) -> Result<(), WorkerError> {
        if response.protocol_version != PROTOCOL_VERSION
            || response.request_id.as_deref() != Some(request_id)
            || response.operation.as_deref() != Some(operation)
        {
            return Err(WorkerError::new(WorkerErrorKind::Protocol, operation));
        }
        Ok(())
    }

    fn require_capabilities(&self, specification: &GenerationSpec) -> Result<(), WorkerError> {
        let specification_value = serde_json::to_value(specification)
            .map_err(|_| WorkerError::new(WorkerErrorKind::Protocol, "generation_spec"))?;
        validate_contract("generation-spec", &specification_value)
            .map_err(|_| WorkerError::new(WorkerErrorKind::Protocol, "generation_spec"))?;
        let output_format = match specification.output.format {
            GenerationSpecOutputFormat::Wav => "wav",
            GenerationSpecOutputFormat::Flac => "flac",
        };
        let duration = u64::try_from(specification.duration_seconds).map_err(|_| {
            WorkerError::new(WorkerErrorKind::UnsupportedCapability, "capabilities")
        })?;
        let sample_rate = u64::try_from(specification.output.sample_rate_hz).map_err(|_| {
            WorkerError::new(WorkerErrorKind::UnsupportedCapability, "capabilities")
        })?;
        let channels = u64::try_from(specification.output.channels).map_err(|_| {
            WorkerError::new(WorkerErrorKind::UnsupportedCapability, "capabilities")
        })?;
        let required = specification
            .required_capabilities
            .as_deref()
            .unwrap_or_default();
        if specification.adapter.id != self.identity.adapter_id
            || specification.adapter.version != self.identity.adapter_version
            || specification.model.id != self.identity.model_id
            || specification.model.revision != self.identity.model_revision
            || !self.capabilities.output_formats.contains(output_format)
            || !self.capabilities.duration_seconds.contains(duration)
            || !self.capabilities.sample_rate_hz.contains(sample_rate)
            || !self.capabilities.channels.contains(channels)
            || required
                .iter()
                .any(|control| !self.capabilities.controls.contains(control))
        {
            return Err(WorkerError::new(
                WorkerErrorKind::UnsupportedCapability,
                "capabilities",
            ));
        }
        Ok(())
    }

    fn create_output_grant(
        &self,
        specification: &GenerationSpec,
        request_id: &str,
    ) -> Result<PathBuf, WorkerError> {
        let mut digest = Sha256::new();
        digest.update(specification.id.as_bytes());
        digest.update(b":");
        digest.update(request_id.as_bytes());
        let name = format!("run-{}", encode_hex(&digest.finalize()));
        let directory = self.config.approved_output_root.join(name);
        fs::create_dir(&directory)
            .map_err(|_| WorkerError::new(WorkerErrorKind::Configuration, "output_grant"))?;
        directory
            .canonicalize()
            .map_err(|_| WorkerError::new(WorkerErrorKind::Configuration, "output_grant"))
    }

    fn verify_generation_result(
        &self,
        specification: &GenerationSpec,
        output_directory: &Path,
        result: &GenerationResult,
    ) -> Result<(), WorkerError> {
        let value = serde_json::to_value(result)
            .map_err(|_| WorkerError::new(WorkerErrorKind::Protocol, "generation_result"))?;
        validate_contract("generation-result", &value)
            .map_err(|_| WorkerError::new(WorkerErrorKind::Protocol, "generation_result"))?;
        if result.generation_spec_id != specification.id
            || result.adapter.id != specification.adapter.id
            || result.adapter.version != specification.adapter.version
            || result.model.id != specification.model.id
            || result.model.revision != specification.model.revision
        {
            return Err(WorkerError::new(
                WorkerErrorKind::Protocol,
                "generation_result",
            ));
        }
        if result.status == GenerationResultStatus::Generated && result.failure.is_some() {
            return Err(WorkerError::new(
                WorkerErrorKind::Protocol,
                "generation_result",
            ));
        }
        for artifact in &result.artifacts {
            let declared_size = u64::try_from(artifact.size_bytes)
                .map_err(|_| WorkerError::new(WorkerErrorKind::ArtifactIntegrity, "artifact"))?;
            if declared_size > self.config.max_artifact_bytes {
                return Err(WorkerError::new(
                    WorkerErrorKind::ArtifactIntegrity,
                    "artifact",
                ));
            }
            let canonical = Path::new(&artifact.path)
                .canonicalize()
                .map_err(|_| WorkerError::new(WorkerErrorKind::ArtifactIntegrity, "artifact"))?;
            if !canonical.starts_with(output_directory) {
                return Err(WorkerError::new(
                    WorkerErrorKind::ArtifactIntegrity,
                    "artifact",
                ));
            }
            let metadata = canonical
                .metadata()
                .map_err(|_| WorkerError::new(WorkerErrorKind::ArtifactIntegrity, "artifact"))?;
            if !metadata.is_file() || metadata.len() != declared_size {
                return Err(WorkerError::new(
                    WorkerErrorKind::ArtifactIntegrity,
                    "artifact",
                ));
            }
            let actual_hash = hash_file(&canonical, self.config.max_artifact_bytes)?;
            if actual_hash != artifact.sha256 {
                return Err(WorkerError::new(
                    WorkerErrorKind::ArtifactIntegrity,
                    "artifact",
                ));
            }
        }
        Ok(())
    }

    fn cleanup_output_grant(&self, output_directory: &Path) {
        if output_directory.starts_with(&self.config.approved_output_root)
            && output_directory != self.config.approved_output_root
        {
            drop(fs::remove_dir_all(output_directory));
        }
    }

    fn fail_active_generation(&mut self, output_directory: &Path) {
        self.terminate_process();
        self.active_generation = None;
        self.cleanup_output_grant(output_directory);
    }

    fn terminate_process(&mut self) {
        let Some(mut process) = self.process.take() else {
            return;
        };
        drop(process.stdin.take());
        let deadline = Instant::now() + self.config.shutdown_timeout;
        loop {
            match process.child.try_wait() {
                Ok(Some(_)) => break,
                Ok(None) if Instant::now() < deadline => thread::sleep(Duration::from_millis(5)),
                Ok(None) | Err(_) => {
                    drop(process.child.kill());
                    drop(process.child.wait());
                    break;
                }
            }
        }
        if let Some(handle) = process.stdout_thread.take() {
            drop(handle.join());
        }
        if let Some(handle) = process.stderr_thread.take() {
            drop(handle.join());
        }
        self.last_stderr_summary = StderrSummary {
            bytes_observed: process.stderr_bytes.load(Ordering::Relaxed),
            truncated: process.stderr_truncated.load(Ordering::Relaxed),
        };
    }
}

impl WorkerInvocationPort for WorkerSupervisor {
    fn generate(
        &mut self,
        specification: &GenerationSpec,
    ) -> Result<GenerationResult, PortFailure> {
        self.generate_with_progress(specification, None, |_| ProgressDecision::Continue)
            .map_err(|_| PortFailure::new("worker_generate"))
    }

    fn cancel(&mut self, generation_spec_id: &str) -> Result<(), PortFailure> {
        let Some((active_specification, request_id, _output_directory)) =
            self.active_generation.clone()
        else {
            return Err(PortFailure::new("worker_cancel"));
        };
        if active_specification != generation_spec_id {
            return Err(PortFailure::new("worker_cancel"));
        }
        let cancel_id = self
            .send_request("cancel", json!({"target_request_id": request_id}))
            .map_err(|_| PortFailure::new("worker_cancel"))?;
        let response = self
            .await_terminal(&cancel_id, "cancel")
            .map_err(|_| PortFailure::new("worker_cancel"))?;
        let payload: CancelPayload =
            parse_payload(&response, "cancel").map_err(|_| PortFailure::new("worker_cancel"))?;
        if payload.status == CancelStatus::Accepted {
            Ok(())
        } else {
            Err(PortFailure::new("worker_cancel"))
        }
    }
}

impl Drop for WorkerSupervisor {
    fn drop(&mut self) {
        let output_directory = self
            .active_generation
            .as_ref()
            .map(|(_, _, directory)| directory.clone());
        self.terminate_process();
        if let Some(directory) = output_directory {
            self.cleanup_output_grant(&directory);
        }
    }
}

fn validate_config(config: &mut WorkerSupervisorConfig) -> Result<(), WorkerError> {
    if !config.executable.is_absolute()
        || config.request_timeout.is_zero()
        || config.shutdown_timeout.is_zero()
        || config.max_artifact_bytes == 0
    {
        return Err(WorkerError::new(
            WorkerErrorKind::Configuration,
            "configuration",
        ));
    }
    config.executable = config
        .executable
        .canonicalize()
        .map_err(|_| WorkerError::new(WorkerErrorKind::Configuration, "executable"))?;
    config.working_directory = config
        .working_directory
        .canonicalize()
        .map_err(|_| WorkerError::new(WorkerErrorKind::Configuration, "working_directory"))?;
    config.approved_output_root = config
        .approved_output_root
        .canonicalize()
        .map_err(|_| WorkerError::new(WorkerErrorKind::Configuration, "output_root"))?;
    if !config.executable.is_file()
        || !config.working_directory.is_dir()
        || !config.approved_output_root.is_dir()
    {
        return Err(WorkerError::new(
            WorkerErrorKind::Configuration,
            "configuration",
        ));
    }
    Ok(())
}

fn validate_identity(identity: &WorkerModelIdentity) -> Result<(), WorkerError> {
    let hash_is_valid = identity.model_artifact_hash.as_ref().is_none_or(|hash| {
        hash.len() == 64
            && hash
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    });
    if identity.adapter_id.is_empty()
        || identity.adapter_version.is_empty()
        || identity.model_id.is_empty()
        || identity.model_revision.is_empty()
        || !hash_is_valid
    {
        return Err(WorkerError::new(
            WorkerErrorKind::Configuration,
            "model_identity",
        ));
    }
    Ok(())
}

fn spawn_process(config: &WorkerSupervisorConfig) -> Result<ChildProcess, WorkerError> {
    let mut command = Command::new(&config.executable);
    command
        .args(&config.arguments)
        .env_clear()
        .envs(&config.environment)
        .current_dir(&config.working_directory)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    let mut child = command
        .spawn()
        .map_err(|_| WorkerError::new(WorkerErrorKind::Process, "spawn"))?;
    let stdin = child
        .stdin
        .take()
        .ok_or_else(|| WorkerError::new(WorkerErrorKind::Process, "stdin"))?;
    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| WorkerError::new(WorkerErrorKind::Process, "stdout"))?;
    let stderr = child
        .stderr
        .take()
        .ok_or_else(|| WorkerError::new(WorkerErrorKind::Process, "stderr"))?;
    let (sender, receiver) = mpsc::channel();
    let stdout_thread = thread::spawn(move || read_stdout(stdout, &sender));
    let stderr_bytes = Arc::new(AtomicU64::new(0));
    let stderr_truncated = Arc::new(AtomicBool::new(false));
    let stderr_count = Arc::clone(&stderr_bytes);
    let stderr_flag = Arc::clone(&stderr_truncated);
    let stderr_thread = thread::spawn(move || drain_stderr(stderr, &stderr_count, &stderr_flag));
    Ok(ChildProcess {
        child,
        stdin: Some(stdin),
        receiver,
        stdout_thread: Some(stdout_thread),
        stderr_thread: Some(stderr_thread),
        stderr_bytes,
        stderr_truncated,
    })
}

fn read_stdout(stdout: impl Read, sender: &mpsc::Sender<ReaderEvent>) {
    let mut reader = BufReader::new(stdout);
    loop {
        let mut line = Vec::new();
        match (&mut reader)
            .take(u64::try_from(MAX_MESSAGE_BYTES + 1).expect("message bound fits u64"))
            .read_until(b'\n', &mut line)
        {
            Ok(0) => {
                drop(sender.send(ReaderEvent::Eof));
                break;
            }
            Ok(_) if line.len() > MAX_MESSAGE_BYTES || !line.ends_with(b"\n") => {
                drop(sender.send(ReaderEvent::Failed));
                break;
            }
            Ok(_) => {
                if sender.send(ReaderEvent::Line(line)).is_err() {
                    break;
                }
            }
            Err(_) => {
                drop(sender.send(ReaderEvent::Failed));
                break;
            }
        }
    }
}

fn drain_stderr(mut stderr: impl Read, bytes_observed: &AtomicU64, truncated: &AtomicBool) {
    let mut buffer = [0_u8; 4096];
    while let Ok(count) = stderr.read(&mut buffer) {
        if count == 0 {
            break;
        }
        let count = u64::try_from(count).unwrap_or(u64::MAX);
        let previous = bytes_observed.fetch_add(count, Ordering::Relaxed);
        if previous.saturating_add(count) > STDERR_ACCOUNTING_LIMIT {
            truncated.store(true, Ordering::Relaxed);
            bytes_observed.store(STDERR_ACCOUNTING_LIMIT, Ordering::Relaxed);
        }
    }
}

fn hash_file(path: &Path, maximum: u64) -> Result<String, WorkerError> {
    let mut file = File::open(path)
        .map_err(|_| WorkerError::new(WorkerErrorKind::ArtifactIntegrity, "artifact"))?;
    let mut digest = Sha256::new();
    let mut total = 0_u64;
    let mut buffer = vec![0_u8; 64 * 1024].into_boxed_slice();
    loop {
        let count = file
            .read(&mut buffer)
            .map_err(|_| WorkerError::new(WorkerErrorKind::ArtifactIntegrity, "artifact"))?;
        if count == 0 {
            break;
        }
        total =
            total
                .checked_add(u64::try_from(count).map_err(|_| {
                    WorkerError::new(WorkerErrorKind::ArtifactIntegrity, "artifact")
                })?)
                .ok_or_else(|| WorkerError::new(WorkerErrorKind::ArtifactIntegrity, "artifact"))?;
        if total > maximum {
            return Err(WorkerError::new(
                WorkerErrorKind::ArtifactIntegrity,
                "artifact",
            ));
        }
        digest.update(&buffer[..count]);
    }
    Ok(encode_hex(&digest.finalize()))
}

fn encode_hex(bytes: &[u8]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut encoded = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        encoded.push(char::from(HEX[usize::from(byte >> 4)]));
        encoded.push(char::from(HEX[usize::from(byte & 0x0f)]));
    }
    encoded
}

#[derive(Debug, Serialize)]
struct RequestEnvelope<'a> {
    protocol_version: &'static str,
    request_id: &'a str,
    operation: &'static str,
    payload: Value,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ResponseEnvelope {
    protocol_version: String,
    request_id: Option<String>,
    operation: Option<String>,
    kind: ResponseKind,
    payload: Box<RawValue>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize)]
#[serde(rename_all = "snake_case")]
enum ResponseKind {
    Progress,
    Result,
    Error,
}

fn parse_response(line: &[u8]) -> Result<ResponseEnvelope, WorkerError> {
    if line.len() > MAX_MESSAGE_BYTES || !line.ends_with(b"\n") {
        return Err(WorkerError::new(WorkerErrorKind::Protocol, "response"));
    }
    let response: ResponseEnvelope = serde_json::from_slice(line)
        .map_err(|_| WorkerError::new(WorkerErrorKind::Protocol, "response"))?;
    if response.protocol_version != PROTOCOL_VERSION {
        return Err(WorkerError::new(WorkerErrorKind::Protocol, "response"));
    }
    Ok(response)
}

fn parse_payload<T: for<'de> Deserialize<'de>>(
    response: &ResponseEnvelope,
    operation: &'static str,
) -> Result<T, WorkerError> {
    serde_json::from_str(response.payload.get())
        .map_err(|_| WorkerError::new(WorkerErrorKind::Protocol, operation))
}

fn parse_worker_error(
    response: &ResponseEnvelope,
    operation: &'static str,
) -> Result<WorkerError, WorkerError> {
    let payload: ErrorPayload = parse_payload(response, operation)?;
    if payload.code.is_empty()
        || payload.code.len() > 128
        || payload.message.is_empty()
        || payload.message.len() > 2_000
    {
        return Err(WorkerError::new(WorkerErrorKind::Protocol, operation));
    }
    let _ = payload.retryable;
    Ok(WorkerError::new(WorkerErrorKind::WorkerRejected, operation))
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ErrorPayload {
    code: String,
    message: String,
    retryable: bool,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ProgressPayload {
    stage: String,
    fraction: f64,
    elapsed_ms: i64,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct HelloPayload {
    worker: WorkerIdentityPayload,
    selected_protocol_version: String,
    compatible_protocol_versions: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct WorkerIdentityPayload {
    id: String,
    version: String,
    code_revision: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct CapabilitiesPayload {
    adapters: Vec<AdapterCapabilityPayload>,
    device_class: String,
    warnings: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct AdapterCapabilityPayload {
    id: String,
    version: String,
    license: String,
    models: Vec<ModelCapabilityPayload>,
    controls: Vec<String>,
    duration_seconds: RangePayload,
    output_formats: Vec<String>,
    sample_rate_hz: RangePayload,
    channels: RangePayload,
    hardware: Vec<String>,
    restrictions: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ModelCapabilityPayload {
    id: String,
    revision: String,
    artifact_hash: Option<String>,
}

#[derive(Debug, Clone, Copy, Deserialize)]
#[serde(deny_unknown_fields)]
struct RangePayload {
    minimum: u64,
    maximum: u64,
}

impl RangePayload {
    const fn contains(self, value: u64) -> bool {
        self.minimum <= value && value <= self.maximum
    }
}

#[derive(Debug, Default)]
struct CapabilitySet {
    controls: BTreeSet<String>,
    duration_seconds: Option<RangePayload>,
    output_formats: BTreeSet<String>,
    sample_rate_hz: Option<RangePayload>,
    channels: Option<RangePayload>,
}

impl CapabilitySet {
    fn select(
        payload: &CapabilitiesPayload,
        identity: &WorkerModelIdentity,
    ) -> Result<Self, WorkerError> {
        if payload.device_class.is_empty()
            || payload.warnings.iter().any(|warning| warning.len() > 2_000)
        {
            return Err(WorkerError::new(WorkerErrorKind::Protocol, "capabilities"));
        }
        let adapter = payload
            .adapters
            .iter()
            .find(|candidate| {
                candidate.id == identity.adapter_id && candidate.version == identity.adapter_version
            })
            .ok_or_else(|| {
                WorkerError::new(WorkerErrorKind::UnsupportedCapability, "capabilities")
            })?;
        let model = adapter
            .models
            .iter()
            .find(|candidate| {
                candidate.id == identity.model_id && candidate.revision == identity.model_revision
            })
            .ok_or_else(|| {
                WorkerError::new(WorkerErrorKind::UnsupportedCapability, "capabilities")
            })?;
        if adapter.license.is_empty()
            || adapter.hardware.is_empty()
            || adapter.restrictions.is_empty()
            || identity
                .model_artifact_hash
                .as_ref()
                .is_some_and(|expected| model.artifact_hash.as_ref() != Some(expected))
            || adapter.duration_seconds.minimum > adapter.duration_seconds.maximum
            || adapter.sample_rate_hz.minimum > adapter.sample_rate_hz.maximum
            || adapter.channels.minimum > adapter.channels.maximum
        {
            return Err(WorkerError::new(WorkerErrorKind::Protocol, "capabilities"));
        }
        Ok(Self {
            controls: adapter.controls.iter().cloned().collect(),
            duration_seconds: Some(adapter.duration_seconds),
            output_formats: adapter.output_formats.iter().cloned().collect(),
            sample_rate_hz: Some(adapter.sample_rate_hz),
            channels: Some(adapter.channels),
        })
    }
}

trait RequiredRange {
    fn contains(&self, value: u64) -> bool;
}

impl RequiredRange for Option<RangePayload> {
    fn contains(&self, value: u64) -> bool {
        self.is_some_and(|range| range.contains(value))
    }
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct LoadModelPayload {
    adapter: LoadedAdapterPayload,
    model: LoadedModelPayload,
    device_class: String,
    memory_bytes: u64,
    warnings: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct LoadedAdapterPayload {
    id: String,
    version: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct LoadedModelPayload {
    id: String,
    revision: String,
    artifact_hash: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct HealthPayload {
    ready: bool,
    model_loaded: bool,
    active_jobs: u64,
    device_class: String,
    resources: HealthResourcesPayload,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct HealthResourcesPayload {
    network: bool,
    model_memory_bytes: u64,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct CancelPayload {
    target_request_id: String,
    status: CancelStatus,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize)]
#[serde(rename_all = "snake_case")]
enum CancelStatus {
    Accepted,
    AlreadyComplete,
    Unsupported,
}

/// Honest implementation status exposed to workspace smoke tests.
pub const IMPLEMENTATION_STATUS: &str = "bounded-rust-worker-supervisor-v1";

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn config_debug_redacts_argument_and_environment_values() {
        let config = WorkerSupervisorConfig {
            executable: PathBuf::from("/synthetic/worker"),
            arguments: vec![OsString::from("SOURCE-TEXT-MUST-NOT-APPEAR")],
            environment: BTreeMap::from([(
                OsString::from("ANTIDOTE_TEST_KEY"),
                OsString::from("PRIVATE-VALUE-MUST-NOT-APPEAR"),
            )]),
            working_directory: PathBuf::from("/synthetic"),
            approved_output_root: PathBuf::from("/synthetic/output"),
            request_timeout: Duration::from_secs(1),
            shutdown_timeout: Duration::from_secs(1),
            max_artifact_bytes: DEFAULT_MAX_ARTIFACT_BYTES,
            allow_mock_simulation: false,
        };
        let debug = format!("{config:?}");
        assert!(!debug.contains("SOURCE-TEXT-MUST-NOT-APPEAR"));
        assert!(!debug.contains("PRIVATE-VALUE-MUST-NOT-APPEAR"));
        assert!(debug.contains("ANTIDOTE_TEST_KEY"));
    }
}
