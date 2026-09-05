# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate the governed System Design equation and notation contract."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "generate_equation_appendix.py"
SPEC = importlib.util.spec_from_file_location("generate_equation_appendix", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
EQUATIONS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EQUATIONS)


class EquationContractTests(unittest.TestCase):
    """Keep equation identity, status, notation, and rendered projections aligned."""

    def test_registry_and_system_design_are_synchronized(self) -> None:
        """Every equation must have one stable label and visible epistemic class."""
        self.assertEqual(EQUATIONS.validate_registry(ROOT), [])
        registry = EQUATIONS.load_registry(ROOT)
        self.assertEqual(len(registry["equations"]), 16)
        self.assertEqual(len(registry["symbols"]), 41)

    def test_generated_appendix_projections_are_current(self) -> None:
        """The reader-facing glossary and classification must track the registry."""
        for path, expected in EQUATIONS.expected_outputs(ROOT).items():
            self.assertEqual(path.read_text(encoding="utf-8"), expected, path)

    def test_human_authority_and_unavailable_models_remain_explicit(self) -> None:
        """Mathematics cannot silently activate inferred or autonomous control."""
        design = (ROOT / "paper" / "sections" / "03-system-design.tex").read_text(
            encoding="utf-8"
        )
        self.assertIn("an inferred value has no branch", design.lower())
        self.assertIn("no state estimator or sensor path exists in v0", design)
        self.assertIn("prohibits autonomous updating", design)
        self.assertIn("deterministic rule-guided planner", design)


if __name__ == "__main__":
    unittest.main()
