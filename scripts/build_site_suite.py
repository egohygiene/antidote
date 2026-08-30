#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Build Antidote's deterministic exact-pinned Holon site-suite input."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Iterable


LOCK_PATH = Path("publication/antidote-site-suite.lock.json")
CONTENT_PATH = Path("publication/antidote-site.content.json")
SITE_PATH = Path("site")
LOCK_SCHEMA = "antidote.holon-site-suite-lock/v1"
CONTENT_SCHEMA = "antidote.site-content/v1"
COMMIT = re.compile(r"^[0-9a-f]{40}$")
PROFILE_KEYS = ("launchkit", "zensical", "siteSuite")
RESERVED_COMPOSITION_PATHS = (
    "paper",
    "magazine",
    "downloads",
    "antidote.pdf",
    "publication.json",
    "site.json",
    "provenance.json",
    "SHA256SUMS",
)


class BuildError(RuntimeError):
    """Raised when reviewed site inputs cannot produce a verified artifact."""


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--holon-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--paper-version", required=True)
    parser.add_argument("--uv-executable", default="uv")
    parser.add_argument("--corepack-executable", default="corepack")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BuildError(f"unable to read JSON input {path}: {error}") from error
    if not isinstance(value, dict):
        raise BuildError(f"JSON input must be an object: {path}")
    return value


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git_blob(path: Path) -> str:
    content = path.read_bytes()
    return hashlib.sha1(
        f"blob {len(content)}\0".encode() + content,
        usedforsecurity=False,
    ).hexdigest()


def run(arguments: list[str], *, cwd: Path) -> None:
    print("+ " + " ".join(arguments))
    try:
        subprocess.run(arguments, cwd=cwd, check=True)
    except (OSError, subprocess.CalledProcessError) as error:
        raise BuildError(f"command failed in {cwd}: {' '.join(arguments)}") from error


def verify_inventory(
    blueprint: dict[str, Any], source_root: Path, label: str
) -> list[Path]:
    reviewed: list[Path] = []
    for record in blueprint.get("files", []):
        if not isinstance(record, dict):
            raise BuildError(f"Holon {label} file inventory is malformed")
        source = source_root / str(record.get("path"))
        if not source.is_file() or sha256_file(source) != record.get("sha256"):
            raise BuildError(
                f"Holon {label} source inventory drifted: {record.get('path')}"
            )
        reviewed.append(source)
    if not reviewed:
        raise BuildError(f"Holon {label} file inventory is empty")
    return reviewed


def verify_holon_source(
    holon_source: Path, lock: dict[str, Any]
) -> tuple[dict[str, Any], list[Path]]:
    holon = lock.get("holon")
    if not isinstance(holon, dict) or COMMIT.fullmatch(str(holon.get("commit"))) is None:
        raise BuildError("site-suite lock lacks one immutable Holon commit")
    try:
        actual_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=holon_source, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise BuildError("Holon source must be an exact Git checkout") from error
    if actual_commit != holon["commit"]:
        raise BuildError(
            "Holon checkout does not match the accepted site-suite commit: "
            f"expected={holon['commit']}, actual={actual_commit}"
        )

    profiles = holon.get("profiles")
    if not isinstance(profiles, dict) or set(profiles) != set(PROFILE_KEYS):
        raise BuildError("site-suite lock must define exactly three Holon profiles")
    roots = {
        "launchkit": holon_source / "blueprints/launchkit/files",
        "zensical": holon_source / "blueprints/zensical/files",
        "siteSuite": holon_source / "blueprints/site-suite/files",
    }
    blueprints: dict[str, dict[str, Any]] = {}
    reviewed: list[Path] = []
    for key in PROFILE_KEYS:
        pin = profiles[key]
        if not isinstance(pin, dict):
            raise BuildError(f"Holon {key} lock record is malformed")
        path = holon_source / str(pin.get("path"))
        blueprint = read_json(path)
        if git_blob(path) != pin.get("gitBlob"):
            raise BuildError(f"Holon {key} blueprint Git blob drifted")
        if sha256_file(path) != pin.get("sha256"):
            raise BuildError(f"Holon {key} blueprint SHA-256 drifted")
        if blueprint.get("version") != pin.get("version"):
            raise BuildError(f"Holon {key} profile version drifted")
        blueprints[key] = blueprint
        reviewed.append(path)
        reviewed.extend(verify_inventory(blueprint, roots[key], key))

    launchkit = blueprints["launchkit"]
    base_path = holon_source / str(launchkit.get("extends", {}).get("profile"))
    if (
        not base_path.is_file()
        or sha256_file(base_path) != launchkit.get("extends", {}).get("sha256")
    ):
        raise BuildError("Holon LaunchKit base profile digest drifted")
    base = read_json(base_path)
    reviewed.append(base_path)
    reviewed.extend(
        verify_inventory(
            base, holon_source / "blueprints/react-vite/files", "react-vite"
        )
    )

    suite = blueprints["siteSuite"]
    if suite.get("schema") != "holon.site-suite-profile/v1":
        raise BuildError("Holon site-suite profile identity drifted")
    variant = suite.get("variants", {}).get("launchkit")
    expected_overlays = [
        "blueprints/launchkit/files",
        "blueprints/zensical/files",
        "blueprints/site-suite/files",
    ]
    if not isinstance(variant, dict) or variant.get("render_overlays") != expected_overlays:
        raise BuildError("Holon LaunchKit site-suite composition order drifted")
    for profile in suite.get("profiles", {}).values():
        if not isinstance(profile, dict):
            raise BuildError("Holon site-suite profile references are malformed")
        path = holon_source / str(profile.get("path"))
        if not path.is_file() or sha256_file(path) != profile.get("sha256"):
            raise BuildError(f"Holon site-suite profile digest drifted: {path}")

    python_lock = holon_source / "blueprints/zensical/files/site-docs/requirements.lock.txt"
    lock_text = python_lock.read_text(encoding="utf-8")
    if "zensical==0.0.57" not in lock_text or "--hash=sha256:" not in lock_text:
        raise BuildError("Holon does not carry the accepted hash-locked Zensical graph")
    reviewed.extend(
        [
            holon_source / "schemas/launchkit-content.v1.schema.json",
            holon_source / "schemas/site-suite-content.v1.schema.json",
            holon_source / "tools/materialization/common.py",
            holon_source / "tools/launchkit_blueprint.py",
            holon_source / "tools/site_suite_blueprint.py",
        ]
    )
    return suite, reviewed


