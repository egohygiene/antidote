#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Generate deterministic Rust, TypeScript, and Python contract projections."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS_ROOT = ROOT / "contracts"
MANIFEST_PATH = CONTRACTS_ROOT / "manifest.json"
JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
REQUIRED_FIXTURE_CATEGORIES = {
    "enum",
    "format",
    "limit",
    "pattern",
    "unknown_field",
    "valid",
    "version",
}


@dataclass(frozen=True)
class Contract:
    """One manifest entry and its parsed schema."""

    name: str
    schema_path: str
    type_name: str
    schema: dict[str, Any]


@dataclass(frozen=True)
class Field:
    """One generated object field."""

    name: str
    schema: dict[str, Any]
    required: bool
    type_hint: str
    root_name: str


@dataclass
class ObjectDefinition:
    """One generated object type."""

    name: str
    root_name: str
    deny_unknown: bool
    fields: list[Field] = field(default_factory=list)


@dataclass(frozen=True)
class EnumDefinition:
    """One generated string enumeration."""

    name: str
    values: tuple[str, ...]


class TypeRegistry:
    """Discover language-neutral type definitions across all schemas."""

    def __init__(self, contracts: list[Contract]) -> None:
        self.contracts = {contract.type_name: contract for contract in contracts}
        self.objects: dict[str, ObjectDefinition] = {}
        self.enums: dict[str, EnumDefinition] = {}
        self.refs: dict[tuple[str, str], str] = {}

    def discover(self) -> None:
        """Discover every root, inline object, local definition, and enum."""
        for contract in self.contracts.values():
            for definition_name, definition in contract.schema.get("$defs", {}).items():
                generated_name = contract.type_name + to_pascal(definition_name)
                self.refs[(contract.type_name, f"#/$defs/{definition_name}")] = (
                    generated_name
                )
                self._register_object(generated_name, contract.type_name, definition)
            self._register_object(
                contract.type_name, contract.type_name, contract.schema
            )

    def _register_type(
        self,
        schema: dict[str, Any],
        type_hint: str,
        root_name: str,
    ) -> None:
        if "$ref" in schema:
            reference = schema["$ref"]
            if (root_name, reference) not in self.refs:
                raise ValueError(
                    f"unsupported or unknown JSON Schema reference: {reference}"
                )
            return
        enum_values = schema.get("enum")
        if enum_values is not None:
            if not all(isinstance(value, str) for value in enum_values):
                raise ValueError(f"only string enums are supported: {type_hint}")
            candidate = EnumDefinition(type_hint, tuple(enum_values))
            existing = self.enums.get(type_hint)
            if existing is not None and existing != candidate:
                raise ValueError(f"conflicting enum type: {type_hint}")
            self.enums[type_hint] = candidate
            return
        non_null_types = schema_types(schema)
        if "object" in non_null_types and schema.get("properties"):
            self._register_object(type_hint, root_name, schema)
            return
        if "array" in non_null_types:
            item_schema = schema.get("items", {})
            self._register_type(item_schema, singular(type_hint), root_name)

    def _register_object(
        self,
        name: str,
        root_name: str,
        schema: dict[str, Any],
    ) -> None:
        if name in self.objects:
            return
        definition = ObjectDefinition(
            name=name,
            root_name=root_name,
            deny_unknown=schema.get("additionalProperties") is False,
        )
        self.objects[name] = definition
        required = set(schema.get("required", []))
        for property_name, property_schema in schema.get("properties", {}).items():
            type_hint = name + to_pascal(property_name)
            self._register_type(property_schema, type_hint, root_name)
            definition.fields.append(
                Field(
                    name=property_name,
                    schema=property_schema,
                    required=property_name in required,
                    type_hint=type_hint,
                    root_name=root_name,
                )
            )

    def type_for(
        self,
        schema: dict[str, Any],
        type_hint: str,
        root_name: str,
        language: Literal["python", "rust", "typescript"],
    ) -> str:
        """Render one discovered schema type for a target language."""
        nullable = schema_is_nullable(schema)
        if "$ref" in schema:
            base = self.refs[(root_name, schema["$ref"])]
        elif "enum" in schema:
            base = type_hint
        elif "const" in schema:
            value = schema["const"]
            if language == "rust":
                base = "String"
            elif language == "typescript":
                base = json.dumps(value)
            else:
                base = f"Literal[{json.dumps(value)}]"
        else:
            types = schema_types(schema)
            primary = types[0] if types else "object"
            if primary == "string":
                base = {"python": "str", "rust": "String", "typescript": "string"}[
                    language
                ]
            elif primary == "integer":
                base = {"python": "int", "rust": "i64", "typescript": "number"}[
                    language
                ]
            elif primary == "number":
                base = {"python": "float", "rust": "f64", "typescript": "number"}[
                    language
                ]
            elif primary == "boolean":
                base = {"python": "bool", "rust": "bool", "typescript": "boolean"}[
                    language
                ]
            elif primary == "array":
                item_schema = schema.get("items", {})
                item_type = self.type_for(
                    item_schema,
                    singular(type_hint),
                    root_name,
                    language,
                )
                base = {
                    "python": f"list[{item_type}]",
                    "rust": f"Vec<{item_type}>",
                    "typescript": f"Array<{item_type}>",
                }[language]
            elif primary == "object" and schema.get("properties"):
                base = type_hint
            elif primary == "object":
                base = {
                    "python": "dict[str, Any]",
                    "rust": "serde_json::Value",
                    "typescript": "Record<string, unknown>",
                }[language]
            else:
                base = {
                    "python": "Any",
                    "rust": "serde_json::Value",
                    "typescript": "unknown",
                }[language]
        if not nullable:
            return base
        return {
            "python": f"{base} | None",
            "rust": f"Option<{base}>",
            "typescript": f"{base} | null",
        }[language]


