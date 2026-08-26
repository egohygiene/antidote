#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Verify file-level migration provenance from the Empathy source tree."""

from __future__ import annotations

import csv
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "research" / "inventory" / "empathy-source-tree.tsv"
EXPECTED_ROWS = 18


def git_blob(path: Path) -> str:
    return subprocess.run(
        ["git", "hash-object", str(path)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def main() -> int:
    with INVENTORY.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))

    errors: list[str] = []
    if len(rows) != EXPECTED_ROWS:
        errors.append(f"inventory has {len(rows)} rows; expected {EXPECTED_ROWS}")
    sources = [row["source_path"] for row in rows]
    if len(sources) != len(set(sources)):
        errors.append("inventory contains duplicate source paths")

    for row in rows:
        if row["disposition"] != "preserve-unchanged":
            continue
        destination = ROOT / row["destination"]
        if not destination.is_file():
            errors.append(f"preserved destination is missing: {row['destination']}")
            continue
        actual = git_blob(destination)
        if actual != row["blob"]:
            errors.append(
                f"preserved blob mismatch for {row['destination']}: "
                f"{actual} != {row['blob']}"
            )

    if errors:
        for error in errors:
            print(f"ERROR {error}")
        return 1
    print(
        f"PASS {len(rows)} Empathy source dispositions are recorded and preserved blobs match."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
