# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Tests for the living atlas and bibliography promotion contract."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SourceGovernanceTests(unittest.TestCase):
    """Keep discovery, bibliography, promotion, and citation distinct."""

    def test_source_governance_contract(self) -> None:
        """The complete source graph must satisfy the offline governance check."""
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check_sources.py")],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("PASS source governance:", result.stdout)
        self.assertIn("catalog sources", result.stdout)
        self.assertIn("verified bibliography entries", result.stdout)


if __name__ == "__main__":
    unittest.main()
