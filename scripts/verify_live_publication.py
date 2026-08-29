#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Verify the live Antidote routes against one immutable merged revision."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlsplit

import tomllib

ROOT = Path(__file__).resolve().parents[1]
REVISION = re.compile(r"[0-9a-f]{40}")
REQUIRED_ROUTES = {
    "home": "",
    "paper": "paper/",
    "paper-pdf": "antidote.pdf",
    "magazine": "magazine/",
    "downloads": "downloads/",
    "publication-manifest": "publication.json",
    "site-catalog": "site.json",
    "checksums": "SHA256SUMS",
}
ROUTE_FILES = {
    "": "index.html",
    "paper/": "paper/index.html",
    "magazine/": "magazine/index.html",
    "downloads/": "downloads/index.html",
}


def sha256_bytes(payload: bytes) -> str:
    """Return the lowercase SHA-256 digest for one response body."""
    return hashlib.sha256(payload).hexdigest()


def normalize_base_url(value: str) -> str:
    """Require one HTTPS publication base URL with no query or fragment."""
    normalized = value.rstrip("/") + "/"
    parsed = urlsplit(normalized)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(f"live publication base must be a clean HTTPS URL: {value}")
    return normalized


def parse_checksums(payload: bytes) -> dict[str, str]:
    """Parse a strict SHA256SUMS response into a unique path map."""
    checksums: dict[str, str] = {}
    for line in payload.decode("utf-8").splitlines():
        if not re.fullmatch(r"[0-9a-f]{64}  .+", line):
            raise ValueError(f"malformed published checksum line: {line}")
        digest, relative = line.split("  ", 1)
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or relative in checksums:
            raise ValueError(f"unsafe or duplicate published checksum path: {relative}")
        checksums[relative] = digest
    return checksums


def validate_live_payloads(
    payloads: dict[str, bytes], base_url: str, expected_revision: str
) -> dict[str, str]:
    """Validate fetched routes, identities, and hashes without network access."""
    base_url = normalize_base_url(base_url)
    if REVISION.fullmatch(expected_revision) is None:
        raise ValueError("expected revision must be a full lowercase Git commit")
    for required in ("site.json", "publication.json", "provenance.json", "SHA256SUMS"):
        if required not in payloads:
            raise KeyError(f"live response is missing: {required}")

    catalog = json.loads(payloads["site.json"].decode("utf-8"))
    publication = json.loads(payloads["publication.json"].decode("utf-8"))
    provenance = json.loads(payloads["provenance.json"].decode("utf-8"))
    route_map = {route["id"]: route["path"] for route in catalog["routes"]}
    if len(catalog["routes"]) != len(route_map) or route_map != REQUIRED_ROUTES:
        raise RuntimeError(
            f"live route contract mismatch: expected={REQUIRED_ROUTES}, actual={route_map}"
        )
    for route in REQUIRED_ROUTES.values():
        if route not in payloads:
            raise KeyError(f"live route was not fetched: /{route}")

    if catalog.get("canonical_url") != base_url:
        raise RuntimeError("live site catalog does not identify the requested base URL")
    if publication.get("pages_url") != base_url:
        raise RuntimeError("live publication manifest is not canonical")
    slots = {slot["id"]: slot for slot in catalog.get("slots", [])}
    if set(slots) != {"paper", "magazine"}:
        raise RuntimeError("live catalog must contain the paper and magazine slots")
    if slots["paper"].get("status") != "available":
        raise RuntimeError("live paper slot is not available")
    if (
        slots["magazine"].get("status") != "planned"
        or slots["magazine"].get("artifacts") != []
        or slots["magazine"].get("manifest_path") is not None
    ):
        raise RuntimeError("live magazine slot exceeds its planned boundary")
    revisions = {
        "site.json": catalog.get("source_revision"),
        "publication.json": publication.get("source_revision"),
        "provenance.json": provenance.get("source_revision"),
    }
    stale = {name: value for name, value in revisions.items() if value != expected_revision}
    if stale:
        raise RuntimeError(
            f"live publication is stale for {expected_revision}: observed={stale}"
        )

    paper_html = payloads["paper/"].decode("utf-8")
    revision_meta = f'<meta name="source-revision" content="{expected_revision}">'
    visible_revision = f"Revision <code>{expected_revision[:12]}</code>"
    if revision_meta not in paper_html or visible_revision not in paper_html:
        raise RuntimeError("live paper HTML does not expose the expected revision canary")
    if not payloads["antidote.pdf"].startswith(b"%PDF-"):
        raise RuntimeError("live /antidote.pdf response is not a PDF")

    checksums = parse_checksums(payloads["SHA256SUMS"])
    route_files = {
        route: ROUTE_FILES.get(route, route)
        for route in REQUIRED_ROUTES.values()
        if route != "SHA256SUMS"
    }
    for route, relative in route_files.items():
        if relative not in checksums:
            raise RuntimeError(f"published checksum inventory is missing: {relative}")
        observed = sha256_bytes(payloads[route])
        if observed != checksums[relative]:
            raise RuntimeError(f"live route checksum mismatch: /{route}")

    artifacts = publication.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise RuntimeError("live publication manifest has no artifacts")
    for artifact_id, artifact in artifacts.items():
        relative = artifact.get("path")
        if not isinstance(relative, str) or relative not in payloads:
            raise RuntimeError(f"live artifact was not fetched: {artifact_id}")
        observed = sha256_bytes(payloads[relative])
        if observed != artifact.get("sha256") or observed != checksums.get(relative):
            raise RuntimeError(f"live artifact hash mismatch: {artifact_id}")
        expected_url = (
            urljoin(base_url, "paper/")
            if artifact_id == "accessible_web"
            else urljoin(base_url, relative)
        )
        if artifact.get("url") != expected_url:
            raise RuntimeError(f"live artifact URL mismatch: {artifact_id}")

    return {
        "base_url": base_url,
        "revision": expected_revision,
        "paper_sha256": sha256_bytes(payloads["antidote.pdf"]),
        "web_sha256": sha256_bytes(payloads["paper/"]),
    }


