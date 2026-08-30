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

CANONICAL_URL = "https://antidote.egohygiene.io/"


def page_template(route: str, links: str, asset_prefix: str) -> str:
    """Return one minimal valid public-page template for a fixture."""
    canonical = f"{{{{SITE_BASE_URL}}}}{route}"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta property="og:url" content="{canonical}">
  <link rel="canonical" href="{canonical}">
  <link rel="stylesheet" href="{asset_prefix}assets/site.css">
  <title>Antidote fixture</title>
  <script type="application/ld+json">{{"url": "{canonical}"}}</script>
</head>
<body>
  <a class="skip-link" href="#content">Skip</a>
  <main id="content"><h1>Antidote fixture</h1>{links}</main>
</body>
</html>
"""


class StagePagesTests(unittest.TestCase):
    """Exercise site routes, catalog states, domains, and safety validation."""

    def create_fixture(self, root: Path) -> Path:
        """Create the smallest valid governed build and site source."""
        (root / "docs" / "assets").mkdir(parents=True)
        (root / "docs" / "magazine").mkdir()
        (root / "docs" / "downloads").mkdir()
        (root / "docs" / "assets" / "site.css").write_text(
            "a:focus-visible { outline: solid; }\n"
            "@media (max-width: 600px) { body { color: white; } }\n"
            "@media (prefers-reduced-motion: reduce) { * { animation: none; } }\n",
            encoding="utf-8",
        )
        (root / "docs" / "assets" / "SHA256SUMS").write_text(
            "nested fixture asset\n", encoding="utf-8"
        )
        (root / "docs" / "index.html").write_text(
            page_template(
                "",
                '<a href="./paper/">Paper</a>'
                '<a href="./magazine/">Magazine</a>'
                '<a href="./downloads/">Downloads</a>'
                '<a href="./antidote.pdf">PDF</a>',
                "./",
            ),
            encoding="utf-8",
        )
        (root / "docs" / "magazine" / "index.html").write_text(
            page_template("magazine/", '<a href="../">Home</a>', "../"),
            encoding="utf-8",
        )
        (root / "docs" / "downloads" / "index.html").write_text(
            page_template(
                "downloads/",
                '<a href="./{{SOURCE_ARCHIVE_NAME}}">Source</a>'
                '<a href="../publication.json">Manifest</a>'
                '<a href="../site.json">Catalog</a>'
                '<a href="../provenance.json">Provenance</a>'
                '<a href="../SHA256SUMS">Checksums</a>',
                "../",
            ),
            encoding="utf-8",
        )
        (root / "docs" / "site.webmanifest").write_text("{}\n", encoding="utf-8")
        suite = root / "site-suite"
        for route in ("docs", "architecture", "legal"):
            (suite / route).mkdir(parents=True, exist_ok=True)
        (suite / "assets").mkdir(parents=True)
        (suite / "index.html").write_text(
            page_template(
                "",
                '<a href="./docs/">Docs</a>'
                '<a href="./architecture/">Architecture</a>'
                '<a href="./legal/">Legal</a>'
                '<a href="./paper/">Paper</a>',
                "./",
            ),
            encoding="utf-8",
        )
        for route in ("docs", "architecture", "legal"):
            (suite / route / "index.html").write_text(
                page_template(f"{route}/", '<a href="../">Home</a>', "../"),
                encoding="utf-8",
            )
        (suite / "assets" / "suite.css").write_text(
            "/* exact-pinned suite fixture */\n", encoding="utf-8"
        )
        (suite / "site-suite.manifest.json").write_text("{}\n", encoding="utf-8")
        suite_inventory = [
            {
                "path": path.relative_to(suite).as_posix(),
                "sha256": STAGE_PAGES.sha256(path),
                "sizeBytes": path.stat().st_size,
            }
            for path in sorted(suite.rglob("*"))
            if path.is_file()
        ]
        (suite / "site-suite.provenance.json").write_text(
            json.dumps(
                {
                    "schema": "antidote.site-suite-provenance/v1",
                    "sourceRevision": "a" * 40,
                    "artifact": {"inventory": suite_inventory},
                }
            )
            + "\n",
            encoding="utf-8",
        )
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
pages_url = "https://antidote.egohygiene.io/"
pages_fallback_url = "https://egohygiene.github.io/antidote/"
pages_custom_domain = "antidote.egohygiene.io"
""".strip()
            + "\n",
            encoding="utf-8",
        )
        build = root / "build" / "egohygiene"
        (build / "web").mkdir(parents=True)
        (build / "arxiv").mkdir()
        (build / "paper.pdf").write_bytes(b"%PDF-fixture")
        (build / "web" / "index.html").write_text(
            page_template("paper/", '<a href="../">Home</a>', "../").replace(
                "{{SITE_BASE_URL}}", CANONICAL_URL
            ),
            encoding="utf-8",
        )
        (build / "arxiv" / "antidote-0.1.0.tar.gz").write_bytes(b"archive")
        (build / "provenance.json").write_text(
            json.dumps({"source_revision": "a" * 40}) + "\n",
            encoding="utf-8",
        )
        return build

    def test_stages_complete_custom_domain_hub(self) -> None:
        """The configured domain exposes the complete stable route contract."""
        with tempfile.TemporaryDirectory(prefix="antidote-pages-") as temporary:
            root = Path(temporary)
            build = self.create_fixture(root)
            output = root / "_site"
            manifest = STAGE_PAGES.stage_site(root, build, root / "site-suite", output)
            catalog = json.loads((output / "site.json").read_text(encoding="utf-8"))
            routes = {route["id"]: route["path"] for route in catalog["routes"]}

            self.assertEqual(manifest["pages_url"], CANONICAL_URL)
            self.assertEqual(manifest["custom_domain"], "antidote.egohygiene.io")
            self.assertEqual(routes, STAGE_PAGES.REQUIRED_ROUTES)
            self.assertTrue((output / "paper" / "index.html").is_file())
            self.assertTrue((output / "magazine" / "index.html").is_file())
            self.assertTrue((output / "downloads" / "index.html").is_file())
            self.assertTrue((output / "antidote.pdf").is_file())
            self.assertTrue((output / "docs" / "index.html").is_file())
            self.assertTrue((output / "architecture" / "index.html").is_file())
            self.assertTrue((output / "legal" / "index.html").is_file())
            self.assertTrue((output / "site-suite.provenance.json").is_file())
            self.assertEqual(
                (output / "paper" / "index.html").read_bytes(),
                (build / "web" / "index.html").read_bytes(),
            )
            self.assertEqual(
                (output / "antidote.pdf").read_bytes(),
                (build / "paper.pdf").read_bytes(),
            )
            self.assertTrue((output / STAGE_PAGES.OWNER_FILE).is_file())
            self.assertFalse((output / "CNAME").exists())
            checksum_text = (output / "SHA256SUMS").read_text(encoding="utf-8")
            self.assertIn("  assets/SHA256SUMS\n", checksum_text)
            paper_artifact = next(
                artifact
                for artifact in catalog["slots"][0]["artifacts"]
                if artifact["id"] == "accessible_web"
            )
            self.assertEqual(paper_artifact["url"], f"{CANONICAL_URL}paper/")

    def test_catalog_keeps_unpublished_magazine_empty(self) -> None:
        """A planned edition cannot imply publication artifacts or metadata."""
        with tempfile.TemporaryDirectory(prefix="antidote-planned-") as temporary:
            root = Path(temporary)
            output = root / "_site"
            STAGE_PAGES.stage_site(
                root, self.create_fixture(root), root / "site-suite", output
            )
            catalog = json.loads((output / "site.json").read_text(encoding="utf-8"))
            slots = {slot["id"]: slot for slot in catalog["slots"]}

            self.assertEqual(slots["paper"]["status"], "available")
            self.assertEqual(slots["magazine"]["status"], "planned")
            self.assertIsNone(slots["magazine"]["stage"])
            self.assertIsNone(slots["magazine"]["manifest_path"])
            self.assertEqual(slots["magazine"]["artifacts"], [])

    def test_normalizes_matching_custom_domain_argument(self) -> None:
        """An equivalent explicit domain remains compatible with configuration."""
        with tempfile.TemporaryDirectory(prefix="antidote-domain-") as temporary:
            root = Path(temporary)
            manifest = STAGE_PAGES.stage_site(
                root,
                self.create_fixture(root),
                root / "site-suite",
                root / "_site",
                custom_domain="Antidote.EgoHygiene.io.",
            )
            self.assertEqual(manifest["pages_url"], CANONICAL_URL)

    def test_rejects_mismatched_custom_domain(self) -> None:
        """Runtime input cannot silently change the configured canonical host."""
        with tempfile.TemporaryDirectory(prefix="antidote-domain-") as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(ValueError, "custom domain mismatch"):
                STAGE_PAGES.stage_site(
                    root,
                    self.create_fixture(root),
                    root / "site-suite",
                    root / "_site",
                    custom_domain="other.egohygiene.io",
                )

    def test_rejects_unsafe_custom_domain(self) -> None:
        """A URL or path cannot be injected as a Pages domain."""
        with self.assertRaisesRegex(ValueError, "invalid Pages custom domain"):
            STAGE_PAGES.validate_custom_domain("https://antidote.example/path")

    def test_rejects_local_routes_that_escape_site(self) -> None:
        """Relative links may not traverse beyond the staged artifact."""
        with tempfile.TemporaryDirectory(prefix="antidote-links-") as temporary:
            root = Path(temporary)
            output = root / "_site"
            STAGE_PAGES.stage_site(
                root, self.create_fixture(root), root / "site-suite", output
            )
            index = output / "index.html"
            index.write_text(
                index.read_text(encoding="utf-8").replace(
                    "</main>", '<a href="../../secret">Escape</a></main>'
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "escapes staged site"):
                STAGE_PAGES.validate_local_links(output)

    def test_rejects_broken_local_fragments(self) -> None:
        """Fragment-only links must identify an element on the same page."""
        with tempfile.TemporaryDirectory(prefix="antidote-fragment-") as temporary:
            root = Path(temporary)
            output = root / "_site"
            STAGE_PAGES.stage_site(
                root, self.create_fixture(root), root / "site-suite", output
            )
            index = output / "index.html"
            index.write_text(
                index.read_text(encoding="utf-8").replace(
                    "</main>", '<a href="#missing">Missing</a></main>'
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(FileNotFoundError, "fragment.*does not resolve"):
                STAGE_PAGES.validate_local_links(output)

    def test_rejects_unowned_or_source_output_directories(self) -> None:
        """Staging cannot erase arbitrary repository content."""
        with tempfile.TemporaryDirectory(prefix="antidote-output-") as temporary:
            root = Path(temporary)
            build = self.create_fixture(root)
            unowned = root / "_site-danger"
            unowned.mkdir()
            sentinel = unowned / "sentinel.txt"
            sentinel.write_text("preserve\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unowned Pages output"):
                STAGE_PAGES.stage_site(root, build, root / "site-suite", unowned)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve\n")

            git_directory = root / ".git"
            git_directory.mkdir()
            git_sentinel = git_directory / "sentinel"
            git_sentinel.write_text("preserve\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non-generated Pages output"):
                STAGE_PAGES.stage_site(
                    root, build, root / "site-suite", git_directory
                )
            self.assertEqual(git_sentinel.read_text(encoding="utf-8"), "preserve\n")

    def test_rejects_fabricated_planned_slot_metadata(self) -> None:
        """Issue, cover, and similar fields cannot leak into a planned slot."""
        with tempfile.TemporaryDirectory(prefix="antidote-planned-") as temporary:
            root = Path(temporary)
            output = root / "_site"
            STAGE_PAGES.stage_site(
                root, self.create_fixture(root), root / "site-suite", output
            )
            catalog_path = output / "site.json"
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            magazine = next(slot for slot in catalog["slots"] if slot["id"] == "magazine")
            magazine["issue_number"] = "1"
            catalog_path.write_text(
                json.dumps(catalog, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "planned publication slot"):
                STAGE_PAGES.validate_site_catalog(
                    output, CANONICAL_URL, "antidote.egohygiene.io"
                )

    def test_rejects_paper_catalog_manifest_divergence(self) -> None:
        """The catalog cannot advertise a different paper version or inventory."""
        with tempfile.TemporaryDirectory(prefix="antidote-paper-") as temporary:
            root = Path(temporary)
            output = root / "_site"
            STAGE_PAGES.stage_site(
                root, self.create_fixture(root), root / "site-suite", output
            )
            catalog = json.loads((output / "site.json").read_text(encoding="utf-8"))
            paper = next(slot for slot in catalog["slots"] if slot["id"] == "paper")
            paper["version"] = "999.0.0"
            paper["artifacts"] = paper["artifacts"][:1]
            with self.assertRaisesRegex(RuntimeError, "paper version"):
                STAGE_PAGES.validate_publication_manifest(
                    output,
                    CANONICAL_URL,
                    catalog,
                    "antidote.egohygiene.io",
                )
            paper["version"] = "0.1.0"
            with self.assertRaisesRegex(RuntimeError, "paper artifacts"):
                STAGE_PAGES.validate_publication_manifest(
                    output,
                    CANONICAL_URL,
                    catalog,
                    "antidote.egohygiene.io",
                )

    def test_stages_documented_fallback_without_custom_domain(self) -> None:
        """Rollback mode retains a canonical GitHub URL and null custom domain."""
        with tempfile.TemporaryDirectory(prefix="antidote-fallback-") as temporary:
            root = Path(temporary)
            build = self.create_fixture(root)
            config_path = root / "beacon-project.toml"
            config = config_path.read_text(encoding="utf-8")
            config = config.replace(
                'pages_url = "https://antidote.egohygiene.io/"',
                'pages_url = "https://egohygiene.github.io/antidote/"',
            )
            config = config.replace(
                'pages_fallback_url = "https://egohygiene.github.io/antidote/"\n',
                "",
            )
            config = config.replace(
                'pages_custom_domain = "antidote.egohygiene.io"',
                'pages_custom_domain = ""',
            )
            config_path.write_text(config, encoding="utf-8")
            paper_path = build / "web" / "index.html"
            paper_path.write_text(
                paper_path.read_text(encoding="utf-8").replace(
                    CANONICAL_URL, "https://egohygiene.github.io/antidote/"
                ),
                encoding="utf-8",
            )

            output = root / "_site"
            manifest = STAGE_PAGES.stage_site(root, build, root / "site-suite", output)
            catalog = json.loads((output / "site.json").read_text(encoding="utf-8"))
            self.assertIsNone(manifest["custom_domain"])
            self.assertIsNone(catalog["custom_domain"])
            self.assertEqual(
                catalog["canonical_url"],
                "https://egohygiene.github.io/antidote/",
            )

    def test_checksum_inventory_requires_complete_coverage(self) -> None:
        """Files added after staging cannot remain outside the integrity set."""
        with tempfile.TemporaryDirectory(prefix="antidote-checksum-") as temporary:
            root = Path(temporary)
            output = root / "_site"
            STAGE_PAGES.stage_site(
                root, self.create_fixture(root), root / "site-suite", output
            )
            (output / "untracked.txt").write_text("not inventoried\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "inventory mismatch"):
                STAGE_PAGES.validate_checksums(output)

    def test_repeated_staging_is_byte_stable(self) -> None:
        """The catalog and complete checksum manifest are deterministic."""
        with tempfile.TemporaryDirectory(prefix="antidote-repeat-") as temporary:
            root = Path(temporary)
            build = self.create_fixture(root)
            first = root / "_site-first"
            second = root / "_site-second"
            STAGE_PAGES.stage_site(root, build, root / "site-suite", first)
            STAGE_PAGES.stage_site(root, build, root / "site-suite", second)

            self.assertEqual(
                (first / "site.json").read_bytes(), (second / "site.json").read_bytes()
            )
            self.assertEqual(
                (first / "SHA256SUMS").read_bytes(),
                (second / "SHA256SUMS").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
