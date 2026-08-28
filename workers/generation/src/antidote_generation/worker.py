# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Stateful protocol implementation for the deterministic Antidote mock worker."""

from __future__ import annotations

import hashlib
import json
import re
import wave
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from threading import Event, Lock, Thread
from typing import Any

from jsonschema.exceptions import ValidationError

from antidote_generation.contracts import ContractRegistry
from antidote_generation.mock_audio import (
    SynthesisOutcome,
    SynthesisRequest,
    analyze_wav,
    sha256_file,
    synthesize_wav,
)
from antidote_generation.protocol import (
    PROTOCOL_VERSION,
    ErrorCode,
    Operation,
    ProtocolError,
    Request,
    error_response,
    response,
)

MOCK_ADAPTER_ID = "antidote.mock"
MOCK_ADAPTER_VERSION = "1.0.0"
MOCK_MODEL_ID = "synthetic-triangle"
MOCK_MODEL_REVISION = "1"
MOCK_MODEL_HASH = hashlib.sha256(
    f"{MOCK_ADAPTER_ID}:{MOCK_MODEL_ID}:{MOCK_MODEL_REVISION}".encode()
).hexdigest()
CODE_REVISION = "antidote-mock-worker-v1"
DEVICE_CLASS = "synthetic-cpu"
MAX_MOCK_DURATION_SECONDS = 30
MAX_MOCK_SAMPLE_RATE_HZ = 48_000
MAX_MOCK_CHANNELS = 2
MAX_SIMULATION_DELAY_MS = 250
SUPPORTED_ANALYSES = frozenset({"wav_metadata", "peak_amplitude"})
SUPPORTED_CAPABILITIES = frozenset(
    {"deterministic_seed", "duration", "sample_rate", "channels"}
)
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")

Emitter = Callable[[dict[str, Any]], None]


@dataclass(slots=True)
class _Job:
    """Mutable cooperative-cancellation state for one generation request."""

    cancel: Event
    thread: Thread


@dataclass(frozen=True, slots=True)
class _GenerationTask:
    """Immutable inputs transferred to one synthetic worker thread."""

    request: Request
    spec: dict[str, Any]
    output_directory: Path
    mode: str
    delay: int
    cancel: Event
    emit: Emitter


