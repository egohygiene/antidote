#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Resolve the immutable Beacon dependency without vendoring its source."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "dependencies" / "beacon.lock.toml"


def run(command: list[str], *, cwd: Path | None = None) -> str:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", required=True)
    arguments = parser.parse_args()

    with LOCK.open("rb") as stream:
        lock = tomllib.load(stream)

    destination = Path(arguments.destination).expanduser()
    if not destination.is_absolute():
        destination = (ROOT / destination).resolve()
    revision = lock["revision"]
    profile = lock["profile"]

    if destination.exists():
        actual = run(["git", "rev-parse", "HEAD"], cwd=destination)
        if actual != revision:
            raise SystemExit(
                f"Beacon checkout mismatch at {destination}: {actual} != {revision}"
            )
        if not (destination / profile / "beacon-template.toml").is_file():
            raise SystemExit(f"Beacon profile is missing from {destination}: {profile}")
        print(f"PASS Beacon {revision} already resolved at {destination}")
        return 0

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="beacon-resolve-", dir=destination.parent
    ) as temporary:
        candidate = Path(temporary) / "checkout"
        run(
            [
                "git",
                "clone",
                "--filter=blob:none",
                "--no-checkout",
                lock["repository"],
                str(candidate),
            ]
        )
        run(["git", "checkout", "--detach", revision], cwd=candidate)
        if not (candidate / profile / "beacon-template.toml").is_file():
            raise SystemExit(f"Pinned Beacon profile is missing: {profile}")
        candidate.rename(destination)

    print(f"PASS resolved Beacon {revision} at {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