def verify_content(
    holon_source: Path, launchkit: dict[str, Any], suite: dict[str, Any]
) -> None:
    tools_path = (holon_source / "tools").resolve()
    sys.path.insert(0, str(tools_path))
    try:
        launchkit_module = importlib.import_module("launchkit_blueprint")
        suite_module = importlib.import_module("site_suite_blueprint")
        errors = launchkit_module.validate_content(launchkit, "launchkit_content")
        errors.extend(suite_module.validate_site_content(suite, "site_suite_content"))
    finally:
        sys.path.pop(0)
    if errors:
        raise BuildError("compiled Holon content is invalid: " + "; ".join(errors))


def render_holon_suite(
    holon_source: Path,
    suite: dict[str, Any],
    resolved_manifest: dict[str, Any],
    target: Path,
) -> None:
    tools_path = (holon_source / "tools").resolve()
    sys.path.insert(0, str(tools_path))
    try:
        common = importlib.import_module("materialization.common")
        render_source_bytes = common.render_source_bytes
    finally:
        sys.path.pop(0)
    variant = suite["variants"]["launchkit"]

    def apply(source_root: Path) -> None:
        for source in sorted(source_root.rglob("*")):
            if source.is_symlink():
                raise BuildError(f"Holon source contains a symlink: {source}")
            if not source.is_file():
                continue
            relative = source.relative_to(source_root)
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(
                render_source_bytes(
                    source.read_bytes(), resolved_manifest, relative.as_posix()
                )
            )

    apply(holon_source / variant["render_source"])
    for overlay in variant["render_overlays"]:
        apply(holon_source / overlay)


def stub_html(title: str) -> bytes:
    return (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<title>{title}</title></head><body><main><h1>{title}</h1>"
        "</main></body></html>\n"
    ).encode()