def _canonical_hash(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _require_fields(
    value: dict[str, Any],
    *,
    required: frozenset[str],
    optional: frozenset[str] = frozenset(),
) -> None:
    if set(value) - required - optional or not required.issubset(value):
        raise ProtocolError(
            ErrorCode.INVALID_INPUT, "operation payload fields are invalid"
        )


def _require_object(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProtocolError(ErrorCode.INVALID_INPUT, "nested payload must be an object")
    return value


def _require_text(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ProtocolError(ErrorCode.INVALID_INPUT, "text field is invalid")
    return value


def _require_sha256(value: object) -> str:
    text = _require_text(value)
    if SHA256_PATTERN.fullmatch(text) is None:
        raise ProtocolError(ErrorCode.INVALID_INPUT, "SHA-256 field is invalid")
    return text


class MockGenerationWorker:
    """Execute protocol v1 without model packages, weights, or network access."""

    def __init__(self, contracts_root: Path) -> None:
        """Create an unloaded worker using repository-owned domain schemas."""
        self._contracts = ContractRegistry(contracts_root)
        self._loaded = False
        self._jobs: dict[str, _Job] = {}
        self._completed: set[str] = set()
        self._lock = Lock()

    def process(self, request: Request, emit: Emitter) -> None:
        """Validate and dispatch one trusted envelope."""
        try:
            handler = {
                Operation.HELLO: self._hello,
                Operation.CAPABILITIES: self._capabilities,
                Operation.LOAD_MODEL: self._load_model,
                Operation.GENERATE: self._generate,
                Operation.ANALYZE: self._analyze,
                Operation.CANCEL: self._cancel,
                Operation.HEALTH: self._health,
            }[request.operation]
            handler(request, emit)
        except ProtocolError as error:
            classified = ProtocolError(
                error.code,
                error.safe_message,
                request_id=error.request_id or request.request_id,
                operation=error.operation or request.operation.value,
                retryable=error.retryable,
            )
            emit(error_response(classified))
        except Exception:  # noqa: BLE001 - redact implementation failures at boundary
            emit(
                error_response(
                    ProtocolError(
                        ErrorCode.INTERNAL_ERROR,
                        "worker operation failed internally",
                        request_id=request.request_id,
                        operation=request.operation.value,
                    )
                )
            )

    def wait_for_all(self, timeout_seconds: float = 10.0) -> None:
        """Wait for the current synthetic jobs during orderly server shutdown."""
        with self._lock:
            threads = [job.thread for job in self._jobs.values()]
        for thread in threads:
            thread.join(timeout_seconds)

    def shutdown(self, timeout_seconds: float = 5.0) -> None:
        """Cooperatively cancel and drain every job after the host closes stdin."""
        with self._lock:
            jobs = list(self._jobs.values())
            for job in jobs:
                job.cancel.set()
        for job in jobs:
            job.thread.join(timeout_seconds)

    def _emit_result(
        self, request: Request, emit: Emitter, payload: dict[str, Any]
    ) -> None:
        emit(response(request.request_id, request.operation.value, "result", payload))

    def _hello(self, request: Request, emit: Emitter) -> None:
        _require_fields(
            request.payload,
            required=frozenset({"host", "supported_protocol_versions"}),
        )
        host = _require_object(request.payload["host"])
        _require_fields(host, required=frozenset({"name", "version"}))
        _require_text(host["name"])
        _require_text(host["version"])
        versions = request.payload["supported_protocol_versions"]
        if not isinstance(versions, list) or not all(
            isinstance(version, str) for version in versions
        ):
            raise ProtocolError(
                ErrorCode.INVALID_INPUT, "supported protocol versions are invalid"
            )
        if PROTOCOL_VERSION not in versions:
            raise ProtocolError(
                ErrorCode.UNSUPPORTED_VERSION,
                "no compatible protocol version is available",
            )
        self._emit_result(
            request,
            emit,
            {
                "worker": {
                    "id": "antidote-generation-mock",
                    "version": "0.1.0",
                    "code_revision": CODE_REVISION,
                },
                "selected_protocol_version": PROTOCOL_VERSION,
                "compatible_protocol_versions": [PROTOCOL_VERSION],
            },
        )

    def _capabilities(self, request: Request, emit: Emitter) -> None:
        _require_fields(
            request.payload,
            required=frozenset(),
            optional=frozenset({"adapter_id"}),
        )
        adapter_filter = request.payload.get("adapter_id")
        if adapter_filter is not None:
            _require_text(adapter_filter)
        adapters = []
        if adapter_filter in {None, MOCK_ADAPTER_ID}:
            adapters.append(
                {
                    "id": MOCK_ADAPTER_ID,
                    "version": MOCK_ADAPTER_VERSION,
                    "license": "MIT",
                    "models": [
                        {
                            "id": MOCK_MODEL_ID,
                            "revision": MOCK_MODEL_REVISION,
                            "artifact_hash": MOCK_MODEL_HASH,
                        }
                    ],
                    "controls": sorted(SUPPORTED_CAPABILITIES),
                    "duration_seconds": {"minimum": 10, "maximum": 30},
                    "output_formats": ["wav"],
                    "sample_rate_hz": {"minimum": 8_000, "maximum": 48_000},
                    "channels": {"minimum": 1, "maximum": 2},
                    "hardware": [DEVICE_CLASS],
                    "restrictions": [
                        "synthetic-test-output-only",
                        "no-model-weights",
                        "no-network-access",
                    ],
                }
            )
        self._emit_result(
            request,
            emit,
            {"adapters": adapters, "device_class": DEVICE_CLASS, "warnings": []},
        )

    def _load_model(self, request: Request, emit: Emitter) -> None:
        _require_fields(request.payload, required=frozenset({"adapter", "model"}))
        adapter = _require_object(request.payload["adapter"])
        model = _require_object(request.payload["model"])
        _require_fields(adapter, required=frozenset({"id", "version"}))
        _require_fields(
            model,
            required=frozenset({"id", "revision"}),
            optional=frozenset({"artifact_hash"}),
        )
        _require_text(adapter["id"])
        _require_text(adapter["version"])
        _require_text(model["id"])
        _require_text(model["revision"])
        if (
            adapter.get("id") != MOCK_ADAPTER_ID
            or adapter.get("version") != MOCK_ADAPTER_VERSION
            or model.get("id") != MOCK_MODEL_ID
            or model.get("revision") != MOCK_MODEL_REVISION
        ):
            raise ProtocolError(
                ErrorCode.UNSUPPORTED_CONTROL,
                "adapter or model identity is unsupported",
            )
        artifact_hash = model.get("artifact_hash")
        if (
            artifact_hash is not None
            and _require_sha256(artifact_hash) != MOCK_MODEL_HASH
        ):
            raise ProtocolError(
                ErrorCode.INTEGRITY_MISMATCH,
                "model identity hash does not match",
            )
        self._loaded = True
        self._emit_result(
            request,
            emit,
            {
                "adapter": {"id": MOCK_ADAPTER_ID, "version": MOCK_ADAPTER_VERSION},
                "model": {
                    "id": MOCK_MODEL_ID,
                    "revision": MOCK_MODEL_REVISION,
                    "artifact_hash": MOCK_MODEL_HASH,
                },
                "device_class": DEVICE_CLASS,
                "memory_bytes": 0,
                "warnings": ["deterministic synthetic mock; no AI model loaded"],
            },
        )

    def _validate_generation(
        self, payload: dict[str, Any]
    ) -> tuple[dict[str, Any], Path, str, int]:
        _require_fields(
            payload,
            required=frozenset({"spec", "output_directory"}),
            optional=frozenset({"simulation"}),
        )
        spec = _require_object(payload["spec"])
        try:
            self._contracts.validate("generation-spec", spec)
        except ValidationError as error:
            path = ".".join(str(item) for item in error.absolute_path) or "root"
            raise ProtocolError(
                ErrorCode.INVALID_INPUT,
                f"generation specification is invalid at {path}",
            ) from error
        output_text = _require_text(payload["output_directory"])
        if "\x00" in output_text:
            raise ProtocolError(ErrorCode.INVALID_INPUT, "output directory is invalid")
        output_directory = Path(output_text)
        if not output_directory.is_absolute():
            raise ProtocolError(
                ErrorCode.INVALID_INPUT, "output directory must be an absolute path"
            )
        simulation = payload.get("simulation", {})
        simulation_object = _require_object(simulation)
        _require_fields(
            simulation_object,
            required=frozenset(),
            optional=frozenset({"mode", "step_delay_ms"}),
        )
        mode = simulation_object.get("mode", "normal")
        delay = simulation_object.get("step_delay_ms", 0)
        if mode not in {"normal", "timeout", "partial", "crash"}:
            raise ProtocolError(ErrorCode.INVALID_INPUT, "simulation mode is invalid")
        if (
            not isinstance(delay, int)
            or isinstance(delay, bool)
            or not 0 <= delay <= MAX_SIMULATION_DELAY_MS
        ):
            raise ProtocolError(ErrorCode.INVALID_INPUT, "simulation delay is invalid")
        self._require_supported_spec(spec)
        return spec, output_directory.resolve(), mode, delay

    def _require_supported_spec(self, spec: dict[str, Any]) -> None:
        if not self._loaded:
            raise ProtocolError(ErrorCode.MODEL_NOT_LOADED, "mock model is not loaded")
        if (
            spec["adapter"] != {"id": MOCK_ADAPTER_ID, "version": MOCK_ADAPTER_VERSION}
            or spec["model"]["id"] != MOCK_MODEL_ID
            or spec["model"]["revision"] != MOCK_MODEL_REVISION
            or spec["output"]["format"] != "wav"
            or spec["duration_seconds"] > MAX_MOCK_DURATION_SECONDS
            or spec["output"]["sample_rate_hz"] > MAX_MOCK_SAMPLE_RATE_HZ
            or spec["output"]["channels"] > MAX_MOCK_CHANNELS
        ):
            raise ProtocolError(
                ErrorCode.UNSUPPORTED_CONTROL,
                "generation specification exceeds declared mock capabilities",
            )
        required = set(spec.get("required_capabilities", []))
        if not required.issubset(SUPPORTED_CAPABILITIES):
            raise ProtocolError(
                ErrorCode.UNSUPPORTED_CONTROL,
                "required generation capability is unsupported",
            )
        artifact_hash = spec["model"].get("artifact_hash")
        if artifact_hash is not None and artifact_hash != MOCK_MODEL_HASH:
            raise ProtocolError(
                ErrorCode.INTEGRITY_MISMATCH, "generation model hash does not match"
            )

    def _generate(self, request: Request, emit: Emitter) -> None:
        spec, output_directory, mode, delay = self._validate_generation(request.payload)
        with self._lock:
            if (
                request.request_id in self._jobs
                or request.request_id in self._completed
            ):
                raise ProtocolError(
                    ErrorCode.INVALID_INPUT, "generation request ID was already used"
                )
            cancel = Event()
            task = _GenerationTask(
                request,
                spec,
                output_directory,
                mode,
                delay,
                cancel,
                emit,
            )
            thread = Thread(
                target=self._run_generation,
                args=(task,),
                name=f"antidote-mock-{request.request_id}",
                daemon=True,
            )
            self._jobs[request.request_id] = _Job(cancel, thread)
            thread.start()

    # The complete result construction stays here so every terminal class shares
    # exactly one canonical generation-result validation path.
    def _run_generation(self, task: _GenerationTask) -> None:
        try:
            spec_hash = _canonical_hash(task.spec)
            request_hash = hashlib.sha256(task.request.request_id.encode()).hexdigest()
            filename = f"mock-{spec_hash[:20]}-{request_hash[:12]}.wav"
            target = task.output_directory / filename

            def progress(fraction: float, elapsed_ms: int) -> None:
                task.emit(
                    response(
                        task.request.request_id,
                        task.request.operation.value,
                        "progress",
                        {
                            "stage": "synthesizing",
                            "fraction": round(fraction, 6),
                            "elapsed_ms": elapsed_ms,
                        },
                    )
                )

            outcome = synthesize_wav(
                SynthesisRequest(
                    target=target,
                    duration_seconds=task.spec["duration_seconds"],
                    sample_rate_hz=task.spec["output"]["sample_rate_hz"],
                    channels=task.spec["output"]["channels"],
                    seed=task.spec.get("seed") or 0,
                    mode=task.mode,
                    step_delay_ms=task.delay,
                ),
                cancel=task.cancel,
                progress=progress,
            )
            result = self._generation_result(task.spec, spec_hash, outcome)
            self._contracts.validate("generation-result", result)
            self._emit_result(task.request, task.emit, result)
        except Exception:  # noqa: BLE001 - asynchronous boundary must be redacted
            task.emit(
                error_response(
                    ProtocolError(
                        ErrorCode.INTERNAL_ERROR,
                        "generation failed internally",
                        request_id=task.request.request_id,
                        operation=task.request.operation.value,
                    )
                )
            )
        finally:
            with self._lock:
                self._jobs.pop(task.request.request_id, None)
                self._completed.add(task.request.request_id)

    def _generation_result(
        self, spec: dict[str, Any], spec_hash: str, outcome: SynthesisOutcome
    ) -> dict[str, Any]:
        failure_map = {
            "cancelled": (ErrorCode.CANCELLED, "generation was cancelled", False),
            "timeout": (ErrorCode.TIMEOUT, "generation timed out", True),
            "partial": (
                ErrorCode.PARTIAL_OUTPUT,
                "generation produced a classified partial artifact",
                True,
            ),
            "crash": (
                ErrorCode.WORKER_CRASH,
                "worker crash was simulated",
                True,
            ),
        }
        status = outcome.status
        result_status = (
            status if status in {"generated", "partial", "cancelled"} else "failed"
        )
        artifacts = []
        if outcome.artifact is not None:
            artifacts.append(
                {
                    "kind": "audio",
                    "path": str(outcome.artifact.path),
                    "sha256": outcome.artifact.sha256,
                    "media_type": "audio/wav",
                    "size_bytes": outcome.artifact.size_bytes,
                }
            )
        failure = None
        warnings = ["synthetic mock output; not model-generated music"]
        if status in failure_map:
            code, message, retryable = failure_map[status]
            failure = {"code": code.value, "message": message, "retryable": retryable}
            warnings.append(message)
        return {
            "schema_version": "1.0.0",
            "id": f"mock-result-{spec_hash[:24]}",
            "generation_spec_id": spec["id"],
            "status": result_status,
            "adapter": {"id": MOCK_ADAPTER_ID, "version": MOCK_ADAPTER_VERSION},
            "model": {"id": MOCK_MODEL_ID, "revision": MOCK_MODEL_REVISION},
            "code_revision": CODE_REVISION,
            "device_class": DEVICE_CLASS,
            "elapsed_ms": outcome.elapsed_ms,
            "effective_parameters": {
                "seed": spec.get("seed") or 0,
                "input_sha256": spec_hash,
                "duration_seconds": spec["duration_seconds"],
                "sample_rate_hz": spec["output"]["sample_rate_hz"],
                "channels": spec["output"]["channels"],
            },
            "artifacts": artifacts,
            "feature_report": None,
            "warnings": warnings,
            "failure": failure,
        }

    def _analyze(self, request: Request, emit: Emitter) -> None:
        _require_fields(request.payload, required=frozenset({"artifact", "analyses"}))
        artifact = _require_object(request.payload["artifact"])
        _require_fields(artifact, required=frozenset({"path", "sha256"}))
        path_text = _require_text(artifact["path"])
        if "\x00" in path_text:
            raise ProtocolError(ErrorCode.INVALID_INPUT, "analysis path is invalid")
        path = Path(path_text)
        expected_hash = _require_sha256(artifact["sha256"])
        analyses = request.payload["analyses"]
        if (
            not path.is_absolute()
            or not isinstance(analyses, list)
            or not analyses
            or not all(isinstance(item, str) for item in analyses)
            or len(set(analyses)) != len(analyses)
        ):
            raise ProtocolError(ErrorCode.INVALID_INPUT, "analysis request is invalid")
        if not set(analyses).issubset(SUPPORTED_ANALYSES):
            raise ProtocolError(
                ErrorCode.UNSUPPORTED_CONTROL, "requested analysis is unsupported"
            )
        try:
            resolved = path.resolve(strict=True)
            actual_hash = sha256_file(resolved)
        except (OSError, ValueError) as error:
            raise ProtocolError(
                ErrorCode.INVALID_INPUT, "analysis artifact is unavailable or invalid"
            ) from error
        if actual_hash != expected_hash:
            raise ProtocolError(
                ErrorCode.INTEGRITY_MISMATCH, "analysis artifact hash does not match"
            )
        try:
            report = analyze_wav(resolved)
        except (OSError, ValueError, wave.Error) as error:
            raise ProtocolError(
                ErrorCode.INVALID_INPUT, "analysis artifact is not a supported WAV"
            ) from error
        self._emit_result(
            request,
            emit,
            {
                "artifact_sha256": actual_hash,
                "requested_analyses": analyses,
                "feature_report": report,
                "adapter": {"id": MOCK_ADAPTER_ID, "version": MOCK_ADAPTER_VERSION},
                "code_revision": CODE_REVISION,
                "device_class": DEVICE_CLASS,
                "warnings": ["declared synthetic WAV features only"],
            },
        )

    def _cancel(self, request: Request, emit: Emitter) -> None:
        _require_fields(request.payload, required=frozenset({"target_request_id"}))
        target = _require_text(request.payload["target_request_id"])
        with self._lock:
            job = self._jobs.get(target)
            if job is not None:
                job.cancel.set()
                status = "accepted"
            elif target in self._completed:
                status = "already_complete"
            else:
                status = "unsupported"
        self._emit_result(
            request, emit, {"target_request_id": target, "status": status}
        )

    def _health(self, request: Request, emit: Emitter) -> None:
        _require_fields(request.payload, required=frozenset())
        with self._lock:
            active_jobs = len(self._jobs)
        self._emit_result(
            request,
            emit,
            {
                "ready": True,
                "model_loaded": self._loaded,
                "active_jobs": active_jobs,
                "device_class": DEVICE_CLASS,
                "resources": {"network": False, "model_memory_bytes": 0},
            },
        )


__all__ = [
    "CODE_REVISION",
    "DEVICE_CLASS",
    "MOCK_ADAPTER_ID",
    "MOCK_ADAPTER_VERSION",
    "MOCK_MODEL_HASH",
    "MOCK_MODEL_ID",
    "MOCK_MODEL_REVISION",
    "MockGenerationWorker",
]
