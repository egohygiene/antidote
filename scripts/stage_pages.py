#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Stage and validate Antidote's deterministic GitHub Pages artifact."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
from pathlib import Path
from urllib.parse import urljoin

import tomllib

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)
LOCAL_LINK = re.compile(r"(?:href|src)=\"([^\"]+)\"")


def sha256(path: Path) -> str:
    """Return the lowercase SHA-256 digest for one file."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_toml(path: Path) -> dict:
    """Load a UTF-8 TOML document."""
    with path.open("rb") as stream:
        return tomllib.load(stream)


def validate_custom_domain(value: str) -> str:
    """Return a normalized custom domain or reject unsafe input."""
    domain = value.strip().lower().rstrip(".")
    if domain and DOMAIN.fullmatch(domain) is None:
        raise ValueError(f"invalid Pages custom domain: {value}")
    return domain


def copy_required(source: Path, destination: Path) -> None:
    """Copy one required file and fail clearly when it is absent or empty."""
    if not source.is_file() or source.stat().st_size == 0:
        raise FileNotFoundError(f"required publication artifact is missing: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def validate_local_links(site: Path) -> None:
    """Require every relative landing-page route to resolve inside the site."""
    index = site / "index.html"
    html = index.read_text(encoding="utf-8")
    for target in LOCAL_LINK.findall(html):
        if target.startswith(("https://", "http://", "mailto:", "#", "data:")):
            continue
        clean = target.split("#", 1)[0].split("?", 1)[0]
        if not clean:
            continue
        resolved = site / clean
        if clean.endswith("/"):
            resolved = resolved / "index.html"
        if not resolved.is_file():
            raise FileNotFoundError(f"landing-page route does not resolve: {target}")


def validate_checksums(site: Path) -> None:
    """Recompute every published checksum from SHA256SUMS."""
    for line in (site / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        observed = sha256(site / relative)
        if observed != expected:
            raise RuntimeError(f"published checksum mismatch: {relative}")


def stage_site(
    root: Path,
    build: Path,
    output: Path,
    *,
    custom_domain: str = "",
) -> dict:
    """Create one complete Pages tree from governed Antidote outputs."""
    root = root.resolve()
    build = build.resolve()
    output = output.resolve()
    if output in {root, Path("/")} or root not in output.parents:
        raise ValueError(f"refusing unsafe Pages output directory: {output}")

    config = load_toml(root / "beacon-project.toml")
    paper = config["paper"]
    provenance = json.loads((build / "provenance.json").read_text(encoding="utf-8"))
    archives = sorted((build / "arxiv").glob("*.tar.gz"))
    if len(archives) != 1:
        raise RuntimeError("Pages staging requires exactly one arXiv source archive")

    domain = validate_custom_domain(custom_domain)
    pages_url = (
        f"https://{domain}/"
        if domain
        else config["publication"]["pages_url"].rstrip("/") + "/"
    )

    shutil.rmtree(output, ignore_errors=True)
    output.mkdir(parents=True)
    landing_source = root / "docs" / "index.html"
    if not landing_source.is_file() or landing_source.stat().st_size == 0:
        raise FileNotFoundError(
            f"required publication artifact is missing: {landing_source}"
        )
    default_pages_url = config["publication"]["pages_url"].rstrip("/") + "/"
    landing = landing_source.read_text(encoding="utf-8").replace(
        default_pages_url, pages_url
    )
    (output / "index.html").write_text(landing, encoding="utf-8")
    copy_required(root / "docs" / "site.webmanifest", output / "site.webmanifest")
    copy_required(build / "paper.pdf", output / "antidote.pdf")
    copy_required(build / "provenance.json", output / "provenance.json")
    shutil.copytree(build / "web", output / "paper")
    copy_required(archives[0], output / "downloads" / archives[0].name)
    (output / ".nojekyll").write_text("", encoding="utf-8")

    artifact_paths = {
        "accessible_web": "paper/index.html",
        "paper_pdf": "antidote.pdf",
        "provenance": "provenance.json",
        "arxiv_source": f"downloads/{archives[0].name}",
    }
    artifacts = {
        key: {
            "path": relative,
            "sha256": sha256(output / relative),
            "url": urljoin(pages_url, relative),
        }
        for key, relative in artifact_paths.items()
    }
    generated_at = dt.datetime.fromtimestamp(
        int(config["provenance"]["source_date_epoch"]), tz=dt.timezone.utc
    ).isoformat()
    manifest = {
        "schema_version": 1,
        "id": paper["id"],
        "title": paper["title"],
        "version": paper["version"],
        "stage": paper["stage"],
        "generated_at": generated_at,
        "pages_url": pages_url,
        "custom_domain": domain or None,
        "source_repository": config["provenance"]["source_repository"],
        "source_revision": provenance["source_revision"],
        "artifacts": artifacts,
    }
    (output / "publication.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    checksum_files = sorted(
        path
        for path in output.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS"
    )
    checksum_lines = [
        f"{sha256(path)}  {path.relative_to(output).as_posix()}"
        for path in checksum_files
    ]
    (output / "SHA256SUMS").write_text(
        "\n".join(checksum_lines) + "\n", encoding="utf-8"
    )

    validate_local_links(output)
    validate_checksums(output)
    print(f"PASS staged Antidote Pages artifact at {output}")
    return manifest


def main() -> int:
    """Parse CLI arguments and stage the repository-owned Pages artifact."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir", default="build/egohygiene")
    parser.add_argument("--output-dir", default="_site")
    parser.add_argument(
        "--custom-domain",
        default=os.environ.get("PAGES_CUSTOM_DOMAIN", ""),
    )
    arguments = parser.parse_args()
    build = Path(arguments.build_dir).expanduser()
    if not build.is_absolute():
        build = ROOT / build
    output = Path(arguments.output_dir).expanduser()
    if not output.is_absolute():
        output = ROOT / output
    stage_site(ROOT, build, output, custom_domain=arguments.custom_domain)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
