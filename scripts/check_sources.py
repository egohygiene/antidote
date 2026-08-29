#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate the Antidote atlas, bibliography shelf, and source promotion gates."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "research" / "sources" / "catalog.json"
ATLAS_PATH = ROOT / "research" / "atlas" / "literature-voyage-v0.1.md"
BIBLIOGRAPHY_PATH = ROOT / "paper" / "references.bib"
ARCHITECTURE_MAP_PATH = (
    ROOT / "research" / "sources" / "architecture-evidence-map.json"
)
COMPARATOR_MATRIX_PATH = (
    ROOT / "research" / "sources" / "comparator-novelty-matrix.json"
)

SOURCE_STATES = {
    "discovered",
    "metadata-verified",
    "full-text-reviewed",
    "promoted",
    "cited",
    "background-only",
    "superseded",
    "rejected",
}
SOURCE_CLASSES = {
    "contextual",
    "guidance",
    "implementation",
    "method",
    "preprint",
    "primary",
    "standard",
    "synthesis",
    "system",
}
CLAIM_BEARING_STATES = {"promoted", "cited"}
ARCHITECTURE_EVIDENCE_ROLES = {
    "scientific-precedent",
    "normative-standard",
    "engineering-pattern",
    "emerging-system",
    "speculative-transfer",
    "qualifying-evidence",
}
SUPPORT_DIRECTIONS = {"supporting", "qualifying", "conflicting", "mixed"}
COMPARATOR_RELATIONSHIPS = {"direct", "adjacent", "enabling", "qualifying"}
COMPARATOR_EVIDENCE_GRADES = {
    "system-peer-reviewed",
    "system-preprint",
    "single-rct",
}
COMPARATOR_DIMENSION_STATUSES = {
    "reported",
    "partial",
    "proposed",
    "not-reported",
    "not-applicable",
}
NOVELTY_DECISIONS = {"rejected", "narrowed", "unresolved"}
COMPARATOR_DIMENSIONS = {
    "state_inputs",
    "semantic_representation",
    "user_agency",
    "journey_representation",
    "audio_strategy",
    "generator_controls",
    "within_session_adaptation",
    "physiological_sensing",
    "longitudinal_learning",
    "evaluation",
    "provenance",
    "privacy",
    "clinical_positioning",
}

ENTRY_START = re.compile(r"@\w+\s*\{\s*([^,\s]+)", re.IGNORECASE)
CITATION = re.compile(r"\\cite\w*\*?(?:\[[^\]]*\]){0,2}\{([^}]+)\}")
FIELD = re.compile(
    r"(?im)^\s*(doi|eprint|url)\s*=\s*\{([^}]+)\}\s*,?\s*$"
)


def bibliography_entries(text: str) -> list[tuple[str, str]]:
    """Return citation keys paired with their entry bodies."""
    starts = list(ENTRY_START.finditer(text))
    entries: list[tuple[str, str]] = []
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        entries.append((match.group(1), text[match.start() : end]))
    return entries


def manuscript_citations() -> set[str]:
    """Collect citation keys from canonical manuscript sources."""
    citations: set[str] = set()
    for path in sorted((ROOT / "paper").rglob("*.tex")):
        text = path.read_text(encoding="utf-8")
        for group in CITATION.findall(text):
            citations.update(key.strip() for key in group.split(",") if key.strip())
    return citations


def normalized_identifier(kind: str, value: str) -> str:
    """Normalize identifiers for duplicate detection."""
    normalized = value.strip().lower().rstrip("/")
    if kind == "url":
        normalized = re.sub(r"^https?://(?:dx\.)?", "", normalized)
    if kind == "doi":
        normalized = re.sub(r"^(?:doi:)?", "", normalized)
    return f"{kind}:{normalized}"


