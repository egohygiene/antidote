#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate the frozen feasibility protocol and generate its appendix view."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = Path("experiments/protocols/antidote-feasibility-v1.1.json")
LOCK_PATH = Path("experiments/protocols/antidote-feasibility-v1.1.lock.json")
DEVIATIONS_PATH = Path("experiments/protocols/antidote-feasibility-v1.1.deviations.json")
HISTORICAL_PROTOCOL_PATH = Path(
    "experiments/protocols/antidote-feasibility-v1.json"
)
HISTORICAL_LOCK_PATH = Path(
    "experiments/protocols/antidote-feasibility-v1.lock.json"
)
HISTORICAL_DEVIATIONS_PATH = Path(
    "experiments/protocols/antidote-feasibility-v1.deviations.json"
)
HISTORICAL_PROTOCOL_SHA256 = (
    "dbedbcbb74303373a7e00e95ad063b025d8cf6033864f4ad5a390d15703ba403"
)
RESPONSE_V2_PATH = Path("contracts/schemas/response-observation.v2.schema.json")
CONSENT_V2_PATH = Path("contracts/schemas/consent-grant.v2.schema.json")
CONTRACT_PATH = Path("paper/manuscript-contract.json")
EQUATIONS_PATH = Path("paper/equations/registry.json")
METHODS_PATH = Path("paper/sections/04-methods.tex")
APPENDIX_PATH = Path("paper/sections/appendix.tex")
OUTPUT_PATH = Path("paper/protocol/feasibility-protocol-checklist.tex")

EXPECTED_STAGES = ["D0", "T0", "T1", "H1"]
EXPECTED_CONDITIONS = ["G", "S", "P"]
EXPECTED_ASSIGNMENT_ORDERS = ["GSP", "GPS", "SGP", "SPG", "PGS", "PSG"]
EXPECTED_H1_SEEDS = [101, 307, 911, 1217, 1601, 2027]
CANONICAL_MISSINGNESS_REASONS = [
    "not_prompted",
    "declined",
    "missed_window",
    "technical_failure",
    "interrupted",
    "not_applicable",
]
REQUIRED_RESPONSE_FIELDS = {
    "schema_version",
    "id",
    "session_id",
    "exposure_id",
    "observed_at",
    "window",
    "instrument_version",
    "revision",
    "supersedes_response_id",
    "correction_reason",
    "perceived_expression",
    "felt_state",
    "wanted_intensity",
    "helpfulness",
    "resonance",
    "mismatch",
    "harm",
    "surprise",
    "interaction_burden",
    "session_burden",
    "ongoing_effect",
    "aftereffect_meaning",
    "missingness",
    "stopped_early",
    "later_aftereffect_requested",
    "allow_personal_model_update",
}
EXPECTED_MEASUREMENT_RESPONSE_FIELDS = {
    "perceived_expression",
    "felt_state",
    "wanted_intensity",
    "helpfulness",
    "resonance",
    "mismatch",
    "harm",
    "surprise",
    "interaction_burden",
    "session_burden",
    "ongoing_effect",
    "aftereffect_meaning",
    "missingness",
    "revision",
    "supersedes_response_id",
    "correction_reason",
}
EXPECTED_IMMEDIATE_CORE_FIELDS = [
    "perceived_expression.valence",
    "perceived_expression.arousal",
    "felt_state.valence",
    "felt_state.arousal",
    "wanted_intensity",
    "helpfulness",
    "resonance",
    "mismatch",
    "harm",
    "surprise",
    "interaction_burden",
    "session_burden",
]
EXPECTED_LATER_CORE_FIELDS = [
    "felt_state.valence",
    "felt_state.arousal",
    "helpfulness",
    "harm",
    "ongoing_effect",
]
EXPECTED_GATE_IDS = [
    "GATE-REAL-MODEL",
    "GATE-PRIVACY",
    "GATE-CONSENT",
    "GATE-INDEPENDENT-REVIEW",
    "GATE-ASSIGNMENT",
    "GATE-INSTRUMENT",
    "GATE-ANALYSIS",
    "GATE-STOP-GO",
]
EXPECTED_CONSENT_SCOPES = [
    "inspect",
    "project",
    "generate",
    "play",
    "retain",
    "analyze",
    "export",
    "learn",
]
EXPECTED_CONSENT_ACTION_ENUM = [
    "inspect",
    "project",
    "generate",
    "analyze",
    "play",
    "retain",
    "learn",
    "export",
]
DEVIATION_ENTRY_FIELDS = {
    "entry_id",
    "entry_type",
    "timestamp",
    "rationale",
    "affected_records",
    "evidence_impact",
    "author",
    "reviewer",
    "disposition",
}


