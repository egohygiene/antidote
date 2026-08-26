#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Invoke the optional pinned Beacon control plane for Antidote."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "dependencies" / "beacon.lock.toml"


def run(command: list[str]) -> None:
    """Run one checked command from the Antidote repository root."""
    print("+ " + " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    """Resolve the immutable Beacon checkout and dispatch one CLI action."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=("validate", "inspect", "doctor", "plan", "build", "package"),
    )
    parser.add_argument(
        "--beacon-root",
        default=os.environ.get("BEACON_ROOT", str(ROOT / ".cache" / "beacon")),
    )
    arguments, passthrough = parser.parse_known_args()

    if shutil.which("cargo") is None:
        raise SystemExit("cargo is required only for optional Beacon CLI commands")

    beacon_root = Path(arguments.beacon_root).expanduser().resolve()
    run(
        [
            sys.executable,
            str(ROOT / "scripts" / "resolve_beacon.py"),
            f"--destination={beacon_root}",
        ]
    )
    with LOCK.open("rb") as stream:
        lock = tomllib.load(stream)

    beacon_arguments = [
        "cargo",
        f"+{lock['rust_toolchain']}",
        "run",
        "--quiet",
        "--locked",
        f"--manifest-path={beacon_root / 'Cargo.toml'}",
        "--",
    ]
    if arguments.action in {"validate", "inspect", "doctor"}:
        beacon_arguments.extend([arguments.action, "research-paper"])
    else:
        beacon_arguments.extend([arguments.action, str(ROOT)])
    beacon_arguments.extend(passthrough)
    run(beacon_arguments)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
