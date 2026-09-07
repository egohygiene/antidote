#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate the frozen feasibility protocol and generate its appendix view."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = Path("experiments/protocols/antidote-feasibility-v1.json")
LOCK_PATH = Path("experiments/protocols/antidote-feasibility-v1.lock.json")
DEVIATIONS_PATH = Path("experiments/protocols/antidote-feasibility-v1.deviations.json")
CONTRACT_PATH = Path("paper/manuscript-contract.json")
EQUATIONS_PATH = Path("paper/equations/registry.json")
METHODS_PATH = Path("paper/sections/04-methods.tex")
APPENDIX_PATH = Path("paper/sections/appendix.tex")
OUTPUT_PATH = Path("paper/protocol/feasibility-protocol-checklist.tex")

EXPECTED_STAGES = ["D0", "T0", "T1", "H1"]
EXPECTED_CONDITIONS = ["G", "S", "P"]
REQUIRED_RESPONSE_FIELDS = {
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
    "missing_fields",
    "missingness_reason",
}


def load_json(project: Path, relative_path: Path) -> dict[str, Any]:
    """Load one repository-owned JSON object."""
    value = json.loads((project / relative_path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{relative_path} must contain a JSON object")
    return value


def protocol_sha256(project: Path) -> str:
    """Return the byte-exact hash of the governed protocol."""
    return hashlib.sha256((project / PROTOCOL_PATH).read_bytes()).hexdigest()


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
        contract = load_json(project, CONTRACT_PATH)
        equations = load_json(project, EQUATIONS_PATH)
    except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        return [f"feasibility protocol inputs are invalid: {error}"]

    expected_identity = {
        "schema": "antidote.feasibility-protocol/v1",
        "protocol_id": "ANT-PROT-FEAS-001",
        "version": "1.0.0",
        "status": "frozen-design-protocol",
        "governed_by": "egohygiene/antidote#40",
        "collection_authority": False,
    }
    for field, expected in expected_identity.items():
        if protocol.get(field) != expected:
            errors.append(f"protocol {field} must equal {expected!r}")

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

    if lock.get("schema") != "antidote.protocol-lock/v1":
        errors.append("protocol lock schema is invalid")
    if lock.get("protocol_id") != protocol.get("protocol_id"):
        errors.append("protocol lock identity does not match the protocol")
    if lock.get("protocol_version") != protocol.get("version"):
        errors.append("protocol lock version does not match the protocol")
    if lock.get("sha256") != protocol_sha256(project):
        errors.append("protocol SHA-256 does not match the frozen lock")
    if lock.get("protocol_path") != PROTOCOL_PATH.as_posix():
        errors.append("protocol lock path does not identify the canonical protocol")
    if lock.get("frozen_on") != protocol.get("frozen_on"):
        errors.append("protocol lock freeze date does not match the protocol")
    if lock.get("governed_by") != protocol.get("governed_by"):
        errors.append("protocol lock owner does not match the protocol")
    if lock.get("collection_authority") is not False:
        errors.append("protocol lock must not grant collection authority")

    if deviations.get("schema") != "antidote.protocol-deviation-log/v1":
        errors.append("protocol deviation-log schema is invalid")
    if deviations.get("protocol_id") != protocol.get("protocol_id"):
        errors.append("deviation log identity does not match the protocol")
    if deviations.get("protocol_version") != protocol.get("version"):
        errors.append("deviation log version does not match the protocol")
    if deviations.get("collection_started") is not False:
        errors.append("deviation log must state that collection has not started")
    if deviations.get("status") != "empty-no-collection":
        errors.append("initial deviation log status must remain empty-no-collection")
    if deviations.get("entries") != []:
        errors.append("initial frozen protocol must have an empty deviation log")

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
    expected_permutations = {"GSP", "GPS", "SGP", "SPG", "PGS", "PSG"}
    if set(assignment.get("permutations", [])) != expected_permutations:
        errors.append("H1 assignment must contain every G/S/P order exactly once")

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
    if not gates or any(gate.get("satisfied") is not False for gate in gates):
        errors.append("every human-collection activation gate must remain false")

    optional_physiology = protocol.get("optional_physiology", {})
    if (
        optional_physiology.get("enabled") is not False
        or optional_physiology.get("primary_endpoint") is not False
        or optional_physiology.get("real_time_steering") is not False
    ):
        errors.append("physiology must remain disabled, supplemental, and non-steering")

    if protocol.get("analysis_plan", {}).get("analysis_is_not_started") is not True:
        errors.append("analysis plan must state that analysis has not started")
    collection_default = protocol.get("privacy_consent_and_retention", {}).get(
        "collection_default", ""
    )
    if "No collection is authorized" not in collection_default:
        errors.append("privacy contract must deny collection by default")

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
                if schema_path == Path(
                    "contracts/schemas/response-observation.v1.schema.json"
                ):
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
    missing_response_fields = REQUIRED_RESPONSE_FIELDS - seen_response_fields
    if missing_response_fields:
        errors.append(
            "protocol does not map required response fields: "
            + ", ".join(sorted(missing_response_fields))
        )

    methods = (project / METHODS_PATH).read_text(encoding="utf-8")
    if r"\AntidotePlaceholder" in methods:
        errors.append("Methods still contains governed content placeholders")
    for marker in (
        "ANT-PROT-FEAS-001",
        "frozen-design-protocol",
        "collection authority",
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
        "% Source: experiments/protocols/antidote-feasibility-v1.json.",
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
