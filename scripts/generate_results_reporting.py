#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate the empty Results contract and generate its table projections."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTING_PATH = Path("experiments/reporting/results-reporting-v1.1.json")
PROTOCOL_PATH = Path("experiments/protocols/antidote-feasibility-v1.1.json")
LOCK_PATH = Path("experiments/protocols/antidote-feasibility-v1.1.lock.json")
DEVIATIONS_PATH = Path(
    "experiments/protocols/antidote-feasibility-v1.1.deviations.json"
)
RESPONSE_SCHEMA_PATH = Path("contracts/schemas/response-observation.v2.schema.json")
H1_PUBLIC_SCHEMA_PATH = Path(
    "contracts/schemas/h1-public-result-envelope.v1.schema.json"
)
RESULTS_PATH = Path("paper/sections/05-results.tex")
MANIFEST_PATH = Path("paper/visuals/manifest.json")
LEDGER_PATH = Path("research/notes/CLAIM_LEDGER.md")

EXPECTED_STAGES = ["D0", "T0", "T1", "H1"]
EXPECTED_TABLES = {
    "ANT-TBL-004": "paper/tables/control-adherence-results.tex",
    "ANT-TBL-005": "paper/tables/exposure-response-completeness.tex",
    "ANT-TBL-006": "paper/tables/outcomes-accounting.tex",
}
EXPECTED_FIGURES = {"ANT-FIG-010", "ANT-FIG-011"}
EXPECTED_MANUSCRIPT_STATE = {
    "formal_study_run": False,
    "formal_human_results_collected": False,
    "t0_exit_gate_promoted": False,
    "t1_qualification_run": False,
    "h1_collection_started": False,
    "physiology_enabled": False,
}
EXPECTED_STAGE_STATES = {
    "D0": "design-record-available",
    "T0": "awaiting-ant-q03-exit-gate",
    "T1": "blocked-no-real-model",
    "H1": "blocked-no-collection-authority",
}
EXPECTED_ANALYSIS_REPORTING = {
    "effect_estimates": ["#/analysis_plan/secondary_within_person_estimands"],
    "uncertainty": ["#/analysis_plan/exact_randomization_analysis"],
    "visualizations": [
        "#/analysis_plan/primary_technical_summaries",
        "#/analysis_plan/primary_human_feasibility_summaries",
        "#/analysis_plan/exact_randomization_analysis",
    ],
    "missingness": ["#/analysis_plan/missingness"],
    "sensitivity_analyses": ["#/analysis_plan/sensitivity_analyses"],
    "exact_randomization_analysis": [
        "#/analysis_plan/exact_randomization_analysis"
    ],
    "progression_decision": ["#/progression_rule"],
}
LEAF_COVERAGE_ROOTS = (
    "#/analysis_plan/primary_technical_summaries",
    "#/analysis_plan/primary_human_feasibility_summaries",
    "#/analysis_plan/secondary_within_person_estimands",
    "#/analysis_plan/sensitivity_analyses",
    "#/analysis_plan/exact_randomization_analysis",
    "#/analysis_plan/missingness",
    "#/analysis_plan/null_and_negative_rule",
    "#/progression_rule",
)
EXPECTED_MISSINGNESS_REASONS = [
    "not_prompted",
    "declined",
    "missed_window",
    "technical_failure",
    "interrupted",
    "not_applicable",
]
EXPECTED_SHARED_H1_EVIDENCE_SET_ID = "ANT-ESET-H1-001"
EXPECTED_PHYSIOLOGY_EVIDENCE_SET_ID = "ANT-ESET-H1-PHYS-001"
H1_COMMON_PACKAGE_FIELDS = {
    "schema_version",
    "package_id",
    "package_kind",
    "source_record_id",
    "stage",
    "evidence_class",
    "source_revision",
    "protocol",
    "analysis_plan",
    "evidence_set",
    "complete_accounting",
    "public_aggregates",
    "artifacts",
    "privacy_review",
    "promotion",
}
H1_PACKAGE_KINDS = {
    "ANT-REC-H1-FLOW-001": "flow",
    "ANT-REC-H1-RESPONSE-001": "response",
    "ANT-REC-H1-SAFETY-001": "safety",
    "ANT-REC-H1-AUDIT-001": "audit",
    "ANT-REC-H1-PHYS-001": "physiology",
}
H1_EVIDENCE_SET_IDS = {
    record_id: (
        EXPECTED_PHYSIOLOGY_EVIDENCE_SET_ID
        if record_id == "ANT-REC-H1-PHYS-001"
        else EXPECTED_SHARED_H1_EVIDENCE_SET_ID
    )
    for record_id in H1_PACKAGE_KINDS
}
FORBIDDEN_PUBLIC_METADATA_KEYS = {
    "participant_id",
    "participant_ids",
    "user_id",
    "user_ids",
    "person_id",
    "person_ids",
    "subject_id",
    "subject_ids",
    "session_id",
    "session_ids",
    "consent_id",
    "consent_ids",
    "consent_grant_id",
    "consent_grant_ids",
    "source_event_id",
    "source_event_ids",
    "event_id",
    "event_ids",
    "exposure_id",
    "exposure_ids",
    "response_id",
    "response_ids",
    "participant_timestamp",
    "participant_timestamps",
    "event_timestamp",
    "event_timestamps",
    "observed_at",
    "collected_at",
    "raw_data",
    "raw_payload",
    "raw_payloads",
    "raw_path",
    "raw_paths",
    "raw_records",
    "raw_responses",
    "free_text_responses",
    "row_level_records",
    "row_level_observations",
    "private_path",
    "private_paths",
    "private_record_id",
    "private_record_ids",
    "private_index_path",
    "payload_path",
    "payload_paths",
    "per_record_hash",
    "per_record_hashes",
    "record_hash",
    "record_hashes",
    "row_id",
    "row_ids",
    "stable_pseudonym",
    "stable_pseudonyms",
    "commitment_nonce",
    "participant_name",
    "email",
    "phone",
}
ALLOWED_EVIDENCE_CLASSES = {
    "decided",
    "technical-synthetic",
    "technical",
    "observed",
    "self-reported",
    "observed-or-self-reported",
    "self-reported-or-observed",
    "unavailable",
}
FORBIDDEN_RESULT_KEYS = {
    "observed_value",
    "count",
    "numerator",
    "denominator",
    "estimate",
    "effect_size",
    "p_value",
    "confidence_interval",
}
STATE_LABELS = {
    "awaiting-ant-q03-exit-gate": "Awaiting issue #18; no qualifying package",
    "blocked-no-real-model": "Blocked; no qualified real model or run",
    "blocked-no-collection-authority": "Blocked; no collection authority or records",
    "disabled-requires-amendment": "Disabled under protocol v1.1.0",
    "design-record-available": "Design artifact only; not performance evidence",
}


