# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Tests for revision- and hash-aware live publication verification."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "verify_live_publication.py"
SPEC = importlib.util.spec_from_file_location("verify_live_publication", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)

BASE_URL = "https://antidote.egohygiene.io/"
REVISION = "a" * 40


def encode(value: dict) -> bytes:
    """Serialize a fixture exactly as the Pages staging code does."""
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def digest(payload: bytes) -> str:
    """Return a fixture payload digest."""
    return hashlib.sha256(payload).hexdigest()


def fixture_payloads() -> dict[str, bytes]:
    """Create a mutually consistent minimal live publication response set."""
    html = (
        '<meta name="source-revision" content="' + REVISION + '">'
        "Revision <code>" + REVISION[:12] + "</code>"
    ).encode()
    pdf = b"%PDF-1.7\nfixture\n"
    archive = b"fixture archive"
    provenance = encode({"source_revision": REVISION})
    site_suite = encode(
        {
            "schema": "antidote.site-suite-provenance/v1",
            "sourceRevision": REVISION,
            "framework": {"commit": VERIFY.HOLON_COMMIT},
        }
    )
    artifacts = {
        "accessible_web": {
            "path": "paper/index.html",
            "sha256": digest(html),
            "url": BASE_URL + "paper/",
        },
        "paper_pdf": {
            "path": "antidote.pdf",
            "sha256": digest(pdf),
            "url": BASE_URL + "antidote.pdf",
        },
        "provenance": {
            "path": "provenance.json",
            "sha256": digest(provenance),
            "url": BASE_URL + "provenance.json",
        },
        "arxiv_source": {
            "path": "downloads/antidote-0.1.0.tar.gz",
            "sha256": digest(archive),
            "url": BASE_URL + "downloads/antidote-0.1.0.tar.gz",
        },
    }
    publication = encode(
        {
            "pages_url": BASE_URL,
            "source_revision": REVISION,
            "artifacts": artifacts,
        }
    )
    routes = [
        {"id": route_id, "path": path}
        for route_id, path in VERIFY.REQUIRED_ROUTES.items()
    ]
    catalog = encode(
        {
            "canonical_url": BASE_URL,
            "source_revision": REVISION,
            "routes": routes,
            "slots": [
                {"id": "paper", "status": "available"},
                {
                    "id": "magazine",
                    "status": "planned",
                    "artifacts": [],
                    "manifest_path": None,
                },
            ],
        }
    )
    route_payloads = {
        "": b"home",
        "docs/": b"docs",
        "architecture/": b"architecture",
        "legal/": b"legal",
        "paper/": html,
        "paper/index.html": html,
        "antidote.pdf": pdf,
        "magazine/": b"magazine",
        "downloads/": b"downloads",
        "publication.json": publication,
        "site.json": catalog,
        "provenance.json": provenance,
        "site-suite.provenance.json": site_suite,
        "downloads/antidote-0.1.0.tar.gz": archive,
    }
    route_files = {
        route: VERIFY.ROUTE_FILES.get(route, route)
        for route in VERIFY.REQUIRED_ROUTES.values()
        if route != "SHA256SUMS"
    }
    checksummed = {
        route_files[route]: digest(payload)
        for route, payload in route_payloads.items()
        if route in route_files
    }
    checksummed.update(
        {
            "provenance.json": digest(provenance),
            "downloads/antidote-0.1.0.tar.gz": digest(archive),
        }
    )
    checksum_payload = "".join(
        f"{value}  {path}\n" for path, value in sorted(checksummed.items())
    ).encode()
    return {**route_payloads, "SHA256SUMS": checksum_payload}


class VerifyLivePublicationTests(unittest.TestCase):
    """Keep stale-cache detection and artifact integrity fail-closed."""

    def test_accepts_one_consistent_merged_revision(self) -> None:
        result = VERIFY.validate_live_payloads(fixture_payloads(), BASE_URL, REVISION)
        self.assertEqual(result["revision"], REVISION)
        self.assertEqual(result["base_url"], BASE_URL)

    def test_rejects_a_stale_manifest_revision(self) -> None:
        payloads = fixture_payloads()
        catalog = json.loads(payloads["site.json"])
        catalog["source_revision"] = "b" * 40
        payloads["site.json"] = encode(catalog)
        with self.assertRaisesRegex(RuntimeError, "stale"):
            VERIFY.validate_live_payloads(payloads, BASE_URL, REVISION)

    def test_rejects_a_stale_pdf_body_even_when_the_route_exists(self) -> None:
        payloads = fixture_payloads()
        payloads["antidote.pdf"] += b"stale"
        with self.assertRaisesRegex(RuntimeError, "checksum mismatch"):
            VERIFY.validate_live_payloads(payloads, BASE_URL, REVISION)

    def test_cache_buster_names_the_expected_revision(self) -> None:
        url = VERIFY.cache_busted_url(BASE_URL, "paper/", REVISION)
        self.assertEqual(url, BASE_URL + "paper/?revision=" + REVISION)


if __name__ == "__main__":
    unittest.main()
