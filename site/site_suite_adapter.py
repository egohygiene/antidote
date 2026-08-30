#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Run a materialized Holon suite through Antidote's bounded build adapter."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import subprocess
import sys


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", type=Path, required=True)
    parser.add_argument("--corepack-executable", default="corepack")
    parser.add_argument("command", choices=("build", "check", "verify"))
    return parser.parse_args()


def load_suite(site_root: Path):
    source = site_root.resolve() / "site_suite.py"
    specification = importlib.util.spec_from_file_location(
        "antidote_materialized_site_suite", source
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("unable to load the materialized Holon site suite")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def apply_adapter(suite, corepack: str) -> None:
    """Change only the package-manager entrypoint left to the consumer."""
    original_run = suite.run

    def run(command: list[str]) -> None:
        if command and command[0] == "pnpm":
            command = [corepack, "pnpm", *command[1:]]
        original_run(command)

    suite.run = run


def main() -> int:
    arguments = parse_arguments()
    try:
        suite = load_suite(arguments.site_root)
        apply_adapter(suite, arguments.corepack_executable)
        if arguments.command == "check":
            suite.check()
        elif arguments.command == "build":
            suite.build()
        else:
            suite.verify()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
