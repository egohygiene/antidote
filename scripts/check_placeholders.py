#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate the governed manuscript skeleton and content placeholders."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = Path("paper/skeleton.json")
ENTRYPOINT_PATH = Path("paper/paper.tex")
PLACEHOLDER = re.compile(
    r"\\AntidotePlaceholder\{([^{}]+)\}\{([^{}]+)\}\{([^{}]+)\}",
    re.DOTALL,
)
LABEL = re.compile(r"\\label\{([^{}]+)\}")
PLACEHOLDER_ID = re.compile(r"ANT-PH-[A-Z]{3}-\d{3}")
ALLOWED_STATES = {"active", "resolved", "retired"}
BLOCKING_STAGES = {"submission-ready", "published"}
REQUIRED_FRONT_MATTER = (
    ("table-of-contents", r"\tableofcontents"),
    ("list-of-figures", r"\listoffigures"),
    ("list-of-tables", r"\listoftables"),
)


def load_manifest(project: Path) -> dict[str, object]:
    """Load the canonical paper skeleton manifest."""
    return json.loads((project / MANIFEST_PATH).read_text(encoding="utf-8"))


def manuscript_placeholders(project: Path) -> list[dict[str, str]]:
    """Collect placeholder macro invocations from canonical section sources."""
    observed: list[dict[str, str]] = []
    for path in sorted((project / "paper" / "sections").glob("*.tex")):
        text = path.read_text(encoding="utf-8")
        for placeholder_id, title, content in PLACEHOLDER.findall(text):
            observed.append(
                {
                    "id": placeholder_id.strip(),
                    "title": re.sub(r"\s+", " ", title).strip(),
                    "content": re.sub(r"\s+", " ", content).strip(),
                    "section_path": path.relative_to(project).as_posix(),
                }
            )
    return observed


