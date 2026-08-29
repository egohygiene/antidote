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
    print(
        "PASS source governance: "
        f"{len(catalog['sources'])} catalog sources, "
        f"{len(entries)} verified bibliography entries, "
        f"{len(citations)} manuscript citation."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
