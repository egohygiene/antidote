#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Generate deterministic provisional visual frames for the paper skeleton."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = Path("paper/visuals/manifest.json")
CUSTOM_PLACEHOLDERS = {"ANT-FIG-001"}


def tex_escape(value: str) -> str:
    """Escape plain text for a generated LaTeX table."""
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
    return "".join(replacements.get(character, character) for character in value)


def generated_visuals(manifest: dict[str, object]) -> list[dict[str, object]]:
    """Return active placeholders owned by this skeleton generator."""
    visuals = manifest.get("visuals", [])
    if not isinstance(visuals, list):
        raise ValueError("visuals must be an array")
    return [
        visual
        for visual in visuals
        if isinstance(visual, dict)
        and visual.get("state") == "placeholder"
        and visual.get("status") == "active"
        and visual.get("id") not in CUSTOM_PLACEHOLDERS
    ]


def wrapped_svg_lines(value: str, *, width: int = 62, limit: int = 4) -> list[str]:
    """Wrap prose into a bounded set of SVG-safe lines."""
    normalized = re.sub(r"\s+", " ", value).strip()
    lines = textwrap.wrap(normalized, width=width)
    if len(lines) > limit:
        lines = lines[:limit]
        lines[-1] = lines[-1].rstrip(" .") + "..."
    return [html.escape(line) for line in lines]


