# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate the frozen thesis, claim, terminology, and section contract."""

from __future__ import annotations

import json
import re
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "paper" / "manuscript-contract.json"
LEDGER_PATH = ROOT / "research" / "notes" / "CLAIM_LEDGER.md"
COORDINATOR_PATH = ROOT / "paper" / "sections" / "manuscript.tex"

EXPECTED_SECTION_PATHS = (
    "paper/paper.tex",
    "paper/sections/manuscript.tex",
    "paper/sections/01-introduction.tex",
    "paper/sections/02-related-work.tex",
    "paper/sections/03-system-design.tex",
    "paper/sections/04-methods.tex",
    "paper/sections/05-results.tex",
    "paper/sections/06-discussion.tex",
    "paper/sections/07-limitations-and-ethics.tex",
    "paper/sections/08-availability-and-contributions.tex",
    "paper/sections/09-conclusion.tex",
    "paper/sections/appendix.tex",
)
REQUIRED_TERMS = {
    "moment-specific personalization",
    "semantic intent",
    "journey",
    "semantic mixin",
    "conditioning state",
    "acoustic realization",
    "exposure",
    "response",
    "usefulness or harm",
    "aftereffect",
}
REQUIRED_LEDGER_CLASSES = {
    "source",
    "source synthesis",
    "hypothesis",
    "observation",
    "interpretation",
    "claim",
    "claim candidate",
    "rejected claim",
}


def load_contract() -> dict[str, object]:
    """Load the canonical manuscript contract."""
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def ledger_entries() -> dict[str, str]:
    """Return claim-ledger IDs paired with their declared evidence class."""
    entries: dict[str, str] = {}
    for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ANT-"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        entries[cells[0]] = cells[1].lower()
    return entries


