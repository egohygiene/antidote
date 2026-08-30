#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Regression coverage for the governed Related Work comparator projection."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "generate_comparator_table.py"
SPEC = importlib.util.spec_from_file_location("generate_comparator_table", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
TABLES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TABLES)


class ComparatorTableTests(unittest.TestCase):
    """Keep the manuscript table synchronized with the reviewed matrix."""

    def test_checked_in_projection_is_current(self) -> None:
        """The active table must be regenerated whenever the matrix changes."""
        expected = TABLES.render_table(TABLES.load_matrix())
        actual = TABLES.OUTPUT_PATH.read_text(encoding="utf-8")
        self.assertEqual(actual, expected)

    def test_projection_preserves_every_comparator_and_boundary(self) -> None:
        """No system, status legend, or proposed-state warning may disappear."""
        table = TABLES.render_table(TABLES.load_matrix())
        for source_id in TABLES.SOURCE_ORDER:
            label, citation = TABLES.SOURCE_LABELS[source_id]
            self.assertIn(label, table)
            self.assertIn(f"\\citep{{{citation}}}", table)
        self.assertIn("Antidote profile", table)
        self.assertIn("proposed, not evaluated", table)
        self.assertIn("not evidence strength", table)


if __name__ == "__main__":
    unittest.main()