def cache_busted_url(base_url: str, path: str, revision: str) -> str:
    """Return one exact route URL with an immutable cache-busting query."""
    return urljoin(base_url, path) + "?" + urlencode({"revision": revision})


def fetch(
    base_url: str,
    path: str,
    revision: str,
    timeout: float,
    attempts: int,
    retry_delay: float,
) -> bytes:
    """Fetch one live route while explicitly revalidating intermediary caches."""
    if attempts < 1 or retry_delay < 0:
        raise ValueError("live fetch attempts must be positive and delay non-negative")
    url = cache_busted_url(base_url, path, revision)
    request = urllib.request.Request(
        url,
        headers={
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": "antidote-publication-verifier/1",
        },
    )
    last_error: urllib.error.HTTPError | urllib.error.URLError | None = None
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            last_error = error
            if attempt < attempts:
                time.sleep(retry_delay)
    assert last_error is not None
    if isinstance(last_error, urllib.error.HTTPError):
        raise RuntimeError(
            f"live route returned HTTP {last_error.code} after {attempts} "
            f"attempt(s): {url}"
        ) from last_error
    raise RuntimeError(
        f"could not reach live route after {attempts} attempt(s) {url}: "
        f"{last_error.reason}"
    ) from last_error


def configured_base_url() -> str:
    """Read the canonical publication base from project configuration."""
    with (ROOT / "beacon-project.toml").open("rb") as stream:
        return tomllib.load(stream)["publication"]["pages_url"]


def current_revision() -> str:
    """Return the checked-out immutable revision for a post-merge check."""
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def main() -> int:
    """Fetch and verify the canonical publication after a Pages deployment."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=configured_base_url())
    parser.add_argument("--expected-revision", default=current_revision())
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--retry-delay", type=float, default=5.0)
    arguments = parser.parse_args()
    base_url = normalize_base_url(arguments.base_url)
    revision = arguments.expected_revision

    initial_paths = ("site.json", "publication.json", "provenance.json", "SHA256SUMS")
    payloads = {
        path: fetch(
            base_url,
            path,
            revision,
            arguments.timeout,
            arguments.attempts,
            arguments.retry_delay,
        )
        for path in initial_paths
    }
    catalog = json.loads(payloads["site.json"].decode("utf-8"))
    publication = json.loads(payloads["publication.json"].decode("utf-8"))
    paths = {route["path"] for route in catalog.get("routes", [])}
    paths.update(
        artifact.get("path")
        for artifact in publication.get("artifacts", {}).values()
        if isinstance(artifact.get("path"), str)
    )
    for path in sorted(paths - payloads.keys()):
        payloads[path] = fetch(
            base_url,
            path,
            revision,
            arguments.timeout,
            arguments.attempts,
            arguments.retry_delay,
        )

    result = validate_live_payloads(payloads, base_url, revision)
    print(
        "PASS live publication revision "
        f"{result['revision']} at {result['base_url']} "
        f"(HTML {result['web_sha256']}, PDF {result['paper_sha256']})."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"ERROR {error}", file=sys.stderr)
        raise SystemExit(1) from None