class ManuscriptContractTests(unittest.TestCase):
    """Keep the issue #35 writing contract complete and synchronized."""

    def test_contract_identity_matches_publication_metadata(self) -> None:
        """The build metadata must expose the contract's working identity."""
        contract = load_contract()
        metadata = tomllib.loads(
            (ROOT / "beacon-project.toml").read_text(encoding="utf-8")
        )
        identity = contract["identity"]
        self.assertEqual(contract["schema"], "antidote.manuscript-contract/v1")
        self.assertEqual(contract["version"], "0.1.0")
        self.assertEqual(contract["status"], "frozen")
        self.assertEqual(identity["working_title"], metadata["paper"]["title"])
        self.assertEqual(identity["subtitle"], metadata["paper"]["subtitle"])

    def test_stage_ladder_is_explicit_and_ordered(self) -> None:
        """Every publication state must declare entry and claim boundaries."""
        stages = load_contract()["stage_ladder"]
        self.assertEqual(
            [stage["id"] for stage in stages],
            [
                "writing-preview",
                "design-protocol",
                "feasibility-revision",
                "reviewable-preprint",
            ],
        )
        self.assertEqual([stage["order"] for stage in stages], [1, 2, 3, 4])
        for stage in stages:
            self.assertTrue(stage["entry_gate"])
            self.assertTrue(stage["permitted_claims"])
            self.assertTrue(stage["prohibited_claims"])

    def test_claim_references_resolve_to_every_required_evidence_class(self) -> None:
        """Contribution claim IDs must resolve to a class-complete ledger."""
        contract = load_contract()
        entries = ledger_entries()
        self.assertEqual(set(entries.values()), REQUIRED_LEDGER_CLASSES)
        self.assertEqual(
            set(contract["claim_policy"]["required_classes"]),
            REQUIRED_LEDGER_CLASSES,
        )
        for contribution in contract["contributions"]:
            self.assertTrue(contribution["claim_ids"])
            for claim_id in contribution["claim_ids"]:
                self.assertIn(claim_id, entries, contribution["id"])
            self.assertTrue(contribution["permitted_verbs"])
            self.assertTrue(contribution["prohibited_inferences"])

    def test_frozen_terminology_resolves_to_the_domain_ontology(self) -> None:
        """Required manuscript terms must stay aligned with canonical concepts."""
        terminology = load_contract()["terminology"]
        self.assertEqual({item["term"] for item in terminology}, REQUIRED_TERMS)
        ontology = (ROOT / "ONTOLOGY.md").read_text(encoding="utf-8")
        for item in terminology:
            self.assertTrue(item["definition"], item["term"])
            self.assertTrue(item["prohibited_conflations"], item["term"])
            for concept in item["ontology_concepts"]:
                self.assertIn(concept, ontology, f"{item['term']}: {concept}")

    def test_every_canonical_source_has_a_complete_section_contract(self) -> None:
        """No manuscript source may be drafted without an evidence boundary."""
        sections = load_contract()["sections"]
        self.assertEqual(
            tuple(section["path"] for section in sections), EXPECTED_SECTION_PATHS
        )
        for section in sections:
            path = ROOT / section["path"]
            self.assertTrue(path.is_file(), section["path"])
            self.assertTrue(section["owner_issues"], section["path"])
            self.assertTrue(section["purpose"], section["path"])
            self.assertTrue(section["required_evidence"], section["path"])
            self.assertTrue(section["completion_criteria"], section["path"])
            self.assertTrue(section["prohibited"], section["path"])

    def test_coordinator_order_and_conclusion_decision_are_frozen(self) -> None:
        """The dedicated conclusion must remain the final numbered section."""
        contract = load_contract()
        coordinator = COORDINATOR_PATH.read_text(encoding="utf-8")
        inputs = re.findall(r"\\input\{([^}]+)\}", coordinator)
        expected_inputs = [
            path.removesuffix(".tex")
            for path in EXPECTED_SECTION_PATHS
            if re.search(r"/\d{2}-", path)
        ]
        self.assertEqual(inputs, expected_inputs)
        conclusion = contract["conclusion_decision"]
        self.assertEqual(conclusion["decision"], "dedicated numbered section")
        self.assertEqual(conclusion["path"], EXPECTED_SECTION_PATHS[-2])
        self.assertEqual(conclusion["owner_issue"], 47)

    def test_intro_uses_the_frozen_design_question(self) -> None:
        """The canonical introduction must not retain the pre-review question."""
        contract = load_contract()
        introduction = (
            ROOT / "paper" / "sections" / "01-introduction.tex"
        ).read_text(encoding="utf-8")
        normalized_introduction = re.sub(r"\s+", " ", introduction)
        self.assertIn(
            contract["research_questions"][0]["question"],
            normalized_introduction,
        )
        self.assertNotIn("better target future state transitions", introduction)

    def test_intro_is_complete_and_preserves_the_staged_questions(self) -> None:
        """Issue #37 prose must retain every evidence-gated research question."""
        contract = load_contract()
        introduction = (
            ROOT / "paper" / "sections" / "01-introduction.tex"
        ).read_text(encoding="utf-8")
        normalized_introduction = re.sub(r"\s+", " ", introduction)
        self.assertNotIn("\\AntidotePlaceholder", introduction)
        self.assertIn("\\label{sec:research-gap}", introduction)
        for research_question in contract["research_questions"]:
            self.assertIn(
                research_question["question"],
                normalized_introduction,
                research_question["id"],
            )

    def test_related_work_is_complete_and_evidence_structured(self) -> None:
        """Issue #38 must retain the promoted streams and bounded handoff."""
        related_work = (
            ROOT / "paper" / "sections" / "02-related-work.tex"
        ).read_text(encoding="utf-8")
        self.assertNotIn("\\AntidotePlaceholder", related_work)
        for label in (
            "sec:related-musical-response",
            "sec:related-personalization",
            "sec:related-closed-loop",
            "sec:related-controllable-generation",
            "sec:related-auditory-beats",
            "sec:related-setting",
            "sec:related-comparison",
            "sec:bounded-contribution",
        ):
            self.assertIn(f"\\label{{{label}}}", related_work)
        for citation in (
            "juslin2008emotional",
            "zentner2008emotions",
            "monroy2026minimalist",
            "ingendoh2023binaural",
            "kaelen2018hidden",
            "rowe2026psychedelic",
            "melechovsky2024mustango",
            "nahumshani2018jitai",
        ):
            self.assertIn(citation, related_work)
        self.assertEqual(
            related_work.count(
                "\\AntidoteTable{research-landscape-comparator}"
            ),
            1,
        )
        self.assertIn("bounded review did not identify", related_work)
        self.assertIn("not a global novelty", related_work)


if __name__ == "__main__":
    unittest.main()
