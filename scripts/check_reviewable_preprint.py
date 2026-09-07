#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate the durable review record required by a strong paper stage."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]
REVIEW_PATH = Path("paper/reviews/reviewable-preprint-v0.1.0.json")
REQUIRED_DEPENDENCIES = {
    *(f"egohygiene/antidote#{number}" for number in range(32, 48)),
    "egohygiene/antidote#77",
    "egohygiene/antidote#82",
}
REQUIRED_AUDIT_AREAS = {
    "conceptual-coherence",
    "literature-and-novelty",
    "claim-and-citation-traceability",
    "system-and-equation-integrity",
    "methods-and-results-boundary",
    "ethics-safety-and-privacy",
    "metadata-contributors-and-licensing",
    "visual-and-accessibility",
    "reproducibility-and-packaging",
    "live-publication",
    "independent-review-boundary",
}
ALLOWED_DISPOSITIONS = {"resolved", "accepted-limitation", "deferred-gated"}
SHA256 = re.compile(r"[0-9a-f]{64}")
GIT_SHA = re.compile(r"[0-9a-f]{40}")


def load_toml(path: Path) -> dict:
    """Load one TOML document."""
    with path.open("rb") as stream:
        return tomllib.load(stream)


def safe_repository_path(root: Path, value: object) -> Path | None:
    """Resolve a repository-relative evidence path without permitting escape."""
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        return None
    candidate = (root / value).resolve()
    if root.resolve() not in candidate.parents:
        return None
    return candidate