def validate_placeholder_system(
    project: Path = ROOT, *, paper_stage: str = "draft"
) -> dict[str, object]:
    """Validate structure, stable IDs, registry projection, and release gates."""
    project = project.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    try:
        manifest = load_manifest(project)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return {
            "errors": [f"paper skeleton manifest is invalid: {error}"],
            "warnings": [],
            "active": [],
        }

    if manifest.get("schema") != "antidote.paper-skeleton/v1":
        errors.append("paper skeleton schema must be antidote.paper-skeleton/v1")
    if manifest.get("version") != "0.1.0":
        errors.append("paper skeleton version must be 0.1.0")
    if manifest.get("governed_by") != "egohygiene/antidote#77":
        errors.append("paper skeleton must be governed by issue #77")
    for field in ("publication_policy", "visual_manifest", "research_shelf"):
        if not isinstance(manifest.get(field), str) or not manifest.get(field):
            errors.append(f"paper skeleton is missing {field}")

    entrypoint = (project / ENTRYPOINT_PATH).read_text(encoding="utf-8")
    declared_front_matter = manifest.get("front_matter")
    if declared_front_matter != [item[0] for item in REQUIRED_FRONT_MATTER]:
        errors.append("paper skeleton front matter order is incomplete")
    positions: list[int] = []
    for _, command in REQUIRED_FRONT_MATTER:
        count = entrypoint.count(command)
        if count != 1:
            errors.append(f"paper entrypoint must contain {command} exactly once")
        positions.append(entrypoint.find(command))
    if positions != sorted(positions) or any(position < 0 for position in positions):
        errors.append("paper front matter commands are not in canonical order")

    appendices = manifest.get("appendices")
    if not isinstance(appendices, list) or not appendices:
        errors.append("paper skeleton must declare appendices")
        appendices = []
    appendix_path = project / "paper" / "sections" / "appendix.tex"
    appendix_text = appendix_path.read_text(encoding="utf-8")
    appendix_labels = set(LABEL.findall(appendix_text))
    appendix_ids: list[str] = []
    for appendix in appendices:
        if not isinstance(appendix, dict):
            errors.append("every appendix entry must be an object")
            continue
        appendix_id = appendix.get("id")
        label = appendix.get("label")
        if not isinstance(appendix_id, str) or not re.fullmatch(r"ANT-APP-[A-Z]", appendix_id):
            errors.append(f"invalid appendix ID: {appendix_id}")
        else:
            appendix_ids.append(appendix_id)
        if label not in appendix_labels:
            errors.append(f"appendix label does not resolve: {label}")
        if not appendix.get("title") or not appendix.get("owner_issues"):
            errors.append(f"appendix entry is incomplete: {appendix_id}")
    for appendix_id, count in Counter(appendix_ids).items():
        if count > 1:
            errors.append(f"duplicate appendix ID: {appendix_id}")

    registered = manifest.get("placeholders")
    if not isinstance(registered, list) or not registered:
        errors.append("paper skeleton must contain registered placeholders")
        registered = []
    observed = manuscript_placeholders(project)
    observed_by_id = {item["id"]: item for item in observed}
    observed_counts = Counter(item["id"] for item in observed)
    registered_ids: list[str] = []
    active: list[dict[str, object]] = []

    for record in registered:
        if not isinstance(record, dict):
            errors.append("every placeholder record must be an object")
            continue
        placeholder_id = record.get("id")
        if not isinstance(placeholder_id, str) or not PLACEHOLDER_ID.fullmatch(
            placeholder_id
        ):
            errors.append(f"invalid placeholder ID: {placeholder_id}")
            continue
        registered_ids.append(placeholder_id)
        for field in (
            "title",
            "section_path",
            "section_label",
            "owner_issues",
            "content_class",
            "purpose",
            "state",
            "layout_words",
        ):
            if field not in record:
                errors.append(f"{placeholder_id} is missing field: {field}")
        state = record.get("state")
        if state not in ALLOWED_STATES:
            errors.append(f"{placeholder_id} has invalid state: {state}")
        owner_issues = record.get("owner_issues")
        if not isinstance(owner_issues, list) or not owner_issues or any(
            not isinstance(issue, int) or issue <= 0 for issue in owner_issues
        ):
            errors.append(f"{placeholder_id} requires positive owner issues")
        layout_words = record.get("layout_words")
        if (
            not isinstance(layout_words, dict)
            or not isinstance(layout_words.get("minimum"), int)
            or not isinstance(layout_words.get("target"), int)
            or layout_words.get("minimum", 0) <= 0
            or layout_words.get("target", 0) < layout_words.get("minimum", 0)
        ):
            errors.append(f"{placeholder_id} has invalid layout word guidance")

        section_path = record.get("section_path")
        section = project / str(section_path)
        if not section.is_file() or project not in section.resolve().parents:
            errors.append(f"{placeholder_id} owning section is missing or unsafe")
        else:
            labels = set(LABEL.findall(section.read_text(encoding="utf-8")))
            if record.get("section_label") not in labels:
                errors.append(f"{placeholder_id} section label does not resolve")

        count = observed_counts[placeholder_id]
        if state == "active":
            active.append(record)
            if count != 1:
                errors.append(f"{placeholder_id} active placeholder must appear exactly once")
            else:
                invocation = observed_by_id[placeholder_id]
                if invocation["title"] != record.get("title"):
                    errors.append(f"{placeholder_id} title drifted from the manifest")
                if invocation["section_path"] != section_path:
                    errors.append(f"{placeholder_id} appears in the wrong section")
                if not invocation["content"].startswith("Lorem ipsum"):
                    errors.append(f"{placeholder_id} layout filler must begin with Lorem ipsum")
                if "\\cite" in invocation["content"] or "\\ref" in invocation["content"]:
                    errors.append(f"{placeholder_id} filler cannot contain claims or references")
            if paper_stage in BLOCKING_STAGES:
                errors.append(f"{placeholder_id} blocks {paper_stage} publication")
        elif count:
            errors.append(f"{placeholder_id} {state} placeholder remains in manuscript source")

    for placeholder_id, count in Counter(registered_ids).items():
        if count > 1:
            errors.append(f"duplicate registered placeholder ID: {placeholder_id}")
    for placeholder_id, count in observed_counts.items():
        if placeholder_id not in set(registered_ids):
            errors.append(f"unregistered manuscript placeholder: {placeholder_id}")
        if count > 1:
            errors.append(f"duplicate manuscript placeholder: {placeholder_id}")

    if active and paper_stage == "draft":
        warnings.append(f"draft paper contains {len(active)} governed content placeholders")
    return {"errors": errors, "warnings": warnings, "active": active, "manifest": manifest}


def main() -> int:
    """Validate one repository paper skeleton."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=str(ROOT))
    parser.add_argument("--paper-stage", default="draft")
    arguments = parser.parse_args()
    result = validate_placeholder_system(
        Path(arguments.project), paper_stage=arguments.paper_stage
    )
    for warning in sorted(set(result["warnings"])):
        print(f"WARN {warning}")
    if result["errors"]:
        for error in result["errors"]:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print(
        "PASS governed paper skeleton "
        f"({len(result['active'])} active content placeholders)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