class DuplicateKeyError(ValueError):
    """Raised when a JSON object repeats a key."""


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Construct a JSON object while rejecting silently overwritten keys."""
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(project: Path, relative: Path) -> dict[str, object]:
    """Load one strict repository JSON object."""
    value = json.loads(
        (project / relative).read_text(encoding="utf-8"),
        object_pairs_hook=unique_object,
    )
    if not isinstance(value, dict):
        raise TypeError(f"JSON root must be an object: {relative}")
    return value


def repository_path(project: Path, value: object) -> Path:
    """Resolve a non-empty repository-relative path without escape."""
    if not isinstance(value, str) or not value:
        raise ValueError("path must be a non-empty string")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"path must remain repository-relative: {value}")
    resolved = (project / relative).resolve()
    if resolved != project and project not in resolved.parents:
        raise ValueError(f"path escapes repository: {value}")
    return resolved


def resolve_json_pointer(document: object, pointer: str) -> object:
    """Resolve one RFC 6901 pointer used by a reporting analysis."""
    if not pointer.startswith("#/"):
        raise ValueError(f"protocol pointer must begin with #/: {pointer}")
    current = document
    for raw_token in pointer[2:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(token)]
        elif isinstance(current, dict):
            current = current[token]
        else:
            raise KeyError(token)
    return current


def pointer_token(value: object) -> str:
    """Encode one value as an RFC 6901 pointer token."""
    return str(value).replace("~", "~0").replace("/", "~1")


def terminal_leaf_pointers(document: object, pointer: str) -> set[str]:
    """Return every scalar leaf pointer below one governed protocol pointer."""
    root = resolve_json_pointer(document, pointer)
    leaves: set[str] = set()

    def visit(value: object, current: str) -> None:
        if isinstance(value, dict) and value:
            for key, child in value.items():
                visit(child, f"{current}/{pointer_token(key)}")
            return
        if isinstance(value, list) and value:
            for index, child in enumerate(value):
                visit(child, f"{current}/{index}")
            return
        leaves.add(current)

    visit(root, pointer)
    return leaves


def nested_key_paths(value: object, prefix: str = "#") -> dict[str, set[str]]:
    """Return the JSON paths at which each nested object key appears."""
    found: dict[str, set[str]] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}/{pointer_token(key)}"
            found.setdefault(key, set()).add(path)
            child_paths = nested_key_paths(child, path)
            for child_key, paths in child_paths.items():
                found.setdefault(child_key, set()).update(paths)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_paths = nested_key_paths(child, f"{prefix}/{index}")
            for child_key, paths in child_paths.items():
                found.setdefault(child_key, set()).update(paths)
    return found


def validate_public_package_structure(
    package: dict[str, object],
    schema: dict[str, object],
    required_fields: set[str],
) -> list[str]:
    """Validate the privacy-critical shape even when jsonschema is unavailable."""
    errors: list[str] = []
    schema_required = schema.get("required", [])
    schema_properties = schema.get("properties", {})
    if not isinstance(schema_required, list) or not isinstance(
        schema_properties, dict
    ):
        return ["H1 public schema has invalid root required/properties metadata"]
    required = set(str(field) for field in schema_required) | required_fields
    missing = required - set(package)
    if missing:
        errors.append(
            "public package is missing fields: " + ", ".join(sorted(missing))
        )
    if schema.get("additionalProperties") is False:
        unknown = set(package) - set(schema_properties)
        if unknown:
            errors.append(
                "public package contains fields outside the public schema: "
                + ", ".join(sorted(unknown))
            )

    definitions = schema.get("$defs", {})
    nested_definitions = {
        "protocol": "versionedArtifact",
        "analysis_plan": "analysisPlan",
        "evidence_set": "evidenceSet",
    }
    for field, definition_name in nested_definitions.items():
        value = package.get(field)
        definition = (
            definitions.get(definition_name, {})
            if isinstance(definitions, dict)
            else {}
        )
        expected = (
            definition.get("required", []) if isinstance(definition, dict) else []
        )
        if not isinstance(value, dict):
            errors.append(f"public package field {field} must be an object")
        elif not isinstance(expected, list) or not set(expected) <= set(value):
            errors.append(f"public package field {field} is structurally incomplete")

    unsafe_paths = nested_key_paths(package)
    for key in sorted(FORBIDDEN_PUBLIC_METADATA_KEYS & set(unsafe_paths)):
        errors.append(
            f"public package contains forbidden metadata key {key}: "
            + ", ".join(sorted(unsafe_paths[key]))
        )
    return errors


def validate_with_jsonschema_if_available(
    instance: dict[str, object], schema: dict[str, object]
) -> list[str]:
    """Use Draft 2020-12 validation when the optional dependency is installed."""
    try:
        import jsonschema  # type: ignore[import-not-found]
    except ImportError:
        return []
    validator = jsonschema.Draft202012Validator(schema)
    errors: list[str] = []
    for error in sorted(
        validator.iter_errors(instance),
        key=lambda item: [str(token) for token in item.path],
    ):
        location = "#/" + "/".join(pointer_token(token) for token in error.path)
        errors.append(f"public package schema error at {location}: {error.message}")
    return errors


def tex_escape(value: object) -> str:
    """Escape one compact reporting label for deterministic LaTeX."""
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    normalized = re.sub(r"\s+", " ", str(value)).strip()
    return "".join(replacements.get(character, character) for character in normalized)


def nested_keys(value: object) -> set[str]:
    """Return every object key in a nested JSON value."""
    if isinstance(value, dict):
        return set(value) | {
            key for child in value.values() for key in nested_keys(child)
        }
    if isinstance(value, list):
        return {key for child in value for key in nested_keys(child)}
    return set()


def validate_reporting(project: Path = ROOT) -> list[str]:
    """Return deterministic cross-artifact Results reporting errors."""
    errors: list[str] = []
    try:
        reporting = load_json(project, REPORTING_PATH)
        protocol = load_json(project, PROTOCOL_PATH)
        lock = load_json(project, LOCK_PATH)
        deviations = load_json(project, DEVIATIONS_PATH)
        response_schema = load_json(project, RESPONSE_SCHEMA_PATH)
        h1_public_schema = load_json(project, H1_PUBLIC_SCHEMA_PATH)
        manifest = load_json(project, MANIFEST_PATH)
        reporting_bytes = (project / REPORTING_PATH).read_bytes()
        deviation_bytes = (project / DEVIATIONS_PATH).read_bytes()
    except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        return [f"Results reporting inputs are invalid: {error}"]

    expected_identity = {
        "schema": "antidote.results-reporting/v1",
        "reporting_id": "ANT-REPORT-RESULTS-001",
        "version": "1.1.0",
        "status": "governed-empty-reporting-contract",
        "governed_by": "egohygiene/antidote#41",
        "amended_by": "egohygiene/antidote#82",
    }
    for field, expected in expected_identity.items():
        if reporting.get(field) != expected:
            errors.append(f"reporting contract {field} must equal {expected!r}")

    if reporting.get("current_manuscript_state") != EXPECTED_MANUSCRIPT_STATE:
        errors.append("current manuscript state must preserve the no-results boundary")
    forbidden = FORBIDDEN_RESULT_KEYS & nested_keys(reporting)
    if forbidden:
        errors.append(
            "empty reporting contract contains result-value keys: "
            + ", ".join(sorted(forbidden))
        )

    protocol_ref = reporting.get("protocol", {})
    if not isinstance(protocol_ref, dict):
        errors.append("reporting protocol reference must be an object")
        protocol_ref = {}
    protocol_bytes = (project / PROTOCOL_PATH).read_bytes()
    protocol_hash = hashlib.sha256(protocol_bytes).hexdigest()
    expected_protocol_ref = {
        "protocol_id": protocol.get("protocol_id"),
        "protocol_version": protocol.get("version"),
        "protocol_path": PROTOCOL_PATH.as_posix(),
        "lock_path": LOCK_PATH.as_posix(),
        "sha256": protocol_hash,
    }
    if protocol_ref != expected_protocol_ref:
        errors.append("reporting contract protocol identity or byte lock has drifted")
    if lock.get("sha256") != protocol_hash:
        errors.append("frozen protocol lock does not match protocol bytes")
    expected_lock_identity = {
        "protocol_id": protocol.get("protocol_id"),
        "protocol_version": protocol.get("version"),
        "protocol_path": PROTOCOL_PATH.as_posix(),
        "collection_authority": False,
    }
    for field, expected in expected_lock_identity.items():
        if lock.get(field) != expected:
            errors.append(f"frozen protocol lock {field} has drifted")
    expected_deviation_identity = {
        "protocol_id": protocol.get("protocol_id"),
        "protocol_version": protocol.get("version"),
        "protocol_sha256": protocol_hash,
    }
    for field, expected in expected_deviation_identity.items():
        if deviations.get(field) != expected:
            errors.append(f"protocol deviation log {field} has drifted")
    if protocol.get("collection_authority") is not False:
        errors.append("reporting contract requires protocol collection authority false")

    analysis_plan = protocol.get("analysis_plan", {})
    missingness_plan = (
        analysis_plan.get("missingness", {})
        if isinstance(analysis_plan, dict)
        else {}
    )
    protocol_missingness = (
        missingness_plan.get("canonical_reasons")
        if isinstance(missingness_plan, dict)
        else None
    )
    if protocol_missingness != EXPECTED_MISSINGNESS_REASONS:
        errors.append("protocol canonical missingness reasons have drifted")
    response_definitions = response_schema.get("$defs", {})
    missingness_definition = (
        response_definitions.get("missingnessEntry", {})
        if isinstance(response_definitions, dict)
        else {}
    )
    missingness_properties = (
        missingness_definition.get("properties", {})
        if isinstance(missingness_definition, dict)
        else {}
    )
    reason_property = (
        missingness_properties.get("reason", {})
        if isinstance(missingness_properties, dict)
        else {}
    )
    schema_missingness = (
        reason_property.get("enum") if isinstance(reason_property, dict) else None
    )
    if schema_missingness != EXPECTED_MISSINGNESS_REASONS:
        errors.append(
            "response-observation v2 missingness enum must exactly match the protocol"
        )

    expected_h1_schema_id = (
        "urn:egohygiene:antidote:schema:h1-public-result-envelope:v1"
    )
    if h1_public_schema.get("$id") != expected_h1_schema_id:
        errors.append("H1 public result-envelope schema identity has drifted")
    if h1_public_schema.get("additionalProperties") is not False:
        errors.append("H1 public result-envelope schema must reject unknown fields")
    schema_common_fields = h1_public_schema.get("required", [])
    if not isinstance(schema_common_fields, list) or set(
        schema_common_fields
    ) != H1_COMMON_PACKAGE_FIELDS:
        errors.append("H1 public result-envelope common fields have drifted")
    h1_definitions = h1_public_schema.get("$defs", {})
    h1_analysis_plan = (
        h1_definitions.get("analysisPlan", {})
        if isinstance(h1_definitions, dict)
        else {}
    )
    h1_analysis_properties = (
        h1_analysis_plan.get("properties", {})
        if isinstance(h1_analysis_plan, dict)
        else {}
    )
    h1_analysis_id = (
        h1_analysis_properties.get("id", {})
        if isinstance(h1_analysis_properties, dict)
        else {}
    )
    if (
        not isinstance(h1_analysis_id, dict)
        or h1_analysis_id.get("const") != "ANT-REPORT-RESULTS-001"
    ):
        errors.append("H1 public analysis-plan schema identity has drifted")

    policies = reporting.get("evidence_policy", {})
    required_policies = {
        "empty_state",
        "synthetic_state",
        "technical_state",
        "human_state",
        "nonpositive_state",
    }
    if not isinstance(policies, dict) or any(
        not isinstance(policies.get(key), str) or not policies.get(key)
        for key in required_policies
    ):
        errors.append("reporting contract evidence policies are incomplete")

    public_policy = reporting.get("public_package_policy", {})
    if not isinstance(public_policy, dict):
        errors.append("reporting contract public-package policy must be an object")
        public_policy = {}
    if (
        public_policy.get("shared_h1_evidence_set_id")
        != EXPECTED_SHARED_H1_EVIDENCE_SET_ID
    ):
        errors.append("public-package policy H1 evidence-set identity has drifted")
    policy_fields = public_policy.get("required_common_fields")
    if (
        not isinstance(policy_fields, list)
        or len(policy_fields) != len(set(map(str, policy_fields)))
        or set(policy_fields) != H1_COMMON_PACKAGE_FIELDS
    ):
        errors.append("public-package policy common-field inventory has drifted")
    for field in (
        "evidence_set_rule",
        "commitment_rule",
        "artifacts_rule",
        "private_index_rule",
        "physiology_rule",
    ):
        if not isinstance(public_policy.get(field), str) or not public_policy.get(
            field
        ):
            errors.append(f"public-package policy requires {field}")
    unsafe_reporting_paths = nested_key_paths(reporting)
    for key in sorted(FORBIDDEN_PUBLIC_METADATA_KEYS & set(unsafe_reporting_paths)):
        errors.append(
            f"reporting metadata contains forbidden public key {key}: "
            + ", ".join(sorted(unsafe_reporting_paths[key]))
        )

    analysis_reporting = reporting.get("analysis_reporting", {})
    if not isinstance(analysis_reporting, dict):
        errors.append("analysis reporting dimensions must be an object")
        analysis_reporting = {}
    elif set(analysis_reporting) != set(EXPECTED_ANALYSIS_REPORTING):
        errors.append("analysis reporting dimensions are incomplete")
    for dimension, expected_pointers in EXPECTED_ANALYSIS_REPORTING.items():
        policy = analysis_reporting.get(dimension, {})
        if not isinstance(policy, dict):
            errors.append(f"analysis reporting dimension {dimension} must be an object")
            continue
        if policy.get("status") != "not-run":
            errors.append(
                f"analysis reporting dimension {dimension} must remain not-run"
            )
        if policy.get("protocol_pointers") != expected_pointers:
            errors.append(
                f"analysis reporting dimension {dimension} protocol pointers "
                "have drifted"
            )
        else:
            for pointer in expected_pointers:
                try:
                    resolve_json_pointer(protocol, pointer)
                except (ValueError, KeyError, IndexError) as error:
                    errors.append(
                        f"analysis reporting dimension {dimension} has an invalid "
                        f"protocol pointer {pointer}: {error}"
                    )
        if not isinstance(policy.get("reporting_rule"), str) or not policy.get(
            "reporting_rule"
        ):
            errors.append(f"analysis reporting dimension {dimension} requires a rule")
    expected_analysis_visuals = EXPECTED_FIGURES | set(EXPECTED_TABLES)
    visualization_policy = analysis_reporting.get("visualizations", {})
    visualization_ids = (
        visualization_policy.get("visual_ids", [])
        if isinstance(visualization_policy, dict)
        else []
    )
    if (
        not isinstance(visualization_ids, list)
        or any(not isinstance(visual_id, str) for visual_id in visualization_ids)
        or set(visualization_ids) != expected_analysis_visuals
    ):
        errors.append("analysis reporting visual inventory has drifted")

    gates = reporting.get("promotion_gates", [])
    if (
        not isinstance(gates, list)
        or [gate.get("stage") for gate in gates] != EXPECTED_STAGES
    ):
        errors.append(f"promotion gates must be ordered as {EXPECTED_STAGES}")
        gates = []
    for gate in gates:
        stage = gate.get("stage")
        if gate.get("current_state") != EXPECTED_STAGE_STATES.get(stage):
            errors.append(f"promotion gate {stage} has an invalid current state")
        for field in ("gate", "required_review", "never_supports"):
            if not isinstance(gate.get(field), str) or not gate.get(field):
                errors.append(f"promotion gate {stage} is missing {field}")

    source_records = reporting.get("source_records", [])
    if not isinstance(source_records, list) or not source_records:
        errors.append("reporting contract must define source records")
        source_records = []
    source_by_id: dict[str, dict[str, object]] = {}
    public_h1_packages: list[tuple[str, dict[str, object]]] = []
    for record in source_records:
        if not isinstance(record, dict):
            errors.append("every source record must be an object")
            continue
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id:
            errors.append("source record requires an ID")
            continue
        if record_id in source_by_id:
            errors.append(f"duplicate source record ID: {record_id}")
        source_by_id[record_id] = record
        if record.get("stage") not in EXPECTED_STAGES:
            errors.append(f"source record {record_id} has an invalid stage")
        required_fields = record.get("required_package_fields")
        if (
            not isinstance(required_fields, list)
            or not required_fields
            or any(not isinstance(field, str) or not field for field in required_fields)
        ):
            errors.append(f"source record {record_id} requires package fields")
            required_field_set: set[str] = set()
        else:
            required_field_set = set(required_fields)
            if len(required_field_set) != len(required_fields):
                errors.append(
                    f"source record {record_id} repeats required package fields"
                )

        is_h1 = record.get("stage") == "H1"
        if is_h1:
            if not str(record.get("path", "")).endswith(".public.json"):
                errors.append(
                    f"H1 source record {record_id} path must end in .public.json"
                )
            if record.get("schema_path") != H1_PUBLIC_SCHEMA_PATH.as_posix():
                errors.append(
                    f"H1 source record {record_id} must use the public-envelope schema"
                )
            if record.get("public_package") is not True:
                errors.append(
                    f"H1 source record {record_id} must be public-package only"
                )
            expected_evidence_set_id = H1_EVIDENCE_SET_IDS.get(record_id)
            if record.get("evidence_set_id") != expected_evidence_set_id:
                errors.append(
                    f"H1 source record {record_id} evidence-set identity has drifted"
                )
            if (
                record_id == "ANT-REC-H1-PHYS-001"
                and record.get("state") != "disabled-requires-amendment"
            ):
                errors.append(
                    "H1 physiology source must remain disabled pending amendment"
                )
            missing_common = H1_COMMON_PACKAGE_FIELDS - required_field_set
            if missing_common:
                errors.append(
                    f"H1 source record {record_id} omits common public fields: "
                    + ", ".join(sorted(missing_common))
                )
        try:
            path = repository_path(project, record.get("path"))
            state = record.get("state")
            if state == "available-design-artifact" and not path.is_file():
                errors.append(f"available design source is missing: {record_id}")
            if (
                state in {"not-created", "disabled-requires-amendment"}
                and path.exists()
            ):
                errors.append(
                    f"unreviewed result source exists despite empty state: {record_id}"
                )
            if is_h1 and path.is_file():
                try:
                    package = load_json(project, Path(str(record.get("path"))))
                except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
                    errors.append(f"H1 public package {record_id} is invalid: {error}")
                else:
                    for package_error in validate_public_package_structure(
                        package, h1_public_schema, required_field_set
                    ):
                        errors.append(f"H1 public package {record_id} {package_error}")
                    for package_error in validate_with_jsonschema_if_available(
                        package, h1_public_schema
                    ):
                        errors.append(f"H1 public package {record_id} {package_error}")
                    if package.get("source_record_id") != record_id:
                        errors.append(
                            f"H1 public package {record_id} source identity has drifted"
                        )
                    if package.get("stage") != "H1":
                        errors.append(
                            f"H1 public package {record_id} stage has drifted"
                        )
                    expected_kind = H1_PACKAGE_KINDS.get(record_id)
                    if (
                        expected_kind is None
                        or package.get("package_kind") != expected_kind
                    ):
                        errors.append(
                            f"H1 public package {record_id} package kind has drifted"
                        )
                    public_h1_packages.append((record_id, package))
        except ValueError as error:
            errors.append(f"source record {record_id} {error}")

    h1_source_ids = {
        record_id
        for record_id, record in source_by_id.items()
        if record.get("stage") == "H1"
    }
    if h1_source_ids != set(H1_PACKAGE_KINDS):
        errors.append("H1 source-record inventory has drifted")

    if public_h1_packages:
        expected_protocol_identity = {
            "id": protocol.get("protocol_id"),
            "version": protocol.get("version"),
            "sha256": protocol_hash,
        }
        expected_analysis_identity = {
            "id": reporting.get("reporting_id"),
            "version": reporting.get("version"),
            "sha256": hashlib.sha256(reporting_bytes).hexdigest(),
            "deviation_log_sha256": hashlib.sha256(deviation_bytes).hexdigest(),
        }
        shared_commitments: dict[str, object] | None = None
        for record_id, package in public_h1_packages:
            if package.get("protocol") != expected_protocol_identity:
                errors.append(
                    f"H1 public package {record_id} protocol identity or hash drifted"
                )
            if package.get("analysis_plan") != expected_analysis_identity:
                errors.append(
                    f"H1 public package {record_id} analysis or deviation hash drifted"
                )
            evidence_set = package.get("evidence_set")
            if not isinstance(evidence_set, dict):
                errors.append(f"H1 public package {record_id} lacks an evidence set")
                continue
            expected_evidence_set_id = H1_EVIDENCE_SET_IDS.get(record_id)
            if evidence_set.get("evidence_set_id") != expected_evidence_set_id:
                errors.append(
                    f"H1 public package {record_id} evidence-set identity drifted"
                )
            if expected_evidence_set_id == EXPECTED_SHARED_H1_EVIDENCE_SET_ID:
                if shared_commitments is None:
                    shared_commitments = evidence_set
                elif evidence_set != shared_commitments:
                    errors.append(
                        "H1 public packages disagree on evidence-set commitment, "
                        "hash, or aggregate record count"
                    )

    analyses = reporting.get("analyses", [])
    if not isinstance(analyses, list) or not analyses:
        errors.append("reporting contract must define analyses")
        analyses = []
    analysis_by_id: dict[str, dict[str, object]] = {}
    for analysis in analyses:
        if not isinstance(analysis, dict):
            errors.append("every analysis must be an object")
            continue
        analysis_id = analysis.get("id")
        if not isinstance(analysis_id, str) or not analysis_id:
            errors.append("analysis requires an ID")
            continue
        if analysis_id in analysis_by_id:
            errors.append(f"duplicate analysis ID: {analysis_id}")
        analysis_by_id[analysis_id] = analysis
        if analysis.get("source_record_id") not in source_by_id:
            errors.append(f"analysis {analysis_id} references an unknown source record")
        pointers = analysis.get("protocol_pointers")
        if (
            not isinstance(pointers, list)
            or not pointers
            or any(not isinstance(pointer, str) for pointer in pointers)
        ):
            errors.append(f"analysis {analysis_id} requires protocol pointers")
        else:
            if len(pointers) != len(set(pointers)):
                errors.append(f"analysis {analysis_id} repeats protocol pointers")
            for pointer in pointers:
                try:
                    resolve_json_pointer(protocol, pointer)
                except (ValueError, KeyError, IndexError) as error:
                    errors.append(
                        f"analysis {analysis_id} has an invalid protocol pointer "
                        f"{pointer}: {error}"
                    )
        if analysis.get("status") not in {
            "design-review-only",
            "not-run",
            "disabled-requires-amendment",
        }:
            errors.append(f"analysis {analysis_id} cannot report a completed result")

    manifest_visuals = {
        visual.get("id"): visual
        for visual in manifest.get("visuals", [])
        if isinstance(visual, dict)
    }
    results_text = (project / RESULTS_PATH).read_text(encoding="utf-8")
    section_labels = set(re.findall(r"\\label\{([^{}]+)\}", results_text))
    slots = reporting.get("result_slots", [])
    if not isinstance(slots, list) or not slots:
        errors.append("reporting contract must define result slots")
        slots = []
    slot_by_id: dict[str, dict[str, object]] = {}
    for slot in slots:
        if not isinstance(slot, dict):
            errors.append("every result slot must be an object")
            continue
        slot_id = slot.get("id")
        if not isinstance(slot_id, str) or not slot_id:
            errors.append("result slot requires an ID")
            continue
        if slot_id in slot_by_id:
            errors.append(f"duplicate result slot ID: {slot_id}")
        slot_by_id[slot_id] = slot
        source = source_by_id.get(str(slot.get("source_record_id")))
        analysis = analysis_by_id.get(str(slot.get("analysis_id")))
        if source is None:
            errors.append(f"result slot {slot_id} references an unknown source record")
        if analysis is None:
            errors.append(f"result slot {slot_id} references an unknown analysis")
        if source is not None and source.get("stage") != slot.get("stage"):
            errors.append(f"result slot {slot_id} stage disagrees with its source")
        if analysis is not None and analysis.get("source_record_id") != slot.get(
            "source_record_id"
        ):
            errors.append(f"result slot {slot_id} analysis uses a different source")
        if slot.get("protocol_version") != protocol.get("version"):
            errors.append(f"result slot {slot_id} protocol version has drifted")
        if slot.get("stage") not in EXPECTED_STAGES:
            errors.append(f"result slot {slot_id} has an invalid stage")
        if slot.get("section_label") not in section_labels:
            errors.append(f"result slot {slot_id} section label does not resolve")
        if slot.get("evidence_class") not in ALLOWED_EVIDENCE_CLASSES:
            errors.append(f"result slot {slot_id} has an invalid evidence class")
        if slot.get("stage") != "H1" and slot.get(
            "current_state"
        ) != EXPECTED_STAGE_STATES.get(slot.get("stage")):
            errors.append(f"result slot {slot_id} has an invalid stage state")
        if slot.get("stage") == "H1" and slot.get("current_state") not in {
            "blocked-no-collection-authority",
            "disabled-requires-amendment",
        }:
            errors.append(f"human result slot {slot_id} must remain blocked")
        for field in ("display_name", "reporting_rule", "prohibited_inference"):
            if not isinstance(slot.get(field), str) or not slot.get(field):
                errors.append(f"result slot {slot_id} is missing {field}")
        visual_ids = slot.get("visual_ids")
        if (
            not isinstance(visual_ids, list)
            or any(not isinstance(visual_id, str) for visual_id in visual_ids)
            or any(
                visual_id not in manifest_visuals
                for visual_id in visual_ids
                if isinstance(visual_id, str)
            )
        ):
            errors.append(f"result slot {slot_id} has invalid visual IDs")
        elif len(visual_ids) != len(set(visual_ids)):
            errors.append(f"result slot {slot_id} repeats visual IDs")

    analyses_with_slots = {
        str(slot.get("analysis_id"))
        for slot in slot_by_id.values()
        if slot.get("analysis_id") in analysis_by_id
    }
    for analysis_id in sorted(set(analysis_by_id) - analyses_with_slots):
        errors.append(f"analysis {analysis_id} is not mapped to any result slot")

    covered_leaf_pointers: set[str] = set()
    for analysis_id in analyses_with_slots:
        pointers = analysis_by_id[analysis_id].get("protocol_pointers", [])
        if isinstance(pointers, list):
            covered_leaf_pointers.update(
                pointer for pointer in pointers if isinstance(pointer, str)
            )
    required_leaf_pointers: set[str] = set()
    for root_pointer in LEAF_COVERAGE_ROOTS:
        try:
            required_leaf_pointers.update(
                terminal_leaf_pointers(protocol, root_pointer)
            )
        except (ValueError, KeyError, IndexError) as error:
            errors.append(
                f"required protocol coverage root {root_pointer} is invalid: {error}"
            )
    for pointer in sorted(required_leaf_pointers - covered_leaf_pointers):
        errors.append(
            f"protocol analysis leaf is not covered by a named analysis and slot: "
            f"{pointer}"
        )

    table_shells = reporting.get("table_shells", [])
    table_outputs: dict[str, str] = {}
    shell_pairs: set[tuple[str, str]] = set()
    for shell in table_shells if isinstance(table_shells, list) else []:
        if not isinstance(shell, dict):
            errors.append("every table shell must be an object")
            continue
        visual_id = shell.get("visual_id")
        output_path = shell.get("output_path")
        if visual_id in table_outputs:
            errors.append(f"duplicate table shell: {visual_id}")
        if isinstance(visual_id, str) and isinstance(output_path, str):
            table_outputs[visual_id] = output_path
        slot_ids = shell.get("slot_ids")
        if not isinstance(slot_ids, list) or not slot_ids:
            errors.append(f"table shell {visual_id} requires result slots")
            continue
        if len(slot_ids) != len(set(map(str, slot_ids))):
            errors.append(f"table shell {visual_id} repeats result slots")
        for slot_id in slot_ids:
            if slot_id not in slot_by_id:
                errors.append(
                    f"table shell {visual_id} references unknown slot {slot_id}"
                )
            if isinstance(visual_id, str) and isinstance(slot_id, str):
                shell_pairs.add((slot_id, visual_id))
        visual = manifest_visuals.get(visual_id)
        if visual is None or visual.get("kind") != "table":
            errors.append(f"table shell {visual_id} lacks a manifest table")
        elif visual.get("state") != "final" or visual.get("status") != "active":
            errors.append(
                f"table shell {visual_id} must be an active final empty-state table"
            )
        try:
            output = repository_path(project, output_path)
            if output.parent != (project / "paper" / "tables").resolve():
                errors.append(
                    f"table shell {visual_id} output must remain in paper/tables"
                )
        except ValueError as error:
            errors.append(f"table shell {visual_id} {error}")
    if table_outputs != EXPECTED_TABLES:
        errors.append("Results table-shell inventory has drifted")

    figure_shells = reporting.get("figure_shells", [])
    figure_ids: set[str] = set()
    for shell in figure_shells if isinstance(figure_shells, list) else []:
        if not isinstance(shell, dict):
            errors.append("every figure shell must be an object")
            continue
        visual_id = shell.get("visual_id")
        if str(visual_id) in figure_ids:
            errors.append(f"duplicate figure shell: {visual_id}")
        figure_ids.add(str(visual_id))
        visual = manifest_visuals.get(visual_id)
        if visual is None or visual.get("kind") != "figure":
            errors.append(f"figure shell {visual_id} lacks a manifest figure")
        elif visual.get("state") != "placeholder" or visual.get("status") != "retired":
            errors.append(
                f"figure shell {visual_id} must remain a retired evidence-contingent slot"
            )
        slot_ids = shell.get("slot_ids")
        if not isinstance(slot_ids, list) or not slot_ids:
            errors.append(f"figure shell {visual_id} requires result slots")
            continue
        if len(slot_ids) != len(set(map(str, slot_ids))):
            errors.append(f"figure shell {visual_id} repeats result slots")
        for slot_id in slot_ids:
            if slot_id not in slot_by_id:
                errors.append(
                    f"figure shell {visual_id} references unknown slot {slot_id}"
                )
            if isinstance(visual_id, str) and isinstance(slot_id, str):
                shell_pairs.add((slot_id, visual_id))
    if figure_ids != EXPECTED_FIGURES:
        errors.append("Results figure-shell inventory has drifted")

    slot_pairs = {
        (slot_id, visual_id)
        for slot_id, slot in slot_by_id.items()
        for visual_id in (
            slot.get("visual_ids", [])
            if isinstance(slot.get("visual_ids"), list)
            else []
        )
        if isinstance(visual_id, str)
    }
    for slot_id, visual_id in sorted(slot_pairs - shell_pairs):
        errors.append(
            f"result slot {slot_id} names {visual_id} without reciprocal shell mapping"
        )
    for slot_id, visual_id in sorted(shell_pairs - slot_pairs):
        errors.append(
            f"visual shell {visual_id} maps orphan result slot {slot_id}"
        )

    if r"\AntidotePlaceholder" in results_text:
        errors.append("Results still contains governed content placeholders")
    for marker in (
        "ANT-REPORT-RESULTS-001",
        "version~1.1.0",
        "no formal human results",
        "No qualifying T1 package",
        r"issue~\#18",
        "ANT-PROT-FEAS-001",
        r"\texttt{.public.json}",
        "sec:results-optional-physiology",
    ):
        if marker not in results_text:
            errors.append(f"Results is missing reporting marker: {marker}")
    ledger = (project / LEDGER_PATH).read_text(encoding="utf-8")
    for claim_id in ("ANT-OBS-003", "ANT-CLM-007"):
        if claim_id not in ledger:
            errors.append(f"claim ledger is missing Results boundary: {claim_id}")
    return errors


def render_table(reporting: dict[str, object], shell: dict[str, object]) -> str:
    """Render one value-free Results table from governed slot metadata."""
    slots = {
        slot["id"]: slot for slot in reporting["result_slots"] if isinstance(slot, dict)
    }
    protocol_id = tex_escape(reporting["protocol"]["protocol_id"])
    lines = [
        "% Generated by scripts/generate_results_reporting.py.",
        "% Empty-state structure only. Never enter result values by hand.",
        r"\small",
        (
            r"\begin{tabular}{@{}"
            r">{\raggedright\arraybackslash}p{0.23\linewidth}"
            r">{\raggedright\arraybackslash}p{0.42\linewidth}"
            r">{\raggedright\arraybackslash}p{0.26\linewidth}@{}}"
        ),
        r"\toprule",
        (
            r"\multicolumn{3}{@{}l}{\textbf{GOVERNED EMPTY STATE --- "
            + tex_escape(shell["visual_id"])
            + r"}} \\"
        ),
        r"\midrule",
        (
            r"\textbf{Future result slot} & \textbf{Governance binding} & "
            r"\textbf{Current evidence state} \\"
        ),
        r"\midrule",
    ]
    for slot_id in shell["slot_ids"]:
        slot = slots[slot_id]
        state = STATE_LABELS[str(slot["current_state"])]
        lines.extend(
            [
                (
                    f"{tex_escape(slot['display_name'])} & "
                    r"{\scriptsize\textbf{Source:} "
                    rf"\nolinkurl{{{tex_escape(slot['source_record_id'])}}}\newline "
                    r"\textbf{Stage:} "
                    f"{tex_escape(slot['stage'])}"
                    r"\newline\textbf{Evidence class:} "
                    f"{tex_escape(slot['evidence_class'])}"
                    r"\newline"
                    r"\textbf{Protocol:} "
                    rf"\nolinkurl{{{protocol_id}}} "
                    f"v{tex_escape(slot['protocol_version'])}"
                    r"\newline\textbf{Analysis:} "
                    rf"\nolinkurl{{{tex_escape(slot['analysis_id'])}}}}} & "
                    f"{tex_escape(state)} \\\\"
                ),
                r"\addlinespace[0.25em]",
            ]
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}%",
            r"\par\smallskip",
            (
                r"{\raggedright\scriptsize Exact planned paths and protocol "
                r"pointers are governed by \texttt{ANT-REPORT-RESULTS-001}. "
                r"No qualifying values are registered; absent is not zero.\par}"
            ),
            "",
        ]
    )
    return "\n".join(lines)


def expected_outputs(project: Path = ROOT) -> dict[Path, str]:
    """Return deterministic table projections from the Results contract."""
    reporting = load_json(project, REPORTING_PATH)
    outputs: dict[Path, str] = {}
    for shell in reporting["table_shells"]:
        outputs[project / str(shell["output_path"])] = render_table(reporting, shell)
    return outputs


def main() -> int:
    """Write or verify the governed empty-state Results tables."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=str(ROOT))
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    project = Path(arguments.project).expanduser().resolve()
    errors = validate_reporting(project)
    if errors:
        for error in sorted(set(errors)):
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    outputs = expected_outputs(project)
    if arguments.write:
        for destination, content in outputs.items():
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")
            print(f"WROTE {destination}")
        return 0
    stale = [
        path
        for path, content in outputs.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != content
    ]
    if stale:
        for path in stale:
            print(
                f"ERROR generated Results table is missing or stale: {path}",
                file=sys.stderr,
            )
        print(
            "Run scripts/generate_results_reporting.py --write after review.",
            file=sys.stderr,
        )
        return 1
    print("PASS governed empty-state Results reporting and table projections.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
