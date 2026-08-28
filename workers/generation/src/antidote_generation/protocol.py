# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Strict, source-text-safe envelopes for the model-worker NDJSON protocol."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

PROTOCOL_VERSION = "1.0.0"
MAX_MESSAGE_BYTES = 65_536
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class Operation(StrEnum):
    """Operations exposed by model-worker protocol v1."""

    HELLO = "hello"
    CAPABILITIES = "capabilities"
    LOAD_MODEL = "load_model"
    GENERATE = "generate"
    ANALYZE = "analyze"
    CANCEL = "cancel"
    HEALTH = "health"


class ErrorCode(StrEnum):
    """Stable protocol and mock-adapter failure classes."""

    INVALID_INPUT = "invalid_input"
    UNSUPPORTED_VERSION = "unsupported_version"
    UNKNOWN_OPERATION = "unknown_operation"
    MESSAGE_TOO_LARGE = "message_too_large"
    UNSUPPORTED_CONTROL = "unsupported_control"
    MODEL_NOT_LOADED = "model_not_loaded"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    PARTIAL_OUTPUT = "partial_output"
    WORKER_CRASH = "worker_crash"
    INTEGRITY_MISMATCH = "integrity_mismatch"
    INTERNAL_ERROR = "internal_error"


@dataclass(frozen=True, slots=True)
class Request:
    """One trusted request envelope."""

    request_id: str
    operation: Operation
    payload: dict[str, Any]


class ProtocolError(ValueError):
    """A classified failure that is safe to return across the process boundary."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        request_id: str | None = None,
        operation: str | None = None,
        retryable: bool = False,
    ) -> None:
        """Create a redacted protocol failure."""
        super().__init__(message)
        self.code = code
        self.safe_message = message
        self.request_id = request_id
        self.operation = operation
        self.retryable = retryable


class _DuplicateKeyError(ValueError):
    """Reject ambiguous JSON objects before trusting envelope fields."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError
        result[key] = value
    return result


def decode_request(raw_line: bytes) -> Request:
    """Decode and validate one size-bounded request without echoing its values."""
    if len(raw_line) > MAX_MESSAGE_BYTES:
        raise ProtocolError(
            ErrorCode.MESSAGE_TOO_LARGE,
            "request exceeds the protocol message-size limit",
        )
    if not raw_line.endswith(b"\n"):
        raise ProtocolError(
            ErrorCode.INVALID_INPUT,
            "request is not newline-delimited",
        )
    try:
        text = raw_line.decode("utf-8")
        value = json.loads(text, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, _DuplicateKeyError) as error:
        raise ProtocolError(
            ErrorCode.INVALID_INPUT,
            "request is not one unambiguous UTF-8 JSON object",
        ) from error
    if not isinstance(value, dict):
        raise ProtocolError(
            ErrorCode.INVALID_INPUT, "request envelope must be an object"
        )

    trusted_id = value.get("request_id")
    request_id = (
        trusted_id
        if isinstance(trusted_id, str) and REQUEST_ID_PATTERN.fullmatch(trusted_id)
        else None
    )
    trusted_operation = value.get("operation")
    operation_text = trusted_operation if isinstance(trusted_operation, str) else None

    if set(value) != {"protocol_version", "request_id", "operation", "payload"}:
        raise ProtocolError(
            ErrorCode.INVALID_INPUT,
            "request envelope fields are invalid",
            request_id=request_id,
            operation=operation_text,
        )
    if value["protocol_version"] != PROTOCOL_VERSION:
        raise ProtocolError(
            ErrorCode.UNSUPPORTED_VERSION,
            "protocol version is unsupported",
            request_id=request_id,
            operation=operation_text,
        )
    if request_id is None:
        raise ProtocolError(ErrorCode.INVALID_INPUT, "request ID is invalid")
    try:
        operation = Operation(value["operation"])
    except (TypeError, ValueError) as error:
        raise ProtocolError(
            ErrorCode.UNKNOWN_OPERATION,
            "operation is unsupported",
            request_id=request_id,
            operation=operation_text,
        ) from error
    if not isinstance(value["payload"], dict):
        raise ProtocolError(
            ErrorCode.INVALID_INPUT,
            "operation payload must be an object",
            request_id=request_id,
            operation=operation.value,
        )
    return Request(request_id, operation, value["payload"])


def response(
    request_id: str | None,
    operation: str | None,
    kind: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build one deterministic response envelope."""
    return {
        "protocol_version": PROTOCOL_VERSION,
        "request_id": request_id,
        "operation": operation,
        "kind": kind,
        "payload": payload,
    }


def error_response(error: ProtocolError) -> dict[str, Any]:
    """Convert a classified exception to a redacted wire response."""
    return response(
        error.request_id,
        error.operation,
        "error",
        {
            "code": error.code.value,
            "message": error.safe_message,
            "retryable": error.retryable,
        },
    )


def encode_response(value: dict[str, Any]) -> bytes:
    """Encode one response with stable key ordering and a newline delimiter."""
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("utf-8")


__all__ = [
    "MAX_MESSAGE_BYTES",
    "PROTOCOL_VERSION",
    "ErrorCode",
    "Operation",
    "ProtocolError",
    "Request",
    "decode_request",
    "encode_response",
    "error_response",
    "response",
]
