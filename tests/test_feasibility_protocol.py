# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate the issue #40 protocol freeze and reader-facing projection."""

from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "generate_protocol_appendix.py"
SPEC = importlib.util.spec_from_file_location("generate_protocol_appendix", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
PROTOCOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROTOCOL)


class FeasibilityProtocolTests(unittest.TestCase):
    """Keep protocol identity, authority, measures, and prose synchronized."""

    def mutated_errors(
        self,
        path: Path,
        mutate: Callable[[dict[str, Any]], None],
    ) -> list[str]:
        """Validate one in-memory JSON mutation without changing repository bytes."""
        original_loader = PROTOCOL.load_json
        mutated = copy.deepcopy(original_loader(ROOT, path))
        mutate(mutated)

        def load_with_override(project: Path, relative_path: Path) -> dict[str, Any]:
            if relative_path == path:
                return mutated
            return original_loader(project, relative_path)

        with mock.patch.object(PROTOCOL, "load_json", side_effect=load_with_override):
            return PROTOCOL.validate_protocol(ROOT)

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

    def test_successor_is_byte_locked_and_has_no_deviations(self) -> None:
        """The successor lock and empty audit log describe the exact protocol bytes."""
        lock = json.loads((ROOT / PROTOCOL.LOCK_PATH).read_text(encoding="utf-8"))
        deviations = json.loads(
            (ROOT / PROTOCOL.DEVIATIONS_PATH).read_text(encoding="utf-8")
        )
        self.assertEqual(lock["sha256"], PROTOCOL.protocol_sha256(ROOT))
        self.assertIs(lock["collection_authority"], False)
        self.assertEqual(lock["protocol_version"], "1.1.0")
        self.assertEqual(lock["amended_by"], "egohygiene/antidote#82")
        self.assertEqual(
            lock["supersedes"]["sha256"], PROTOCOL.HISTORICAL_PROTOCOL_SHA256
        )
        self.assertIs(deviations["qualifying_records_started"], False)
        self.assertIs(deviations["human_collection_started"], False)
        self.assertEqual(deviations["entries"], [])

    def test_version_1_0_0_remains_byte_exact_and_auditable(self) -> None:
        """A corrective successor must preserve its historical frozen predecessor."""
        self.assertEqual(
            PROTOCOL.file_sha256(ROOT, PROTOCOL.HISTORICAL_PROTOCOL_PATH),
            PROTOCOL.HISTORICAL_PROTOCOL_SHA256,
        )
        historical_lock = json.loads(
            (ROOT / PROTOCOL.HISTORICAL_LOCK_PATH).read_text(encoding="utf-8")
        )
        historical_deviations = json.loads(
            (ROOT / PROTOCOL.HISTORICAL_DEVIATIONS_PATH).read_text(encoding="utf-8")
        )
        self.assertEqual(
            historical_lock["sha256"], PROTOCOL.HISTORICAL_PROTOCOL_SHA256
        )
        self.assertEqual(historical_deviations["entries"], [])

    def test_assignment_space_drift_is_rejected(self) -> None:
        """The balanced design has 6! schedules, never six independent draws."""

        def mutate(protocol: dict[str, Any]) -> None:
            protocol["human_protocol"]["assignment"]["allowable_schedule_count"] = (
                46656
            )

        errors = self.mutated_errors(PROTOCOL.PROTOCOL_PATH, mutate)
        self.assertIn("H1 assignment space must equal 6! = 720 schedules", errors)

    def test_canonical_missingness_reason_drift_is_rejected(self) -> None:
        """Protocol and response-schema reason enums must remain byte-for-byte exact."""

        def mutate_protocol(protocol: dict[str, Any]) -> None:
            protocol["analysis_plan"]["missingness"]["canonical_reasons"][-1] = (
                "missing"
            )

        protocol_errors = self.mutated_errors(
            PROTOCOL.PROTOCOL_PATH, mutate_protocol
        )
        self.assertIn(
            "protocol missingness reasons must equal the canonical enum",
            protocol_errors,
        )

        def mutate_schema(schema: dict[str, Any]) -> None:
            schema["$defs"]["missingnessEntry"]["properties"]["reason"]["enum"][
                0
            ] = "missing"

        schema_errors = self.mutated_errors(PROTOCOL.RESPONSE_V2_PATH, mutate_schema)
        self.assertIn(
            "H1 response schema missingness reasons drifted from protocol",
            schema_errors,
        )

    def test_all_declined_responses_cannot_satisfy_progression(self) -> None:
        """Audit-complete declines must never be promoted to usable observations."""

        def mutate(protocol: dict[str, Any]) -> None:
            analysis = protocol["analysis_plan"]
            analysis["response_completeness"]["usable_voluntary_value"] = (
                "An audit-complete decline is a usable response."
            )
            progression = protocol["progression_rule"]["proceed_only_if"]
            for index, criterion in enumerate(progression):
                progression[index] = criterion.replace(
                    "does not count as usable", "counts as usable"
                )

        errors = self.mutated_errors(PROTOCOL.PROTOCOL_PATH, mutate)
        self.assertIn(
            "usable voluntary response must exclude declined fields",
            errors,
        )
        self.assertTrue(
            any(
                error.startswith("progression rule is missing criterion:")
                for error in errors
            )
        )

    def test_collection_authority_or_gate_activation_is_rejected(self) -> None:
        """The protocol cannot silently activate an unsafe or unreviewed H1 run."""

        def mutate(protocol: dict[str, Any]) -> None:
            protocol["collection_authority"] = True
            protocol["human_collection_activation_gates"][0]["satisfied"] = True

        errors = self.mutated_errors(PROTOCOL.PROTOCOL_PATH, mutate)
        self.assertIn("protocol collection_authority must equal False", errors)
        self.assertIn(
            "every human-collection activation gate must remain false",
            errors,
        )

    def test_future_deviations_are_shape_checked_not_blanket_rejected(self) -> None:
        """Post-start logs may append valid entries but reject malformed audit data."""
        protocol = json.loads(
            (ROOT / PROTOCOL.PROTOCOL_PATH).read_text(encoding="utf-8")
        )
        future_log = {
            "schema": "antidote.protocol-deviation-log/v1",
            "protocol_id": "ANT-PROT-FEAS-001",
            "protocol_version": "1.1.0",
            "protocol_sha256": PROTOCOL.protocol_sha256(ROOT),
            "status": "active-after-qualifying-record",
            "append_only": True,
            "qualifying_records_started": True,
            "human_collection_started": False,
            "entries": [
                {
                    "entry_id": "ANT-DEV-001",
                    "entry_type": "deviation",
                    "timestamp": "2026-09-08T12:34:56Z",
                    "rationale": "A declared timeout prevented one analyzer output.",
                    "affected_records": ["ANT-REC-T1-001"],
                    "evidence_impact": "Retain the failed attempt in its denominator.",
                    "author": "protocol operator",
                    "reviewer": "independent reviewer",
                    "disposition": "exclude only the unavailable analyzer value",
                }
            ],
        }
        self.assertEqual(
            PROTOCOL.validate_deviation_log(
                future_log, protocol, PROTOCOL.protocol_sha256(ROOT)
            ),
            [],
        )

        malformed = copy.deepcopy(future_log)
        del malformed["entries"][0]["reviewer"]
        malformed["entries"][0]["timestamp"] = "tomorrow"
        errors = PROTOCOL.validate_deviation_log(
            malformed, protocol, PROTOCOL.protocol_sha256(ROOT)
        )
        self.assertTrue(
            any("fields must equal" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("timestamp must be second-precision UTC" in error for error in errors),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
