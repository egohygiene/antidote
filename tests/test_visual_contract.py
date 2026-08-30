# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate the scientific figure and table governance contract."""

from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
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
        self.assertEqual(len(manifest["visuals"]), 16)
        self.assertEqual(
            {visual["id"] for visual in result["active"]},
            {"ANT-FIG-001", "ANT-TBL-002"},
        )
        self.assertEqual(
            {visual["id"]: visual["state"] for visual in result["active"]},
            {
                "ANT-FIG-001": "placeholder",
                "ANT-TBL-002": "draft",
            },
        )
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

    def test_placeholder_cannot_enter_submission_ready_output(self) -> None:
        """Visible draft state must block stronger publication stages."""
        result = VISUALS.validate_visual_system(ROOT, paper_stage="submission-ready")
        self.assertTrue(
            any("must be final" in error for error in result["errors"]),
            result["errors"],
        )

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
