# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate the direct-reference and additional-reading separation."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "generate_research_shelf.py"
SPEC = importlib.util.spec_from_file_location("generate_research_shelf", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
SHELF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SHELF)


class ResearchShelfTests(unittest.TestCase):
    """Keep gathered reading visible without turning it into cited evidence."""

    def test_checked_in_shelf_is_current(self) -> None:
        """The appendix projection must track sources and manuscript citations."""
        expected = SHELF.render_shelf(ROOT)
        actual = (ROOT / "paper" / "research-shelf.tex").read_text(encoding="utf-8")
        self.assertEqual(actual, expected)

    def test_cited_and_additional_keys_do_not_overlap(self) -> None:
        """An entry must not appear as both a direct and additional source."""
        cited = SHELF.citation_keys(ROOT)
        shelf = SHELF.render_shelf(ROOT)
        for key in cited:
            self.assertNotIn(f"\\texttt{{{key}}}", shelf)


if __name__ == "__main__":
    unittest.main()