def validate_reviewable_preprint(root: Path = ROOT) -> list[str]:
    """Return deterministic validation errors for the reviewable-preprint gate."""
    errors: list[str] = []
    config_path = root / "beacon-project.toml"
    review_path = root / REVIEW_PATH
    try:
        config = load_toml(config_path)
    except (OSError, tomllib.TOMLDecodeError) as error:
        return [f"review gate cannot load publication metadata: {error}"]

    paper = config.get("paper", {})
    stage = paper.get("stage")
    if stage not in {"submission-ready", "published"}:
        return errors
    if not review_path.is_file():
        return [f"{stage} publication is missing review record: {REVIEW_PATH}"]

    try:
        review = json.loads(review_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"review record cannot be loaded: {error}"]

    if review.get("schema") != "antidote.reviewable-preprint-review/v1":
        errors.append("review record schema must be antidote.reviewable-preprint-review/v1")
    if review.get("version") != paper.get("version"):
        errors.append("review record version must match paper version")
    if review.get("gate_issue") != "egohygiene/antidote#48":
        errors.append("review record must identify gate issue #48")
    if review.get("decision") != "reviewable-design-protocol-preprint":
        errors.append("review decision must remain reviewable-design-protocol-preprint")
    if review.get("publication_stage") != stage:
        errors.append("review record and publication metadata stages disagree")

    baseline = review.get("reviewed_baseline", {})
    if not GIT_SHA.fullmatch(str(baseline.get("source_revision", ""))):
        errors.append("reviewed baseline must name a full Git revision")
    if baseline.get("canonical_url") != config.get("publication", {}).get("pages_url"):
        errors.append("reviewed baseline canonical URL does not match publication metadata")
    for key in ("html_sha256", "pdf_sha256"):
        if not SHA256.fullmatch(str(baseline.get(key, ""))):
            errors.append(f"reviewed baseline has an invalid {key}")
    if baseline.get("verification") != "passed-exact-revision-and-hashes":
        errors.append("reviewed baseline must record exact-revision and hash verification")

    dependencies = review.get("dependencies", [])
    dependency_ids = {
        item.get("issue") for item in dependencies if isinstance(item, dict)
    }
    if dependency_ids != REQUIRED_DEPENDENCIES:
        errors.append("review dependency inventory does not match the complete writing gate")
    for item in dependencies:
        if not isinstance(item, dict):
            errors.append("review dependency entry must be an object")
            continue
        if item.get("status") != "closed":
            errors.append(f"review dependency is not closed: {item.get('issue')}")
        evidence = item.get("evidence")
        target = safe_repository_path(root, evidence)
        if target is None or not target.exists():
            errors.append(
                f"review dependency has missing or unsafe evidence: {item.get('issue')}"
            )

    dispositions = review.get("audit_dispositions", [])
    areas = {
        item.get("area") for item in dispositions if isinstance(item, dict)
    }
    if areas != REQUIRED_AUDIT_AREAS:
        errors.append("review record does not cover every required audit area")
    for item in dispositions:
        if not isinstance(item, dict):
            errors.append("audit disposition must be an object")
            continue
        if item.get("disposition") not in ALLOWED_DISPOSITIONS:
            errors.append(f"invalid review disposition: {item.get('area')}")
        if not item.get("finding") or not item.get("rationale"):
            errors.append(f"review disposition is incomplete: {item.get('area')}")
        evidence = item.get("evidence", [])
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"review disposition has no evidence: {item.get('area')}")
        else:
            for value in evidence:
                target = safe_repository_path(root, value)
                if target is None or not target.exists():
                    errors.append(
                        f"review disposition has missing or unsafe evidence: {item.get('area')}"
                    )

    spot_checks = review.get("primary_source_spot_checks", [])
    if not isinstance(spot_checks, list) or len(spot_checks) < 10:
        errors.append("review record must retain at least ten primary-source spot checks")
    else:
        identifiers: set[str] = set()
        for item in spot_checks:
            if not isinstance(item, dict):
                errors.append("primary-source spot check must be an object")
                continue
            identifier = str(item.get("id", ""))
            if not identifier or identifier in identifiers:
                errors.append(f"duplicate or empty source spot-check ID: {identifier}")
            identifiers.add(identifier)
            source_record = safe_repository_path(root, item.get("source_record"))
            if (
                source_record is None
                or not source_record.is_file()
                or source_record.parent != (root / "research" / "sources").resolve()
            ):
                errors.append(f"invalid source record for spot check: {identifier}")
            if not str(item.get("primary_url", "")).startswith(("http://", "https://")):
                errors.append(f"spot check lacks a primary URL: {identifier}")
            if item.get("disposition") not in {"verified", "verified-with-qualification"}:
                errors.append(f"invalid source spot-check disposition: {identifier}")
            if not item.get("checked_on") or not item.get("verified_points"):
                errors.append(f"source spot check is incomplete: {identifier}")

    deferrals = review.get("justified_deferrals", [])
    h1_deferral = next(
        (
            item
            for item in deferrals
            if isinstance(item, dict) and item.get("issue") == "egohygiene/antidote#84"
        ),
        None,
    )
    if h1_deferral is None or h1_deferral.get("disposition") != "deferred-gated":
        errors.append("review record must retain the gated issue #84 deferral")
    elif h1_deferral.get("collection_authority") is not False:
        errors.append("issue #84 deferral must keep collection authority false")

    independence = review.get("review_independence", {})
    if independence.get("external_peer_review") is not False:
        errors.append("review record must not imply external peer review")
    if independence.get("mode") != "separate-pass-tool-assisted-review":
        errors.append("review mode must identify the separate tool-assisted pass")
    if len(independence.get("lenses", [])) < 4:
        errors.append("review record must retain multiple independent review lenses")

    browser_audit = review.get("browser_audit", {})
    launch_surface = browser_audit.get("launch_surface", {})
    paper_surface = browser_audit.get("paper_surface", {})
    candidate_surface = browser_audit.get("candidate_static_surface", {})
    if launch_surface.get("status") != "readable-with-deferred-hydration-defect":
        errors.append("browser audit must retain the inherited hydration defect")
    if launch_surface.get("tracking_issue") != "egohygiene/antidote#89":
        errors.append("browser hydration defect must remain assigned to issue #89")
    if paper_surface.get("status") != "passed":
        errors.append("browser audit must record a passing paper surface")
    if paper_surface.get("horizontal_overflow") is not False:
        errors.append("browser audit must reject horizontal paper overflow")
    if paper_surface.get("rendered_figures") != paper_surface.get(
        "figures_with_alt_text"
    ):
        errors.append("browser audit must retain alt text for every rendered figure")
    if candidate_surface.get("status") != "passed":
        errors.append("candidate static-surface validation must pass")

    post_merge = review.get("post_merge_verification", {})
    if post_merge.get("status") != "required-after-merge":
        errors.append("current revision must retain the post-merge live verification gate")
    workflow = safe_repository_path(root, post_merge.get("enforced_by"))
    if workflow is None or not workflow.is_file():
        errors.append("post-merge verification workflow is missing")
    if post_merge.get("expected_revision_source") != "github.sha":
        errors.append("post-merge verification must bind to github.sha")

    prohibited = review.get("claims_not_authorized", [])
    for boundary in (
        "peer reviewed",
        "clinically validated",
        "therapeutically effective",
        "neurological mechanism established",
        "human feasibility completed",
    ):
        if boundary not in prohibited:
            errors.append(f"review record omits prohibited claim boundary: {boundary}")

    return errors


def main() -> int:
    """Validate a project review record from the command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=str(ROOT))
    arguments = parser.parse_args()
    errors = validate_reviewable_preprint(Path(arguments.project).resolve())
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print("PASS reviewable design/protocol preprint gate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
