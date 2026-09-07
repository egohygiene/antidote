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
REPORTING_PATH = Path("experiments/reporting/results-reporting-v1.json")
PROTOCOL_PATH = Path("experiments/protocols/antidote-feasibility-v1.json")
LOCK_PATH = Path("experiments/protocols/antidote-feasibility-v1.lock.json")
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
    "uncertainty": ["#/analysis_plan/uncertainty"],
    "visualizations": [
        "#/analysis_plan/primary_technical_summaries",
        "#/analysis_plan/primary_human_feasibility_summaries",
        "#/analysis_plan/uncertainty",
    ],
    "missingness": ["#/analysis_plan/missingness"],
    "sensitivity_analyses": ["#/analysis_plan/sensitivity_analyses"],
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
    "disabled-requires-amendment": "Disabled under protocol v1.0.0",
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
        manifest = load_json(project, MANIFEST_PATH)
    except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        return [f"Results reporting inputs are invalid: {error}"]

    expected_identity = {
        "schema": "antidote.results-reporting/v1",
        "reporting_id": "ANT-REPORT-RESULTS-001",
        "version": "1.0.0",
        "status": "governed-empty-reporting-contract",
        "governed_by": "egohygiene/antidote#41",
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
    if protocol.get("collection_authority") is not False:
        errors.append("reporting contract requires protocol collection authority false")

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

    analysis_reporting = reporting.get("analysis_reporting", {})
    if not isinstance(analysis_reporting, dict) or set(analysis_reporting) != set(
        EXPECTED_ANALYSIS_REPORTING
    ):
        errors.append("analysis reporting dimensions are incomplete")
        analysis_reporting = {}
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
                f"analysis reporting dimension {dimension} protocol pointers have drifted"
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
        except ValueError as error:
            errors.append(f"source record {record_id} {error}")

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
        if not isinstance(pointers, list) or not pointers:
            errors.append(f"analysis {analysis_id} requires protocol pointers")
        else:
            for pointer in pointers:
                try:
                    resolve_json_pointer(protocol, str(pointer))
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
        if not isinstance(visual_ids, list) or any(
            visual_id not in manifest_visuals for visual_id in visual_ids
        ):
            errors.append(f"result slot {slot_id} has invalid visual IDs")

    table_shells = reporting.get("table_shells", [])
    table_outputs: dict[str, str] = {}
    mapped_table_slots: set[str] = set()
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
        for slot_id in slot_ids:
            if slot_id not in slot_by_id:
                errors.append(
                    f"table shell {visual_id} references unknown slot {slot_id}"
                )
            mapped_table_slots.add(str(slot_id))
        visual = manifest_visuals.get(visual_id)
        if visual is None or visual.get("kind") != "table":
            errors.append(f"table shell {visual_id} lacks a manifest table")
        elif visual.get("state") != "draft":
            errors.append(f"table shell {visual_id} must be a governed draft")
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
        figure_ids.add(str(visual_id))
        visual = manifest_visuals.get(visual_id)
        if visual is None or visual.get("kind") != "figure":
            errors.append(f"figure shell {visual_id} lacks a manifest figure")
        elif visual.get("state") != "placeholder":
            errors.append(f"figure shell {visual_id} must remain a placeholder")
        for slot_id in shell.get("slot_ids", []):
            if slot_id not in slot_by_id:
                errors.append(
                    f"figure shell {visual_id} references unknown slot {slot_id}"
                )
    if figure_ids != EXPECTED_FIGURES:
        errors.append("Results figure-shell inventory has drifted")

    for slot_id, slot in slot_by_id.items():
        for visual_id in slot.get("visual_ids", []):
            if visual_id.startswith("ANT-TBL-") and slot_id not in mapped_table_slots:
                errors.append(f"result slot {slot_id} is not mapped into its table")

    if r"\AntidotePlaceholder" in results_text:
        errors.append("Results still contains governed content placeholders")
    for marker in (
        "ANT-REPORT-RESULTS-001",
        "no formal human results",
        r"issue~\#18",
        "ANT-PROT-FEAS-001",
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
                    r"\textbf{Protocol:} "
                    rf"\nolinkurl{{{tex_escape(reporting['protocol']['protocol_id'])}}} "
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
