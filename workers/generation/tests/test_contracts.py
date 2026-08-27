# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Exercise every canonical fixture through the Python validation boundary."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema.exceptions import ValidationError

from antidote_generation import ContractRegistry

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS_ROOT = REPOSITORY_ROOT / "contracts"


def load_fixture_cases() -> list[dict[str, Any]]:
    """Load the shared language-neutral fixture suite."""
    suite = json.loads(
        (CONTRACTS_ROOT / "fixtures" / "cases.json").read_text(encoding="utf-8")
    )
    return suite["cases"]


@pytest.mark.parametrize("case", load_fixture_cases(), ids=lambda case: case["name"])
def test_fixture_validity(case: dict[str, Any]) -> None:
    """Require Python to agree with the fixture's declared validity."""
    registry = ContractRegistry(CONTRACTS_ROOT)
    if case["valid"]:
        registry.validate(case["contract"], case["data"])
    else:
        with pytest.raises(ValidationError):
            registry.validate(case["contract"], case["data"])


def test_registry_exposes_every_manifest_contract() -> None:
    """Keep the Python boundary synchronized with the manifest."""
    manifest = json.loads(
        (CONTRACTS_ROOT / "manifest.json").read_text(encoding="utf-8")
    )
    registry = ContractRegistry(CONTRACTS_ROOT)

    expected = tuple(sorted(item["name"] for item in manifest["contracts"]))
    assert registry.names == expected
