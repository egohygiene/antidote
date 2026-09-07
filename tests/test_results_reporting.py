# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate the issue #41 empty-state Results reporting contract."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import tempfile
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

    def copied_validation_project(self) -> Path:
        """Copy only the governed inputs needed for one isolated mutation test."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        project = Path(temporary.name)
        required_paths = (
            REPORTING.REPORTING_PATH,
            REPORTING.PROTOCOL_PATH,
            REPORTING.LOCK_PATH,
            REPORTING.DEVIATIONS_PATH,
            REPORTING.RESPONSE_SCHEMA_PATH,
            REPORTING.H1_PUBLIC_SCHEMA_PATH,
            REPORTING.RESULTS_PATH,
            REPORTING.MANIFEST_PATH,
            REPORTING.LEDGER_PATH,
        )
        for relative in required_paths:
            destination = project / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        return project

    def write_json(
        self, project: Path, relative: Path, value: dict[str, object]
    ) -> None:
        """Write one deterministic JSON mutation in an isolated project."""
        destination = project / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(value, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def public_package(
        self,
        project: Path,
        record_id: str,
        package_kind: str,
        evidence_sha256: str,
        evidence_set_id: str = "ANT-ESET-H1-001",
    ) -> dict[str, object]:
        """Build one schema-valid, aggregate-only package for mutation tests."""
        reporting_bytes = (project / REPORTING.REPORTING_PATH).read_bytes()
        protocol = json.loads(
            (project / REPORTING.PROTOCOL_PATH).read_text(encoding="utf-8")
        )
        common: dict[str, object] = {
            "schema_version": "1.0.0",
            "package_id": f"ANT-PKG-H1-{package_kind.upper()}",
            "package_kind": package_kind,
            "source_record_id": record_id,
            "stage": "H1",
            "evidence_class": "human-aggregate",
            "source_revision": "a" * 40,
            "protocol": {
                "id": protocol["protocol_id"],
                "version": protocol["version"],
                "sha256": hashlib.sha256(
                    (project / REPORTING.PROTOCOL_PATH).read_bytes()
                ).hexdigest(),
            },
            "analysis_plan": {
                "id": "ANT-REPORT-RESULTS-001",
                "version": "1.1.0",
                "sha256": hashlib.sha256(reporting_bytes).hexdigest(),
                "deviation_log_sha256": hashlib.sha256(
                    (project / REPORTING.DEVIATIONS_PATH).read_bytes()
                ).hexdigest(),
            },
            "evidence_set": {
                "evidence_set_id": evidence_set_id,
                "commitment_profile": "antidote-evidence-set-commitment/v1",
                "evidence_set_sha256": evidence_sha256,
                "record_count": 18,
            },
            "complete_accounting": {"denominator": 18, "categories": []},
            "public_aggregates": [],
            "artifacts": [],
            "privacy_review": {
                "status": "passed",
                "scope": "aggregate-only-public-envelope",
            },
            "promotion": {"disposition": "not-promoted", "claim_ids": []},
        }
        accounting = {"denominator": 18, "categories": []}
        if package_kind == "flow":
            common.update(
                {
                    "assignment_commitment": {
                        "status": "committed",
                        "schedule_count": 720,
                        "commitment_sha256": "b" * 64,
                    },
                    "flow_accounting": accounting,
                    "interruptions": accounting,
                    "withdrawals": accounting,
                    "failures": accounting,
                    "exclusions": accounting,
                    "missingness": accounting,
                }
            )
        elif package_kind == "response":
            common.update(
                {
                    "instrument_version": "ANT-INSTRUMENT-H1-001-v1.1.0",
                    "response_accounting": accounting,
                    "correction_accounting": accounting,
                    "immediate_windows": accounting,
                    "later_windows": accounting,
                    "missingness": accounting,
                    "analysis_outputs": [],
                }
            )
        return common

    def test_reporting_contract_and_manuscript_are_synchronized(self) -> None:
        """The governed empty state must pass every cross-artifact check."""
        self.assertEqual(REPORTING.validate_reporting(ROOT), [])

    def test_generated_empty_state_tables_are_current(self) -> None:
        """Result tables must be deterministic projections, not hand-edited values."""
        for path, expected in REPORTING.expected_outputs(ROOT).items():
            self.assertEqual(path.read_text(encoding="utf-8"), expected, path)
            self.assertIn("GOVERNED EMPTY STATE", expected)
            self.assertIn("No qualifying values are registered", expected)
            self.assertIn(r"\textbf{Stage:}", expected)
            self.assertIn(r"\textbf{Evidence class:}", expected)

    def test_future_slots_resolve_source_protocol_and_analysis(self) -> None:
        """Every result slot must identify its complete promotion context."""
        contract = self.load_contract()
        sources = {record["id"]: record for record in contract["source_records"]}
        analyses = {analysis["id"]: analysis for analysis in contract["analyses"]}
        for slot in contract["result_slots"]:
            self.assertIn(slot["source_record_id"], sources, slot["id"])
            self.assertIn(slot["analysis_id"], analyses, slot["id"])
            self.assertEqual(slot["protocol_version"], "1.1.0", slot["id"])
            self.assertEqual(
                slot["stage"], sources[slot["source_record_id"]]["stage"], slot["id"]
            )
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

    def test_every_governed_protocol_leaf_has_an_analysis_and_slot(self) -> None:
        """Parent container pointers cannot hide an unreported terminal choice."""
        contract = self.load_contract()
        slotted_analyses = {slot["analysis_id"] for slot in contract["result_slots"]}
        covered = {
            pointer
            for analysis in contract["analyses"]
            if analysis["id"] in slotted_analyses
            for pointer in analysis["protocol_pointers"]
        }
        protocol = json.loads(
            (ROOT / REPORTING.PROTOCOL_PATH).read_text(encoding="utf-8")
        )
        required: set[str] = set()
        for root_pointer in REPORTING.LEAF_COVERAGE_ROOTS:
            required.update(
                REPORTING.terminal_leaf_pointers(protocol, root_pointer)
            )
        self.assertEqual(required - covered, set())
        self.assertEqual(
            {analysis["id"] for analysis in contract["analyses"]},
            slotted_analyses,
        )

    def test_parent_pointer_does_not_cover_an_unreported_leaf(self) -> None:
        """Mutating a leaf-mapped analysis to its parent must fail closed."""
        project = self.copied_validation_project()
        contract = json.loads(
            (project / REPORTING.REPORTING_PATH).read_text(encoding="utf-8")
        )
        sensitivity = next(
            analysis
            for analysis in contract["analyses"]
            if analysis["id"] == "ANT-AN-H1-SENSITIVITY-001"
        )
        sensitivity["protocol_pointers"] = [
            "#/analysis_plan/sensitivity_analyses"
        ]
        self.write_json(project, REPORTING.REPORTING_PATH, contract)
        errors = REPORTING.validate_reporting(project)
        self.assertTrue(
            any(
                "#/analysis_plan/sensitivity_analyses/0" in error
                and "not covered" in error
                for error in errors
            ),
            errors,
        )

    def test_orphan_visual_shell_mapping_is_rejected(self) -> None:
        """A shell-to-slot edge must be declared identically from both sides."""
        project = self.copied_validation_project()
        contract = json.loads(
            (project / REPORTING.REPORTING_PATH).read_text(encoding="utf-8")
        )
        slot = next(
            slot
            for slot in contract["result_slots"]
            if slot["id"] == "ANT-RES-T0-SLICE"
        )
        slot["visual_ids"].remove("ANT-TBL-004")
        self.write_json(project, REPORTING.REPORTING_PATH, contract)
        errors = REPORTING.validate_reporting(project)
        self.assertIn(
            "visual shell ANT-TBL-004 maps orphan result slot ANT-RES-T0-SLICE",
            errors,
        )

    def test_missingness_enum_drift_is_rejected(self) -> None:
        """Protocol and response-schema reason vocabularies must remain exact."""
        project = self.copied_validation_project()
        schema = json.loads(
            (project / REPORTING.RESPONSE_SCHEMA_PATH).read_text(encoding="utf-8")
        )
        schema["$defs"]["missingnessEntry"]["properties"]["reason"]["enum"][
            -1
        ] = "unavailable"
        self.write_json(project, REPORTING.RESPONSE_SCHEMA_PATH, schema)
        errors = REPORTING.validate_reporting(project)
        self.assertIn(
            "response-observation v2 missingness enum must exactly match the protocol",
            errors,
        )

    def test_unsafe_h1_path_and_metadata_key_are_rejected(self) -> None:
        """Public H1 metadata cannot point to raw paths or direct identifiers."""
        project = self.copied_validation_project()
        contract = json.loads(
            (project / REPORTING.REPORTING_PATH).read_text(encoding="utf-8")
        )
        flow = next(
            record
            for record in contract["source_records"]
            if record["id"] == "ANT-REC-H1-FLOW-001"
        )
        flow["path"] = "experiments/results/antidote-h1-flow-v1.json"
        flow["participant_id"] = "forbidden-direct-id"
        self.write_json(project, REPORTING.REPORTING_PATH, contract)
        errors = REPORTING.validate_reporting(project)
        self.assertTrue(
            any("path must end in .public.json" in error for error in errors)
        )
        self.assertTrue(
            any("forbidden public key participant_id" in error for error in errors)
        )

    def test_h1_source_evidence_set_drift_is_rejected(self) -> None:
        """Disabled physiology cannot silently join the active H1 evidence set."""
        project = self.copied_validation_project()
        contract = json.loads(
            (project / REPORTING.REPORTING_PATH).read_text(encoding="utf-8")
        )
        physiology = next(
            record
            for record in contract["source_records"]
            if record["id"] == "ANT-REC-H1-PHYS-001"
        )
        physiology["evidence_set_id"] = "ANT-ESET-H1-001"
        self.write_json(project, REPORTING.REPORTING_PATH, contract)
        errors = REPORTING.validate_reporting(project)
        self.assertIn(
            "H1 source record ANT-REC-H1-PHYS-001 evidence-set identity has drifted",
            errors,
        )

    def test_present_h1_packages_must_share_commitments_and_hashes(self) -> None:
        """Split aggregate envelopes cannot silently describe different evidence."""
        project = self.copied_validation_project()
        contract = json.loads(
            (project / REPORTING.REPORTING_PATH).read_text(encoding="utf-8")
        )
        selected = {
            "ANT-REC-H1-FLOW-001": "flow",
            "ANT-REC-H1-RESPONSE-001": "response",
        }
        for record in contract["source_records"]:
            if record["id"] in selected:
                record["state"] = "available-public-aggregate"
        self.write_json(project, REPORTING.REPORTING_PATH, contract)
        for record_id, package_kind in selected.items():
            record = next(
                record
                for record in contract["source_records"]
                if record["id"] == record_id
            )
            evidence_hash = "c" * 64 if package_kind == "flow" else "d" * 64
            package = self.public_package(
                project, record_id, package_kind, evidence_hash
            )
            self.write_json(project, Path(record["path"]), package)
        errors = REPORTING.validate_reporting(project)
        self.assertIn(
            "H1 public packages disagree on evidence-set commitment, hash, or "
            "aggregate record count",
            errors,
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
        h1_evidence_sets = {
            record["id"]: record["evidence_set_id"]
            for record in contract["source_records"]
            if record["stage"] == "H1"
        }
        self.assertEqual(h1_evidence_sets, REPORTING.H1_EVIDENCE_SET_IDS)

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
