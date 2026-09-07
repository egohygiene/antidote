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
        self.assertEqual(contract["version"], "0.4.0")
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

    def test_system_design_is_complete_and_status_bounded(self) -> None:
        """Issue #39 must retain its equations, authority, and implementation boundary."""
        system_design = (
            ROOT / "paper" / "sections" / "03-system-design.tex"
        ).read_text(encoding="utf-8")
        self.assertNotIn("\\AntidotePlaceholder", system_design)
        for label in (
            "sec:conceptual-conditional-model",
            "sec:design-record-chain",
            "sec:design-semantic-intent",
            "sec:design-two-rate-architecture",
            "sec:design-predictive-horizon",
            "sec:design-continuity",
            "sec:design-response-update",
            "sec:design-provenance-failures",
        ):
            self.assertIn(f"\\label{{{label}}}", system_design)
        for citation in (
            "nahumshani2018jitai",
            "garcia1989mpc",
            "kaelbling1998pomdp",
            "amershi2014interactive",
            "melechovsky2024mustango",
            "w3c2024webaudio",
            "moreau2013prov",
        ):
            self.assertIn(citation, system_design)
        self.assertIn("current person-authored value", system_design)
        self.assertIn("not implemented", system_design)
        self.assertIn("repository evidence, not human-outcome evidence", system_design)
        self.assertEqual(system_design.count("\\AntidoteFigure{"), 7)

    def test_methods_is_complete_and_bound_to_the_frozen_protocol(self) -> None:
        """Issue #40 must preserve one prospective non-collecting protocol."""
        methods = (ROOT / "paper" / "sections" / "04-methods.tex").read_text(
            encoding="utf-8"
        )
        normalized_methods = re.sub(r"\s+", " ", methods)
        self.assertNotIn("\\AntidotePlaceholder", methods)
        for label in (
            "sec:methods-feasibility-stages",
            "sec:methods-session-structure",
            "sec:methods-technical-verification",
            "sec:methods-within-person-measures",
            "sec:methods-assignment-missingness",
            "sec:methods-analysis-plan",
            "sec:methods-protocol-freeze",
        ):
            self.assertIn(f"\\label{{{label}}}", methods)
        for citation in (
            "porcino2020spent",
            "eldridge2016feasibility",
            "konigorski2022studyu",
            "shiffman2008ema",
            "betella2016slider",
        ):
            self.assertIn(citation, methods)
        for marker in (
            "ANT-PROT-FEAS-001",
            "frozen-design-protocol",
            "collection authority",
            "blocked-no-real-model",
            "blocked-no-collection-authority",
            "ANT-EQ-014",
            "ANT-EQ-015",
            "ANT-EQ-016",
        ):
            self.assertIn(marker, methods)
        self.assertIn("no formal human study has begun", normalized_methods)
        self.assertIn("technical controllability cannot", normalized_methods)

    def test_results_is_complete_without_invented_evidence(self) -> None:
        """Issue #41 must expose reportability without fabricating findings."""
        results = (ROOT / "paper" / "sections" / "05-results.tex").read_text(
            encoding="utf-8"
        )
        normalized_results = re.sub(r"\s+", " ", results)
        self.assertNotIn("\\AntidotePlaceholder", results)
        for label in (
            "sec:results-technical-verification",
            "sec:results-control-adherence",
            "sec:results-exposure-completeness",
            "sec:results-subjective-response",
            "sec:results-nonpositive-observations",
            "sec:results-optional-physiology",
            "sec:results-promotion-rule",
        ):
            self.assertIn(f"\\label{{{label}}}", results)
        for marker in (
            "ANT-REPORT-RESULTS-001",
            "ANT-PROT-FEAS-001",
            "ANT-REC-T0-001",
            "ANT-REC-T1-001",
            "blocked-no-collection-authority",
            "no formal human results",
            "never entered as a zero",
        ):
            self.assertIn(marker, normalized_results)
        self.assertIn("vohra2015cent", results)
        self.assertIn("eldridge2016feasibility", results)
        self.assertEqual(results.count("\\AntidoteTable{"), 3)
        self.assertEqual(results.count("\\AntidoteFigure{"), 0)
        self.assertEqual(normalized_results.count("governed visual slot"), 2)
        self.assertIn("retired and absent from the manuscript", normalized_results)

    def test_discussion_is_complete_and_evidence_proportional(self) -> None:
        """Issue #42 must interpret the design without promoting unavailable evidence."""
        discussion = (ROOT / "paper" / "sections" / "06-discussion.tex").read_text(
            encoding="utf-8"
        )
        normalized_discussion = re.sub(r"\s+", " ", discussion)
        self.assertNotIn("\\AntidotePlaceholder", discussion)
        for label in (
            "sec:discussion-design-contribution",
            "sec:discussion-negotiated-personalization",
            "sec:discussion-alternatives",
            "sec:discussion-future-program",
        ):
            self.assertIn(f"\\label{{{label}}}", discussion)
        for citation in (
            "janssen2012tune",
            "daly2016abcmi",
            "ehrlich2019closedloop",
            "agres2023affectmachine",
            "zhang2026mindmelody",
            "juslin2008emotional",
            "zentner2008emotions",
            "silverman2020complicated",
            "monroy2026minimalist",
            "sayal2025musicloop",
            "venkatesan2026mdt",
        ):
            self.assertIn(citation, discussion)
        for boundary in (
            "not a global first-system claim",
            "Semantic Intent Mixer",
            "predictive horizon",
            "semantic-plan distance",
            "measured acoustic-boundary distance",
            "waveform scheduling",
            "None of the three is implemented or validated end to end",
            "Five evidentiary distinctions must therefore remain non-interchangeable",
            "probability-space sculpting",
            "population affect-label pipeline",
            "static recommender",
            "Direct physiological conditioning",
            "one-shot generator",
            "mutation manifest",
            "seed policy",
            "output-rights review",
            "Unsupported controls would remain explicitly unsupported",
            "Optional real-time sensing",
            "genuinely continuous generation",
            "blocked-no-collection-authority",
            "Testing RQ3",
            "multi-participant work",
            "Neither efficacy nor mechanism is tested here",
            "intensity may be welcome, unwanted, mixed, or harmful",
        ):
            self.assertIn(boundary, normalized_discussion)
        ledger_rows = {}
        for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
            if line.startswith("| ANT-"):
                cells = [cell.strip() for cell in line.strip("|").split("|")]
                ledger_rows[cells[0]] = cells
        for claim_id in (
            "ANT-OBS-002",
            "ANT-CLM-002",
            "ANT-CLM-004",
            "ANT-CLM-006",
            "ANT-CLM-007",
        ):
            self.assertIn("Discussion", ledger_rows[claim_id][4], claim_id)

    def test_limitations_and_ethics_preserve_residual_risk_and_authority(self) -> None:
        """Issue #43 must audit controls without claiming mitigation or approval."""
        limitations = (
            ROOT / "paper" / "sections" / "07-limitations-and-ethics.tex"
        ).read_text(encoding="utf-8")
        appendix = (ROOT / "paper" / "sections" / "appendix.tex").read_text(
            encoding="utf-8"
        )
        normalized = re.sub(r"\s+", " ", limitations)
        self.assertNotIn("\\AntidotePlaceholder", limitations)
        self.assertNotIn("ANT-PH-APP-005", appendix)
        for label in (
            "sec:limitations-construct-validity",
            "sec:limitations-internal-validity",
            "sec:limitations-external-validity",
            "sec:limitations-system-failures",
            "sec:ethics-emotional-safety",
            "sec:ethics-consent-privacy",
            "sec:ethics-licensing-accessibility",
            "sec:ethics-review-gate",
        ):
            self.assertIn(f"\\label{{{label}}}", limitations)
        for citation in (
            "silverman2020complicated",
            "kleppmann2019localfirst",
            "moreau2013prov",
            "barnett2023ethical",
            "whoitu2019safelistening",
            "who2021ethics",
        ):
            self.assertIn(citation, limitations)
        for boundary in (
            "not as an effective mitigation",
            "not perfect security",
            "do not prove semantic correctness",
            "does not demonstrate comprehension",
            "None of those controls alone establish hearing safety",
            "blocked-no-collection-authority",
            "No formal participant study",
            "Publication of this design and protocol cannot activate it",
            "formal collection, recruitment, therapeutic use",
        ):
            self.assertIn(boundary, normalized)
        self.assertEqual(
            limitations.count("\\AntidoteTable{risk-mitigation-status}"), 1
        )

    def test_availability_and_contributions_match_public_artifact_boundaries(self) -> None:
        """Issue #44 must state exact access, license, role, and conflict status."""
        availability = (
            ROOT / "paper" / "sections" / "08-availability-and-contributions.tex"
        ).read_text(encoding="utf-8")
        appendix = (ROOT / "paper" / "sections" / "appendix.tex").read_text(
            encoding="utf-8"
        )
        normalized = re.sub(r"\s+", " ", availability)
        self.assertNotIn("\\AntidotePlaceholder", availability)
        self.assertNotIn("ANT-PH-APP-006", appendix)
        for label in (
            "sec:data-and-code-availability",
            "sec:availability-public-artifacts",
            "sec:availability-exclusions",
            "sec:acknowledgements",
            "sec:contributor-statement",
        ):
            self.assertIn(f"\\label{{{label}}}", availability)
        for marker in (
            "https://github.com/egohygiene/antidote",
            "https://antidote.egohygiene.io/paper/",
            "https://antidote.egohygiene.io/antidote.pdf",
            "https://antidote.egohygiene.io/downloads/",
            "publication.json",
            "site.json",
            "SHA256SUMS",
            "not an arXiv submission",
            "No DOI, arXiv identifier, archival release",
            "cross-platform or perpetual byte identity is therefore not claimed",
            "blocked-no-collection-authority",
            "root MIT license does not relicense the manuscript",
            "OpenAI ChatGPT and Codex",
            "exact regeneration of AI-assisted intermediate drafts is not claimed",
            "Writing---original draft",
            "self-study",
            "No external commercial sponsorship",
        ):
            self.assertIn(marker, normalized)
        for marker in (
            "Source and build identity",
            "Protocol and reporting identity",
            "Model and artifact identity",
            "Exposure and response identity",
            "Claim and exclusion audit",
            "No qualifying H1 exposure or response package exists",
        ):
            self.assertIn(marker, appendix)

    def test_author_roles_and_citation_metadata_are_synchronized(self) -> None:
        """The CRediT source and preferred paper citation must match metadata."""
        metadata = tomllib.loads(
            (ROOT / "beacon-project.toml").read_text(encoding="utf-8")
        )
        author = metadata["paper"]["authors"][0]
        self.assertEqual(author["name"], "Alan Szmyt")
        self.assertEqual(author["affiliation"], "Ego Hygiene")
        self.assertEqual(
            author["credit_roles"],
            [
                "Conceptualization",
                "Data curation",
                "Investigation",
                "Methodology",
                "Project administration",
                "Software",
                "Validation",
                "Visualization",
                "Writing - original draft",
                "Writing - review and editing",
            ],
        )
        availability = (
            ROOT / "paper" / "sections" / "08-availability-and-contributions.tex"
        ).read_text(encoding="utf-8")
        self.assertIn(f'version {metadata["paper"]["version"]}', availability)
        for role in author["credit_roles"]:
            rendered_role = role.replace(" - ", "---")
            self.assertIn(rendered_role, availability)
        citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
        self.assertIn('title: "Antidote research software"', citation)
        self.assertIn("type: software", citation)
        self.assertIn("preferred-citation:", citation)
        self.assertIn(f'title: "{metadata["paper"]["title"]}"', citation)
        self.assertIn('affiliation: "Ego Hygiene"', citation)
        self.assertIn(f'version: "{metadata["paper"]["version"]}"', citation)
        self.assertIn('url: "https://antidote.egohygiene.io/paper/"', citation)
        self.assertNotIn("identifiers:", citation)
        self.assertNotIn("date-released:", citation)


if __name__ == "__main__":
    unittest.main()
