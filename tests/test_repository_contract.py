# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Static separation-of-concerns checks for Antidote publishing."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE_DOCUMENTS = (
    "PURPOSE.md",
    "VISION.md",
    "PRINCIPLES.md",
    "PILLARS.md",
    "MANIFESTO.md",
    "EPISTEMOLOGY.md",
    "AI_CONSTITUTION.md",
    "ONTOLOGY.md",
    "PERSONAL_MODEL.md",
    "FOUNDATIONS.md",
    "SYSTEM.md",
    "ARCHITECTURE.md",
    "METHODOLOGY.md",
    "DESIGN.md",
    "DESIGN_SYSTEM.md",
    "DECISIONS.md",
    "ROADMAP.md",
    "META.md",
)


class RepositoryContractTests(unittest.TestCase):
    """Keep the native and optional control-plane boundaries explicit."""

    def test_native_entrypoints_use_the_project_task_adapter(self) -> None:
        """Make and Task must share the same Antidote-owned implementation."""
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        taskfile = (ROOT / "Taskfile.yml").read_text(encoding="utf-8")
        self.assertIn("scripts/tasks.py", makefile)
        self.assertIn("scripts/tasks.py", taskfile)
        self.assertNotIn("BEACON_PROFILE", makefile)
        self.assertNotIn("resolve_beacon.py", taskfile)

    def test_pages_deployment_requires_explicit_activation(self) -> None:
        """A merge cannot deploy until the maintainer enables the repository gate."""
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("vars.PAGES_ENABLED == 'true'", workflow)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertIn("PAGES_CUSTOM_DOMAIN", workflow)

    def test_pages_ci_proves_publication_reproducibility(self) -> None:
        """Pages review must compare independently built governed artifacts."""
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("task reproducibility", workflow)

    def test_lorem_ipsum_is_wrapped_as_non_evidence(self) -> None:
        """Layout filler may appear only through the explicit draft macro."""
        section_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((ROOT / "paper" / "sections").glob("*.tex"))
        )
        placeholders = re.findall(
            r"\\AntidotePlaceholder\{[^{}]+\}\{([^{}]+)\}",
            section_text,
            flags=re.DOTALL,
        )
        self.assertGreater(len(placeholders), 0)
        self.assertEqual(section_text.count("Lorem ipsum"), len(placeholders))
        self.assertTrue(all("Lorem ipsum" in body for body in placeholders))

    def test_architecture_corpus_has_unique_antidote_documents(self) -> None:
        """Every governed architecture node must exist with a stable unique ID."""
        document_ids: set[str] = set()
        for relative in ARCHITECTURE_DOCUMENTS:
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), relative)
            self.assertIn("schema: aether.architecture-document/v1", text, relative)
            match = re.search(r"^id: (antidote-[a-z-]+)$", text, re.MULTILINE)
            self.assertIsNotNone(match, relative)
            assert match is not None
            self.assertNotIn(match.group(1), document_ids, relative)
            document_ids.add(match.group(1))
            self.assertRegex(text, r"(?m)^status: provisional$", relative)
        self.assertEqual(len(document_ids), 18)

    def test_meta_indexes_every_architecture_document(self) -> None:
        """The human meta index must link every canonical architecture file."""
        meta = (ROOT / "META.md").read_text(encoding="utf-8")
        for relative in ARCHITECTURE_DOCUMENTS:
            self.assertIn(f"({relative})", meta, relative)

    def test_contract_schemas_are_valid_json_with_unique_ids(self) -> None:
        """Cross-language schemas must be parseable and independently identified."""
        paths = sorted((ROOT / "contracts" / "schemas").glob("*.schema.json"))
        self.assertEqual(len(paths), 7)
        identifiers: set[str] = set()
        for path in paths:
            schema = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(
                schema.get("$schema"),
                "https://json-schema.org/draft/2020-12/schema",
                path.name,
            )
            identifier = schema.get("$id")
            self.assertIsInstance(identifier, str, path.name)
            self.assertTrue(identifier.startswith("urn:egohygiene:antidote:"), path.name)
            self.assertNotIn(identifier, identifiers, path.name)
            identifiers.add(identifier)
            self.assertFalse(schema.get("additionalProperties", True), path.name)

    def test_local_markdown_links_resolve(self) -> None:
        """New architecture and support navigation must not contain dead local links."""
        selected = [ROOT / relative for relative in ARCHITECTURE_DOCUMENTS]
        selected.extend(
            ROOT / relative
            for relative in (
                "AGENTS.md",
                "CONTRIBUTING.md",
                "SECURITY.md",
                "SUPPORT.md",
                "contracts/README.md",
                "docs/architecture-overview.md",
                "docs/getting-started.md",
                "workers/generation/README.md",
            )
        )
        link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        for document in selected:
            for target in link_pattern.findall(document.read_text(encoding="utf-8")):
                if target.startswith(("http://", "https://", "#")):
                    continue
                path_text = target.split("#", maxsplit=1)[0]
                resolved = (document.parent / path_text).resolve()
                self.assertTrue(resolved.exists(), f"{document}: {target}")


if __name__ == "__main__":
    unittest.main()
