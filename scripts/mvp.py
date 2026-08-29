#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Expose reproducible workspace and contract checks for the Antidote MVP."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = ROOT / "apps" / "desktop"
WORKER = ROOT / "workers" / "generation"


def executable(environment_name: str, default: str) -> str:
    """Resolve a configurable executable and fail with an actionable message."""
    value = os.environ.get(environment_name, default)
    if shutil.which(value) is None:
        raise RuntimeError(
            f"required executable {value!r} is unavailable; "
            "follow docs/getting-started.md"
        )
    return value


def run(command: list[str], *, cwd: Path = ROOT) -> None:
    """Run one checked command without shell interpolation."""
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def generate_contracts(python: str, *, check: bool) -> None:
    """Generate or verify all disposable language projections."""
    command = [python, str(ROOT / "scripts" / "generate_contracts.py")]
    if check:
        command.append("--check")
    run(command)


def bootstrap(python: str) -> None:
    """Restore every pinned language workspace without model downloads."""
    generate_contracts(python, check=True)
    pnpm = executable("PNPM", "pnpm")
    uv = executable("UV", "uv")
    cargo = executable("CARGO", "cargo")
    run([pnpm, "install", "--frozen-lockfile"])
    run(
        [
            uv,
            "sync",
            "--project",
            str(WORKER),
            "--locked",
            "--all-groups",
        ]
    )
    run([cargo, "fetch", "--locked"])


def contract_checks(python: str) -> None:
    """Validate drift and shared fixtures in every language boundary."""
    generate_contracts(python, check=True)
    cargo = executable("CARGO", "cargo")
    pnpm = executable("PNPM", "pnpm")
    uv = executable("UV", "uv")
    run([cargo, "test", "--locked", "--package", "antidote-contracts"])
    run(
        [
            pnpm,
            "--filter",
            "@egohygiene/antidote-desktop",
            "test:contracts",
        ]
    )
    run(
        [
            uv,
            "run",
            "--project",
            str(WORKER),
            "--locked",
            "pytest",
            "tests/test_contracts.py",
        ],
        cwd=WORKER,
    )


def format_checks() -> None:
    """Require deterministic formatting in each language workspace."""
    cargo = executable("CARGO", "cargo")
    pnpm = executable("PNPM", "pnpm")
    uv = executable("UV", "uv")
    run([cargo, "fmt", "--all", "--check"])
    run([pnpm, "format:check"])
    run(
        [
            uv,
            "run",
            "--project",
            str(WORKER),
            "--locked",
            "ruff",
            "format",
            "--check",
            "--exclude=workers/generation/src/antidote_generation/generated/contracts.py",
            str(ROOT / "scripts" / "generate_contracts.py"),
            str(ROOT / "scripts" / "mvp.py"),
            str(WORKER),
        ]
    )


def lint_checks() -> None:
    """Run static analysis across all MVP workspaces."""
    cargo = executable("CARGO", "cargo")
    pnpm = executable("PNPM", "pnpm")
    uv = executable("UV", "uv")
    run(
        [
            cargo,
            "clippy",
            "--workspace",
            "--all-targets",
            "--all-features",
            "--locked",
            "--",
            "-D",
            "warnings",
        ]
    )
    run([pnpm, "lint"])
    run(
        [
            uv,
            "run",
            "--project",
            str(WORKER),
            "--locked",
            "ruff",
            "check",
            str(ROOT / "scripts" / "generate_contracts.py"),
            str(ROOT / "scripts" / "mvp.py"),
            str(WORKER),
        ]
    )


def tests() -> None:
    """Build and test the scaffold without a model or private input."""
    cargo = executable("CARGO", "cargo")
    pnpm = executable("PNPM", "pnpm")
    uv = executable("UV", "uv")
    run([cargo, "test", "--workspace", "--all-features", "--locked"])
    run([pnpm, "typecheck"])
    run([pnpm, "build"])
    run([pnpm, "test"])
    run(
        [
            uv,
            "run",
            "--project",
            str(WORKER),
            "--locked",
            "pytest",
        ],
        cwd=WORKER,
    )


def check(python: str) -> None:
    """Run the complete application-foundation quality gate."""
    contract_checks(python)
    format_checks()
    lint_checks()
    tests()


def parse_arguments() -> argparse.Namespace:
    """Parse the stable MVP task interface."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=(
            "bootstrap",
            "check",
            "contracts",
            "contracts-check",
            "format",
            "lint",
            "test",
        ),
    )
    parser.add_argument("--python", default=sys.executable)
    return parser.parse_args()


def main() -> int:
    """Dispatch one MVP workspace task."""
    arguments = parse_arguments()
    if arguments.command == "bootstrap":
        bootstrap(arguments.python)
    elif arguments.command == "contracts":
        generate_contracts(arguments.python, check=False)
    elif arguments.command == "contracts-check":
        contract_checks(arguments.python)
    elif arguments.command == "format":
        format_checks()
    elif arguments.command == "lint":
        lint_checks()
    elif arguments.command == "test":
        tests()
    elif arguments.command == "check":
        check(arguments.python)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"ERROR {error}", file=sys.stderr)
        raise SystemExit(1) from error