def apply_consumer_inputs(
    repository_root: Path, site: Path, content: dict[str, Any]
) -> list[Path]:
    assets = content["assets"]
    public_assets = site / "public/assets"
    public_assets.mkdir(parents=True, exist_ok=True)
    selected: list[Path] = []
    for key in ("favicon", "socialImage"):
        source = repository_root / str(assets[key])
        if not source.is_file():
            raise BuildError(f"Antidote site asset is missing: {source}")
        shutil.copyfile(source, public_assets / source.name)
        selected.append(source)

    landing_style = repository_root / str(assets["landingStyles"])
    docs_style = repository_root / str(assets["documentationStyles"])
    if not landing_style.is_file() or not docs_style.is_file():
        raise BuildError("Antidote site identity styles are missing")
    (site / "src/styles/identity.css").write_bytes(landing_style.read_bytes())
    holon_docs_style = site / "site-docs/styles/extra.css"
    holon_docs_style.write_bytes(
        holon_docs_style.read_bytes().rstrip() + b"\n\n" + docs_style.read_bytes()
    )
    selected.extend([landing_style, docs_style])

    docs_builder = site / "site_docs.py"
    docs_builder_text = docs_builder.read_text(encoding="utf-8")
    setting = "            'custom_dir = \"overrides\"',\n"
    if docs_builder_text.count(setting) != 1:
        raise BuildError("Holon Zensical theme configuration boundary drifted")
    docs_builder.write_text(
        docs_builder_text.replace(setting, setting + '            "font = false",\n'),
        encoding="utf-8",
    )

    public = site / "public"
    for route, title in (
        ("paper/index.html", "Antidote paper"),
        ("magazine/index.html", "Antidote magazine"),
        ("downloads/index.html", "Antidote downloads"),
    ):
        destination = public / route
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(stub_html(title))
    for relative in (
        "publication.json",
        "site.json",
        "provenance.json",
        "site-suite.provenance.json",
    ):
        (public / relative).write_text("{}\n", encoding="utf-8")
    (public / "SHA256SUMS").write_text("suite-build-stub\n", encoding="utf-8")
    (public / "antidote.pdf").write_bytes(b"%PDF-1.7\nsite-suite-build-stub\n")
    return selected


def source_digest(
    paths: Iterable[Path], repository_root: Path, holon_source: Path
) -> str:
    records: list[dict[str, Any]] = []
    for path in set(item.resolve() for item in paths):
        if path == repository_root or repository_root in path.parents:
            label = "antidote:" + path.relative_to(repository_root).as_posix()
        elif path == holon_source or holon_source in path.parents:
            label = "holon:" + path.relative_to(holon_source).as_posix()
        else:
            raise BuildError(f"source digest input is outside reviewed roots: {path}")
        records.append(
            {
                "path": label,
                "sha256": sha256_file(path),
                "sizeBytes": path.stat().st_size,
            }
        )
    records.sort(key=lambda record: str(record["path"]))
    return sha256_bytes(canonical_bytes(records))


def inventory(root: Path, excluded: Iterable[str] = ()) -> list[dict[str, Any]]:
    exclusions = set(excluded)
    return [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": sha256_file(path),
            "sizeBytes": path.stat().st_size,
        }
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.relative_to(root).as_posix() not in exclusions
    ]


def safe_output(repository_root: Path, output: Path) -> Path:
    root = repository_root.resolve()
    resolved = output.resolve()
    if root not in resolved.parents:
        raise BuildError("site-suite output must remain inside the Antidote checkout")
    relative = resolved.relative_to(root)
    if not relative.parts or not (
        relative.parts[0].startswith(".antidote-pages-")
        or relative.parts[0].startswith(".antidote-site-suite-")
    ):
        raise BuildError(
            "site-suite output must use a dedicated .antidote-pages-* or "
            ".antidote-site-suite-* path"
        )
    return resolved


