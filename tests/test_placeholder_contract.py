# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate the complete paper-shaped skeleton and release blockers."""

from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "check_placeholders.py"
SPEC = importlib.util.spec_from_file_location("check_placeholders", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
PLACEHOLDERS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PLACEHOLDERS)
EXPECTED_ACTIVE_PLACEHOLDERS = 0


class PlaceholderContractTests(unittest.TestCase):
    """Keep the layout skeleton explicit, stable, and impossible to publish."""

    def fixture(self, temporary: str) -> Path:
        """Copy only the paper tree and entrypoint needed by the validator."""
        root = Path(temporary)
        shutil.copytree(ROOT / "paper", root / "paper")
        return root

    def test_canonical_skeleton_is_complete(self) -> None:
        """Every active content gap must have one stable governed identity."""
        result = PLACEHOLDERS.validate_placeholder_system(ROOT)
        self.assertEqual(result["errors"], [])
        self.assertEqual(len(result["active"]), EXPECTED_ACTIVE_PLACEHOLDERS)
        identifiers = [record["id"] for record in result["active"]]
        self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_submission_ready_stage_has_no_content_placeholder_blocker(self) -> None:
        """The completed manuscript carries no active content filler."""
        result = PLACEHOLDERS.validate_placeholder_system(
            ROOT, paper_stage="submission-ready"
        )
        self.assertEqual(result["errors"], [])

    def test_unregistered_placeholder_is_rejected(self) -> None:
        """A contributor cannot add anonymous layout filler."""
        with tempfile.TemporaryDirectory(prefix="antidote-skeleton-") as temporary:
            root = self.fixture(temporary)
            section = root / "paper" / "sections" / "03-system-design.tex"
            section.write_text(
                section.read_text(encoding="utf-8")
                + "\n\\AntidotePlaceholder{ANT-PH-SYS-999}{Anonymous block}{Lorem ipsum dolor sit amet, consectetur adipiscing elit.}\n",
                encoding="utf-8",
            )
            result = PLACEHOLDERS.validate_placeholder_system(root)
            self.assertIn(
                "unregistered manuscript placeholder: ANT-PH-SYS-999",
                result["errors"],
            )

    def test_resolved_placeholder_cannot_remain_in_source(self) -> None:
        """Registry state and section replacement must advance atomically."""
        with tempfile.TemporaryDirectory(prefix="antidote-skeleton-") as temporary:
            root = self.fixture(temporary)
            path = root / "paper" / "skeleton.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            resolved = next(
                record
                for record in manifest["placeholders"]
                if record["state"] == "resolved"
            )
            section = root / resolved["section_path"]
            section.write_text(
                section.read_text(encoding="utf-8")
                + f"\n\\AntidotePlaceholder{{{resolved['id']}}}"
                + f"{{{resolved['title']}}}"
                + "{Lorem ipsum dolor sit amet, consectetur adipiscing elit.}\n",
                encoding="utf-8",
            )
            result = PLACEHOLDERS.validate_placeholder_system(root)
            self.assertIn(
                f"{resolved['id']} resolved placeholder remains in manuscript source",
                result["errors"],
            )


if __name__ == "__main__":
    unittest.main()
