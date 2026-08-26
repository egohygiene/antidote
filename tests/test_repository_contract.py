# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Static separation-of-concerns checks for Antidote publishing."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTests(unittest.TestCase):
    """Keep the native and optional control-plane boundaries explicit."""

    def test_native_entrypoints_use_the_project_task_adapter(self) -> None:
        """Make and Task must share the same Antidote-owned implementation."""
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        taskfile = (ROOT / "Taskfile.yml").read_text(encoding="utf-8")
        self.assertIn("scripts/tasks.py", makefile)
        self.assertIn("scripts/tasks.py", taskfile)
        self.assertNotIn("BEACON_PROFILE", makefile)
        self.assertNotIn("resolve_beacon.py", taskfile)

    def test_pages_deployment_requires_explicit_activation(self) -> None:
        """A merge cannot deploy until the maintainer enables the repository gate."""
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("vars.PAGES_ENABLED == 'true'", workflow)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertIn("PAGES_CUSTOM_DOMAIN", workflow)

    def test_pages_ci_proves_publication_reproducibility(self) -> None:
        """Pages review must compare independently built governed artifacts."""
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("task reproducibility", workflow)

    def test_lorem_ipsum_is_wrapped_as_non_evidence(self) -> None:
        """Layout filler may appear only through the explicit draft macro."""
        section_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((ROOT / "paper" / "sections").glob("*.tex"))
        )
        placeholders = re.findall(
            r"\\AntidotePlaceholder\{[^{}]+\}\{([^{}]+)\}",
            section_text,
            flags=re.DOTALL,
        )
        self.assertGreater(len(placeholders), 0)
        self.assertEqual(section_text.count("Lorem ipsum"), len(placeholders))
        self.assertTrue(all("Lorem ipsum" in body for body in placeholders))


if __name__ == "__main__":
    unittest.main()
