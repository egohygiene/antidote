#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate Antidote's governed scientific figure and table system."""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = Path("paper/visuals/manifest.json")
REGISTRY_PATH = Path("paper/visuals/captions.tex")
CONTRACT_PATH = Path("paper/manuscript-contract.json")
LEDGER_PATH = Path("research/notes/CLAIM_LEDGER.md")
VISUAL_ID = re.compile(r"ANT-(?:FIG|TBL)-\d{3}")
SLUG = re.compile(r"[a-z0-9][a-z0-9-]*")
REFERENCE = re.compile(r"\\Antidote(Figure|Table)\{([^{}]+)\}")
LABEL = re.compile(r"\\label\{([^{}]+)\}")
SPEC_HEADINGS = (
    "## Scientific purpose",
    "## Required content",
    "## Evidence and claim boundary",
    "## Source plan",
    "## Accessibility plan",
    "## Failure conditions",
)
ALLOWED_STATES = {"planned", "placeholder", "draft", "final"}
ALLOWED_STATUSES = {"active", "inactive", "retired"}
ALLOWED_SOURCE_MODES = {
    "deterministic-vector",
    "deterministic-table",
    "generated-editorial",
}


class DuplicateKeyError(ValueError):
    """Raised when a JSON object repeats a key."""


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Build one JSON object while rejecting silently overwritten keys."""
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, object]:
    """Load a strict JSON object."""
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def project_path(project: Path, relative: object) -> Path:
    """Resolve one manifest path without allowing repository escape."""
    if not isinstance(relative, str) or not relative:
        raise ValueError("manifest path must be a non-empty string")
    resolved = (project / relative).resolve()
    if resolved != project and project not in resolved.parents:
        raise ValueError(f"manifest path escapes project: {relative}")
    return resolved


def tex_escape(value: str) -> str:
    """Escape plain registry text for deterministic LaTeX inclusion."""
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
    normalized = re.sub(r"\s+", " ", value).strip()
    return "".join(replacements.get(character, character) for character in normalized)


def registry_text(manifest: dict[str, object]) -> str:
    """Render the centralized LaTeX caption registry from the manifest."""
    visuals = manifest.get("visuals", [])
    if not isinstance(visuals, list):
        raise ValueError("visuals must be an array")
    lines = [
        "% Generated from paper/visuals/manifest.json.",
        "% Edit the manifest, then run scripts/check_visuals.py --write-registry.",
        "",
    ]
    for visual in visuals:
        if not isinstance(visual, dict):
            raise ValueError("every visual must be an object")
        lines.extend(
            [
                r"\AntidoteDeclareVisualText",
                f"  {{{visual.get('slug', '')}}}",
                f"  {{{tex_escape(str(visual.get('caption', '')))}}}",
                f"  {{{tex_escape(str(visual.get('alt_text', '')))}}}",
                f"  {{{tex_escape(str(visual.get('long_description', '')))}}}",
                f"  {{{visual.get('state', '')}}}",
                "",
            ]
        )
    return "\n".join(lines)


def manuscript_text(project: Path) -> str:
    """Collect canonical manuscript and table LaTeX for reference checks."""
    paths = sorted((project / "paper").rglob("*.tex"))
    registry = (project / REGISTRY_PATH).resolve()
    return "\n".join(
        path.read_text(encoding="utf-8") for path in paths if path.resolve() != registry
    )


def contract_visuals(project: Path) -> dict[tuple[str, str], int]:
    """Return every visual promised by the frozen manuscript contract."""
    contract = load_json(project / CONTRACT_PATH)
    expected: dict[tuple[str, str], int] = {}
    for section in contract.get("sections", []):
        if not isinstance(section, dict):
            continue
        path = section.get("path")
        for name in section.get("planned_visuals", []):
            if isinstance(path, str) and isinstance(name, str):
                expected[(path, name)] = expected.get((path, name), 0) + 1
    return expected


def claim_ids(project: Path) -> set[str]:
    """Collect stable claim-ledger identifiers."""
    ledger = (project / LEDGER_PATH).read_text(encoding="utf-8")
    return set(re.findall(r"(?m)^\| (ANT-[A-Z]+-\d{3}) \|", ledger))


def svg_dimensions(path: Path) -> tuple[float, float, str | None]:
    """Return numeric SVG dimensions and its declared governance state."""
    root = ET.parse(path).getroot()

    def number(name: str) -> float:
        value = root.attrib.get(name, "")
        match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)(?:px)?", value)
        if match is None:
            raise ValueError(f"SVG {name} must be a numeric pixel dimension: {path}")
        return float(match.group(1))

    return number("width"), number("height"), root.attrib.get("data-antidote-state")


def duplicates(values: list[str]) -> set[str]:
    """Return values that occur more than once."""
    return {value for value, count in Counter(values).items() if count > 1}


def validate_visual_system(
    project: Path = ROOT, *, paper_stage: str = "draft"
) -> dict[str, object]:
    """Validate manifest, assets, references, captions, and source specifications."""
    project = project.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    try:
        manifest = load_json(project / MANIFEST_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return {"errors": [f"visual manifest is invalid: {error}"], "warnings": [], "active": []}

    if manifest.get("schema") != "antidote.visual-manifest/v1":
        errors.append("visual manifest schema must be antidote.visual-manifest/v1")
    if manifest.get("version") != "0.1.0":
        errors.append("visual manifest version must be 0.1.0")
    for policy in (
        "format_policy",
        "accessibility_policy",
        "licensing_policy",
        "reuse_policy",
    ):
        if not isinstance(manifest.get(policy), str) or not manifest.get(policy):
            errors.append(f"visual manifest policy is missing: {policy}")

    visuals = manifest.get("visuals")
    if not isinstance(visuals, list) or not visuals:
        errors.append("visual manifest must contain a non-empty visuals array")
        visuals = []

    tex = manuscript_text(project)
    references = REFERENCE.findall(tex)
    reference_counts = Counter(slug for _, slug in references)
    explicit_labels = LABEL.findall(tex)
    for label in sorted(duplicates(explicit_labels)):
        errors.append(f"duplicate LaTeX label: {label}")

    known_claims = claim_ids(project)
    expected_contract = contract_visuals(project)
    observed_contract: Counter[tuple[str, str]] = Counter()
    active: list[dict[str, object]] = []
    ids: list[str] = []
    slugs: list[str] = []
    labels: list[str] = []
    filenames: list[str] = []
    captions: list[str] = []
    alt_texts: list[str] = []
    long_descriptions: list[str] = []

    required_fields = (
        "id",
        "kind",
        "slug",
        "title",
        "scientific_purpose",
        "section_path",
        "section_label",
        "owner_issues",
        "filename",
        "label",
        "dimensions",
        "state",
        "status",
        "source",
        "caption",
        "alt_text",
        "long_description",
        "claim_ids",
        "reuse_targets",
        "reuse_authority",
    )
    for index, visual in enumerate(visuals):
        if not isinstance(visual, dict):
            errors.append(f"visual at index {index} must be an object")
            continue
        visual_id = str(visual.get("id", f"index-{index}"))
        for field in required_fields:
            if field not in visual:
                errors.append(f"{visual_id} is missing field: {field}")

        kind = visual.get("kind")
        slug = visual.get("slug")
        label = visual.get("label")
        filename = visual.get("filename")
        state = visual.get("state")
        status = visual.get("status")
        if not isinstance(visual.get("id"), str) or not VISUAL_ID.fullmatch(visual_id):
            errors.append(f"invalid visual ID: {visual_id}")
        if kind not in {"figure", "table"}:
            errors.append(f"{visual_id} kind must be figure or table")
        expected_prefix = "ANT-FIG-" if kind == "figure" else "ANT-TBL-"
        if kind in {"figure", "table"} and not visual_id.startswith(expected_prefix):
            errors.append(f"{visual_id} does not match its {kind} kind")
        if not isinstance(slug, str) or not SLUG.fullmatch(slug):
            errors.append(f"{visual_id} has an invalid slug: {slug}")
            continue
        expected_label = f"{'fig' if kind == 'figure' else 'tab'}:{slug}"
        if label != expected_label:
            errors.append(f"{visual_id} label must be {expected_label}")
        if state not in ALLOWED_STATES:
            errors.append(f"{visual_id} has invalid state: {state}")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{visual_id} has invalid status: {status}")
        if status == "active" and state == "planned":
            errors.append(f"{visual_id} cannot be active while planned")
        if status == "inactive" and state != "planned":
            errors.append(f"{visual_id} inactive visuals must remain planned")
        if (
            paper_stage in {"submission-ready", "published"}
            and status == "active"
            and state != "final"
        ):
            errors.append(f"{visual_id} must be final for {paper_stage} publication")

        for field in ("title", "scientific_purpose", "caption", "alt_text", "long_description"):
            value = visual.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{visual_id} requires non-empty {field}")
        caption = str(visual.get("caption", "")).strip()
        alt_text = str(visual.get("alt_text", "")).strip()
        long_description = str(visual.get("long_description", "")).strip()
        if caption and alt_text and caption.casefold() == alt_text.casefold():
            errors.append(f"{visual_id} caption and alt text must be non-duplicative")
        if alt_text and long_description and len(long_description.split()) <= len(alt_text.split()):
            errors.append(f"{visual_id} long description must add detail beyond alt text")

        section_path = visual.get("section_path")
        try:
            section = project_path(project, section_path)
            if not section.is_file():
                errors.append(f"{visual_id} owning section is missing: {section_path}")
            elif visual.get("section_label") not in LABEL.findall(
                section.read_text(encoding="utf-8")
            ):
                errors.append(
                    f"{visual_id} section label does not resolve: "
                    f"{visual.get('section_label')}"
                )
        except ValueError as error:
            errors.append(f"{visual_id} {error}")

        owner_issues = visual.get("owner_issues")
        if not isinstance(owner_issues, list) or not owner_issues or any(
            not isinstance(issue, int) or issue <= 0 for issue in owner_issues
        ):
            errors.append(f"{visual_id} requires positive integer owner issues")

        contract_name = visual.get("contract_visual")
        if contract_name is not None:
            if not isinstance(contract_name, str) or not contract_name:
                errors.append(f"{visual_id} contract_visual must be null or non-empty")
            elif isinstance(section_path, str):
                key = (section_path, contract_name)
                observed_contract[key] += 1
                if key not in expected_contract:
                    errors.append(f"{visual_id} does not resolve to a planned manuscript visual")

        dimensions = visual.get("dimensions")
        if not isinstance(dimensions, dict):
            errors.append(f"{visual_id} dimensions must be an object")
        else:
            if dimensions.get("role") not in {"actual", "target"}:
                errors.append(f"{visual_id} dimensions role must be actual or target")
            if dimensions.get("unit") not in {"px", "in"}:
                errors.append(f"{visual_id} dimensions unit must be px or in")
            for axis in ("width", "height"):
                if not isinstance(dimensions.get(axis), (int, float)) or (
                    dimensions.get(axis, 0) <= 0
                ):
                    errors.append(f"{visual_id} dimensions require positive {axis}")

        source = visual.get("source")
        if not isinstance(source, dict):
            errors.append(f"{visual_id} source must be an object")
            source = {}
        mode = source.get("mode")
        source_format = source.get("format")
        if mode not in ALLOWED_SOURCE_MODES:
            errors.append(f"{visual_id} has invalid source mode: {mode}")
        for field in ("format", "specification", "provenance", "license"):
            if not isinstance(source.get(field), str) or not source.get(field):
                errors.append(f"{visual_id} source requires {field}")
        try:
            spec = project_path(project, source.get("specification"))
            if not spec.is_file():
                errors.append(f"{visual_id} source specification is missing")
            else:
                spec_text = spec.read_text(encoding="utf-8")
                if visual_id not in spec_text:
                    errors.append(f"{visual_id} source specification omits its ID")
                for heading in SPEC_HEADINGS:
                    if heading not in spec_text:
                        errors.append(f"{visual_id} specification is missing: {heading}")
        except ValueError as error:
            errors.append(f"{visual_id} {error}")

        prompt_record = source.get("prompt_record")
        if mode == "generated-editorial":
            if source_format != "png":
                errors.append(f"{visual_id} generated editorial assets must use PNG")
            if not isinstance(prompt_record, str) or not prompt_record:
                errors.append(f"{visual_id} generated editorial asset requires a prompt record")
            else:
                try:
                    if not project_path(project, prompt_record).is_file():
                        errors.append(f"{visual_id} prompt record is missing")
                except ValueError as error:
                    errors.append(f"{visual_id} {error}")
        elif prompt_record is not None:
            errors.append(f"{visual_id} deterministic source must not declare a prompt record")

        if not isinstance(filename, str) or not filename:
            errors.append(f"{visual_id} filename must be non-empty")
            asset = None
        else:
            try:
                asset = project_path(project, filename)
            except ValueError as error:
                errors.append(f"{visual_id} {error}")
                asset = None
        if isinstance(filename, str) and isinstance(source_format, str):
            if Path(filename).suffix.lower() != f".{source_format}":
                errors.append(f"{visual_id} filename does not match source format")
            expected_parent = "paper/figures/" if kind == "figure" else "paper/tables/"
            if not filename.startswith(expected_parent):
                errors.append(f"{visual_id} filename must remain under {expected_parent}")

        if status == "active":
            active.append(visual)
            if reference_counts[slug] != 1:
                errors.append(f"{visual_id} active visual must be referenced exactly once")
            reference_kind = "Figure" if kind == "figure" else "Table"
            if (reference_kind, slug) not in references:
                errors.append(f"{visual_id} reference kind does not match {kind}")
            if asset is None or not asset.is_file():
                errors.append(f"{visual_id} active asset is missing: {filename}")
            elif kind == "figure" and source_format == "svg":
                try:
                    width, height, svg_state = svg_dimensions(asset)
                    if isinstance(dimensions, dict) and dimensions.get("role") == "actual":
                        expected_dimensions = (
                            float(dimensions.get("width", 0)),
                            float(dimensions.get("height", 0)),
                        )
                        if (width, height) != expected_dimensions:
                            errors.append(f"{visual_id} SVG dimensions do not match the manifest")
                    if svg_state != state:
                        errors.append(
                            f"{visual_id} SVG governance state does not match the manifest"
                        )
                    svg_text = asset.read_text(encoding="utf-8")
                    if state == "placeholder" and "PROVISIONAL" not in svg_text:
                        errors.append(
                            f"{visual_id} placeholder asset lacks a visible provisional marker"
                        )
                    if state == "final" and "PROVISIONAL" in svg_text:
                        errors.append(f"{visual_id} final asset retains a provisional marker")
                except (ET.ParseError, ValueError, OSError) as error:
                    errors.append(f"{visual_id} SVG is invalid: {error}")
        elif reference_counts[slug]:
            errors.append(f"{visual_id} inactive visual is referenced by the manuscript")

        claim_list = visual.get("claim_ids")
        if not isinstance(claim_list, list) or not claim_list:
            errors.append(f"{visual_id} requires at least one claim-ledger ID")
        else:
            for claim_id in claim_list:
                if claim_id not in known_claims:
                    errors.append(f"{visual_id} claim ID does not resolve: {claim_id}")

        targets = visual.get("reuse_targets")
        if targets != ["pdf", "web", "magazine"]:
            errors.append(f"{visual_id} reuse targets must be pdf, web, and magazine")
        if visual.get("reuse_authority") != "paper":
            errors.append(f"{visual_id} reuse authority must remain paper")

        ids.append(visual_id)
        slugs.append(slug)
        labels.append(str(label))
        filenames.append(str(filename))
        captions.append(caption)
        alt_texts.append(alt_text)
        long_descriptions.append(long_description)

    for field, values in (
        ("ID", ids),
        ("slug", slugs),
        ("label", labels),
        ("filename", filenames),
        ("caption", captions),
        ("alt text", alt_texts),
        ("long description", long_descriptions),
    ):
        for value in sorted(duplicates(values)):
            errors.append(f"duplicate visual {field}: {value}")

    manifest_labels = set(labels)
    for label in sorted(manifest_labels & set(explicit_labels)):
        errors.append(f"visual label is duplicated explicitly in LaTeX: {label}")
    for kind, slug in references:
        if slug not in set(slugs):
            errors.append(f"manuscript references unknown visual: {slug}")

    for key, count in expected_contract.items():
        if count != 1:
            errors.append(f"manuscript contract repeats planned visual: {key[0]} / {key[1]}")
        if observed_contract[key] != 1:
            errors.append(f"manifest must allocate planned visual: {key[0]} / {key[1]}")

    try:
        registry = project / REGISTRY_PATH
        expected_registry = registry_text(manifest)
        if not registry.is_file():
            errors.append(f"centralized caption registry is missing: {REGISTRY_PATH}")
        elif registry.read_text(encoding="utf-8") != expected_registry:
            errors.append("caption registry is stale or contains orphaned entries")
    except (OSError, ValueError) as error:
        errors.append(f"caption registry cannot be validated: {error}")

    return {"errors": errors, "warnings": warnings, "active": active, "manifest": manifest}


def main() -> int:
    """Validate the canonical visual system or refresh its LaTeX registry."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=str(ROOT))
    parser.add_argument("--paper-stage", default="draft")
    parser.add_argument("--write-registry", action="store_true")
    arguments = parser.parse_args()
    project = Path(arguments.project).expanduser().resolve()
    if arguments.write_registry:
        manifest = load_json(project / MANIFEST_PATH)
        destination = project / REGISTRY_PATH
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(registry_text(manifest), encoding="utf-8")
    result = validate_visual_system(project, paper_stage=arguments.paper_stage)
    for warning in sorted(set(result["warnings"])):
        print(f"WARN {warning}")
    if result["errors"]:
        for error in result["errors"]:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print(f"PASS governed scientific visual system ({len(result['active'])} active).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
