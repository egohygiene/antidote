#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Expose the project-owned research-paper build contract to any task runner."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]
REPRODUCIBLE_ARTIFACTS = (
    Path("paper.pdf"),
    Path("web/index.html"),
    Path("provenance.json"),
)


def run(command: list[str]) -> None:
    """Run one checked command from the project build-kit root."""
    print("+ " + " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def resolve(value: str) -> Path:
    """Resolve a user path relative to the build-kit root."""
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def resolve_project(value: str) -> Path:
    """Resolve the initialized project or the profile reference fixture."""
    if value != "auto":
        return resolve(value)
    if (ROOT / "beacon-project.toml").is_file():
        return ROOT
    return ROOT / "examples" / "reference-paper"


def build(project: Path, output: Path, theme: str, python: str) -> None:
    """Build all governed research-paper artifacts."""
    run(
        [
            python,
            str(ROOT / "scripts" / "build.py"),
            f"--project={project}",
            f"--output={output}",
            f"--theme={theme}",
        ]
    )


def validate(
    project: Path,
    output: Path,
    theme: str,
    python: str,
    *,
    check_external_links: bool = False,
) -> None:
    """Validate source, rendered output, and the independent arXiv archive."""
    command = [
        python,
        str(ROOT / "scripts" / "check.py"),
        f"--project={project}",
        f"--build-dir={output}",
        f"--theme={theme}",
        "--compile-arxiv",
    ]
    if check_external_links:
        command.append("--check-external-links")
    run(command)


def compare_file(first: Path, second: Path) -> None:
    """Fail when two expected deterministic artifacts differ."""
    if first.read_bytes() != second.read_bytes():
        raise RuntimeError(f"reproducibility mismatch: {first.name}")


def verify_reproducibility(project: Path, theme: str, python: str) -> None:
    """Build twice in clean directories and compare governed artifacts."""
    with tempfile.TemporaryDirectory(prefix="beacon-research-paper-") as temporary:
        temporary_root = Path(temporary)
        first = temporary_root / "first"
        second = temporary_root / "second"
        build(project, first, theme, python)
        build(project, second, theme, python)
        for relative in REPRODUCIBLE_ARTIFACTS:
            compare_file(first / relative, second / relative)
        first_archives = sorted((first / "arxiv").glob("*.tar.gz"))
        second_archives = sorted((second / "arxiv").glob("*.tar.gz"))
        if len(first_archives) != 1 or len(second_archives) != 1:
            raise RuntimeError("expected exactly one arXiv archive per build")
        compare_file(first_archives[0], second_archives[0])
    print("PASS reproducible PDF, web, provenance, and arXiv-source outputs.")


def bootstrap_check(theme: str, python: str) -> None:
    """Prove the profile initializer emits a self-contained project."""
    initializer = ROOT / "scripts" / "bootstrap.py"
    if not initializer.is_file() or not (ROOT / "scaffold").is_dir():
        print("SKIP bootstrap-check is only applicable to the Beacon profile checkout.")
        return
    with tempfile.TemporaryDirectory(prefix="beacon-research-bootstrap-") as temporary:
        temporary_root = Path(temporary)
        project = temporary_root / "project"
        output = temporary_root / "build"
        run(
            [
                python,
                str(initializer),
                f"--destination={project}",
                "--title=Bootstrap smoke paper",
                "--author=Beacon Maintainers",
                "--project-id=bootstrap-smoke",
                f"--theme={theme}",
            ]
        )
        build(project, output, theme, python)
        validate(project, output, theme, python)
    print("PASS standalone project bootstrap.")


def verify_inventory(python: str) -> None:
    """Verify the byte-preserved Empathy migration inventory."""
    run([python, str(ROOT / "scripts" / "check_source_inventory.py")])


def run_tests(python: str) -> None:
    """Run Antidote-owned publication contract tests."""
    run(
        [
            python,
            "-m",
            "unittest",
            "discover",
            "--start-directory=tests",
            "--pattern=test_*.py",
            "--verbose",
        ]
    )


def run_mvp(command: str, python: str) -> None:
    """Run one application-foundation command through the MVP task driver."""
    run(
        [
            python,
            str(ROOT / "scripts" / "mvp.py"),
            command,
            f"--python={python}",
        ]
    )


def build_site_suite(
    build_directory: Path,
    holon_source: Path,
    destination: Path,
    python: str,
) -> None:
    """Build the exact-pinned Holon surfaces for one Antidote revision."""
    provenance = json.loads(
        (build_directory / "provenance.json").read_text(encoding="utf-8")
    )
    with (ROOT / "beacon-project.toml").open("rb") as stream:
        paper_version = tomllib.load(stream)["paper"]["version"]
    run(
        [
            python,
            str(ROOT / "scripts" / "build_site_suite.py"),
            f"--repository-root={ROOT}",
            f"--holon-source={holon_source}",
            f"--output={destination}",
            f"--source-revision={provenance['source_revision']}",
            f"--paper-version={paper_version}",
        ]
    )


def invoke_site_staging(
    build: Path, site_suite: Path, destination: Path, python: str
) -> None:
    """Stage one complete site tree from an already validated paper build."""
    run(
        [
            python,
            str(ROOT / "scripts" / "stage_pages.py"),
            f"--build-dir={build}",
            f"--site-suite-dir={site_suite}",
            f"--output-dir={destination}",
        ]
    )


def verify_site_reproducibility(
    build: Path, site_suite: Path, python: str
) -> None:
    """Stage twice and require byte-identical route and integrity trees."""
    with tempfile.TemporaryDirectory(
        prefix=".antidote-pages-", dir=ROOT
    ) as temporary:
        temporary_root = Path(temporary)
        first = temporary_root / "first"
        second = temporary_root / "second"
        invoke_site_staging(build, site_suite, first, python)
        invoke_site_staging(build, site_suite, second, python)
        first_files = {
            path.relative_to(first) for path in first.rglob("*") if path.is_file()
        }
        second_files = {
            path.relative_to(second) for path in second.rglob("*") if path.is_file()
        }
        if first_files != second_files:
            raise RuntimeError("site reproducibility file inventory mismatch")
        for relative in sorted(first_files):
            compare_file(first / relative, second / relative)
    print("PASS reproducible Pages routes, manifests, and checksum inventory.")


def stage_site(
    project: Path,
    output: Path,
    theme: str,
    python: str,
    holon_source: Path | None,
) -> None:
    """Build and stage the Antidote-owned GitHub Pages projection."""
    if holon_source is None:
        raise ValueError(
            "site commands require --holon-source pointing to the exact pinned checkout"
        )
    build(project, output, theme, python)
    validate(project, output, theme, python)
    with tempfile.TemporaryDirectory(
        prefix=".antidote-pages-", dir=ROOT
    ) as temporary:
        site_suite = Path(temporary) / "site-suite"
        build_site_suite(output, holon_source, site_suite, python)
        verify_site_reproducibility(output, site_suite, python)
        invoke_site_staging(output, site_suite, ROOT / "_site", python)


def preview_site(
    project: Path,
    output: Path,
    theme: str,
    python: str,
    holon_source: Path | None,
    host: str,
    port: int,
) -> None:
    """Stage the governed site and serve that exact tree for local review."""
    if not 1 <= port <= 65535:
        raise ValueError(f"preview port is outside the valid range: {port}")
    stage_site(project, output, theme, python, holon_source)
    print(f"Previewing the staged publication at http://{host}:{port}/")
    run(
        [
            python,
            "-m",
            "http.server",
            str(port),
            "--bind",
            host,
            "--directory",
            str(ROOT / "_site"),
        ]
    )


def verify_live_publication(
    python: str, base_url: str, expected_revision: str
) -> None:
    """Verify that the canonical Pages routes expose one merged revision."""
    command = [python, str(ROOT / "scripts" / "verify_live_publication.py")]
    if base_url:
        command.append(f"--base-url={base_url}")
    if expected_revision:
        command.append(f"--expected-revision={expected_revision}")
    run(command)


def check_all(project: Path, output: Path, python: str) -> None:
    """Validate both governed theme projections and the source inventory."""
    build_root = output.parent
    for theme in ("neutral", "egohygiene"):
        themed_output = build_root / theme
        build(project, themed_output, theme, python)
        validate(project, themed_output, theme, python)
        verify_reproducibility(project, theme, python)
    verify_inventory(python)


def clean(output: Path) -> None:
    """Remove only the selected generated output directory."""
    if output in {Path("/"), ROOT} or ROOT not in output.parents:
        raise RuntimeError(f"refusing unsafe clean target: {output}")
    shutil.rmtree(output, ignore_errors=True)


def parse_arguments() -> argparse.Namespace:
    """Parse the stable project task interface."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=(
            "build",
            "bootstrap-check",
            "check",
            "check-all",
            "check-content",
            "check-links",
            "check-site",
            "clean",
            "inventory",
            "mvp-bootstrap",
            "mvp-check",
            "mvp-contracts",
            "mvp-contracts-check",
            "mvp-format",
            "mvp-lint",
            "mvp-test",
            "live-check",
            "preview",
            "reproducibility",
            "site",
            "test",
        ),
    )
    parser.add_argument("--project", default="auto")
    parser.add_argument("--build-dir", default="build/neutral")
    parser.add_argument("--theme", choices=("neutral", "egohygiene"), default="neutral")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--preview-host", default="127.0.0.1")
    parser.add_argument("--preview-port", type=int, default=8000)
    parser.add_argument("--base-url", default="")
    parser.add_argument("--expected-revision", default="")
    parser.add_argument("--holon-source", default="")
    return parser.parse_args()


def main() -> int:
    """Dispatch one research-paper project task."""
    arguments = parse_arguments()
    project = resolve_project(arguments.project)
    output = resolve(arguments.build_dir)
    holon_source = resolve(arguments.holon_source) if arguments.holon_source else None

    if arguments.command == "build":
        build(project, output, arguments.theme, arguments.python)
    elif arguments.command == "check-all":
        check_all(project, output, arguments.python)
    elif arguments.command == "check-content":
        build(project, output, arguments.theme, arguments.python)
        validate(project, output, arguments.theme, arguments.python)
    elif arguments.command == "check-links":
        build(project, output, arguments.theme, arguments.python)
        validate(
            project,
            output,
            arguments.theme,
            arguments.python,
            check_external_links=True,
        )
    elif arguments.command == "reproducibility":
        verify_reproducibility(project, arguments.theme, arguments.python)
    elif arguments.command == "bootstrap-check":
        bootstrap_check(arguments.theme, arguments.python)
    elif arguments.command == "inventory":
        verify_inventory(arguments.python)
    elif arguments.command.startswith("mvp-"):
        run_mvp(arguments.command.removeprefix("mvp-"), arguments.python)
    elif arguments.command in {"site", "check-site"}:
        stage_site(
            project,
            output,
            arguments.theme,
            arguments.python,
            holon_source,
        )
        if arguments.command == "check-site":
            run_tests(arguments.python)
    elif arguments.command == "preview":
        preview_site(
            project,
            output,
            arguments.theme,
            arguments.python,
            holon_source,
            arguments.preview_host,
            arguments.preview_port,
        )
    elif arguments.command == "live-check":
        verify_live_publication(
            arguments.python,
            arguments.base_url,
            arguments.expected_revision,
        )
    elif arguments.command == "test":
        run_tests(arguments.python)
    elif arguments.command == "check":
        build(project, output, arguments.theme, arguments.python)
        validate(project, output, arguments.theme, arguments.python)
        verify_reproducibility(project, arguments.theme, arguments.python)
    elif arguments.command == "clean":
        clean(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
