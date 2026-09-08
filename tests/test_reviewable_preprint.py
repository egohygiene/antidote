# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Regression tests for the issue #48 reviewable-publication gate."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    """Load one repository script without making scripts a package."""
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


REVIEW = load_module(
    "check_reviewable_preprint", ROOT / "scripts" / "check_reviewable_preprint.py"
)
TASKS = load_module("publication_tasks", ROOT / "scripts" / "tasks.py")


class ReviewablePreprintTests(unittest.TestCase):
    """Keep review evidence and strong-stage validation inseparable."""

    def test_repository_review_record_passes(self) -> None:
        """The committed review dossier must satisfy the complete gate."""
        self.assertEqual(REVIEW.validate_reviewable_preprint(ROOT), [])

    def test_submission_ready_validation_always_checks_external_links(self) -> None:
        """Every native strong-stage entry point must perform a live link audit."""
        command = TASKS.validation_command(
            ROOT,
            ROOT / "build" / "egohygiene",
            "egohygiene",
            "python3",
        )
        self.assertIn("--check-external-links", command)

    def test_draft_validation_does_not_require_network(self) -> None:
        """Reusable draft fixtures remain locally buildable without network access."""
        with tempfile.TemporaryDirectory(prefix="antidote-review-stage-") as temporary:
            project = Path(temporary)
            (project / "beacon-project.toml").write_text(
                '[paper]\nstage = "draft"\n', encoding="utf-8"
            )
            command = TASKS.validation_command(
                project,
                project / "build",
                "neutral",
                "python3",
            )
            self.assertNotIn("--check-external-links", command)


if __name__ == "__main__":
    unittest.main()