def validate() -> list[str]:
    """Return all source-governance validation errors."""
    errors: list[str] = []
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    bibliography = BIBLIOGRAPHY_PATH.read_text(encoding="utf-8")
    architecture_map = json.loads(
        ARCHITECTURE_MAP_PATH.read_text(encoding="utf-8")
    )
    comparator_matrix = json.loads(
        COMPARATOR_MATRIX_PATH.read_text(encoding="utf-8")
    )
    sources = catalog.get("sources")

    if catalog.get("schema") != "antidote.source-catalog/v1":
        errors.append("catalog schema must be antidote.source-catalog/v1")
    if not isinstance(sources, list) or len(sources) < 60:
        errors.append("catalog must preserve at least 60 distinct atlas sources")
        return errors

    ids: list[str] = []
    persistent_ids: list[str] = []
    canonical_urls: list[str] = []
    catalog_bib_keys: list[str] = []
    cited_catalog_keys: set[str] = set()

    for source in sources:
        source_id = source.get("id")
        if not isinstance(source_id, str) or not re.fullmatch(
            r"[a-z0-9][a-z0-9.-]*", source_id
        ):
            errors.append(f"invalid source id: {source_id!r}")
            continue
        ids.append(source_id)
        for field in (
            "working_title",
            "domains",
            "source_class",
            "status",
            "owner",
            "priority",
            "canonical_url",
        ):
            if not source.get(field):
                errors.append(f"{source_id}: missing {field}")
        if source.get("status") not in SOURCE_STATES:
            errors.append(f"{source_id}: invalid status {source.get('status')!r}")
        if source.get("source_class") not in SOURCE_CLASSES:
            errors.append(
                f"{source_id}: invalid source class {source.get('source_class')!r}"
            )
        if source.get("owner") not in catalog.get("owners", {}):
            errors.append(f"{source_id}: unknown owner {source.get('owner')!r}")
        if not isinstance(source.get("priority"), int) or source["priority"] < 1:
            errors.append(f"{source_id}: priority must be a positive integer")

        canonical_url = source.get("canonical_url")
        if isinstance(canonical_url, str):
            canonical_urls.append(canonical_url.rstrip("/").lower())
            if canonical_url not in atlas:
                errors.append(f"{source_id}: canonical URL is absent from atlas")
        for resource in source.get("resources", []):
            if resource not in atlas:
                errors.append(f"{source_id}: resource URL is absent from atlas: {resource}")

        persistent_id = source.get("persistent_id")
        if isinstance(persistent_id, str):
            persistent_ids.append(persistent_id.lower())

        bib_key = source.get("bibliography_key")
        if bib_key:
            catalog_bib_keys.append(bib_key)

        if source.get("status") in CLAIM_BEARING_STATES:
            if not bib_key:
                errors.append(f"{source_id}: claim-bearing source lacks bibliography key")
            record = source.get("source_record")
            if not record:
                errors.append(f"{source_id}: claim-bearing source lacks source record")
            else:
                record_path = ROOT / record
                if not record_path.is_file():
                    errors.append(f"{source_id}: missing source record {record}")
                else:
                    record_text = record_path.read_text(encoding="utf-8")
                    for heading in (
                        "## Verified metadata",
                        "## Source claims assessed",
                        "## Limitations and unresolved questions",
                        "## Allowed manuscript use",
                        "## Prohibited manuscript use",
                    ):
                        if heading not in record_text:
                            errors.append(f"{source_id}: record missing {heading}")
            if source.get("status") == "cited" and bib_key:
                cited_catalog_keys.add(bib_key)

    for label, values in (
        ("source id", ids),
        ("persistent identifier", persistent_ids),
        ("canonical URL", canonical_urls),
        ("catalog bibliography key", catalog_bib_keys),
    ):
        for value, count in Counter(values).items():
            if count > 1:
                errors.append(f"duplicate {label}: {value}")

    entries = bibliography_entries(bibliography)
    bibliography_keys = [key for key, _ in entries]
    for key, count in Counter(bibliography_keys).items():
        if count > 1:
            errors.append(f"duplicate bibliography key: {key}")

    bibliography_key_set = set(bibliography_keys)
    for key in sorted(set(catalog_bib_keys) - bibliography_key_set):
        errors.append(f"catalog bibliography key missing from shelf: {key}")
    for key in sorted(bibliography_key_set - set(catalog_bib_keys)):
        errors.append(f"bibliography shelf entry missing from catalog: {key}")

    identifiers: dict[str, str] = {}
    for key, body in entries:
        for kind, value in FIELD.findall(body):
            identifier = normalized_identifier(kind.lower(), value)
            previous = identifiers.get(identifier)
            if previous is not None and previous != key:
                errors.append(
                    f"duplicate bibliography {kind.lower()} in {previous} and {key}: {value}"
                )
            identifiers[identifier] = key

    citations = manuscript_citations()
    for key in sorted(citations - bibliography_key_set):
        errors.append(f"manuscript citation missing from bibliography: {key}")
    for key in sorted(citations - cited_catalog_keys):
        errors.append(f"manuscript citation is not governed as cited: {key}")
    for key in sorted(cited_catalog_keys - citations):
        errors.append(f"catalog source marked cited but absent from manuscript: {key}")

    if architecture_map.get("schema") != "antidote.architecture-evidence-map/v1":
        errors.append(
            "architecture evidence map schema must be "
            "antidote.architecture-evidence-map/v1"
        )
    required_clusters = architecture_map.get("required_clusters")
    if not isinstance(required_clusters, list) or not required_clusters:
        errors.append("architecture evidence map must define required clusters")
        required_clusters = []
    map_entries = architecture_map.get("entries")
    if not isinstance(map_entries, list) or not map_entries:
        errors.append("architecture evidence map must contain entries")
        map_entries = []

    map_source_ids: list[str] = []
    covered_clusters: set[str] = set()
    catalog_id_set = set(ids)
    for entry in map_entries:
        source_id = entry.get("source_id")
        if not isinstance(source_id, str):
            errors.append("architecture map entry lacks source_id")
            continue
        map_source_ids.append(source_id)
        if source_id not in catalog_id_set:
            errors.append(f"architecture map references unknown source: {source_id}")
        cluster = entry.get("cluster")
        if cluster not in required_clusters:
            errors.append(f"{source_id}: architecture map has invalid cluster {cluster!r}")
        else:
            covered_clusters.add(cluster)
        if entry.get("evidence_role") not in ARCHITECTURE_EVIDENCE_ROLES:
            errors.append(
                f"{source_id}: invalid architecture evidence role "
                f"{entry.get('evidence_role')!r}"
            )
        if entry.get("support_direction") not in SUPPORT_DIRECTIONS:
            errors.append(
                f"{source_id}: invalid support direction "
                f"{entry.get('support_direction')!r}"
            )
        for field in ("subsystem", "bounded_claim", "does_not_establish"):
            if not entry.get(field):
                errors.append(f"{source_id}: architecture map missing {field}")

    for source_id, count in Counter(map_source_ids).items():
        if count > 1:
            errors.append(f"duplicate architecture map source: {source_id}")
    for cluster in sorted(set(required_clusters) - covered_clusters):
        errors.append(f"architecture map lacks required cluster: {cluster}")

    if comparator_matrix.get("schema") != "antidote.comparator-novelty-matrix/v1":
        errors.append(
            "comparator matrix schema must be "
            "antidote.comparator-novelty-matrix/v1"
        )
    if set(comparator_matrix.get("dimension_definitions", {})) != COMPARATOR_DIMENSIONS:
        errors.append("comparator matrix must define the exact governed dimensions")
    absence_rule = comparator_matrix.get("search_boundary", {}).get("absence_rule", "")
    if "does not exist" not in absence_rule:
        errors.append(
            "comparator matrix must distinguish not-reported from nonexistence"
        )

    comparators = comparator_matrix.get("comparators")
    if not isinstance(comparators, list) or len(comparators) < 8:
        errors.append("comparator matrix must contain at least eight systems")
        comparators = []
    comparator_source_ids: list[str] = []
    direct_comparators = 0
    for comparator in comparators:
        source_id = comparator.get("source_id")
        if not isinstance(source_id, str):
            errors.append("comparator row lacks source_id")
            continue
        comparator_source_ids.append(source_id)
        if source_id not in catalog_id_set:
            errors.append(f"comparator matrix references unknown source: {source_id}")
        if comparator.get("relationship") not in COMPARATOR_RELATIONSHIPS:
            errors.append(
                f"{source_id}: invalid comparator relationship "
                f"{comparator.get('relationship')!r}"
            )
        if comparator.get("relationship") == "direct":
            direct_comparators += 1
        if comparator.get("evidence_grade") not in COMPARATOR_EVIDENCE_GRADES:
            errors.append(
                f"{source_id}: invalid comparator evidence grade "
                f"{comparator.get('evidence_grade')!r}"
            )
        for field in (
            "system",
            "version_reviewed",
            "peer_review_status",
            "overlap",
            "limitations",
        ):
            if not comparator.get(field):
                errors.append(f"{source_id}: comparator row missing {field}")
        dimensions = comparator.get("dimensions")
        if not isinstance(dimensions, dict) or set(dimensions) != COMPARATOR_DIMENSIONS:
            errors.append(f"{source_id}: comparator dimensions are incomplete")
            continue
        for dimension, cell in dimensions.items():
            if not isinstance(cell, dict):
                errors.append(f"{source_id}: {dimension} must be an object")
                continue
            if cell.get("status") not in COMPARATOR_DIMENSION_STATUSES:
                errors.append(
                    f"{source_id}: {dimension} has invalid status "
                    f"{cell.get('status')!r}"
                )
            if not cell.get("detail"):
                errors.append(f"{source_id}: {dimension} lacks bounded detail")

    for source_id, count in Counter(comparator_source_ids).items():
        if count > 1:
            errors.append(f"duplicate comparator source: {source_id}")
    if direct_comparators < 5:
        errors.append("comparator matrix must preserve at least five direct systems")
    if "mindmelody-2605.01235" not in comparator_source_ids:
        errors.append("comparator matrix must include the MindMelody dossier")

    synthesis_ids: list[str] = []
    for synthesis in comparator_matrix.get("evidence_syntheses", []):
        source_id = synthesis.get("source_id")
        if not isinstance(source_id, str) or source_id not in catalog_id_set:
            errors.append(f"invalid comparator synthesis source: {source_id!r}")
            continue
        synthesis_ids.append(source_id)
        for field in ("version_reviewed", "evidence_grade", "bounded_result"):
            if not synthesis.get(field):
                errors.append(f"{source_id}: comparator synthesis missing {field}")
    if len(synthesis_ids) < 2:
        errors.append("comparator matrix must preserve at least two syntheses")

    novelty_decisions = comparator_matrix.get("novelty_decisions")
    if not isinstance(novelty_decisions, list) or not novelty_decisions:
        errors.append("comparator matrix must contain novelty decisions")
        novelty_decisions = []
    decision_ids: list[str] = []
    decision_statuses: set[str] = set()
    for decision in novelty_decisions:
        decision_id = decision.get("claim_id")
        if not isinstance(decision_id, str):
            errors.append("novelty decision lacks claim_id")
            continue
        decision_ids.append(decision_id)
        status = decision.get("status")
        if status not in NOVELTY_DECISIONS:
            errors.append(f"{decision_id}: invalid novelty status {status!r}")
        else:
            decision_statuses.add(status)
        for field in ("claim", "source_ids", "bounded_result"):
            if not decision.get(field):
                errors.append(f"{decision_id}: novelty decision missing {field}")
        for source_id in decision.get("source_ids", []):
            if source_id not in catalog_id_set:
                errors.append(
                    f"{decision_id}: novelty decision references unknown source "
                    f"{source_id}"
                )
    for decision_id, count in Counter(decision_ids).items():
        if count > 1:
            errors.append(f"duplicate novelty decision: {decision_id}")
    for status in sorted(NOVELTY_DECISIONS - decision_statuses):
        errors.append(f"comparator matrix lacks {status} novelty decision")

    return errors


def main() -> int:
    """Validate the source corpus and print one stable summary."""
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    entries = bibliography_entries(BIBLIOGRAPHY_PATH.read_text(encoding="utf-8"))
    citations = manuscript_citations()
    architecture_map = json.loads(
        ARCHITECTURE_MAP_PATH.read_text(encoding="utf-8")
    )
    comparator_matrix = json.loads(
        COMPARATOR_MATRIX_PATH.read_text(encoding="utf-8")
    )
    print(
        "PASS source governance: "
        f"{len(catalog['sources'])} catalog sources, "
        f"{len(entries)} verified bibliography entries, "
        f"{len(citations)} manuscript citation, "
        f"{len(architecture_map['entries'])} architecture mappings, "
        f"{len(comparator_matrix['comparators'])} comparator rows, "
        f"{len(comparator_matrix['novelty_decisions'])} novelty decisions."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
