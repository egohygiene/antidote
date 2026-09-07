# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate the scientific figure and table governance contract."""

from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "check_visuals.py"
SPEC = importlib.util.spec_from_file_location("check_visuals", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
VISUALS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VISUALS)


class VisualContractTests(unittest.TestCase):
    """Keep visual inventory, assets, captions, and manuscript references aligned."""

    def fixture(self, temporary: str) -> Path:
        """Copy only the source trees required by visual validation."""
        root = Path(temporary)
        shutil.copytree(ROOT / "paper", root / "paper")
        ledger = root / "research" / "notes"
        ledger.mkdir(parents=True)
        shutil.copy2(ROOT / "research" / "notes" / "CLAIM_LEDGER.md", ledger)
        shutil.copy2(ROOT / "EPISTEMOLOGY.md", root / "EPISTEMOLOGY.md")
        shutil.copytree(ROOT / "experiments", root / "experiments")
        return root

    def manifest(self, root: Path) -> dict:
        """Load one fixture manifest."""
        return json.loads(
            (root / "paper" / "visuals" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )

    def write_manifest(self, root: Path, manifest: dict) -> None:
        """Write one changed fixture manifest and its synchronized registry."""
        path = root / "paper" / "visuals" / "manifest.json"
        path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        registry = root / "paper" / "visuals" / "captions.tex"
        registry.write_text(VISUALS.registry_text(manifest), encoding="utf-8")

    def test_canonical_visual_system_is_complete(self) -> None:
        """Every promised manuscript visual must be allocated and valid."""
        result = VISUALS.validate_visual_system(ROOT)
        self.assertEqual(result["errors"], [])
        manifest = result["manifest"]
        self.assertEqual(len(manifest["visuals"]), 19)
        self.assertEqual(
            {visual["id"] for visual in result["active"]},
            {
                visual["id"]
                for visual in manifest["visuals"]
                if visual["status"] == "active"
            },
        )
        states = {visual["id"]: visual["state"] for visual in result["active"]}
        self.assertEqual(len(states), 17)
        self.assertEqual(set(states.values()), {"final"})
        retired = {
            visual["id"]
            for visual in manifest["visuals"]
            if visual["status"] == "retired"
        }
        self.assertEqual(retired, {"ANT-FIG-010", "ANT-FIG-011"})
        self.assertEqual(
            {visual["kind"] for visual in manifest["visuals"]},
            {"figure", "table"},
        )

    def test_duplicate_labels_fail_closed(self) -> None:
        """A label cannot identify two visual records."""
        with tempfile.TemporaryDirectory(prefix="antidote-visual-") as temporary:
            root = self.fixture(temporary)
            manifest = self.manifest(root)
            manifest["visuals"][1]["label"] = manifest["visuals"][0]["label"]
            self.write_manifest(root, manifest)
            result = VISUALS.validate_visual_system(root)
            self.assertTrue(
                any("duplicate visual label" in error for error in result["errors"])
            )

    def test_active_asset_and_reference_are_required(self) -> None:
        """An active visual cannot disappear from source or manuscript."""
        with tempfile.TemporaryDirectory(prefix="antidote-visual-") as temporary:
            root = self.fixture(temporary)
            asset = root / "paper" / "figures" / "semantic-acoustic-response-loop.svg"
            asset.rename(asset.with_suffix(".missing"))
            result = VISUALS.validate_visual_system(root)
            self.assertTrue(any("active asset is missing" in error for error in result["errors"]))

        with tempfile.TemporaryDirectory(prefix="antidote-visual-") as temporary:
            root = self.fixture(temporary)
            introduction = root / "paper" / "sections" / "01-introduction.tex"
            introduction.write_text(
                introduction.read_text(encoding="utf-8").replace(
                    "\\AntidoteFigure{semantic-acoustic-response-loop}", ""
                ),
                encoding="utf-8",
            )
            result = VISUALS.validate_visual_system(root)
            self.assertTrue(
                any("referenced exactly once" in error for error in result["errors"])
            )

    def test_orphaned_caption_registry_is_rejected(self) -> None:
        """The centralized LaTeX projection cannot drift from the manifest."""
        with tempfile.TemporaryDirectory(prefix="antidote-visual-") as temporary:
            root = self.fixture(temporary)
            registry = root / "paper" / "visuals" / "captions.tex"
            registry.write_text(
                registry.read_text(encoding="utf-8") + "% orphan\n",
                encoding="utf-8",
            )
            result = VISUALS.validate_visual_system(root)
            self.assertTrue(any("orphaned" in error for error in result["errors"]))

    def test_generated_publication_figure_drift_is_rejected(self) -> None:
        """Generated final figures cannot silently diverge from their source."""
        with tempfile.TemporaryDirectory(prefix="antidote-visual-") as temporary:
            root = self.fixture(temporary)
            asset = root / "paper" / "figures" / "consent-scoped-context-projection.svg"
            asset.write_text(
                asset.read_text(encoding="utf-8").replace(
                    "CONSENT-SCOPED CONTEXT PROJECTION", "UNTRACKED CHANGE", 1
                ),
                encoding="utf-8",
            )
            result = VISUALS.validate_visual_system(root)
            self.assertIn(
                "generated publication figure is stale: "
                "paper/figures/consent-scoped-context-projection.svg",
                result["errors"],
            )

    def test_submission_ready_requires_every_active_visual_to_be_final(self) -> None:
        """Canonical finals pass while a regressed active state fails closed."""
        result = VISUALS.validate_visual_system(ROOT, paper_stage="submission-ready")
        self.assertEqual(result["errors"], [])

        with tempfile.TemporaryDirectory(prefix="antidote-visual-") as temporary:
            root = self.fixture(temporary)
            manifest = self.manifest(root)
            active = next(
                visual for visual in manifest["visuals"] if visual["status"] == "active"
            )
            active["state"] = "draft"
            self.write_manifest(root, manifest)
            result = VISUALS.validate_visual_system(
                root, paper_stage="submission-ready"
            )
            self.assertTrue(
                any("must be final" in error for error in result["errors"]),
                result["errors"],
            )

    def test_equation_map_enumerates_the_complete_registry(self) -> None:
        """Every governed equation ID must remain machine-visible in the map."""
        asset = ROOT / "paper" / "figures" / "moment-journey-equation-map.svg"
        root = ET.parse(asset).getroot()
        observed = {
            equation_id
            for element in root.iter()
            for equation_id in element.attrib.get("data-equations", "").split()
        }
        self.assertEqual(
            observed,
            {f"ANT-EQ-{number:03d}" for number in range(1, 17)},
        )

    def test_protocol_timeline_preserves_order_and_authority_boundary(self) -> None:
        """The visual must project all eight stages without implying collection."""
        asset = ROOT / "paper" / "figures" / "feasibility-protocol-timeline.svg"
        root = ET.parse(asset).getroot()
        stage_orders = [
            int(element.attrib["data-stage-order"])
            for element in root.iter()
            if "data-stage-order" in element.attrib
        ]
        self.assertEqual(stage_orders, list(range(1, 9)))
        content = " ".join("".join(root.itertext()).split()).casefold()
        self.assertIn("ant-prot-feas-001 v1.1.0", content)
        self.assertIn("collection authority = false", content)
        self.assertIn("next exposure ≥ 48 hours", content)

    def test_deterministic_svg_requires_accessible_closed_content(self) -> None:
        """Deterministic figures cannot depend on inaccessible or remote content."""
        with tempfile.TemporaryDirectory(prefix="antidote-visual-") as temporary:
            root = self.fixture(temporary)
            asset = root / "paper" / "figures" / "holistic-two-rate-architecture.svg"
            svg = asset.read_text(encoding="utf-8")
            svg = svg.replace('viewBox="0 0 1800 1200"', 'viewBox="0 0 900 600"')
            svg = svg.replace('role="img"', 'role="presentation"')
            svg = svg.replace(
                "</svg>", '<image href="https://example.invalid/asset.png"/></svg>'
            )
            asset.write_text(svg, encoding="utf-8")
            result = VISUALS.validate_visual_system(root)
            self.assertTrue(any("viewBox must match" in error for error in result["errors"]))
            self.assertTrue(any("root role must be img" in error for error in result["errors"]))
            self.assertTrue(
                any(
                    "prohibited elements: image" in error
                    for error in result["errors"]
                )
            )
            self.assertTrue(any("external reference" in error for error in result["errors"]))

    def test_two_rate_architecture_preserves_governed_topology(self) -> None:
        """The release diagram must retain its authority and timing boundaries."""
        asset = ROOT / "paper" / "figures" / "holistic-two-rate-architecture.svg"
        root = ET.parse(asset).getroot()
        manifest = self.manifest(ROOT)
        visual = next(
            item for item in manifest["visuals"] if item["id"] == "ANT-FIG-002"
        )
        self.assertTrue(
            {
                "ANT-OBS-002",
                "ANT-CLM-003",
                "ANT-CLM-004",
                "ANT-CLM-005",
                "ANT-NEG-003",
                "ANT-NEG-004",
            }.issubset(visual["claim_ids"])
        )
        expected_nodes = {
            1: ("consented-context", "implemented"),
            2: ("state-belief", "proposed"),
            3: ("semantic-intent", "proposed"),
            4: ("journey-plan", "implemented"),
            5: ("human-approval", "implemented"),
            6: ("approved-generation-spec", "implemented"),
            7: ("model-adapter", "hybrid"),
            8: ("generate-verify", "hybrid"),
            9: ("future-audio-buffer", "proposed"),
            10: ("deterministic-renderer", "proposed"),
            11: ("listening-exposure", "hybrid"),
            12: ("response-record", "hybrid"),
        }
        node_elements = [
            element for element in root.iter() if "data-step" in element.attrib
        ]
        steps = [int(element.attrib["data-step"]) for element in node_elements]
        self.assertEqual(len(node_elements), len(expected_nodes))
        self.assertEqual(len(steps), len(set(steps)))
        observed_nodes = {
            int(element.attrib["data-step"]): (
                element.attrib.get("data-node"),
                element.attrib.get("data-status"),
            )
            for element in node_elements
        }
        self.assertEqual(observed_nodes, expected_nodes)
        for element in root.iter():
            if element.attrib.get("data-status") != "hybrid":
                continue
            self.assertTrue(
                any(
                    child.attrib.get("data-role") == "hybrid-divider"
                    for child in element.iter()
                ),
                element.attrib.get("data-node"),
            )

        boundaries = {
            element.attrib["data-boundary"]
            for element in root.iter()
            if "data-boundary" in element.attrib
        }
        self.assertTrue(
            {
                "human-authority",
                "no-automatic-learning",
                "variable-latency-generation",
                "fast-audio-loop",
                "response-record-zone",
                "worker-capability",
                "provenance",
                "safety-paths",
            }.issubset(boundaries)
        )

        directed_flows = [
            element
            for element in root.iter()
            if element.tag.rsplit("}", 1)[-1] == "path"
            and "data-flow" in element.attrib
        ]
        expected_flows = {
            "response-to-future-proposal",
            "approval-to-model-adapter",
            "cancel-to-generation",
            "fallback-to-renderer",
            "stop-to-exposure",
            "context-to-belief",
            "belief-to-intent",
            "intent-to-plan",
            "plan-to-approval",
            "adapter-to-generate",
            "generate-to-buffer",
            "buffer-to-renderer",
            "renderer-to-exposure",
            "exposure-to-response",
        }
        self.assertEqual(len(directed_flows), len(expected_flows))
        self.assertEqual(
            {flow.attrib["data-flow"] for flow in directed_flows},
            expected_flows,
        )
        for flow in directed_flows:
            self.assertIn("marker-end", flow.attrib)
            self.assertNotIn("marker-start", flow.attrib)

        identified_elements = [
            element for element in root.iter() if "id" in element.attrib
        ]
        element_ids = [element.attrib["id"] for element in identified_elements]
        self.assertEqual(len(element_ids), len(set(element_ids)))
        elements_by_id = {
            element.attrib["id"]: element
            for element in identified_elements
        }
        approval = elements_by_id["approved-generation-spec"]
        self.assertEqual(approval.attrib.get("data-flow"), "approval-to-model-adapter")
        self.assertEqual(approval.attrib.get("data-status"), "implemented")
        future = elements_by_id["future-proposal-only"]
        self.assertEqual(future.attrib.get("data-flow"), "response-to-future-proposal")
        self.assertEqual(future.attrib.get("data-status"), "proposed")

    def test_generated_editorial_mode_requires_prompt_provenance(self) -> None:
        """Generated artwork may not bypass its prompt record."""
        with tempfile.TemporaryDirectory(prefix="antidote-visual-") as temporary:
            root = self.fixture(temporary)
            manifest = self.manifest(root)
            visual = manifest["visuals"][3]
            visual["source"]["mode"] = "generated-editorial"
            visual["source"]["format"] = "png"
            visual["filename"] = visual["filename"].replace(".svg", ".png")
            self.write_manifest(root, manifest)
            result = VISUALS.validate_visual_system(root)
            self.assertTrue(
                any("requires a prompt record" in error for error in result["errors"])
            )


if __name__ == "__main__":
    unittest.main()
