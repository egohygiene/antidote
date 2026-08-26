# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Tests for Antidote's product-owned Pages staging contract."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPOSITORY_ROOT / "scripts" / "stage_pages.py"
SPEC = importlib.util.spec_from_file_location("stage_pages", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
STAGE_PAGES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STAGE_PAGES)


class StagePagesTests(unittest.TestCase):
    """Exercise default routes, custom domains, and safety validation."""

    def create_fixture(self, root: Path) -> Path:
        """Create the smallest valid governed build and site source."""
        (root / "docs").mkdir(parents=True)
        (root / "docs" / "index.html").write_text(
            '<link rel="canonical" href="https://egohygiene.github.io/antidote/">'
            '<a href="./paper/">Read</a><a href="./antidote.pdf">PDF</a>',
            encoding="utf-8",
        )
        (root / "docs" / "site.webmanifest").write_text("{}\n", encoding="utf-8")
        (root / "beacon-project.toml").write_text(
            """
[paper]
id = "antidote"
title = "Antidote"
version = "0.1.0"
stage = "draft"

[provenance]
source_repository = "https://github.com/egohygiene/antidote"
source_date_epoch = 1787724808

[publication]
pages_url = "https://egohygiene.github.io/antidote/"
""".strip()
            + "\n",
            encoding="utf-8",
        )
        build = root / "build" / "egohygiene"
        (build / "web").mkdir(parents=True)
        (build / "arxiv").mkdir()
        (build / "paper.pdf").write_bytes(b"%PDF-fixture")
        (build / "web" / "index.html").write_text(
            "<main>Paper</main>", encoding="utf-8"
        )
        (build / "arxiv" / "antidote-0.1.0.tar.gz").write_bytes(b"archive")
        (build / "provenance.json").write_text(
            json.dumps({"source_revision": "a" * 40}) + "\n",
            encoding="utf-8",
        )
        return build

    def test_stages_default_github_pages_routes(self) -> None:
        """The default site uses the repository's GitHub Pages base URL."""
        with tempfile.TemporaryDirectory(prefix="antidote-pages-") as temporary:
            root = Path(temporary)
            build = self.create_fixture(root)
            output = root / "_site"
            manifest = STAGE_PAGES.stage_site(root, build, output)

            self.assertEqual(
                manifest["pages_url"], "https://egohygiene.github.io/antidote/"
            )
            self.assertFalse((output / "CNAME").exists())
            self.assertTrue((output / "paper" / "index.html").is_file())
            self.assertTrue((output / "antidote.pdf").is_file())
            self.assertTrue((output / "SHA256SUMS").is_file())

    def test_stages_valid_custom_domain(self) -> None:
        """A configured domain becomes the canonical published base URL."""
        with tempfile.TemporaryDirectory(prefix="antidote-domain-") as temporary:
            root = Path(temporary)
            build = self.create_fixture(root)
            output = root / "_site"
            manifest = STAGE_PAGES.stage_site(
                root,
                build,
                output,
                custom_domain="Antidote.EgoHygiene.io.",
            )

            self.assertEqual(manifest["pages_url"], "https://antidote.egohygiene.io/")
            self.assertEqual(manifest["custom_domain"], "antidote.egohygiene.io")
            self.assertFalse((output / "CNAME").exists())
            landing = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn("https://antidote.egohygiene.io/", landing)
            self.assertNotIn("https://egohygiene.github.io/antidote/", landing)

    def test_rejects_unsafe_custom_domain(self) -> None:
        """A URL or path cannot be injected into the CNAME artifact."""
        with self.assertRaisesRegex(ValueError, "invalid Pages custom domain"):
            STAGE_PAGES.validate_custom_domain("https://antidote.example/path")


if __name__ == "__main__":
    unittest.main()