def svg_text(visual: dict[str, object]) -> str:
    """Render one exact-dimension provisional SVG frame."""
    dimensions = visual["dimensions"]
    assert isinstance(dimensions, dict)
    width = int(dimensions["width"])
    height = int(dimensions["height"])
    visual_id = html.escape(str(visual["id"]))
    raw_title = str(visual["title"])
    title = html.escape(raw_title)
    title_lines = wrapped_svg_lines(raw_title, width=44, limit=2)
    title_spans = "\n".join(
        f'    <tspan x="{width * 0.08:.0f}" dy="{height * 0.055:.0f}">{line}</tspan>'
        for line in title_lines
    )
    purpose_lines = wrapped_svg_lines(str(visual["scientific_purpose"]))
    purpose = "\n".join(
        f'    <tspan x="{width * 0.08:.0f}" dy="{height * 0.045:.0f}">{line}</tspan>'
        for line in purpose_lines
    )
    cards = (
        ("PLANNED STRUCTURE", "Composition and relationships", "Final geometry is owned by issue #46."),
        ("EVIDENCE BOUNDARY", "No results or mechanisms asserted", "Caption and claim IDs remain authoritative."),
        ("REPLACEMENT GATE", "Deterministic, reviewable asset", "Must pass accessibility and print review."),
    )
    card_width = width * 0.255
    gap = width * 0.035
    start_x = width * 0.08
    card_y = height * 0.61
    card_height = height * 0.22
    card_parts: list[str] = []
    for index, (heading, line_one, line_two) in enumerate(cards):
        x = start_x + index * (card_width + gap)
        copy_lines = wrapped_svg_lines(line_one, width=27, limit=2)
        note_lines = wrapped_svg_lines(line_two, width=34, limit=2)
        copy_spans = "\n".join(
            f'    <tspan x="{x + card_width * 0.08:.0f}" dy="{height * 0.022:.0f}">{line}</tspan>'
            for line in copy_lines
        )
        note_spans = "\n".join(
            f'    <tspan x="{x + card_width * 0.08:.0f}" dy="{height * 0.019:.0f}">{line}</tspan>'
            for line in note_lines
        )
        card_parts.extend(
            [
                f'  <rect x="{x:.0f}" y="{card_y:.0f}" width="{card_width:.0f}" height="{card_height:.0f}" rx="{height * 0.018:.0f}" fill="#F5F1E8" stroke="#668A7A" stroke-width="3"/>',
                f'  <text x="{x + card_width * 0.08:.0f}" y="{card_y + card_height * 0.26:.0f}" class="card-head">{heading}</text>',
                f'  <text x="{x + card_width * 0.08:.0f}" y="{card_y + card_height * 0.43:.0f}" class="card-copy">\n{copy_spans}\n  </text>',
                f'  <text x="{x + card_width * 0.08:.0f}" y="{card_y + card_height * 0.70:.0f}" class="card-note">\n{note_spans}\n  </text>',
            ]
        )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description" data-antidote-state="placeholder" data-antidote-generator="scripts/generate_skeleton_visuals.py">
  <title id="title">PROVISIONAL {title}</title>
  <desc id="description">Visible layout placeholder for {title}. It contains no results and asserts no mechanism.</desc>
  <defs>
    <linearGradient id="background" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#102C33"/>
      <stop offset="1" stop-color="#1D4A45"/>
    </linearGradient>
    <style>
      .kicker {{ font: 700 {height * 0.023:.0f}px sans-serif; letter-spacing: 0.14em; fill: #F2B780; }}
      .title {{ font: 700 {height * 0.045:.0f}px sans-serif; fill: #FFFFFF; }}
      .purpose {{ font: 400 {height * 0.027:.0f}px sans-serif; fill: #D9E7E1; }}
      .card-head {{ font: 700 {height * 0.017:.0f}px sans-serif; letter-spacing: 0.05em; fill: #27564D; }}
      .card-copy {{ font: 600 {height * 0.016:.0f}px sans-serif; fill: #172D31; }}
      .card-note {{ font: 400 {height * 0.013:.0f}px sans-serif; fill: #536A68; }}
      .footer {{ font: 700 {height * 0.018:.0f}px sans-serif; letter-spacing: 0.08em; fill: #F2B780; }}
    </style>
  </defs>
  <rect width="{width}" height="{height}" fill="url(#background)"/>
  <circle cx="{width * 0.91:.0f}" cy="{height * 0.18:.0f}" r="{height * 0.14:.0f}" fill="none" stroke="#5C9A8B" stroke-width="3" opacity="0.45"/>
  <circle cx="{width * 0.91:.0f}" cy="{height * 0.18:.0f}" r="{height * 0.09:.0f}" fill="none" stroke="#F2B780" stroke-width="3" opacity="0.55"/>
  <text x="{width * 0.08:.0f}" y="{height * 0.12:.0f}" class="kicker">{visual_id} · PROVISIONAL VISUAL FRAME</text>
  <text x="{width * 0.08:.0f}" y="{height * 0.17:.0f}" class="title">
{title_spans}
  </text>
  <text x="{width * 0.08:.0f}" y="{height * 0.34:.0f}" class="purpose">
{purpose}
  </text>
{chr(10).join(card_parts)}
  <text x="{width * 0.08:.0f}" y="{height * 0.93:.0f}" class="footer">LAYOUT ONLY · NOT EVIDENCE · NOT RESULTS · REPLACE THROUGH ISSUE #46</text>
</svg>
'''


def table_text(visual: dict[str, object]) -> str:
    """Render one visibly provisional, data-free LaTeX table frame."""
    visual_id = tex_escape(str(visual["id"]))
    title = tex_escape(str(visual["title"]))
    purpose = tex_escape(re.sub(r"\s+", " ", str(visual["scientific_purpose"])).strip())
    return rf'''% Generated by scripts/generate_skeleton_visuals.py.
% Layout-only placeholder. Do not enter observations or results by hand.
\small
\begin{{tabular}}{{@{{}}>{{\raggedright\arraybackslash}}p{{0.22\linewidth}}>{{\raggedright\arraybackslash}}p{{0.68\linewidth}}@{{}}}}
\toprule
\multicolumn{{2}}{{@{{}}l}}{{\textbf{{PROVISIONAL --- {visual_id}}}}} \\
\midrule
Planned title & \textbf{{{title}}} \\
Planned purpose & {purpose} \\
Evidence state & No observations, measurements, outcomes, or claims are represented. \\
Replacement gate & Issue \#46 must replace this frame with a governed, accessible table projection. \\
\bottomrule
\end{{tabular}}%
\par\smallskip
{{\raggedright\scriptsize\bfseries Layout only --- not evidence and not results.\par}}
'''


def expected_assets(project: Path = ROOT) -> dict[Path, str]:
    """Return canonical generated asset paths and contents."""
    manifest = json.loads((project / MANIFEST_PATH).read_text(encoding="utf-8"))
    assets: dict[Path, str] = {}
    for visual in generated_visuals(manifest):
        relative = Path(str(visual["filename"]))
        assets[relative] = (
            svg_text(visual) if visual.get("kind") == "figure" else table_text(visual)
        )
    return assets


def main() -> int:
    """Write or verify all generated skeleton visual frames."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=str(ROOT))
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    project = Path(arguments.project).expanduser().resolve()
    stale: list[str] = []
    assets = expected_assets(project)
    for relative, expected in assets.items():
        destination = project / relative
        if arguments.write:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(expected, encoding="utf-8")
        elif not destination.is_file() or destination.read_text(encoding="utf-8") != expected:
            stale.append(str(relative))
    if stale:
        for relative in stale:
            print(f"ERROR generated skeleton visual is stale or missing: {relative}", file=sys.stderr)
        return 1
    action = "wrote" if arguments.write else "verified"
    print(f"PASS {action} {len(assets)} deterministic skeleton visual frames.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
