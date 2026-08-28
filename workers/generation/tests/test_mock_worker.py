# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Prove every mock-worker operation and required failure class."""

from __future__ import annotations

import json
import subprocess
import sys
from io import BytesIO
from pathlib import Path
from threading import Event, Lock
from typing import Any

import pytest

from antidote_generation.mock_audio import sha256_file
from antidote_generation.protocol import (
    MAX_MESSAGE_BYTES,
    PROTOCOL_VERSION,
    ErrorCode,
    Operation,
    ProtocolError,
    Request,
    decode_request,
    encode_response,
)
from antidote_generation.server import serve
from antidote_generation.worker import (
    MOCK_ADAPTER_ID,
    MOCK_ADAPTER_VERSION,
    MOCK_MODEL_HASH,
    MOCK_MODEL_ID,
    MOCK_MODEL_REVISION,
    MockGenerationWorker,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS_ROOT = REPOSITORY_ROOT / "contracts"
SENSITIVE_FIXTURE_TEXT = "SOURCE-TEXT-MUST-NEVER-LEAK"
FIXTURE_SEED = 8_675_309
FIXTURE_DURATION_SECONDS = 10
FIXTURE_SAMPLE_RATE_HZ = 8_000


class Collector:
    """Thread-safe response collector with a progress signal."""

    def __init__(self) -> None:
        """Create an empty collector."""
        self.values: list[dict[str, Any]] = []
        self.progress = Event()
        self._lock = Lock()

    def emit(self, value: dict[str, Any]) -> None:
        """Collect one response and signal progress without inspecting source text."""
        with self._lock:
            self.values.append(value)
        if value["kind"] == "progress":
            self.progress.set()

    def terminal(self, request_id: str) -> dict[str, Any]:
        """Return the unique terminal response for a request."""
        with self._lock:
            matches = [
                value
                for value in self.values
                if value["request_id"] == request_id
                and value["kind"] in {"result", "error"}
            ]
        assert len(matches) == 1
        return matches[0]


def request(request_id: str, operation: Operation, payload: dict[str, Any]) -> Request:
    """Build one already-decoded request for focused worker tests."""
    return Request(request_id, operation, payload)


def generation_spec(**overrides: object) -> dict[str, Any]:
    """Build a canonical deterministic synthetic generation specification."""
    spec: dict[str, Any] = {
        "schema_version": "1.0.0",
        "id": "spec-synthetic-001",
        "session_id": "session-synthetic-001",
        "journey_plan_id": "journey-synthetic-001",
        "journey_plan_hash": "a" * 64,
        "adapter": {"id": MOCK_ADAPTER_ID, "version": MOCK_ADAPTER_VERSION},
        "model": {
            "id": MOCK_MODEL_ID,
            "revision": MOCK_MODEL_REVISION,
            "artifact_hash": MOCK_MODEL_HASH,
        },
        "duration_seconds": FIXTURE_DURATION_SECONDS,
        "seed": FIXTURE_SEED,
        "prompt": SENSITIVE_FIXTURE_TEXT,
        "negative_prompt": "synthetic exclusion",
        "parameters": {"fixture": True},
        "required_capabilities": ["deterministic_seed"],
        "output": {
            "format": "wav",
            "sample_rate_hz": FIXTURE_SAMPLE_RATE_HZ,
            "channels": 1,
        },
        "created_at": "2026-08-28T12:00:00Z",
    }
    spec.update(overrides)
    return spec


def load_mock(worker: MockGenerationWorker, collector: Collector) -> None:
    """Load the built-in immutable mock identity."""
    worker.process(
        request(
            "load-001",
            Operation.LOAD_MODEL,
            {
                "adapter": {"id": MOCK_ADAPTER_ID, "version": MOCK_ADAPTER_VERSION},
                "model": {
                    "id": MOCK_MODEL_ID,
                    "revision": MOCK_MODEL_REVISION,
                    "artifact_hash": MOCK_MODEL_HASH,
                },
            },
        ),
        collector.emit,
    )
    assert collector.terminal("load-001")["kind"] == "result"


def generate(  # noqa: PLR0913
    worker: MockGenerationWorker,
    collector: Collector,
    output_directory: Path,
    *,
    request_id: str = "generate-001",
    spec: dict[str, Any] | None = None,
    simulation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run one asynchronous generation request to completion."""
    payload: dict[str, Any] = {
        "spec": spec or generation_spec(),
        "output_directory": str(output_directory),
    }
    if simulation is not None:
        payload["simulation"] = simulation
    worker.process(request(request_id, Operation.GENERATE, payload), collector.emit)
    worker.wait_for_all()
    return collector.terminal(request_id)


@pytest.mark.parametrize(
    ("raw", "code"),
    [
        (b"not-json\n", ErrorCode.INVALID_INPUT),
        (
            (
                b'{"protocol_version":"1.0.0","request_id":"x",'
                b'"operation":"health","payload":{}}'
            ),
            ErrorCode.INVALID_INPUT,
        ),
        (
            b'{"protocol_version":"1.0.0","request_id":"x","request_id":"y","operation":"health","payload":{}}\n',
            ErrorCode.INVALID_INPUT,
        ),
        (
            b'{"protocol_version":"2.0.0","request_id":"x","operation":"health","payload":{}}\n',
            ErrorCode.UNSUPPORTED_VERSION,
        ),
        (
            b'{"protocol_version":"1.0.0","request_id":"x","operation":"unknown","payload":{}}\n',
            ErrorCode.UNKNOWN_OPERATION,
        ),
        (
            (
                b'{"protocol_version":"1.0.0","request_id":"bad id",'
                b'"operation":"health","payload":{}}\n'
            ),
            ErrorCode.INVALID_INPUT,
        ),
    ],
)
def test_envelope_failures_are_closed(raw: bytes, code: ErrorCode) -> None:
    """Reject malformed, ambiguous, unknown, or untrusted envelopes."""
    with pytest.raises(ProtocolError) as captured:
        decode_request(raw)
    assert captured.value.code is code


def test_hello_capabilities_load_and_health_cover_control_operations() -> None:
    """Exercise discovery, compatibility, loading, and health operations."""
    worker = MockGenerationWorker(CONTRACTS_ROOT)
    collector = Collector()
    worker.process(
        request(
            "hello-001",
            Operation.HELLO,
            {
                "host": {"name": "synthetic-host", "version": "0.1.0"},
                "supported_protocol_versions": [PROTOCOL_VERSION],
            },
        ),
        collector.emit,
    )
    worker.process(
        request("capabilities-001", Operation.CAPABILITIES, {}), collector.emit
    )
    load_mock(worker, collector)
    worker.process(request("health-001", Operation.HEALTH, {}), collector.emit)

    assert (
        collector.terminal("hello-001")["payload"]["selected_protocol_version"]
        == PROTOCOL_VERSION
    )
    capabilities = collector.terminal("capabilities-001")["payload"]["adapters"]
    assert capabilities[0]["id"] == MOCK_ADAPTER_ID
    assert capabilities[0]["restrictions"] == [
        "synthetic-test-output-only",
        "no-model-weights",
        "no-network-access",
    ]
    health = collector.terminal("health-001")["payload"]
    assert health["ready"] is True
    assert health["model_loaded"] is True
    assert health["resources"]["network"] is False


def test_generation_is_deterministic_and_redacts_progress(tmp_path: Path) -> None:
    """Repeat a fixture and require identical WAV hashes without source-text output."""
    hashes = []
    for index in range(2):
        worker = MockGenerationWorker(CONTRACTS_ROOT)
        collector = Collector()
        load_mock(worker, collector)
        terminal = generate(
            worker,
            collector,
            tmp_path / f"run-{index}",
            request_id=f"generate-{index}",
        )
        result = terminal["payload"]
        assert result["status"] == "generated"
        artifact = result["artifacts"][0]
        assert sha256_file(Path(artifact["path"])) == artifact["sha256"]
        assert result["effective_parameters"]["seed"] == FIXTURE_SEED
        hashes.append(artifact["sha256"])
        encoded = b"".join(encode_response(value) for value in collector.values)
        assert SENSITIVE_FIXTURE_TEXT.encode() not in encoded
        assert any(value["kind"] == "progress" for value in collector.values)
    assert hashes[0] == hashes[1]
    assert (
        hashes[0] == "2fca813bc0f01e9f54a3fe2dbe19a6edd81cd016a051d693158bccc78d682b7b"
    )


def test_analyze_reports_declared_features_and_checks_integrity(tmp_path: Path) -> None:
    """Analyze a generated WAV and reject a mismatched declared digest."""
    worker = MockGenerationWorker(CONTRACTS_ROOT)
    collector = Collector()
    load_mock(worker, collector)
    generated = generate(worker, collector, tmp_path / "audio")["payload"]
    artifact = generated["artifacts"][0]
    worker.process(
        request(
            "analyze-001",
            Operation.ANALYZE,
            {
                "artifact": {"path": artifact["path"], "sha256": artifact["sha256"]},
                "analyses": ["wav_metadata", "peak_amplitude"],
            },
        ),
        collector.emit,
    )
    report = collector.terminal("analyze-001")["payload"]["feature_report"]
    assert report["duration_seconds"] == FIXTURE_DURATION_SECONDS
    assert report["sample_rate_hz"] == FIXTURE_SAMPLE_RATE_HZ
    assert report["channels"] == 1
    assert 0 < report["peak_amplitude"] < 1

    worker.process(
        request(
            "analyze-bad-hash",
            Operation.ANALYZE,
            {
                "artifact": {"path": artifact["path"], "sha256": "0" * 64},
                "analyses": ["wav_metadata"],
            },
        ),
        collector.emit,
    )
    assert (
        collector.terminal("analyze-bad-hash")["payload"]["code"]
        == "integrity_mismatch"
    )


def test_concurrent_identical_specs_use_isolated_atomic_paths(tmp_path: Path) -> None:
    """Prevent identical concurrent requests from sharing a temporary artifact."""
    worker = MockGenerationWorker(CONTRACTS_ROOT)
    collector = Collector()
    load_mock(worker, collector)
    output = tmp_path / "concurrent"
    payload = {"spec": generation_spec(), "output_directory": str(output)}
    worker.process(
        request("generate-concurrent-a", Operation.GENERATE, payload), collector.emit
    )
    worker.process(
        request("generate-concurrent-b", Operation.GENERATE, payload), collector.emit
    )
    worker.wait_for_all()
    first = collector.terminal("generate-concurrent-a")["payload"]["artifacts"][0]
    second = collector.terminal("generate-concurrent-b")["payload"]["artifacts"][0]
    assert first["path"] != second["path"]
    assert first["sha256"] == second["sha256"]
    assert not list(output.glob("*.part"))


def test_cancellation_classifies_and_removes_partial_artifacts(tmp_path: Path) -> None:
    """Accept cancellation during generation and leave no audio or temporary output."""
    worker = MockGenerationWorker(CONTRACTS_ROOT)
    collector = Collector()
    load_mock(worker, collector)
    output = tmp_path / "cancelled"
    worker.process(
        request(
            "generate-cancel",
            Operation.GENERATE,
            {
                "spec": generation_spec(),
                "output_directory": str(output),
                "simulation": {"step_delay_ms": 20},
            },
        ),
        collector.emit,
    )
    assert collector.progress.wait(timeout=2)
    worker.process(
        request(
            "cancel-001",
            Operation.CANCEL,
            {"target_request_id": "generate-cancel"},
        ),
        collector.emit,
    )
    worker.wait_for_all()
    assert collector.terminal("cancel-001")["payload"]["status"] == "accepted"
    assert collector.terminal("generate-cancel")["payload"]["status"] == "cancelled"
    assert not list(output.glob("*.wav"))
    assert not list(output.glob("*.part"))

    worker.process(
        request(
            "cancel-complete",
            Operation.CANCEL,
            {"target_request_id": "generate-cancel"},
        ),
        collector.emit,
    )
    worker.process(
        request(
            "cancel-missing",
            Operation.CANCEL,
            {"target_request_id": "never-started"},
        ),
        collector.emit,
    )
    assert (
        collector.terminal("cancel-complete")["payload"]["status"] == "already_complete"
    )
    assert collector.terminal("cancel-missing")["payload"]["status"] == "unsupported"


@pytest.mark.parametrize(
    ("mode", "expected_status", "expected_code", "artifact_count"),
    [
        ("timeout", "failed", "timeout", 0),
        ("partial", "partial", "partial_output", 1),
        ("crash", "failed", "worker_crash", 0),
    ],
)
def test_simulated_terminal_classes(
    tmp_path: Path,
    mode: str,
    expected_status: str,
    expected_code: str,
    artifact_count: int,
) -> None:
    """Keep timeout, partial output, and crash classifications explicit."""
    worker = MockGenerationWorker(CONTRACTS_ROOT)
    collector = Collector()
    load_mock(worker, collector)
    result = generate(
        worker,
        collector,
        tmp_path / mode,
        request_id=f"generate-{mode}",
        simulation={"mode": mode},
    )["payload"]
    assert result["status"] == expected_status
    assert result["failure"]["code"] == expected_code
    assert len(result["artifacts"]) == artifact_count


def test_invalid_and_unsupported_generation_fail_before_mutation(
    tmp_path: Path,
) -> None:
    """Reject invalid, unloaded, and unsupported specs before creating directories."""
    output = tmp_path / "must-not-exist"
    worker = MockGenerationWorker(CONTRACTS_ROOT)
    collector = Collector()
    invalid = generation_spec(duration_seconds=9)
    terminal = generate(worker, collector, output, spec=invalid)
    assert terminal["payload"]["code"] == "invalid_input"
    assert not output.exists()

    collector = Collector()
    valid = generation_spec()
    terminal = generate(worker, collector, output, spec=valid)
    assert terminal["payload"]["code"] == "model_not_loaded"
    assert not output.exists()

    collector = Collector()
    load_mock(worker, collector)
    unsupported = generation_spec(duration_seconds=31)
    terminal = generate(worker, collector, output, spec=unsupported)
    assert terminal["payload"]["code"] == "unsupported_control"
    assert not output.exists()


def test_server_bounds_messages_and_continues_with_next_envelope() -> None:
    """Discard an oversized line and safely process the following health request."""
    health = {
        "protocol_version": PROTOCOL_VERSION,
        "request_id": "health-after-oversize",
        "operation": "health",
        "payload": {},
    }
    input_stream = BytesIO(
        b"x" * (MAX_MESSAGE_BYTES + 1)
        + b"\n"
        + json.dumps(health, separators=(",", ":")).encode()
        + b"\n"
    )
    output_stream = BytesIO()
    assert serve(input_stream, output_stream, contracts_root=CONTRACTS_ROOT) == 0
    responses = [json.loads(line) for line in output_stream.getvalue().splitlines()]
    assert responses[0]["payload"]["code"] == "message_too_large"
    assert responses[1]["request_id"] == "health-after-oversize"
    assert responses[1]["payload"]["ready"] is True


def test_server_eof_cancels_and_drains_active_generation(tmp_path: Path) -> None:
    """Treat a closed host channel as cooperative shutdown, not an orphaned job."""
    envelopes = [
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "load-before-eof",
            "operation": "load_model",
            "payload": {
                "adapter": {"id": MOCK_ADAPTER_ID, "version": MOCK_ADAPTER_VERSION},
                "model": {
                    "id": MOCK_MODEL_ID,
                    "revision": MOCK_MODEL_REVISION,
                    "artifact_hash": MOCK_MODEL_HASH,
                },
            },
        },
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": "generate-before-eof",
            "operation": "generate",
            "payload": {
                "spec": generation_spec(),
                "output_directory": str(tmp_path),
                "simulation": {"step_delay_ms": 250},
            },
        },
    ]
    input_stream = BytesIO(
        b"".join(
            json.dumps(envelope, separators=(",", ":")).encode() + b"\n"
            for envelope in envelopes
        )
    )
    output_stream = BytesIO()
    assert serve(input_stream, output_stream, contracts_root=CONTRACTS_ROOT) == 0
    responses = [json.loads(line) for line in output_stream.getvalue().splitlines()]
    terminal = [
        value
        for value in responses
        if value["request_id"] == "generate-before-eof" and value["kind"] == "result"
    ]
    assert terminal[0]["payload"]["status"] == "cancelled"
    assert not list(tmp_path.glob("*.part"))
    assert not list(tmp_path.glob("*.wav"))


def test_unexpected_worker_failure_is_classified_without_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Convert an unexpected adapter exception to one generic internal error."""
    worker = MockGenerationWorker(CONTRACTS_ROOT)
    collector = Collector()

    def fail_without_exposure(*_arguments: object) -> None:
        raise RuntimeError

    monkeypatch.setattr(worker, "_health", fail_without_exposure)
    worker.process(request("health-failure", Operation.HEALTH, {}), collector.emit)
    terminal = collector.terminal("health-failure")
    assert terminal["payload"] == {
        "code": "internal_error",
        "message": "worker operation failed internally",
        "retryable": False,
    }


def test_installed_module_entrypoint_processes_ndjson() -> None:
    """Prove the packaged worker is executable as a real local process."""
    envelope = {
        "protocol_version": PROTOCOL_VERSION,
        "request_id": "health-process",
        "operation": "health",
        "payload": {},
    }
    completed = subprocess.run(
        [sys.executable, "-m", "antidote_generation"],
        input=json.dumps(envelope).encode() + b"\n",
        capture_output=True,
        check=True,
        timeout=5,
    )
    response_value = json.loads(completed.stdout)
    assert response_value["request_id"] == "health-process"
    assert response_value["payload"]["ready"] is True
    assert completed.stderr == b""