def load_json(project: Path, relative_path: Path) -> dict[str, Any]:
    """Load one repository-owned JSON object."""
    value = json.loads((project / relative_path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{relative_path} must contain a JSON object")
    return value


def file_sha256(project: Path, relative_path: Path) -> str:
    """Return the byte-exact hash of one repository-owned file."""
    return hashlib.sha256((project / relative_path).read_bytes()).hexdigest()


def protocol_sha256(project: Path) -> str:
    """Return the byte-exact hash of the current governed protocol."""
    return file_sha256(project, PROTOCOL_PATH)


def contains_markers(value: object, markers: tuple[str, ...]) -> bool:
    """Return whether normalized prose contains every required marker."""
    text = str(value)
    return all(marker in text for marker in markers)


def validate_deviation_log(
    deviations: dict[str, Any],
    protocol: dict[str, Any],
    expected_protocol_sha256: str,
) -> list[str]:
    """Validate the current empty log and the shape of future append-only entries."""
    errors: list[str] = []
    if deviations.get("schema") != "antidote.protocol-deviation-log/v1":
        errors.append("protocol deviation-log schema is invalid")
    if deviations.get("protocol_id") != protocol.get("protocol_id"):
        errors.append("deviation log identity does not match the protocol")
    if deviations.get("protocol_version") != protocol.get("version"):
        errors.append("deviation log version does not match the protocol")
    if deviations.get("protocol_sha256") != expected_protocol_sha256:
        errors.append("deviation log protocol hash does not match the protocol")
    if deviations.get("append_only") is not True:
        errors.append("protocol deviation log must declare append_only true")

    qualifying_started = deviations.get("qualifying_records_started")
    human_started = deviations.get("human_collection_started")
    if not isinstance(qualifying_started, bool):
        errors.append("deviation log qualifying_records_started must be boolean")
    if not isinstance(human_started, bool):
        errors.append("deviation log human_collection_started must be boolean")
    if human_started is True and qualifying_started is not True:
        errors.append("human collection cannot precede a qualifying record")

    entries = deviations.get("entries")
    if not isinstance(entries, list):
        errors.append("protocol deviation log entries must be an array")
        return errors

    status = deviations.get("status")
    if qualifying_started is False:
        if status != "empty-no-collection":
            errors.append(
                "a pre-collection deviation log must have empty-no-collection status"
            )
        if entries:
            errors.append(
                "a pre-collection material change requires a new protocol version"
            )
    elif status not in {"active-after-qualifying-record", "closed"}:
        errors.append("a post-start deviation log must have an active or closed status")

    seen_ids: set[str] = set()
    for index, entry in enumerate(entries):
        prefix = f"deviation log entry {index}"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if set(entry) != DEVIATION_ENTRY_FIELDS:
            errors.append(
                f"{prefix} fields must equal {sorted(DEVIATION_ENTRY_FIELDS)}"
            )
        entry_id = entry.get("entry_id")
        if not isinstance(entry_id, str) or not re.fullmatch(
            r"ANT-(?:AMD|DEV)-\d{3}", entry_id
        ):
            errors.append(f"{prefix} entry_id is invalid")
        elif entry_id in seen_ids:
            errors.append(f"{prefix} entry_id is duplicated")
        else:
            seen_ids.add(entry_id)
        if entry.get("entry_type") not in {"amendment", "deviation"}:
            errors.append(f"{prefix} entry_type must be amendment or deviation")
        timestamp = entry.get("timestamp")
        if not isinstance(timestamp, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", timestamp
        ):
            errors.append(f"{prefix} timestamp must be second-precision UTC")
        affected_records = entry.get("affected_records")
        if (
            not isinstance(affected_records, list)
            or not affected_records
            or not all(
                isinstance(record, str) and record.strip()
                for record in affected_records
            )
        ):
            errors.append(f"{prefix} affected_records must be an array of strings")
        for field in (
            "rationale",
            "evidence_impact",
            "author",
            "reviewer",
            "disposition",
        ):
            value = entry.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{prefix} {field} must be a non-empty string")
    return errors


def resolve_json_pointer(document: Any, pointer: str) -> Any:
    """Resolve an RFC 6901 JSON pointer within one loaded document."""
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise ValueError(f"JSON pointer must start with '/': {pointer}")
    value = document
    for raw_token in pointer[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            value = value[int(token)]
        elif isinstance(value, dict):
            value = value[token]
        else:
            raise KeyError(token)
    return value


def tex_escape(value: object) -> str:
    """Escape protocol prose for deterministic LaTeX output."""
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


def validate_protocol(project: Path = ROOT) -> list[str]:
    """Return deterministic protocol, schema, and manuscript drift errors."""
    errors: list[str] = []
    try:
        protocol = load_json(project, PROTOCOL_PATH)
        lock = load_json(project, LOCK_PATH)
        deviations = load_json(project, DEVIATIONS_PATH)
        historical_protocol = load_json(project, HISTORICAL_PROTOCOL_PATH)
        historical_lock = load_json(project, HISTORICAL_LOCK_PATH)
        historical_deviations = load_json(project, HISTORICAL_DEVIATIONS_PATH)
        contract = load_json(project, CONTRACT_PATH)
        equations = load_json(project, EQUATIONS_PATH)
        response_schema = load_json(project, RESPONSE_V2_PATH)
        consent_schema = load_json(project, CONSENT_V2_PATH)
    except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        return [f"feasibility protocol inputs are invalid: {error}"]

    current_hash = protocol_sha256(project)
    historical_hash = file_sha256(project, HISTORICAL_PROTOCOL_PATH)
    if historical_hash != HISTORICAL_PROTOCOL_SHA256:
        errors.append(
            "historical protocol 1.0.0 bytes drifted from the preserved SHA-256"
        )
    expected_historical_lock = {
        "schema": "antidote.protocol-lock/v1",
        "protocol_id": "ANT-PROT-FEAS-001",
        "protocol_version": "1.0.0",
        "protocol_path": HISTORICAL_PROTOCOL_PATH.as_posix(),
        "sha256": HISTORICAL_PROTOCOL_SHA256,
        "frozen_on": "2026-09-07",
        "governed_by": "egohygiene/antidote#40",
        "collection_authority": False,
    }
    if historical_lock != expected_historical_lock:
        errors.append("historical protocol 1.0.0 lock drifted")
    expected_historical_deviations = {
        "schema": "antidote.protocol-deviation-log/v1",
        "protocol_id": "ANT-PROT-FEAS-001",
        "protocol_version": "1.0.0",
        "status": "empty-no-collection",
        "collection_started": False,
        "entries": [],
    }
    if historical_deviations != expected_historical_deviations:
        errors.append("historical protocol 1.0.0 deviation log drifted")
    if historical_protocol.get("version") != "1.0.0":
        errors.append("historical protocol file no longer identifies version 1.0.0")

    expected_identity = {
        "schema": "antidote.feasibility-protocol/v1",
        "protocol_id": "ANT-PROT-FEAS-001",
        "version": "1.1.0",
        "status": "frozen-design-protocol",
        "governed_by": "egohygiene/antidote#40",
        "amended_by": "egohygiene/antidote#82",
        "collection_authority": False,
        "qualifying_records_started": False,
        "human_collection_started": False,
    }
    for field, expected in expected_identity.items():
        if protocol.get(field) != expected:
            errors.append(f"protocol {field} must equal {expected!r}")

    supersession = protocol.get("supersession", {})
    expected_supersession_fields = {
        "revision_class": "pre-collection-corrective",
        "supersedes_version": "1.0.0",
        "superseded_protocol_path": HISTORICAL_PROTOCOL_PATH.as_posix(),
        "superseded_lock_path": HISTORICAL_LOCK_PATH.as_posix(),
        "superseded_deviation_log_path": HISTORICAL_DEVIATIONS_PATH.as_posix(),
        "supersedes_sha256": HISTORICAL_PROTOCOL_SHA256,
        "qualifying_records_started_under_superseded_version": False,
        "human_collection_started_under_superseded_version": False,
    }
    if not isinstance(supersession, dict):
        errors.append("protocol supersession record must be an object")
        supersession = {}
    for field, expected in expected_supersession_fields.items():
        if supersession.get(field) != expected:
            errors.append(f"protocol supersession {field} must equal {expected!r}")
    if not contains_markers(
        supersession.get("history_rule", ""),
        ("Version 1.0.0", "remain in-tree", "No observation"),
    ):
        errors.append("protocol supersession history rule is incomplete")

    expected_scope = {
        "technical_feasibility": True,
        "within_person_record_feasibility": True,
        "clinical_efficacy": False,
        "diagnosis_or_treatment": False,
        "neurological_mechanism": False,
        "population_generalization": False,
        "autonomous_personalization": False,
    }
    if protocol.get("scope") != expected_scope:
        errors.append("protocol scope must preserve the feasibility-only boundary")

    freeze = protocol.get("freeze_and_deviations", {})
    expected_freeze_paths = {
        "protocol_path": PROTOCOL_PATH.as_posix(),
        "lock_path": LOCK_PATH.as_posix(),
        "deviation_log_path": DEVIATIONS_PATH.as_posix(),
    }
    for field, expected in expected_freeze_paths.items():
        if freeze.get(field) != expected:
            errors.append(f"protocol freeze {field} must equal {expected!r}")

    if lock.get("schema") != "antidote.protocol-lock/v1":
        errors.append("protocol lock schema is invalid")
    if lock.get("protocol_id") != protocol.get("protocol_id"):
        errors.append("protocol lock identity does not match the protocol")
    if lock.get("protocol_version") != protocol.get("version"):
        errors.append("protocol lock version does not match the protocol")
    if lock.get("sha256") != current_hash:
        errors.append("protocol SHA-256 does not match the frozen lock")
    if lock.get("protocol_path") != PROTOCOL_PATH.as_posix():
        errors.append("protocol lock path does not identify the canonical protocol")
    if lock.get("frozen_on") != protocol.get("frozen_on"):
        errors.append("protocol lock freeze date does not match the protocol")
    if lock.get("governed_by") != protocol.get("governed_by"):
        errors.append("protocol lock owner does not match the protocol")
    if lock.get("amended_by") != protocol.get("amended_by"):
        errors.append("protocol lock amendment owner does not match the protocol")
    if lock.get("collection_authority") is not False:
        errors.append("protocol lock must not grant collection authority")
    for field in ("qualifying_records_started", "human_collection_started"):
        if lock.get(field) is not False:
            errors.append(f"protocol lock {field} must remain false")
    expected_lock_supersedes = {
        "protocol_version": "1.0.0",
        "protocol_path": HISTORICAL_PROTOCOL_PATH.as_posix(),
        "lock_path": HISTORICAL_LOCK_PATH.as_posix(),
        "deviation_log_path": HISTORICAL_DEVIATIONS_PATH.as_posix(),
        "sha256": HISTORICAL_PROTOCOL_SHA256,
    }
    if lock.get("supersedes") != expected_lock_supersedes:
        errors.append("protocol lock supersession record is invalid")

    errors.extend(validate_deviation_log(deviations, protocol, current_hash))

    stages = protocol.get("stages", [])
    stage_ids = [stage.get("id") for stage in stages if isinstance(stage, dict)]
    if stage_ids != EXPECTED_STAGES:
        errors.append(f"protocol stages must be ordered as {EXPECTED_STAGES}")
    for stage in stages:
        if not isinstance(stage, dict):
            errors.append("each protocol stage must be an object")
            continue
        if (
            stage.get("id") == "T1"
            and stage.get("current_state") != "blocked-no-real-model"
        ):
            errors.append("T1 must remain blocked until a real model is qualified")
        if (
            stage.get("id") == "H1"
            and stage.get("current_state") != "blocked-no-collection-authority"
        ):
            errors.append(
                "H1 must remain blocked until separate collection authority exists"
            )

    contract_rqs = [item.get("id") for item in contract.get("research_questions", [])]
    protocol_rqs = [item.get("id") for item in protocol.get("research_questions", [])]
    if protocol_rqs != contract_rqs:
        errors.append(
            "protocol research questions drifted from the manuscript contract"
        )

    human = protocol.get("human_protocol", {})
    conditions = human.get("conditions", []) if isinstance(human, dict) else []
    if [condition.get("id") for condition in conditions] != EXPECTED_CONDITIONS:
        errors.append(f"human conditions must be ordered as {EXPECTED_CONDITIONS}")
    if human.get("planned_completed_exposures") != 18:
        errors.append("H1 must declare 18 planned completed exposures")
    if human.get("maximum_scheduled_attempts") != 24:
        errors.append("H1 must declare the 24-attempt stopping ceiling")
    if human.get("blocks") != 6 or human.get("conditions_per_block") != 3:
        errors.append("H1 must preserve the six-block, three-condition design")
    if human.get("audio_duration_seconds") != 480:
        errors.append("H1 must preserve the eight-minute exposure duration")
    if human.get("minimum_between_exposures_hours") != 48:
        errors.append("H1 must preserve at least 48 hours between exposures")
    assignment = human.get("assignment", {})
    if assignment.get("permutations") != EXPECTED_ASSIGNMENT_ORDERS:
        errors.append(
            "H1 assignment must contain every G/S/P order exactly once in frozen order"
        )
    expected_schedule_count = math.factorial(len(EXPECTED_ASSIGNMENT_ORDERS))
    if assignment.get("allowable_schedule_count") != expected_schedule_count:
        errors.append("H1 assignment space must equal 6! = 720 schedules")
    if not contains_markers(
        assignment.get("rule", ""), ("exactly 6! = 720", "exactly once")
    ):
        errors.append("H1 assignment rule must state the balanced 6! schedule space")
    if not contains_markers(
        assignment.get("uniform_selection_algorithm", ""),
        (
            "zero-based lexicographic",
            "32-byte",
            "four-byte unsigned big-endian counter",
            "SHA-256",
            "64800",
            "mod 720",
        ),
    ):
        errors.append("H1 uniform assignment algorithm is not fully frozen")

    h1_seed_policy = human.get("h1_seed_policy", {})
    if h1_seed_policy.get("deterministic_seed_required") is not True:
        errors.append("H1 must require deterministic seeds")
    if h1_seed_policy.get("block_seeds") != EXPECTED_H1_SEEDS:
        errors.append(f"H1 block seeds must remain {EXPECTED_H1_SEEDS}")
    if not contains_markers(
        h1_seed_policy.get("mapping", ""),
        ("chronological blocks 1 through 6", "same block seed"),
    ):
        errors.append("H1 block-seed mapping is incomplete")
    if not contains_markers(
        h1_seed_policy.get("commitment", ""),
        ("before session 1", "do not regenerate", "replace a seed"),
    ):
        errors.append("H1 seed commitment and no-substitution rule are incomplete")

    intensity_scale = human.get("subjective_scale_anchors", {}).get(
        "intensity", {}
    )
    if intensity_scale.get("range") != [0, 1] or intensity_scale.get(
        "anchors"
    ) != {"0": "not at all intense", "1": "extremely intense"}:
        errors.append("H1 intensity anchors must remain non-circular and frozen")

    implementation = human.get("implementation_boundary", {})
    if implementation.get("current_desktop_mvp_is_h1_instrument") is not False:
        errors.append("the current desktop MVP must not be an H1 instrument")
    if implementation.get("current_desktop_mvp_records_are_h1_eligible") is not False:
        errors.append("current desktop records must remain ineligible for H1")
    if implementation.get("h1_response_contract") != RESPONSE_V2_PATH.as_posix():
        errors.append("H1 implementation boundary must name the response v2 contract")
    if implementation.get("h1_consent_contract") != CONSENT_V2_PATH.as_posix():
        errors.append("H1 implementation boundary must name the consent v2 contract")
    if implementation.get("current_desktop_contract_generation") != "v1 runtime payloads":
        errors.append("H1 boundary must preserve the current v1 runtime distinction")

    technical = protocol.get("technical_protocol", {})
    if technical.get("seed_set") != [101, 307, 911]:
        errors.append("T1 seed set must remain frozen")
    attempts = technical.get("planned_attempts", {})
    if attempts.get("total_if_all_controls_supported") != 39:
        errors.append("T1 must retain the 39-attempt qualification ceiling")
    if sum(
        attempts.get(field, 0)
        for field in (
            "baseline",
            "four_supported_mutation_pairs",
            "boundary_continuity",
            "failure_and_recovery",
        )
    ) != attempts.get("total_if_all_controls_supported"):
        errors.append("T1 planned-attempt components do not equal their total")

    gates = protocol.get("human_collection_activation_gates", [])
    if [
        gate.get("id") for gate in gates if isinstance(gate, dict)
    ] != EXPECTED_GATE_IDS:
        errors.append("human-collection activation gates are incomplete or reordered")
    if not gates or any(
        not isinstance(gate, dict) or gate.get("satisfied") is not False
        for gate in gates
    ):
        errors.append("every human-collection activation gate must remain false")

    optional_physiology = protocol.get("optional_physiology", {})
    if (
        optional_physiology.get("enabled") is not False
        or optional_physiology.get("primary_endpoint") is not False
        or optional_physiology.get("real_time_steering") is not False
    ):
        errors.append("physiology must remain disabled, supplemental, and non-steering")

    analysis = protocol.get("analysis_plan", {})
    if analysis.get("version") != "1.1.0":
        errors.append("analysis plan version must match protocol version 1.1.0")
    if analysis.get("analysis_is_not_started") is not True:
        errors.append("analysis plan must state that analysis has not started")

    quantiles = analysis.get("latency_quantiles", {})
    if quantiles.get("probabilities") != [0.5, 0.9, 0.95]:
        errors.append("latency quantiles must remain frozen at q50, q90, and q95")
    if not contains_markers(
        quantiles.get("median", ""), ("ordered values", "arithmetic mean")
    ):
        errors.append("latency median definition is incomplete")
    if not contains_markers(
        quantiles.get("quantile_algorithm", ""),
        (
            "Fixed linear interpolation",
            "h=(n-1)p+1",
            "Q(p)=(1-g)x(j)+g x(j+1)",
            "unrounded seconds",
        ),
    ):
        errors.append("latency quantile algorithm is not fully frozen")

    exact_randomization = analysis.get("exact_randomization_analysis", {})
    expected_randomization_outcomes = [
        "immediate helpfulness",
        "immediate resonance",
        "immediate mismatch",
        "immediate harm",
        "immediate interaction burden",
        "immediate session burden",
    ]
    if exact_randomization.get("outcomes") != expected_randomization_outcomes:
        errors.append("exact randomization outcome registry drifted")
    if exact_randomization.get("contrasts") != [
        "P-minus-S",
        "P-minus-G",
        "S-minus-G",
    ]:
        errors.append("exact randomization contrast registry drifted")
    if not contains_markers(
        exact_randomization.get("eligibility", ""),
        ("all three chronological position values", "all six blocks", "unavailable"),
    ):
        errors.append("exact randomization eligibility is incomplete")
    if not contains_markers(
        exact_randomization.get("schedule_enumeration", ""),
        ("6! = 720", "including the observed schedule", "do not make independent"),
    ):
        errors.append("exact randomization schedule enumeration is invalid")
    if not contains_markers(
        exact_randomization.get("statistic", ""),
        ("six within-block differences", "arithmetic mean T"),
    ):
        errors.append("exact randomization statistic is incomplete")
    if not contains_markers(
        exact_randomization.get("two_sided_tail", ""),
        (
            "p_exact=tail_count/720",
            "unrounded",
            "included in the tail",
            "no random tie breaking",
        ),
    ):
        errors.append("exact randomization tail and tie rule is incomplete")

    completeness = analysis.get("response_completeness", {})
    if completeness.get("immediate_core_fields") != EXPECTED_IMMEDIATE_CORE_FIELDS:
        errors.append("immediate usable-response core-field registry drifted")
    if completeness.get("later_core_fields") != EXPECTED_LATER_CORE_FIELDS:
        errors.append("later usable-response core-field registry drifted")
    if not contains_markers(
        completeness.get("usable_voluntary_value", ""),
        ("non-null", "person-supplied", "are not usable responses"),
    ):
        errors.append("usable voluntary response must exclude declined fields")
    if not contains_markers(
        completeness.get("progression_threshold_calculation", ""),
        (
            "ceil(0.80 * N_started)",
            "at least 3 usable values in each condition",
            "ceil(0.70 * N_started)",
            "at least 2 usable values in each condition",
        ),
    ):
        errors.append("usable-response progression calculation is incomplete")

    missingness = analysis.get("missingness", {})
    if missingness.get("canonical_reasons") != CANONICAL_MISSINGNESS_REASONS:
        errors.append("protocol missingness reasons must equal the canonical enum")
    if not contains_markers(
        missingness.get("primary", ""),
        ("No outcome imputation", "each absent field", "exactly one canonical reason"),
    ):
        errors.append("field-level no-imputation missingness rule is incomplete")
    expected_bound_keys = {
        "helpfulness_and_resonance",
        "mismatch_harm_interaction_burden_session_burden",
        "valence_and_arousal",
        "intensity_and_surprise",
    }
    numeric_bounds = missingness.get("numeric_bounds", {})
    if not isinstance(numeric_bounds, dict) or set(numeric_bounds) != expected_bound_keys:
        errors.append("numeric missing-value bounds are incomplete")

    progression = protocol.get("progression_rule", {})
    progression_items = progression.get("proceed_only_if", [])
    if not isinstance(progression_items, list):
        errors.append("progression proceed_only_if must be an array")
        progression_items = []
    required_progression_markers = [
        ("15 of 18", "at least 4 per condition"),
        ("100 percent of assigned attempts", "audit-completeness"),
        (
            "immediate core field",
            "ceil(0.80 * N_started)",
            "decline remains audit-complete but does not count as usable",
        ),
        (
            "later core field",
            "ceil(0.70 * N_started)",
            "decline remains audit-complete but does not count as usable",
        ),
        ("100 percent of eligible response records", "latest correction lineage"),
        ("median interaction burden", "0.5"),
        ("both prespecified interaction-burden bound decisions",),
        ("no safety event remains unresolved",),
        ("participant", "independent reviewer", "separately judge"),
    ]
    for markers in required_progression_markers:
        if not any(contains_markers(item, markers) for item in progression_items):
            errors.append(
                "progression rule is missing criterion: " + ", ".join(markers)
            )
    if not contains_markers(
        progression.get("purpose", ""),
        ("not evidence of efficacy", "advisory usefulness", "safety"),
    ):
        errors.append("progression interpretation boundary is incomplete")
    if "Stop or revise" not in str(progression.get("otherwise", "")):
        errors.append("progression rule must define the non-proceed disposition")

    safety = protocol.get("safety_and_adverse_events", {})
    definitions = safety.get("operational_definitions", {})
    expected_definition_keys = {
        "high_harm",
        "repeated_high_harm",
        "serious_event",
        "unresolved",
    }
    if not isinstance(definitions, dict) or set(definitions) != expected_definition_keys:
        errors.append("safety operational definitions are incomplete")
        definitions = {}
    safety_definition_markers = {
        "high_harm": ("greater than or equal to 0.75", "rating is absent"),
        "repeated_high_harm": (
            "two distinct started exposures",
            "count as one exposure",
        ),
        "serious_event": (
            "urgent human assessment",
            "stop-control failure",
            "not a diagnosis",
        ),
        "unresolved": (
            "documented disposition",
            "independent review",
            "before another exposure",
        ),
    }
    for name, markers in safety_definition_markers.items():
        if not contains_markers(definitions.get(name, ""), markers):
            errors.append(f"safety definition {name} is not operationally frozen")
    stop_triggers = safety.get("immediate_stop_triggers", [])
    if not isinstance(stop_triggers, list) or len(stop_triggers) != 5:
        errors.append("safety rule must retain all five immediate stop-trigger classes")
    if not contains_markers(
        safety.get("review_rule", ""),
        ("unresolved adverse response", "repeated high harm", "independent review"),
    ):
        errors.append("safety pause-and-review rule is incomplete")

    privacy = protocol.get("privacy_consent_and_retention", {})
    collection_default = privacy.get("collection_default", "")
    if "No collection is authorized" not in collection_default:
        errors.append("privacy contract must deny collection by default")
    if privacy.get("h1_response_contract") != RESPONSE_V2_PATH.as_posix():
        errors.append("privacy boundary must name the response v2 contract")
    if privacy.get("h1_consent_contract") != CONSENT_V2_PATH.as_posix():
        errors.append("privacy boundary must name the consent v2 contract")
    if privacy.get("consent_scopes") != EXPECTED_CONSENT_SCOPES:
        errors.append("H1 consent scopes are incomplete or reordered")

    equation_ids = {equation.get("id") for equation in equations.get("equations", [])}
    for measure in protocol.get("technical_protocol", {}).get("measures", []):
        for equation_id in measure.get("equation_ids", []):
            if equation_id not in equation_ids:
                errors.append(
                    f"technical measure references unknown equation: {equation_id}"
                )

    seen_response_fields: set[str] = set()
    for measure in protocol.get("measurement_registry", []):
        for contract_path in measure.get("contract_paths", []):
            try:
                schema_path_text, pointer = contract_path.split("#", maxsplit=1)
                schema_path = Path(schema_path_text)
                if schema_path.is_absolute() or ".." in schema_path.parts:
                    raise ValueError("schema path must remain repository-relative")
                schema = load_json(project, schema_path)
                resolve_json_pointer(schema, pointer)
                if (
                    schema_path.name.startswith("response-observation")
                    and schema_path != RESPONSE_V2_PATH
                ):
                    errors.append(
                        "H1 measurement registry must not reference a response v1 path"
                    )
                if schema_path == RESPONSE_V2_PATH:
                    tokens = pointer.rstrip("/").split("/")
                    if tokens:
                        seen_response_fields.add(tokens[-1])
            except (
                OSError,
                ValueError,
                KeyError,
                IndexError,
                json.JSONDecodeError,
            ) as error:
                errors.append(
                    f"measurement contract path does not resolve: {contract_path}: {error}"
                )
    missing_response_fields = (
        EXPECTED_MEASUREMENT_RESPONSE_FIELDS - seen_response_fields
    )
    if missing_response_fields:
        errors.append(
            "protocol does not map required H1 response measures: "
            + ", ".join(sorted(missing_response_fields))
        )

    if response_schema.get("$id") != (
        "urn:egohygiene:antidote:schema:response-observation:v2"
    ):
        errors.append("H1 response schema identity is invalid")
    if response_schema.get("properties", {}).get("schema_version", {}).get(
        "const"
    ) != "2.0.0":
        errors.append("H1 response schema version must equal 2.0.0")
    if set(response_schema.get("required", [])) != REQUIRED_RESPONSE_FIELDS:
        errors.append("H1 response schema required-field set drifted")
    missingness_definition = response_schema.get("$defs", {}).get(
        "missingnessEntry", {}
    )
    if missingness_definition.get("required") != ["field", "reason"]:
        errors.append("H1 response missingness entries must require field and reason")
    schema_missingness_reasons = (
        missingness_definition.get("properties", {})
        .get("reason", {})
        .get("enum")
    )
    if schema_missingness_reasons != CANONICAL_MISSINGNESS_REASONS:
        errors.append("H1 response schema missingness reasons drifted from protocol")
    response_missingness = response_schema.get("properties", {}).get(
        "missingness", {}
    )
    if response_missingness.get("uniqueItems") is not True or response_missingness.get(
        "items", {}
    ).get("$ref") != "#/$defs/missingnessEntry":
        errors.append("H1 response missingness must be unique field-level entries")
    if response_schema.get("properties", {}).get("wanted_intensity", {}).get(
        "enum"
    ) != ["yes", "no", "unsure", None]:
        errors.append("H1 wanted-intensity schema must preserve yes, no, and unsure")
    for field in ("revision", "supersedes_response_id", "correction_reason"):
        if field not in response_schema.get("properties", {}):
            errors.append(f"H1 response correction field is missing: {field}")
    if not response_schema.get("allOf"):
        errors.append("H1 response schema must enforce correction and null lineage")

    if consent_schema.get("$id") != "urn:egohygiene:antidote:schema:consent-grant:v2":
        errors.append("H1 consent schema identity is invalid")
    if consent_schema.get("properties", {}).get("schema_version", {}).get(
        "const"
    ) != "2.0.0":
        errors.append("H1 consent schema version must equal 2.0.0")
    consent_actions = consent_schema.get("properties", {}).get("actions", {})
    consent_action_enum = consent_actions.get("items", {}).get("enum")
    if (
        consent_actions.get("maxItems") != 1
        or consent_action_enum != EXPECTED_CONSENT_ACTION_ENUM
        or set(consent_action_enum) != set(EXPECTED_CONSENT_SCOPES)
    ):
        errors.append("H1 consent schema must preserve one independently revocable action")

    methods = (project / METHODS_PATH).read_text(encoding="utf-8")
    if r"\AntidotePlaceholder" in methods:
        errors.append("Methods still contains governed content placeholders")
    for marker in (
        "ANT-PROT-FEAS-001",
        "1.1.0",
        "frozen-design-protocol",
        "collection authority",
        "720",
        "ANT-EQ-014",
        "ANT-EQ-015",
        "ANT-EQ-016",
    ):
        if marker not in methods:
            errors.append(f"Methods is missing protocol marker: {marker}")

    appendix = (project / APPENDIX_PATH).read_text(encoding="utf-8")
    if r"\input{paper/protocol/feasibility-protocol-checklist}" not in appendix:
        errors.append("appendix does not include the generated protocol checklist")
    return errors


def render_checklist(project: Path = ROOT) -> str:
    """Render the reader-facing projection of the canonical protocol."""
    protocol = load_json(project, PROTOCOL_PATH)
    human = protocol["human_protocol"]
    lock = load_json(project, LOCK_PATH)
    deviations = load_json(project, DEVIATIONS_PATH)
    protocol_hash = str(lock["sha256"])
    lines = [
        "% Generated by scripts/generate_protocol_appendix.py.",
        "% Source: experiments/protocols/antidote-feasibility-v1.1.json.",
        "",
        (
            r"\noindent\textbf{Protocol identity.} "
            rf"\texttt{{{tex_escape(protocol['protocol_id'])}}}, version~{tex_escape(protocol['version'])}, "
            rf"was frozen as a \texttt{{{tex_escape(protocol['status'])}}} artifact on "
            rf"{tex_escape(protocol['frozen_on'])}. Its byte-exact SHA-256 is shown "
            r"below in two contiguous halves."
        ),
        r"\begin{center}",
        rf"  \small\texttt{{{protocol_hash[:32]}}}\\[-0.2em]",
        rf"  \small\texttt{{{protocol_hash[32:]}}}",
        r"\end{center}",
        "",
        (
            r"\noindent\textbf{Protocol succession.} This is the pre-collection "
            r"corrective successor to version~"
            rf"{tex_escape(protocol['supersession']['supersedes_version'])}. The "
            r"superseded protocol remains preserved at "
            rf"\nolinkurl{{{tex_escape(protocol['supersession']['superseded_protocol_path'])}}} "
            r"with byte-exact SHA-256 "
            rf"\nolinkurl{{{tex_escape(protocol['supersession']['supersedes_sha256'])}}}. "
            r"No qualifying record or human collection began under the predecessor."
        ),
        "",
        (
            r"\noindent\textbf{Authority status.} Collection authority is "
            r"\textbf{false}; no formal human study has begun. The amendment and "
            rf"deviation log contains {len(deviations['entries'])} entries."
        ),
        "",
        r"\subsection*{Evidence stages}",
        r"\begin{description}[leftmargin=3.3em,style=nextline,itemsep=0.45em]",
    ]
    for stage in protocol["stages"]:
        lines.append(
            rf"  \item[\texttt{{{tex_escape(stage['id'])}}}] "
            rf"\textbf{{{tex_escape(stage['name'])}.}}\\ "
            rf"Current state: \nolinkurl{{{tex_escape(stage['current_state'])}}}. "
            rf"Unit: {tex_escape(stage['unit'])}."
        )
    lines.extend(
        [
            r"\end{description}",
            "",
            r"\subsection*{Prospective H1 schedule}",
            r"\begin{itemize}[leftmargin=1.35em,itemsep=0.4em]",
            (
                rf"  \item {human['blocks']} blocks $\times$ {human['conditions_per_block']} conditions "
                rf"= {human['planned_completed_exposures']} planned completed exposures, "
                rf"with an absolute ceiling of {human['maximum_scheduled_attempts']} scheduled attempts."
            ),
            (
                rf"  \item Each proposed exposure is {human['audio_duration_seconds'] // 60} minutes; "
                rf"at least {human['minimum_between_exposures_hours']} hours separate exposures, "
                rf"with at most {human['maximum_exposures_per_seven_days']} in seven days."
            ),
            (
                r"  \item The later aftereffect window targets "
                rf"{human['later_aftereffect_window_hours']['target']} hours and accepts "
                rf"{human['later_aftereffect_window_hours']['minimum']}--"
                rf"{human['later_aftereffect_window_hours']['maximum']} hours."
            ),
            (
                r"  \item The balanced block-order assignment contains exactly "
                rf"{human['assignment']['allowable_schedule_count']} schedules "
                r"($6!$), selected by the frozen uniform algorithm; the six H1 "
                r"block seeds are committed before session~1."
            ),
            r"\end{itemize}",
            "",
            r"\begin{description}[leftmargin=2.8em,style=nextline,itemsep=0.45em]",
        ]
    )
    for condition in human["conditions"]:
        lines.append(
            rf"  \item[\texttt{{{tex_escape(condition['id'])}}}] "
            rf"\textbf{{{tex_escape(condition['name'])}.}} "
            rf"{tex_escape(condition['instruction'])}"
        )
    lines.extend(
        [
            r"\end{description}",
            "",
            r"\subsection*{Human-collection activation gates}",
            r"\begin{itemize}[leftmargin=1.35em,itemsep=0.42em]",
        ]
    )
    for gate in protocol["human_collection_activation_gates"]:
        state = "not satisfied" if gate["satisfied"] is False else "satisfied"
        lines.append(
            rf"  \item \texttt{{{tex_escape(gate['id'])}}} --- "
            rf"\textbf{{{state}.}} {tex_escape(gate['requirement'])}"
        )
    lines.extend(
        [
            r"\end{itemize}",
            "",
            r"\subsection*{Freeze and audit rule}",
            r"\begin{itemize}[leftmargin=1.35em,itemsep=0.42em]",
            rf"  \item {tex_escape(protocol['freeze_and_deviations']['before_first_qualifying_record'])}",
            rf"  \item {tex_escape(protocol['freeze_and_deviations']['after_first_qualifying_record'])}",
            rf"  \item {tex_escape(protocol['analysis_plan']['null_and_negative_rule'])}",
            r"\end{itemize}",
            "",
        ]
    )
    return "\n".join(lines)


def expected_outputs(project: Path = ROOT) -> dict[Path, str]:
    """Return the deterministic generated protocol projection."""
    return {project / OUTPUT_PATH: render_checklist(project)}


def main() -> int:
    """Write or verify the frozen protocol appendix projection."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=str(ROOT))
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    project = Path(arguments.project).expanduser().resolve()
    errors = validate_protocol(project)
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
        print(
            "ERROR protocol appendix projection is missing or stale; "
            "run scripts/generate_protocol_appendix.py --write",
            file=sys.stderr,
        )
        return 1
    print("PASS frozen feasibility protocol and appendix projection.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
