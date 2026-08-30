# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Tests for Antidote's exact-pinned Holon consumer boundary."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "build_site_suite.py"
SPEC = importlib.util.spec_from_file_location("build_site_suite", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)

HOLON_COMMIT = "2600baff6f6d944094da81b77e1a9a2e9e7a1cd6"
IDENTITY_PROOF = "1c9fd6352cf4dc7e8274dab42270946d17c81aa1"


class SiteSuiteContractTests(unittest.TestCase):
    """Keep shared framework pins and consumer ownership fail-closed."""

    def test_lock_records_exact_framework_and_consumer_proof(self) -> None:
        lock = json.loads(
            (ROOT / "publication" / "antidote-site-suite.lock.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(lock["schema"], BUILDER.LOCK_SCHEMA)
        self.assertEqual(lock["holon"]["commit"], HOLON_COMMIT)
        self.assertEqual(lock["consumerProof"]["mergedCommit"], IDENTITY_PROOF)
        self.assertEqual(set(lock["holon"]["profiles"]), set(BUILDER.PROFILE_KEYS))
        for profile in lock["holon"]["profiles"].values():
            self.assertRegex(profile["gitBlob"], r"^[0-9a-f]{40}$")
            self.assertRegex(profile["sha256"], r"^[0-9a-f]{64}$")

    def test_output_is_limited_to_owned_temporary_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            accepted = root / ".antidote-site-suite-fixture" / "dist"
            self.assertEqual(BUILDER.safe_output(root, accepted), accepted.resolve())
            for rejected in (root / "site", root / "_site", root.parent / "escape"):
                with self.assertRaises(BUILDER.BuildError):
                    BUILDER.safe_output(root, rejected)

    def test_content_keeps_demo_and_evidence_boundaries_explicit(self) -> None:
        content = json.loads(
            (ROOT / "publication" / "antidote-site.content.json").read_text(
                encoding="utf-8"
            )
        )
        serialized = json.dumps(content).lower()
        for marker in (
            "synthetic",
            "no invented human results",
            "not a medical treatment",
            "no real model",
            "evidence",
        ):
            self.assertIn(marker, serialized)

    def test_pages_workflow_checks_out_only_the_exact_holon_commit(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(f'HOLON_COMMIT: "{HOLON_COMMIT}"', workflow)
        self.assertIn("ref: ${{ env.HOLON_COMMIT }}", workflow)
        self.assertIn('HOLON_SOURCE=".holon-source"', workflow)
        self.assertNotIn("ref: main", workflow)


if __name__ == "__main__":
    unittest.main()
