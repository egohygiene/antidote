# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Runtime validation against the repository-owned Antidote JSON Schemas."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError, ValidationError


class UnknownContractError(KeyError):
    """Raised when a caller requests a contract outside the v1 manifest."""


class ContractRegistry:
    """Load canonical schemas without copying them into the worker package."""

    def __init__(self, contracts_root: Path) -> None:
        """Load and compile the repository contract manifest."""
        self._root = Path(contracts_root).resolve()
        manifest = json.loads(
            (self._root / "manifest.json").read_text(encoding="utf-8")
        )
        self._validators: dict[str, Draft202012Validator] = {}
        for item in manifest["contracts"]:
            schema = json.loads(
                (self._root / item["schema"]).read_text(encoding="utf-8")
            )
            Draft202012Validator.check_schema(schema)
            self._validators[item["name"]] = Draft202012Validator(
                schema,
                format_checker=FormatChecker(),
            )

    @property
    def names(self) -> tuple[str, ...]:
        """Return the deterministic set of supported contract names."""
        return tuple(sorted(self._validators))

    def validate(self, name: str, value: object) -> None:
        """Validate one value or raise a JSON Schema validation error."""
        try:
            validator = self._validators[name]
        except KeyError as error:
            raise UnknownContractError(name) from error
        validator.validate(value)


__all__ = [
    "ContractRegistry",
    "SchemaError",
    "UnknownContractError",
    "ValidationError",
]
