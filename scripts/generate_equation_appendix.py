#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate the equation registry and generate its two appendix projections."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = Path("paper/equations/registry.json")
NOTATION_PATH = Path("paper/equations/notation-glossary.tex")
CLASSIFICATION_PATH = Path("paper/equations/equation-classification.tex")
EQUATION_ID = re.compile(r"ANT-EQ-\d{3}")
EQUATION_LABEL = re.compile(r"\\label\{(eq:[A-Za-z0-9:._-]+)\}")
ALLOWED_CLASSES = {
    "definitional",
    "conceptual",
    "proposed-operationalization",
    "estimated-model",
    "future-empirical-model",
}
ALLOWED_IMPLEMENTATION_STATES = {
    "implemented-mock-slice",
    "formalized-only",
    "unavailable",
}


def tex_escape(value: object) -> str:
    """Escape plain registry prose while preserving mathematical fields."""
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    normalized = re.sub(r"\s+", " ", str(value)).strip()
    return "".join(replacements.get(character, character) for character in normalized)


def display_token(value: str) -> str:
    """Turn one stable machine token into readable appendix prose."""
    return value.replace("-", " ")


def load_registry(project: Path = ROOT) -> dict[str, object]:
    """Load the canonical equation registry."""
    return json.loads((project / REGISTRY_PATH).read_text(encoding="utf-8"))


def validate_registry(project: Path = ROOT) -> list[str]:
    """Return deterministic errors for registry and System Design drift."""
    errors: list[str] = []
    try:
        registry = load_registry(project)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return [f"equation registry is invalid: {error}"]

    if registry.get("schema") != "antidote.equation-registry/v1":
        errors.append("equation registry schema must be antidote.equation-registry/v1")
    if registry.get("version") != "0.1.0":
        errors.append("equation registry version must be 0.1.0")
    if registry.get("governed_by") != "egohygiene/antidote#39":
        errors.append("equation registry must be governed by issue #39")
    if set(registry.get("classification_order", [])) != ALLOWED_CLASSES:
        errors.append("equation registry must declare every permitted equation class")
    if set(registry.get("implementation_states", [])) != ALLOWED_IMPLEMENTATION_STATES:
        errors.append("equation registry implementation states are incomplete")

    source_path = project / str(registry.get("source", ""))
    if not source_path.is_file() or project.resolve() not in source_path.resolve().parents:
        errors.append("equation registry source is missing or unsafe")
        source_text = ""
    else:
        source_text = source_path.read_text(encoding="utf-8")

    equations = registry.get("equations")
    if not isinstance(equations, list) or not equations:
        errors.append("equation registry must contain equations")
        equations = []
    identifiers: list[str] = []
    labels: list[str] = []
    classes: set[str] = set()
    for equation in equations:
        if not isinstance(equation, dict):
            errors.append("every equation record must be an object")
            continue
        identifier = equation.get("id")
        label = equation.get("label")
        equation_class = equation.get("class")
        implementation_state = equation.get("implementation_state")
        if not isinstance(identifier, str) or not EQUATION_ID.fullmatch(identifier):
            errors.append(f"invalid equation ID: {identifier}")
        else:
            identifiers.append(identifier)
            if source_text.count(identifier) != 1:
                errors.append(f"{identifier} must appear exactly once in System Design")
        if not isinstance(label, str) or not label.startswith("eq:"):
            errors.append(f"invalid equation label: {label}")
        else:
            labels.append(label)
        if equation_class not in ALLOWED_CLASSES:
            errors.append(f"{identifier} has invalid class: {equation_class}")
        else:
            classes.add(str(equation_class))
            display_class = display_token(str(equation_class)).capitalize()
            if identifier and not re.search(
                rf"{re.escape(str(identifier))}---{re.escape(display_class)};",
                source_text,
            ):
                errors.append(f"{identifier} visible class marker is missing or stale")
        if implementation_state not in ALLOWED_IMPLEMENTATION_STATES:
            errors.append(
                f"{identifier} has invalid implementation state: {implementation_state}"
            )
        for field in ("plain_language", "prohibited_inference"):
            if not isinstance(equation.get(field), str) or not equation.get(field):
                errors.append(f"{identifier} is missing {field}")

    for identifier, count in Counter(identifiers).items():
        if count > 1:
            errors.append(f"duplicate equation ID: {identifier}")
    for label, count in Counter(labels).items():
        if count > 1:
            errors.append(f"duplicate equation label: {label}")
    if classes != ALLOWED_CLASSES:
        errors.append("the equation family must use every declared epistemic class")
    source_labels = set(EQUATION_LABEL.findall(source_text))
    if source_labels != set(labels):
        errors.append("System Design equation labels and registry labels differ")

    symbols = registry.get("symbols")
    if not isinstance(symbols, list) or not symbols:
        errors.append("equation registry must contain a symbol glossary")
        symbols = []
    symbol_names: list[str] = []
    for symbol in symbols:
        if not isinstance(symbol, dict):
            errors.append("every symbol record must be an object")
            continue
        latex = symbol.get("latex")
        if not isinstance(latex, str) or not latex.strip():
            errors.append("symbol record is missing latex")
        else:
            symbol_names.append(latex)
        for field in ("unit", "meaning"):
            if not isinstance(symbol.get(field), str) or not symbol.get(field):
                errors.append(f"symbol {latex} is missing {field}")
    for symbol, count in Counter(symbol_names).items():
        if count > 1:
            errors.append(f"duplicate symbol glossary entry: {symbol}")
    return errors


