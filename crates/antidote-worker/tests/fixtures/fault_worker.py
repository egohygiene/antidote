# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Synthetic process-fault fixture for Rust supervisor integration tests."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

MODEL_HASH = "9d994d01452850f4f539b420486247d262b8a4a5afffefa85f333e334daa1c2e"


def emit(request: dict[str, Any], payload: dict[str, Any]) -> None:
    """Emit one protocol result for the current request."""
    value = {
        "protocol_version": "1.0.0",
        "request_id": request["request_id"],
        "operation": request["operation"],
        "kind": "result",
        "payload": payload,
    }
    sys.stdout.write(json.dumps(value, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def handle(request: dict[str, Any]) -> None:
    """Answer setup operations, then inject the selected generation fault."""
    operation = request["operation"]
    if operation == "hello":
        emit(
            request,
            {
                "worker": {
                    "id": "antidote-fault-fixture",
                    "version": "0.1.0",
                    "code_revision": "fixture-v1",
                },
                "selected_protocol_version": "1.0.0",
                "compatible_protocol_versions": ["1.0.0"],
            },
        )
    elif operation == "capabilities":
        emit(
            request,
            {
                "adapters": [
                    {
                        "id": "antidote.mock",
                        "version": "1.0.0",
                        "license": "MIT",
                        "models": [
                            {
                                "id": "synthetic-triangle",
                                "revision": "1",
                                "artifact_hash": MODEL_HASH,
                            }
                        ],
                        "controls": [
                            "channels",
                            "deterministic_seed",
                            "duration",
                            "sample_rate",
                        ],
                        "duration_seconds": {"minimum": 10, "maximum": 30},
                        "output_formats": ["wav"],
                        "sample_rate_hz": {"minimum": 8000, "maximum": 48000},
                        "channels": {"minimum": 1, "maximum": 2},
                        "hardware": ["synthetic-cpu"],
                        "restrictions": ["test-faults-only"],
                    }
                ],
                "device_class": "synthetic-cpu",
                "warnings": [],
            },
        )
    elif operation == "load_model":
        emit(
            request,
            {
                "adapter": {"id": "antidote.mock", "version": "1.0.0"},
                "model": {
                    "id": "synthetic-triangle",
                    "revision": "1",
                    "artifact_hash": MODEL_HASH,
                },
                "device_class": "synthetic-cpu",
                "memory_bytes": 0,
                "warnings": ["process-fault fixture"],
            },
        )
    elif operation == "health":
        emit(
            request,
            {
                "ready": True,
                "model_loaded": True,
                "active_jobs": 0,
                "device_class": "synthetic-cpu",
                "resources": {"network": False, "model_memory_bytes": 0},
            },
        )
    elif operation == "generate":
        mode = os.environ.get("ANTIDOTE_FAULT_MODE")
        if mode == "crash":
            raise SystemExit(73)
        if mode == "malformed":
            sys.stdout.write('{"protocol_version":"1.0.0","request_id":\n')
            sys.stdout.flush()
        elif mode == "escape":
            escaped = Path(request["payload"]["output_directory"]).parent / "escaped.wav"
            escaped.write_bytes(b"synthetic escape fixture")
            spec = request["payload"]["spec"]
            emit(
                request,
                {
                    "schema_version": "1.0.0",
                    "id": "fault-result-escape",
                    "generation_spec_id": spec["id"],
                    "status": "generated",
                    "adapter": spec["adapter"],
                    "model": {
                        "id": spec["model"]["id"],
                        "revision": spec["model"]["revision"],
                    },
                    "code_revision": "fixture-v1",
                    "device_class": "synthetic-cpu",
                    "elapsed_ms": 0,
                    "artifacts": [
                        {
                            "kind": "audio",
                            "path": str(escaped),
                            "sha256": hashlib.sha256(escaped.read_bytes()).hexdigest(),
                            "media_type": "audio/wav",
                            "size_bytes": escaped.stat().st_size,
                        }
                    ],
                    "warnings": ["synthetic path-escape fixture"],
                },
            )
        else:
            raise SystemExit(74)


def main() -> int:
    """Serve deterministic setup responses until a process fault is requested."""
    sys.stderr.write("SYNTHETIC-DIAGNOSTIC-MUST-NOT-BE-RETAINED\n")
    sys.stderr.flush()
    for line in sys.stdin:
        handle(json.loads(line))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
