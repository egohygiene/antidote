# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate the issue #40 protocol freeze and reader-facing projection."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "generate_protocol_appendix.py"
SPEC = importlib.util.spec_from_file_location("generate_protocol_appendix", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
PROTOCOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROTOCOL)


class FeasibilityProtocolTests(unittest.TestCase):
    """Keep protocol identity, authority, measures, and prose synchronized."""

    def test_protocol_and_manuscript_are_synchronized(self) -> None:
        """The frozen protocol must pass every cross-artifact validation."""
        self.assertEqual(PROTOCOL.validate_protocol(ROOT), [])

    def test_generated_appendix_projection_is_current(self) -> None:
        """Reader-facing protocol status must derive from the locked source."""
        for path, expected in PROTOCOL.expected_outputs(ROOT).items():
            self.assertEqual(path.read_text(encoding="utf-8"), expected, path)

    def test_human_collection_and_model_updating_remain_blocked(self) -> None:
        """A design freeze cannot silently become study or adaptation authority."""
        protocol = json.loads(
            (ROOT / PROTOCOL.PROTOCOL_PATH).read_text(encoding="utf-8")
        )
        self.assertIs(protocol["collection_authority"], False)
        self.assertTrue(protocol["human_collection_activation_gates"])
        self.assertTrue(
            all(
                gate["satisfied"] is False
                for gate in protocol["human_collection_activation_gates"]
            )
        )
        self.assertIs(protocol["scope"]["clinical_efficacy"], False)
        self.assertIs(protocol["scope"]["autonomous_personalization"], False)
        self.assertIs(protocol["optional_physiology"]["enabled"], False)
        self.assertIn("ANT-EQ-015", protocol["analysis_plan"]["equation_boundary"])
        self.assertIn("ANT-EQ-016", protocol["analysis_plan"]["equation_boundary"])

    def test_initial_freeze_is_byte_locked_and_has_no_deviations(self) -> None:
        """The lock and empty audit log must describe the exact protocol bytes."""
        lock = json.loads((ROOT / PROTOCOL.LOCK_PATH).read_text(encoding="utf-8"))
        deviations = json.loads(
            (ROOT / PROTOCOL.DEVIATIONS_PATH).read_text(encoding="utf-8")
        )
        self.assertEqual(lock["sha256"], PROTOCOL.protocol_sha256(ROOT))
        self.assertIs(lock["collection_authority"], False)
        self.assertIs(deviations["collection_started"], False)
        self.assertEqual(deviations["entries"], [])


if __name__ == "__main__":
    unittest.main()