def render_notation(project: Path = ROOT) -> str:
    """Render the centralized notation glossary."""
    registry = load_registry(project)
    lines = [
        "% Generated by scripts/generate_equation_appendix.py.",
        "% Source: paper/equations/registry.json.",
        "",
        r"\noindent This glossary is canonical for the first design/protocol manuscript. Units are explicit because tuples and typed records are not silently added as numerical vectors.",
        "",
        r"\begin{itemize}[leftmargin=1.35em,itemsep=0.52em]",
    ]
    for symbol in registry["symbols"]:
        latex = symbol["latex"]
        unit = tex_escape(symbol["unit"])
        meaning = tex_escape(symbol["meaning"])
        lines.append(
            rf"  \item ${{{latex}}}$ --- {meaning} \textit{{Unit or type: {unit}.}}"
        )
    lines.extend([r"\end{itemize}", ""])
    return "\n".join(lines)


def render_classification(project: Path = ROOT) -> str:
    """Render equation classes, implementation states, and prohibited inferences."""
    registry = load_registry(project)
    lines = [
        "% Generated by scripts/generate_equation_appendix.py.",
        "% Source: paper/equations/registry.json.",
        "",
        r"\noindent Each equation below is a design artifact at its declared epistemic and implementation state. No equation is presented as a validated law of affective response.",
        "",
        r"\begin{itemize}[leftmargin=1.35em,itemsep=0.72em]",
    ]
    for equation in registry["equations"]:
        identifier = tex_escape(equation["id"])
        equation_class = tex_escape(display_token(equation["class"]))
        implementation = tex_escape(display_token(equation["implementation_state"]))
        meaning = tex_escape(equation["plain_language"])
        prohibited = tex_escape(equation["prohibited_inference"])
        label = equation["label"]
        lines.extend(
            [
                rf"  \item \textbf{{{identifier} --- {equation_class}.}} Equation~\ref{{{label}}}. {meaning}",
                rf"  \textit{{Implementation: {implementation}. Prohibited inference: {prohibited}}}",
            ]
        )
    lines.extend([r"\end{itemize}", ""])
    return "\n".join(lines)


def expected_outputs(project: Path = ROOT) -> dict[Path, str]:
    """Return both deterministic generated appendix projections."""
    return {
        project / NOTATION_PATH: render_notation(project),
        project / CLASSIFICATION_PATH: render_classification(project),
    }


def main() -> int:
    """Write or verify the governed equation appendix projections."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=str(ROOT))
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    project = Path(arguments.project).expanduser().resolve()
    errors = validate_registry(project)
    if errors:
        for error in sorted(set(errors)):
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    outputs = expected_outputs(project)
    if arguments.write:
        for destination, content in outputs.items():
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")
            print(f"WROTE {destination}")
        return 0
    stale = [path for path, content in outputs.items() if not path.is_file() or path.read_text(encoding="utf-8") != content]
    if stale:
        print(
            "ERROR equation appendix projection is missing or stale; "
            "run scripts/generate_equation_appendix.py --write",
            file=sys.stderr,
        )
        return 1
    print(f"PASS governed equation system ({len(load_registry(project)['equations'])} equations).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