def to_pascal(value: str) -> str:
    """Convert a JSON name or value to a stable PascalCase identifier."""
    words = [word for word in re.split(r"[^A-Za-z0-9]+", value) if word]
    converted = "".join(word[:1].upper() + word[1:] for word in words)
    if not converted:
        converted = "Value"
    if converted[0].isdigit():
        converted = "V" + converted
    return converted


def singular(value: str) -> str:
    """Create readable deterministic names for array item types."""
    if value.endswith("ies"):
        return value[:-3] + "y"
    if value.endswith("sses"):
        return value[:-2]
    if value.endswith("s") and not value.endswith("ss"):
        return value[:-1]
    return value + "Item"


def schema_types(schema: dict[str, Any]) -> list[str]:
    """Return the non-null JSON types declared by a schema node."""
    declared = schema.get("type")
    if declared is None:
        return []
    values = declared if isinstance(declared, list) else [declared]
    return [value for value in values if value != "null"]


def schema_is_nullable(schema: dict[str, Any]) -> bool:
    """Return whether a schema node explicitly accepts JSON null."""
    declared = schema.get("type")
    return isinstance(declared, list) and "null" in declared


def load_manifest() -> tuple[dict[str, Any], list[Contract]]:
    """Load and validate the deterministic contract manifest."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "1.0.0":
        raise ValueError("contract manifest schema_version must be 1.0.0")
    entries = manifest.get("contracts", [])
    names = [entry["name"] for entry in entries]
    if names != sorted(names) or len(names) != len(set(names)):
        raise ValueError("contract manifest names must be sorted and unique")

    contracts: list[Contract] = []
    ids: set[str] = set()
    type_names: set[str] = set()
    for entry in entries:
        schema_path = CONTRACTS_ROOT / entry["schema"]
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        schema_id = schema.get("$id")
        if schema.get("$schema") != JSON_SCHEMA_DIALECT:
            raise ValueError(f"{schema_path.name} must use JSON Schema 2020-12")
        if not isinstance(schema_id, str) or not schema_id.startswith(
            "urn:egohygiene:antidote:schema:"
        ):
            raise ValueError(f"{schema_path.name} has an invalid $id")
        if schema_id in ids:
            raise ValueError(f"duplicate schema $id: {schema_id}")
        ids.add(schema_id)
        version = schema.get("properties", {}).get("schema_version", {}).get("const")
        if version != "1.0.0":
            raise ValueError(
                f"{schema_path.name} must pin payload schema_version 1.0.0"
            )
        type_name = entry["type_name"]
        if type_name in type_names:
            raise ValueError(f"duplicate generated type name: {type_name}")
        type_names.add(type_name)
        contracts.append(
            Contract(
                name=entry["name"],
                schema_path=entry["schema"],
                type_name=type_name,
                schema=schema,
            )
        )
    return manifest, contracts


def verify_fixtures(contracts: list[Contract]) -> None:
    """Verify fixture coverage and synthetic-data markers before generation."""
    suite_path = CONTRACTS_ROOT / "fixtures" / "cases.json"
    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    cases = suite.get("cases", [])
    known = {contract.name for contract in contracts}
    categories = {case.get("category") for case in cases}
    missing_categories = REQUIRED_FIXTURE_CATEGORIES - categories
    if missing_categories:
        raise ValueError(f"fixture categories missing: {sorted(missing_categories)}")
    case_names = [case.get("name") for case in cases]
    if len(case_names) != len(set(case_names)):
        raise ValueError("fixture names must be unique")
    for name in known:
        matching = [case for case in cases if case.get("contract") == name]
        if not any(case.get("valid") is True for case in matching):
            raise ValueError(f"contract {name} has no valid fixture")
        if not any(case.get("valid") is False for case in matching):
            raise ValueError(f"contract {name} has no invalid fixture")
    unknown = {case.get("contract") for case in cases} - known
    if unknown:
        raise ValueError(f"fixtures reference unknown contracts: {sorted(unknown)}")
    serialized = json.dumps(cases).lower()
    if "@" in serialized or "http://" in serialized or "https://" in serialized:
        raise ValueError("fixtures must not contain contact details or external URLs")
    if serialized.count("synthetic") < len(known):
        raise ValueError("fixtures must remain visibly synthetic")


def enum_variant(value: str, used: set[str]) -> str:
    """Create a unique Rust enum variant for an exact serialized value."""
    candidate = to_pascal(value)
    if candidate in {"Self", "Super", "Crate"}:
        candidate += "Value"
    base = candidate
    suffix = 2
    while candidate in used:
        candidate = f"{base}{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def render_rust(registry: TypeRegistry, contracts: list[Contract]) -> str:
    """Render Rust structs, enums, and embedded canonical schemas."""
    lines = [
        "// @generated by scripts/generate_contracts.py; DO NOT EDIT.",
        "",
        "#![allow(clippy::module_name_repetitions)]",
        "",
        "use serde::{Deserialize, Serialize};",
        "",
    ]
    for definition in sorted(registry.enums.values(), key=lambda item: item.name):
        lines.extend(
            [
                "#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]",
                f"pub enum {definition.name} {{",
            ]
        )
        used: set[str] = set()
        for value in definition.values:
            variant = enum_variant(value, used)
            lines.extend(
                [f"    #[serde(rename = {json.dumps(value)})]", f"    {variant},"]
            )
        lines.extend(["}", ""])

    for definition in sorted(registry.objects.values(), key=lambda item: item.name):
        lines.append("#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]")
        if definition.deny_unknown:
            lines.append("#[serde(deny_unknown_fields)]")
        lines.append(f"pub struct {definition.name} {{")
        for item in definition.fields:
            rendered = registry.type_for(
                item.schema,
                item.type_hint,
                item.root_name,
                "rust",
            )
            if not item.required and not rendered.startswith("Option<"):
                rendered = f"Option<{rendered}>"
            if not item.required:
                lines.append(
                    '    #[serde(default, skip_serializing_if = "Option::is_none")]'
                )
            lines.append(f"    pub {item.name}: {rendered},")
        lines.extend(["}", ""])

    lines.append("pub const CONTRACT_SCHEMAS: &[crate::ContractSchema] = &[")
    for contract in contracts:
        schema_id = contract.schema["$id"]
        relative = f"../../../contracts/{contract.schema_path}"
        lines.extend(
            [
                "    crate::ContractSchema {",
                f"        name: {json.dumps(contract.name)},",
                f"        filename: {json.dumps(contract.schema_path)},",
                f"        id: {json.dumps(schema_id)},",
            ]
        )
        include_line = f"        document: include_str!({json.dumps(relative)}),"
        if len(include_line) <= 100:
            lines.append(include_line)
        else:
            lines.extend(
                [
                    "        document: include_str!(",
                    f"            {json.dumps(relative)}",
                    "        ),",
                ]
            )
        lines.append("    },")
    lines.append("];")
    return "\n".join(lines) + "\n"


def render_typescript(registry: TypeRegistry, contracts: list[Contract]) -> str:
    """Render TypeScript interfaces and literal unions."""
    lines = [
        "// @generated by scripts/generate_contracts.py; DO NOT EDIT.",
        "",
    ]
    for definition in sorted(registry.enums.values(), key=lambda item: item.name):
        values = " | ".join(json.dumps(value) for value in definition.values)
        lines.extend([f"export type {definition.name} = {values};", ""])
    for definition in sorted(registry.objects.values(), key=lambda item: item.name):
        lines.append(f"export interface {definition.name} {{")
        for item in definition.fields:
            rendered = registry.type_for(
                item.schema,
                item.type_hint,
                item.root_name,
                "typescript",
            )
            optional = "" if item.required else "?"
            lines.append(f"  {item.name}{optional}: {rendered};")
        if not definition.deny_unknown:
            lines.append("  [key: string]: unknown;")
        lines.extend(["}", ""])
    lines.append("export interface ContractByName {")
    for contract in contracts:
        lines.append(f"  {json.dumps(contract.name)}: {contract.type_name};")
    lines.extend(["}", ""])
    lines.append("export const contractSchemaIds = {")
    for contract in contracts:
        lines.append(
            f"  {json.dumps(contract.name)}: {json.dumps(contract.schema['$id'])},"
        )
    lines.extend(["} as const;", ""])
    return "\n".join(lines)


def render_python(registry: TypeRegistry, contracts: list[Contract]) -> str:
    """Render Python TypedDict and Literal projections."""
    lines = [
        "# @generated by scripts/generate_contracts.py; DO NOT EDIT.",
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any, Literal, NotRequired, TypedDict",
        "",
    ]
    for definition in sorted(registry.enums.values(), key=lambda item: item.name):
        values = ", ".join(json.dumps(value) for value in definition.values)
        lines.extend([f"{definition.name} = Literal[{values}]", ""])
    for definition in sorted(registry.objects.values(), key=lambda item: item.name):
        lines.append(f"class {definition.name}(TypedDict):")
        if not definition.fields:
            lines.append("    pass")
        for item in definition.fields:
            rendered = registry.type_for(
                item.schema,
                item.type_hint,
                item.root_name,
                "python",
            )
            if not item.required:
                rendered = f"NotRequired[{rendered}]"
            lines.append(f"    {item.name}: {rendered}")
        lines.append("")
    lines.append("ContractName = Literal[")
    for contract in contracts:
        lines.append(f"    {json.dumps(contract.name)},")
    lines.extend(["]", ""])
    lines.append("CONTRACT_SCHEMA_IDS: dict[ContractName, str] = {")
    for contract in contracts:
        lines.append(
            f"    {json.dumps(contract.name)}: {json.dumps(contract.schema['$id'])},"
        )
    lines.extend(["}", ""])
    return "\n".join(lines)


def generated_outputs(
    manifest: dict[str, Any],
    contracts: list[Contract],
) -> dict[Path, str]:
    """Build every expected generated output in memory."""
    registry = TypeRegistry(contracts)
    registry.discover()
    renderers = {
        "python": render_python,
        "rust": render_rust,
        "typescript": render_typescript,
    }
    return {
        ROOT / path: renderers[language](registry, contracts)
        for language, path in manifest["outputs"].items()
    }


def write_or_check(outputs: dict[Path, str], *, check: bool) -> None:
    """Write projections or fail when committed projections have drifted."""
    drifted: list[str] = []
    for path, expected in outputs.items():
        if check:
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                drifted.append(str(path.relative_to(ROOT)))
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(expected, encoding="utf-8")
        print(f"generated {path.relative_to(ROOT)}")
    if drifted:
        joined = "\n".join(f"- {path}" for path in drifted)
        raise RuntimeError(
            "generated contract projections are stale; run "
            "python3 scripts/generate_contracts.py:\n" + joined
        )


def parse_arguments() -> argparse.Namespace:
    """Parse the deterministic generation interface."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of writing when generated projections have drifted",
    )
    return parser.parse_args()


def main() -> int:
    """Validate source contracts and synchronize generated projections."""
    arguments = parse_arguments()
    manifest, contracts = load_manifest()
    verify_fixtures(contracts)
    write_or_check(generated_outputs(manifest, contracts), check=arguments.check)
    if arguments.check:
        print(
            "PASS generated Rust, TypeScript, and Python contract projections "
            "are current."
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, TypeError, ValueError, RuntimeError) as error:
        print(f"ERROR {error}", file=sys.stderr)
        raise SystemExit(1) from error
