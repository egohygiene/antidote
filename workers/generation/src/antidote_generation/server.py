# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Concurrent NDJSON process boundary for the Antidote generation worker."""

from __future__ import annotations

import sys
from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from io import BufferedReader, BufferedWriter

from antidote_generation.protocol import (
    MAX_MESSAGE_BYTES,
    ErrorCode,
    ProtocolError,
    decode_request,
    encode_response,
    error_response,
)
from antidote_generation.worker import MockGenerationWorker


class NdjsonWriter:
    """Serialize worker-thread responses onto one stdout stream."""

    def __init__(self, stream: BufferedWriter) -> None:
        """Wrap a binary stream with a process-local write lock."""
        self._stream = stream
        self._lock = Lock()

    def emit(self, value: dict[str, Any]) -> None:
        """Write and flush exactly one protocol response line."""
        encoded = encode_response(value)
        with self._lock:
            self._stream.write(encoded)
            self._stream.flush()


def _discard_oversized_remainder(stream: BufferedReader, first: bytes) -> None:
    if first.endswith(b"\n"):
        return
    while remainder := stream.readline(MAX_MESSAGE_BYTES + 1):
        if remainder.endswith(b"\n"):
            return


def serve(
    input_stream: BufferedReader,
    output_stream: BufferedWriter,
    *,
    contracts_root: Path,
) -> int:
    """Serve requests until EOF, then drain active synthetic work."""
    writer = NdjsonWriter(output_stream)
    worker = MockGenerationWorker(contracts_root)
    while line := input_stream.readline(MAX_MESSAGE_BYTES + 1):
        if len(line) > MAX_MESSAGE_BYTES:
            _discard_oversized_remainder(input_stream, line)
            writer.emit(
                error_response(
                    ProtocolError(
                        ErrorCode.MESSAGE_TOO_LARGE,
                        "request exceeds the protocol message-size limit",
                    )
                )
            )
            continue
        try:
            request = decode_request(line)
        except ProtocolError as error:
            writer.emit(error_response(error))
            continue
        worker.process(request, writer.emit)
    worker.shutdown()
    return 0


def main() -> int:
    """Run the repository-local worker over standard input and output."""
    repository_root = Path(__file__).resolve().parents[4]
    return serve(
        sys.stdin.buffer,
        sys.stdout.buffer,
        contracts_root=repository_root / "contracts",
    )


__all__ = ["NdjsonWriter", "main", "serve"]