def build(
    repository_root: Path,
    holon_source: Path,
    output: Path,
    source_revision: str,
    paper_version: str,
    uv: str = "uv",
    corepack: str = "corepack",
) -> dict[str, Any]:
    repository_root = repository_root.resolve()
    holon_source = holon_source.resolve()
    output = safe_output(repository_root, output)
    if COMMIT.fullmatch(source_revision) is None:
        raise BuildError("--source-revision must be a full lowercase commit SHA")
    if not paper_version.strip():
        raise BuildError("--paper-version must be non-empty")

    lock = read_json(repository_root / LOCK_PATH)
    content = read_json(repository_root / CONTENT_PATH)
    if lock.get("schema") != LOCK_SCHEMA or content.get("schema") != CONTENT_SCHEMA:
        raise BuildError("Antidote site inputs do not use the accepted v1 contracts")
    suite, holon_inputs = verify_holon_source(holon_source, lock)

    launchkit = deepcopy(content.get("launchkit"))
    site_suite_content = deepcopy(content.get("siteSuite"))
    if not isinstance(launchkit, dict) or not isinstance(site_suite_content, dict):
        raise BuildError("Antidote site content is incomplete")
    metrics = launchkit.get("demo", {}).get("metrics")
    proof = launchkit.get("proof", {}).get("items")
    if not isinstance(metrics, list) or not isinstance(proof, list):
        raise BuildError("Antidote LaunchKit evidence fields are malformed")
    metrics.extend(
        [
            {"label": "Version", "value": paper_version},
            {"label": "Revision", "value": source_revision[:12]},
        ]
    )
    if len(metrics) > 4:
        metrics.pop(0)
    proof.extend(
        [
            f"Holon {lock['holon']['commit'][:12]}",
            f"Source {source_revision[:12]}",
        ]
    )
    verify_content(holon_source, launchkit, site_suite_content)

    site_config = content["site"]
    asset_base = site_config["canonicalUrl"]
    parameters = {
        "canonical_url": site_config["canonicalUrl"],
        "identity_favicon_url": f"{asset_base}assets/favicon.svg",
        "identity_social_image_url": f"{asset_base}assets/social-preview.svg",
        "identity_stylesheet": f"{asset_base}assets/site.css",
        "launchkit_content": launchkit,
        "package_name": site_config["packageName"],
        "repository_url": "https://github.com/egohygiene/antidote",
        "site_base_path": site_config["basePath"],
        "site_description": site_config["description"],
        "site_suite_content": site_suite_content,
        "site_title": site_config["title"],
    }
    resolved_manifest = {
        "schema_version": "1.0.0",
        "repository": "egohygiene/antidote",
        "repository_class": "publication",
        "security_level": "hardened",
        "pins": {"foundation": f"egohygiene/holon@{lock['holon']['commit']}"},
        "capabilities": ["site-react-vite", "landing-launchkit", "docs-zensical"],
        "sites": ["landing", "docs", "architecture", "legal"],
        "preserve_paths": [],
        "parameters": parameters,
        "ownership": {"generator": "egohygiene/holon", "preserve_paths": []},
    }

    with tempfile.TemporaryDirectory(prefix="antidote-site-suite-") as temporary:
        work = Path(temporary)
        site = work / "source"
        site.mkdir()
        render_holon_suite(holon_source, suite, resolved_manifest, site)
        consumer_inputs = apply_consumer_inputs(repository_root, site, content)
        run([corepack, "pnpm", "install", "--frozen-lockfile"], cwd=site)
        environment = work / "zensical-environment"
        run([uv, "venv", "--python", sys.executable, str(environment)], cwd=site)
        python = environment / "bin/python"
        run(
            [
                uv,
                "pip",
                "install",
                "--python",
                str(python),
                "--require-hashes",
                "--requirement",
                "site-docs/requirements.lock.txt",
            ],
            cwd=site,
        )
        run(
            [
                str(python),
                str(repository_root / SITE_PATH / "site_suite_adapter.py"),
                "--site-root",
                str(site),
                "--corepack-executable",
                corepack,
                "check",
            ],
            cwd=site,
        )

        shutil.rmtree(output, ignore_errors=True)
        shutil.copytree(site / "dist", output)
        for relative in RESERVED_COMPOSITION_PATHS:
            target = output / relative
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink(missing_ok=True)

        source_paths = [
            repository_root / LOCK_PATH,
            repository_root / CONTENT_PATH,
            repository_root / "scripts" / "build_site_suite.py",
            repository_root / SITE_PATH / "site_suite_adapter.py",
            repository_root / SITE_PATH / "README.md",
            *holon_inputs,
            *consumer_inputs,
        ]
        manifest = {
            "schema": "antidote.site-suite-provenance/v1",
            "sourceRevision": source_revision,
            "paperVersion": paper_version,
            "sourceDigest": source_digest(
                source_paths, repository_root, holon_source
            ),
            "framework": lock["holon"],
            "consumerProof": lock["consumerProof"],
            "ownership": lock["ownership"],
            "routes": {
                "landing": "/",
                "documentation": "/docs/",
                "architecture": "/architecture/",
                "legal": "/legal/",
            },
            "artifact": {
                "algorithm": "sha256",
                "inventory": inventory(
                    output, excluded=("site-suite.provenance.json",)
                ),
            },
            "composition": {
                "owner": "egohygiene/antidote",
                "consumerOwnedRoutesAddedLater": sorted(RESERVED_COMPOSITION_PATHS),
                "networkAtRuntime": False,
            },
        }
        (output / "site-suite.provenance.json").write_bytes(canonical_bytes(manifest))
    return manifest


def main() -> int:
    arguments = parse_arguments()
    try:
        manifest = build(
            arguments.repository_root,
            arguments.holon_source,
            arguments.output,
            arguments.source_revision,
            arguments.paper_version,
            arguments.uv_executable,
            arguments.corepack_executable,
        )
    except BuildError as error:
        print(f"Antidote site-suite build failed: {error}", file=sys.stderr)
        return 1
    print(
        "Built exact-pinned Antidote site suite "
        f"{manifest['sourceDigest']} at {arguments.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
