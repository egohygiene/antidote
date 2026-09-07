# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate the issue #41 empty-state Results reporting contract."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "generate_results_reporting.py"
SPEC = importlib.util.spec_from_file_location("generate_results_reporting", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
REPORTING = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPORTING)


class ResultsReportingTests(unittest.TestCase):
    """Keep every future result bound to evidence while current slots are empty."""

    def load_contract(self) -> dict[str, object]:
        """Load the canonical reporting contract."""
        return json.loads((ROOT / REPORTING.REPORTING_PATH).read_text(encoding="utf-8"))

    def test_reporting_contract_and_manuscript_are_synchronized(self) -> None:
        """The governed empty state must pass every cross-artifact check."""
        self.assertEqual(REPORTING.validate_reporting(ROOT), [])

    def test_generated_empty_state_tables_are_current(self) -> None:
        """Result tables must be deterministic projections, not hand-edited values."""
        for path, expected in REPORTING.expected_outputs(ROOT).items():
            self.assertEqual(path.read_text(encoding="utf-8"), expected, path)
            self.assertIn("GOVERNED EMPTY STATE", expected)
            self.assertIn("No qualifying values are registered", expected)

    def test_future_slots_resolve_source_protocol_and_analysis(self) -> None:
        """Every result slot must identify its complete promotion context."""
        contract = self.load_contract()
        sources = {record["id"]: record for record in contract["source_records"]}
        analyses = {analysis["id"]: analysis for analysis in contract["analyses"]}
        for slot in contract["result_slots"]:
            self.assertIn(slot["source_record_id"], sources, slot["id"])
            self.assertIn(slot["analysis_id"], analyses, slot["id"])
            self.assertEqual(slot["protocol_version"], "1.0.0", slot["id"])
            self.assertEqual(
                analyses[slot["analysis_id"]]["source_record_id"],
                slot["source_record_id"],
                slot["id"],
            )

    def test_analysis_reporting_is_explicit_and_value_free(self) -> None:
        """Effects, uncertainty, visuals, missingness, and sensitivity stay planned."""
        contract = self.load_contract()
        policies = contract["analysis_reporting"]
        self.assertEqual(set(policies), set(REPORTING.EXPECTED_ANALYSIS_REPORTING))
        for (
            dimension,
            expected_pointers,
        ) in REPORTING.EXPECTED_ANALYSIS_REPORTING.items():
            self.assertEqual(policies[dimension]["status"], "not-run")
            self.assertEqual(
                policies[dimension]["protocol_pointers"], expected_pointers
            )
            self.assertTrue(policies[dimension]["reporting_rule"])
        self.assertFalse(
            REPORTING.FORBIDDEN_RESULT_KEYS & REPORTING.nested_keys(contract)
        )

    def test_no_qualifying_result_package_is_registered(self) -> None:
        """Reserved package identities must remain absent until promotion review."""
        contract = self.load_contract()
        self.assertTrue(
            all(
                value is False
                for value in contract["current_manuscript_state"].values()
            )
        )
        for record in contract["source_records"]:
            path = ROOT / record["path"]
            if record["state"] == "available-design-artifact":
                self.assertTrue(path.is_file(), record["id"])
            else:
                self.assertFalse(path.exists(), record["id"])

    def test_human_slots_and_physiology_remain_blocked(self) -> None:
        """A reporting shell cannot create collection or sensor authority."""
        contract = self.load_contract()
        human_slots = [
            slot for slot in contract["result_slots"] if slot["stage"] == "H1"
        ]
        self.assertTrue(human_slots)
        self.assertTrue(
            all(
                slot["current_state"]
                in {"blocked-no-collection-authority", "disabled-requires-amendment"}
                for slot in human_slots
            )
        )
        physiology = next(
            slot for slot in human_slots if slot["id"] == "ANT-RES-H1-PHYSIOLOGY"
        )
        self.assertEqual(physiology["evidence_class"], "unavailable")
        self.assertEqual(physiology["current_state"], "disabled-requires-amendment")


if __name__ == "__main__":
    unittest.main()
