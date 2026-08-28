# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Deterministic, dependency-free synthetic WAV generation and analysis."""

from __future__ import annotations

import hashlib
import struct
import wave
from dataclasses import dataclass
from time import monotonic, sleep
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from threading import Event

MAX_ARTIFACT_BYTES = 64 * 1024 * 1024
CHUNK_FRAMES = 4_000
SAMPLE_WIDTH_BYTES = 2


class MockAudioError(ValueError):
    """A deliberately detail-free synthetic audio validation failure."""


@dataclass(frozen=True, slots=True)
class AudioArtifact:
    """One locally realized synthetic audio object."""

    path: Path
    sha256: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class SynthesisOutcome:
    """The classified result of a mock synthesis attempt."""

    status: str
    artifact: AudioArtifact | None
    elapsed_ms: int


@dataclass(frozen=True, slots=True)
class SynthesisRequest:
    """Validated controls for one deterministic synthesis attempt."""

    target: Path
    duration_seconds: int
    sample_rate_hz: int
    channels: int
    seed: int
    mode: str = "normal"
    step_delay_ms: int = 0


def sha256_file(path: Path) -> str:
    """Hash one bounded local artifact."""
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(64 * 1024):
            size += len(chunk)
            if size > MAX_ARTIFACT_BYTES:
                raise MockAudioError
            digest.update(chunk)
    return digest.hexdigest()


def _pcm_chunk(
    start_frame: int,
    frame_count: int,
    sample_rate_hz: int,
    channels: int,
    seed: int,
) -> bytes:
    """Create deterministic little-endian PCM frames from public parameters."""
    frequency_hz = 180 + (seed % 241)
    amplitude = 8_192
    fade_frames = max(1, sample_rate_hz // 20)
    samples = bytearray()
    for frame in range(start_frame, start_frame + frame_count):
        cycle = (frame * frequency_hz * 4 * amplitude) // sample_rate_hz
        phase = cycle % (4 * amplitude)
        if phase < amplitude:
            value = phase
        elif phase < 3 * amplitude:
            value = 2 * amplitude - phase
        else:
            value = phase - 4 * amplitude
        value = value * min(frame, fade_frames) // fade_frames
        packed = struct.pack("<h", value)
        samples.extend(packed * channels)
    return bytes(samples)


def synthesize_wav(
    synthesis: SynthesisRequest,
    cancel: Event,
    progress: Callable[[float, int], None],
) -> SynthesisOutcome:
    """Write a deterministic WAV through a temporary file and classify its outcome."""
    started = monotonic()
    temporary = synthesis.target.with_suffix(synthesis.target.suffix + ".part")
    partial = synthesis.target.with_suffix(".partial.wav")
    temporary.parent.mkdir(parents=True, exist_ok=True)
    temporary.unlink(missing_ok=True)
    partial.unlink(missing_ok=True)

    total_frames = synthesis.duration_seconds * synthesis.sample_rate_hz
    stop_frame = total_frames if synthesis.mode == "normal" else total_frames // 2
    written = 0
    try:
        with wave.open(str(temporary), "wb") as output:
            output.setnchannels(synthesis.channels)
            output.setsampwidth(SAMPLE_WIDTH_BYTES)
            output.setframerate(synthesis.sample_rate_hz)
            while written < stop_frame:
                if cancel.is_set():
                    return SynthesisOutcome(
                        "cancelled", None, round((monotonic() - started) * 1_000)
                    )
                count = min(CHUNK_FRAMES, stop_frame - written)
                output.writeframesraw(
                    _pcm_chunk(
                        written,
                        count,
                        synthesis.sample_rate_hz,
                        synthesis.channels,
                        synthesis.seed,
                    )
                )
                written += count
                progress(written / total_frames, round((monotonic() - started) * 1_000))
                if synthesis.step_delay_ms:
                    sleep(synthesis.step_delay_ms / 1_000)

        elapsed_ms = round((monotonic() - started) * 1_000)
        if cancel.is_set():
            return SynthesisOutcome("cancelled", None, elapsed_ms)
        if synthesis.mode in {"timeout", "crash"}:
            return SynthesisOutcome(synthesis.mode, None, elapsed_ms)
        if synthesis.mode == "partial":
            temporary.replace(partial)
            return SynthesisOutcome(
                "partial",
                AudioArtifact(partial, sha256_file(partial), partial.stat().st_size),
                elapsed_ms,
            )
        temporary.replace(synthesis.target)
        return SynthesisOutcome(
            "generated",
            AudioArtifact(
                synthesis.target,
                sha256_file(synthesis.target),
                synthesis.target.stat().st_size,
            ),
            elapsed_ms,
        )
    finally:
        temporary.unlink(missing_ok=True)
        if cancel.is_set():
            partial.unlink(missing_ok=True)


def analyze_wav(path: Path) -> dict[str, Any]:
    """Measure declared, deterministic container and peak-amplitude features."""
    if path.stat().st_size > MAX_ARTIFACT_BYTES:
        raise MockAudioError
    with wave.open(str(path), "rb") as source:
        channels = source.getnchannels()
        sample_rate_hz = source.getframerate()
        frames = source.getnframes()
        if source.getsampwidth() != SAMPLE_WIDTH_BYTES:
            raise MockAudioError
        peak = 0
        while raw := source.readframes(CHUNK_FRAMES):
            for (sample,) in struct.iter_unpack("<h", raw):
                peak = max(peak, abs(sample))
    return {
        "duration_seconds": frames / sample_rate_hz,
        "sample_rate_hz": sample_rate_hz,
        "channels": channels,
        "peak_amplitude": peak / 32_767,
        "analyzer_versions": {"antidote.mock.wav": "1.0.0"},
    }


__all__ = [
    "AudioArtifact",
    "MockAudioError",
    "SynthesisOutcome",
    "SynthesisRequest",
    "analyze_wav",
    "sha256_file",
    "synthesize_wav",
]
