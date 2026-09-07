# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Regression coverage for the issue #43 limitations and ethics audit."""

from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "generate_risk_table.py"
SPEC = importlib.util.spec_from_file_location("generate_risk_table", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
RISKS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RISKS)


class RiskRegisterTests(unittest.TestCase):
    """Keep mitigations, residual uncertainty, and blocking gates distinct."""

    def test_register_and_checked_in_projection_are_current(self) -> None:
        """The reviewed register must validate and deterministically own the table."""
        register = RISKS.load_register()
        self.assertEqual(RISKS.validate_register(register), [])
        expected = RISKS.render_table(register)
        actual = (ROOT / RISKS.OUTPUT_PATH).read_text(encoding="utf-8")
        self.assertEqual(actual, expected)

    def test_every_status_and_collection_block_remain_visible(self) -> None:
        """No table revision may silently imply mitigation or collection authority."""
        register = RISKS.load_register()
        self.assertFalse(register["formal_collection_authorized"])
        self.assertEqual(
            {risk["status"] for risk in register["risks"]},
            set(RISKS.STATUS_LABELS),
        )
        table = RISKS.render_table(register)
        self.assertIn("Every row retains residual uncertainty", table)
        self.assertIn("Blocked", table)
        self.assertNotIn("PROVISIONAL", table)

    def test_missing_gate_or_authority_change_fails_closed(self) -> None:
        """A risk cannot be resolved by omission or by enabling collection here."""
        register = copy.deepcopy(RISKS.load_register())
        register["risks"][0]["blocking_gate"] = "none"
        register["formal_collection_authorized"] = True
        errors = RISKS.validate_register(register)
        self.assertIn("risk register must not authorize formal collection", errors)
        self.assertTrue(any("cannot omit its blocking gate" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
