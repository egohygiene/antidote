#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Generate Antidote's exact, claim-bearing publication figures."""

from __future__ import annotations

import argparse
import html
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = Path("paper/visuals/manifest.json")
GENERATED_IDS = (
    "ANT-FIG-001",
    "ANT-FIG-003",
    "ANT-FIG-004",
    "ANT-FIG-005",
    "ANT-FIG-006",
    "ANT-FIG-007",
    "ANT-FIG-008",
    "ANT-FIG-009",
)


def esc(value: object) -> str:
    """Escape one SVG text value."""
    return html.escape(str(value), quote=True)


def rect(
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    css: str = "card",
    radius: float = 20,
    attrs: str = "",
) -> str:
    """Return one rounded SVG rectangle."""
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
        f'rx="{radius}" class="{css}" {attrs}/>'
    )


def text(
    x: float,
    y: float,
    value: object,
    *,
    css: str = "body",
    anchor: str = "start",
    attrs: str = "",
) -> str:
    """Return one escaped SVG text node."""
    return (
        f'<text x="{x}" y="{y}" class="{css}" text-anchor="{anchor}" '
        f'{attrs}>{esc(value)}</text>'
    )


def multiline(
    x: float,
    y: float,
    values: list[str] | tuple[str, ...],
    *,
    css: str = "body",
    anchor: str = "start",
    line_height: float = 34,
    attrs: str = "",
) -> str:
    """Return vertically stacked SVG text lines."""
    spans = "".join(
        f'<tspan x="{x}" dy="{0 if index == 0 else line_height}">{esc(value)}</tspan>'
        for index, value in enumerate(values)
    )
    return (
        f'<text x="{x}" y="{y}" class="{css}" text-anchor="{anchor}" '
        f'{attrs}>{spans}</text>'
    )


def arrow(
    path: str,
    *,
    css: str = "flow",
    marker: str = "arrow-navy",
    attrs: str = "",
) -> str:
    """Return a directed SVG path with exactly one arrowhead."""
    return (
        f'<path d="{path}" class="{css}" marker-end="url(#{marker})" '
        f'{attrs}/>'
    )


def pill(
    x: float,
    y: float,
    width: float,
    label: str,
    *,
    css: str = "pill",
    text_css: str = "pill-text",
    text_attrs: str = "",
) -> str:
    """Return a labeled status pill."""
    return "\n".join(
        (
            rect(x, y, width, 44, css=css, radius=22),
            text(
                x + width / 2,
                y + 30,
                label,
                css=text_css,
                anchor="middle",
                attrs=text_attrs,
            ),
        )
    )


def shell(visual: dict[str, object], body: str, *, extra_defs: str = "") -> str:
    """Wrap a figure body in the shared accessible Antidote SVG system."""
    dimensions = visual["dimensions"]
    assert isinstance(dimensions, dict)
    width = int(dimensions["width"])
    height = int(dimensions["height"])
    title = esc(visual["title"])
    description = esc(visual["long_description"])
    visual_id = esc(visual["id"])
    defs_extension = f"    {extra_defs}\n" if extra_defs else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description" data-antidote-state="final" data-antidote-generator="scripts/generate_publication_figures.py" data-visual-id="{visual_id}">
  <title id="title">{title}</title>
  <desc id="description">{description}</desc>
  <defs>
    <linearGradient id="wave" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#7650d8"/>
      <stop offset="0.45" stop-color="#277bc0"/>
      <stop offset="0.75" stop-color="#1b9f9a"/>
      <stop offset="1" stop-color="#c88018"/>
    </linearGradient>
    <pattern id="hatch" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <line x1="0" y1="0" x2="0" y2="14" stroke="#8a78d5" stroke-width="4" opacity="0.28"/>
    </pattern>
    <marker id="arrow-navy" markerWidth="18" markerHeight="18" refX="16" refY="9" orient="auto" markerUnits="userSpaceOnUse">
      <path d="M0 0 L18 9 L0 18 Z" fill="#17375e"/>
    </marker>
    <marker id="arrow-violet" markerWidth="18" markerHeight="18" refX="16" refY="9" orient="auto" markerUnits="userSpaceOnUse">
      <path d="M0 0 L18 9 L0 18 Z" fill="#5742cf"/>
    </marker>
    <marker id="arrow-plum" markerWidth="18" markerHeight="18" refX="16" refY="9" orient="auto" markerUnits="userSpaceOnUse">
      <path d="M0 0 L18 9 L0 18 Z" fill="#98245f"/>
    </marker>
    <marker id="arrow-gold" markerWidth="18" markerHeight="18" refX="16" refY="9" orient="auto" markerUnits="userSpaceOnUse">
      <path d="M0 0 L18 9 L0 18 Z" fill="#aa6c00"/>
    </marker>
    <style>
      text {{ font-family: "DejaVu Sans Condensed", "DejaVu Sans", Arial, sans-serif; }}
      .title {{ font-size: 48px; font-weight: 800; letter-spacing: 0.015em; fill: #142b4b; }}
      .subtitle {{ font-size: 27px; font-weight: 500; fill: #465970; }}
      .section {{ font-size: 31px; font-weight: 800; letter-spacing: 0.018em; fill: #291542; }}
      .section-blue {{ font-size: 31px; font-weight: 800; letter-spacing: 0.018em; fill: #15375e; }}
      .card {{ fill: #fffdfa; stroke: #17375e; stroke-width: 4; }}
      .card-violet {{ fill: #f8f5ff; stroke: #5742cf; stroke-width: 4; }}
      .card-gold {{ fill: #fff5dc; stroke: #aa6c00; stroke-width: 4; }}
      .card-plum {{ fill: #fff4f8; stroke: #98245f; stroke-width: 4; }}
      .card-blue {{ fill: #eef8fd; stroke: #277bc0; stroke-width: 4; }}
      .card-teal {{ fill: #effaf7; stroke: #167f78; stroke-width: 4; }}
      .card-muted {{ fill: #f4f1ed; stroke: #68798c; stroke-width: 4; stroke-dasharray: 12 8; }}
      .head {{ font-size: 31px; font-weight: 800; fill: #142b4b; }}
      .body {{ font-size: 25px; font-weight: 500; fill: #354b64; }}
      .body-strong {{ font-size: 25px; font-weight: 750; fill: #17375e; }}
      .small {{ font-size: 21px; font-weight: 550; fill: #52667c; }}
      .tiny {{ font-size: 18px; font-weight: 600; fill: #52667c; }}
      .equation {{ font-size: 29px; font-weight: 650; fill: #291542; }}
      .flow {{ fill: none; stroke: #17375e; stroke-width: 5; stroke-linejoin: round; }}
      .flow-violet {{ fill: none; stroke: #5742cf; stroke-width: 5; stroke-dasharray: 13 9; stroke-linejoin: round; }}
      .flow-plum {{ fill: none; stroke: #98245f; stroke-width: 5; stroke-linejoin: round; }}
      .flow-gold {{ fill: none; stroke: #aa6c00; stroke-width: 6; stroke-linejoin: round; }}
      .boundary {{ fill: none; stroke: #64768a; stroke-width: 3; stroke-dasharray: 12 9; }}
      .pill {{ fill: #e6eef7; stroke: #17375e; stroke-width: 2; }}
      .pill-violet {{ fill: #eeeaff; stroke: #5742cf; stroke-width: 2; }}
      .pill-gold {{ fill: #ffedbd; stroke: #aa6c00; stroke-width: 2; }}
      .pill-plum {{ fill: #ffe8f1; stroke: #98245f; stroke-width: 2; }}
      .pill-teal {{ fill: #e2f5ef; stroke: #167f78; stroke-width: 2; }}
      .pill-text {{ font-size: 21px; font-weight: 800; fill: #17375e; letter-spacing: 0.015em; }}
      .pill-text-violet {{ font-size: 21px; font-weight: 800; fill: #4b37bb; letter-spacing: 0.015em; }}
      .pill-text-gold {{ font-size: 21px; font-weight: 800; fill: #795000; letter-spacing: 0.015em; }}
      .pill-text-plum {{ font-size: 21px; font-weight: 800; fill: #8d1f58; letter-spacing: 0.015em; }}
      .footer {{ font-size: 22px; font-weight: 800; fill: #52667c; letter-spacing: 0.02em; }}
    </style>
{defs_extension}  </defs>
  <rect width="{width}" height="{height}" fill="#fffaf6"/>
  {body}
</svg>
'''


def person_moment_loop(visual: dict[str, object]) -> str:
    """Render the introductory inspectability chain."""
    body: list[str] = [
        text(600, 48, "PERSON + MOMENT → JOURNEY → AUDIO → RESPONSE", css="title", anchor="middle", attrs='style="font-size:38px"'),
        text(600, 80, "A governed chain of records — not a causal or therapeutic mechanism", css="subtitle", anchor="middle"),
    ]
    cards = (
        (55, "1", "PERSON + MOMENT", ("chosen context", "desired direction"), "card-gold"),
        (340, "2", "SEMANTIC JOURNEY", ("intent + stages", "constraints + approval"), "card-violet"),
        (625, "3", "ACOUSTIC REALIZATION", ("artifact + hash", "measured features"), "card-blue"),
        (910, "4", "EXPOSURE + RESPONSE", ("what was heard", "what was reported"), "card-teal"),
    )
    for x, number, heading, details, css in cards:
        body.extend(
            (
                f'<g data-node="step-{number}">',
                rect(x, 110, 235, 170, css=css),
                text(x + 26, 146, number, css="body-strong"),
                text(x + 118, 177, heading, css="head", anchor="middle", attrs='style="font-size:18px"'),
                multiline(x + 118, 218, details, css="body", anchor="middle", line_height=31, attrs='style="font-size:21px"'),
                "</g>",
            )
        )
    for x in (290, 575, 860):
        body.append(arrow(f"M{x} 195 H{x + 38}", attrs='data-relation="proposed-test"'))
    body.extend(
        (
            arrow("M1025 286 V326 H180 V286", css="flow-violet", marker="arrow-violet", attrs='data-relation="future-advisory-proposal"'),
            pill(380, 316, 440, "FUTURE ADVISORY PROPOSAL", css="pill-violet", text_css="pill-text-violet"),
            text(600, 392, "Human review required · no automatic learning · every transition remains a hypothesis to test", css="footer", anchor="middle", attrs='style="font-size:18px"'),
        )
    )
    return shell(visual, "\n  ".join(body))


def consent_projection(visual: dict[str, object]) -> str:
    """Render the private-context and consent projection boundary."""
    body: list[str] = [
        text(800, 64, "CONSENT-SCOPED CONTEXT PROJECTION", css="title", anchor="middle"),
        text(800, 102, "The model sees a reviewed purpose-bounded projection — never unrestricted history", css="subtitle", anchor="middle"),
        rect(45, 150, 320, 555, css="card-plum"),
        text(205, 202, "PRIVATE CONTEXT", css="section", anchor="middle"),
        multiline(90, 258, ("Manual check-in", "Selected journal excerpt", "Prior response record", "Optional signal feature"), css="body", line_height=64),
        pill(82, 548, 246, "SOURCE RECORDS", css="pill-plum", text_css="pill-text-plum"),
        text(205, 635, "Outside worker boundary", css="body-strong", anchor="middle"),
        text(205, 672, "retained separately", css="small", anchor="middle"),
        rect(430, 150, 340, 555, css="card-gold"),
        text(600, 202, "CONSENT GRANT", css="section", anchor="middle"),
        multiline(480, 258, ("Purpose", "Allowed fields", "Allowed actions", "Expiry + retention", "Review + correction"), css="body", line_height=58),
        pill(478, 574, 244, "HUMAN AUTHORITY", css="pill-gold", text_css="pill-text-gold"),
        text(600, 655, "missing or stale → block", css="body-strong", anchor="middle"),
        rect(835, 150, 340, 555, css="card-violet"),
        text(1005, 202, "WORKING PROJECTION", css="section", anchor="middle"),
        multiline(885, 258, ("Minimized semantic items", "Source-event lineage", "Derivation version", "Edits + omissions", "Visible exclusions"), css="body", line_height=58),
        pill(875, 574, 260, "REVIEWED FOR USE", css="pill-violet", text_css="pill-text-violet"),
        text(1005, 655, "cᵂᵒʳᵏᵢ,ₜ = π(Sᶜᵗˣᵢ,ₜ ; Aᵢ,ₜ)", css="equation", anchor="middle"),
        rect(1240, 150, 315, 260, css="card-blue"),
        text(1398, 202, "PLANNING INPUT", css="section-blue", anchor="middle"),
        multiline(1285, 260, ("journey proposal", "human correction", "explicit approval"), css="body", line_height=54),
        rect(1240, 445, 315, 260, css="card-teal"),
        text(1398, 497, "WORKER INPUT", css="section-blue", anchor="middle"),
        multiline(1285, 555, ("immutable specification", "approved projection only", "no database access"), css="body", line_height=54),
        arrow("M365 330 H418", css="flow-gold", marker="arrow-gold", attrs='data-flow="source-to-consent"'),
        arrow("M770 330 H823", css="flow-gold", marker="arrow-gold", attrs='data-flow="consent-to-projection"'),
        arrow("M1175 280 H1228", attrs='data-flow="projection-to-plan"'),
        arrow("M1398 410 V433", attrs='data-flow="approval-to-worker"'),
        rect(420, 754, 760, 84, css="card-muted", radius=18),
        text(800, 790, "EXCLUDED · REVOKED · EXPIRED · OUT OF PURPOSE", css="head", anchor="middle", attrs='style="font-size:27px"'),
        text(800, 821, "record the reason and stop — no bypass path", css="small", anchor="middle"),
        arrow("M600 705 V742", css="flow-plum", marker="arrow-plum", attrs='data-flow="consent-failure"'),
        text(800, 878, "CONSENT AND LOCAL EXECUTION SUPPORT INSPECTION; THEY DO NOT PROVE PRIVACY OR MEANINGFUL CONSENT", css="footer", anchor="middle"),
    ]
    return shell(visual, "\n  ".join(body))


def semantic_mixer(visual: dict[str, object]) -> str:
    """Render the human-authorized semantic control surface."""
    body: list[str] = [
        text(800, 62, "SEMANTIC INTENT MIXER", css="title", anchor="middle"),
        text(800, 100, "Human-scale controls become typed, reversible conditioning — not hidden prompt concatenation", css="subtitle", anchor="middle"),
        rect(45, 145, 530, 730, css="card-gold"),
        text(310, 198, "PERSON-AUTHORED CONTROLS", css="section", anchor="middle", attrs='style="font-size:26px"'),
        text(310, 232, "illustrative positions · not response data", css="small", anchor="middle"),
    ]
    knobs = (
        ("GROUNDING", 0.70, "steady · embodied"),
        ("RELEASE", 0.45, "space to move"),
        ("BRIGHTNESS", 0.30, "soft · not dark"),
        ("FAMILIARITY", 0.62, "known textures"),
        ("SPACE", 0.76, "open · spacious"),
    )
    for index, (label, value, note) in enumerate(knobs):
        y = 292 + index * 105
        end = 125 + 350 * value
        body.extend(
            (
                text(92, y, label, css="body-strong"),
                text(520, y, note, css="small", anchor="end"),
                f'<line x1="96" y1="{y + 28}" x2="510" y2="{y + 28}" stroke="#a7b2bd" stroke-width="10" stroke-linecap="round"/>',
                f'<line x1="96" y1="{y + 28}" x2="{end:.0f}" y2="{y + 28}" stroke="#aa6c00" stroke-width="10" stroke-linecap="round"/>',
                f'<circle cx="{end:.0f}" cy="{y + 28}" r="18" fill="#fffaf6" stroke="#17375e" stroke-width="4"/>',
                text(96, y + 62, "0 bound", css="tiny"),
                text(303, y + 62, "neutral", css="tiny", anchor="middle"),
                text(510, y + 62, "1 bound", css="tiny", anchor="end"),
            )
        )
    body.extend(
        (
            rect(625, 145, 410, 730, css="card-violet"),
            text(830, 198, "TYPED COMPOSITION", css="section", anchor="middle"),
            pill(685, 240, 290, "VISIBLE AUTHORITY ORDER", css="pill-violet", text_css="pill-text-violet", text_attrs='style="font-size:17px"'),
            multiline(680, 322, ("1  current user value", "2  accepted suggestion", "3  neutral default"), css="body", line_height=48),
            text(830, 500, "αⱼ,ₜ = (1−ρⱼ)αⱼ,ₜ₋₁ + ρⱼkᵉᶠᶠⱼ,ₜ", css="equation", anchor="middle", attrs='style="font-size:25px"'),
            text(830, 540, "ordinary controls only", css="small", anchor="middle"),
            multiline(680, 614, ("Ξ  exclusions + safety", "≺  conflict priority", "mⱼ  versioned mixin", "⊕  typed composition"), css="body", line_height=48),
            pill(690, 797, 280, "INSPECT · EDIT · REJECT", css="pill-plum", text_css="pill-text-plum", text_attrs='style="font-size:17px"'),
            rect(1085, 145, 470, 305, css="card-blue"),
            text(1320, 198, "CONDITIONING STATE", css="section-blue", anchor="middle"),
            multiline(1135, 266, ("resolved semantic condition qᵢ,ₙ", "constraints + uncertainty", "provenance + adapter capabilities"), css="body", line_height=58),
            rect(1085, 505, 470, 370, css="card-teal"),
            text(1320, 558, "APPROVED COMPILATION", css="section-blue", anchor="middle"),
            multiline(1135, 625, ("journey plan Jᵢ,ₜ", "↓ capability-bounded Compileₐ", "conditioning γ⁽ᵃ⁾ᵢ,ₙ", "optional native prompt φ⁽ᵃ⁾ᵢ,ₙ"), css="body", line_height=54),
            pill(1178, 799, 284, "HUMAN APPROVAL GATE", css="pill-gold", text_css="pill-text-gold", text_attrs='style="font-size:17px"'),
            arrow("M575 510 H613", css="flow-gold", marker="arrow-gold", attrs='data-flow="controls-to-mixer"'),
            arrow("M1035 330 H1073", attrs='data-flow="mixer-to-conditioning"'),
            arrow("M1320 450 V493", css="flow-gold", marker="arrow-gold", attrs='data-flow="approval-to-compilation"'),
            text(800, 945, "A MIXIN CAN GUIDE A MODEL ADAPTER; IT DOES NOT DIRECTLY CONTROL ACOUSTICS, EMOTION, OR BENEFIT", css="footer", anchor="middle"),
        )
    )
    return shell(visual, "\n  ".join(body))


def predictive_horizon(visual: dict[str, object]) -> str:
    """Render belief, receding-horizon, and buffer timing boundaries."""
    body: list[str] = [
        text(900, 58, "BELIEF → NEGOTIATED HORIZON → VERIFIED FUTURE AUDIO", css="title", anchor="middle"),
        text(900, 96, "Slow uncertain planning stays outside deterministic playback deadlines", css="subtitle", anchor="middle"),
        rect(45, 140, 430, 255, css="card-violet"),
        text(260, 188, "STATE BELIEF bᵢ,ₜ(x)", css="section", anchor="middle"),
        multiline(88, 245, ("possible represented states", "confidence + alternatives", "missingness widens uncertainty"), css="body", line_height=43),
        pill(105, 333, 310, "PERSON CAN CORRECT", css="pill-gold", text_css="pill-text-gold"),
        rect(540, 140, 1215, 255, css="card-gold"),
        text(1148, 188, "SHORT RECEDING HORIZON Hₚ", css="section", anchor="middle"),
    ]
    horizon_cards = (
        (590, "NOW", "uₜ", "approval required", "card-gold"),
        (860, "NEXT", "uₜ₊₁", "proposal only", "card-violet"),
        (1130, "LATER", "uₜ₊₂", "proposal only", "card-violet"),
        (1400, "HORIZON", "uₜ₊Hₚ", "replan later", "card-muted"),
    )
    for x, heading, symbol, note, css in horizon_cards:
        body.extend(
            (
                rect(x, 228, 220, 120, css=css, radius=16),
                text(x + 110, 264, heading, css="small", anchor="middle"),
                text(x + 110, 306, symbol, css="equation", anchor="middle"),
                text(x + 110, 336, note, css="tiny", anchor="middle"),
            )
        )
    body.extend(
        (
            arrow("M475 268 H528", css="flow-gold", marker="arrow-gold", attrs='data-flow="correction-to-horizon"'),
            text(900, 438, "PLAYBACK CURSOR", css="section-blue", anchor="middle"),
            f'<line x1="90" y1="650" x2="1710" y2="650" stroke="#17375e" stroke-width="7"/>',
            f'<line x1="405" y1="480" x2="405" y2="714" stroke="#98245f" stroke-width="7"/>',
            text(405, 740, "t", css="equation", anchor="middle"),
            rect(90, 515, 315, 110, css="card-teal", radius=12),
            text(248, 558, "ALREADY PLAYING", css="head", anchor="middle", attrs='style="font-size:27px"'),
            text(248, 596, "verified artifact", css="small", anchor="middle"),
            rect(405, 515, 470, 110, css="card-blue", radius=12),
            text(640, 558, "VERIFIED BUFFER Bᵢ,ₜ", css="head", anchor="middle", attrs='style="font-size:27px"'),
            text(640, 596, "safe to schedule", css="small", anchor="middle"),
            rect(875, 515, 365, 110, css="card-violet", radius=12),
            text(1058, 558, "GENERATING", css="head", anchor="middle", attrs='style="font-size:27px"'),
            text(1058, 596, "not yet playable", css="small", anchor="middle"),
            rect(1240, 515, 225, 110, css="card-muted", radius=12),
            text(1352, 558, "MARGIN Mᵢ,ₜ", css="head", anchor="middle", attrs='style="font-size:24px"'),
            text(1352, 596, "uncertainty", css="small", anchor="middle"),
            rect(1465, 515, 245, 110, css="card-plum", radius=12),
            text(1588, 558, "DEADLINE", css="head", anchor="middle", attrs='style="font-size:27px"'),
            text(1588, 596, "audio needs bytes", css="small", anchor="middle"),
            text(900, 686, "ORDER IS STRUCTURAL · WIDTHS DO NOT REPORT MEASURED LATENCY", css="footer", anchor="middle"),
            pill(358, 758, 1085, "Bᵢ,ₜ ≥ ℓₒᵦₛₑᵣᵥₑ + ℓₚₗₐₙ + ℓgₑₙₑᵣₐₜₑ + ℓᵥₑᵣᵢfᵧ + ℓₛcₕₑdᵤₗₑ + Mᵢ,ₜ", css="pill-violet", text_css="pill-text-violet"),
            text(1710, 474, "IF MARGIN FAILS", css="body-strong", anchor="end"),
            text(1710, 505, "approved loop · bed · continuation · ending", css="small", anchor="end"),
            arrow("M1588 625 V754 H1460", css="flow-plum", marker="arrow-plum", attrs='data-flow="deadline-to-fallback"'),
            text(900, 836, "THE BELIEF IS NOT A VERDICT · THE HORIZON IS NOT AN OPTIMAL POLICY · THE BUFFER DOES NOT PROVE MUSICAL FIT", css="footer", anchor="middle"),
        )
    )
    return shell(visual, "\n  ".join(body))


def synthetic_wave_path(x0: float, x1: float, y: float, *, phase: float) -> str:
    """Create one deterministic illustrative sine-wave SVG path."""
    points: list[str] = []
    samples = 120
    for index in range(samples + 1):
        fraction = index / samples
        x = x0 + (x1 - x0) * fraction
        amplitude = 28 * (0.72 + 0.28 * math.sin(math.pi * fraction))
        value = y + amplitude * math.sin(phase + fraction * math.pi * 11)
        points.append(f"{'M' if index == 0 else 'L'}{x:.1f},{value:.1f}")
    return " ".join(points)


def continuity_renderer(visual: dict[str, object]) -> str:
    """Render independent semantic, acoustic, and waveform continuity lanes."""
    wave_a = synthetic_wave_path(170, 930, 755, phase=0.0)
    wave_b = synthetic_wave_path(870, 1630, 755, phase=1.15)
    body: list[str] = [
        text(900, 58, "THREE CONTINUITY CONTRACTS — CHECKED INDEPENDENTLY", css="title", anchor="middle"),
        text(900, 96, "Prompt motion, musical compatibility, and signal joining are not interchangeable", css="subtitle", anchor="middle"),
        rect(45, 135, 1710, 195, css="card-violet"),
        text(95, 184, "1  SEMANTIC PLAN", css="section"),
        rect(400, 175, 420, 100, css="card-violet", radius=14),
        text(610, 217, "qᵗᵃⁱˡᵢ,ₙ", css="equation", anchor="middle"),
        text(610, 254, "typed intent + stage role", css="small", anchor="middle"),
        rect(980, 175, 420, 100, css="card-violet", radius=14),
        text(1190, 217, "qʰᵉᵃᵈᵢ,ₙ₊₁", css="equation", anchor="middle"),
        text(1190, 254, "next typed condition", css="small", anchor="middle"),
        arrow("M820 225 H968", css="flow-violet", marker="arrow-violet", attrs='data-check="semantic"'),
        pill(1440, 190, 260, "Dˢᵉᵐₙ ≤ τˢᵉᵐ", css="pill-violet", text_css="pill-text-violet"),
        text(1440, 292, "versioned distance", css="small"),
        rect(45, 360, 1710, 255, css="card-blue"),
        text(95, 410, "2  MUSICAL + ACOUSTIC BOUNDARY", css="section-blue"),
        multiline(110, 470, ("tempo + beat phase", "key / chord compatibility", "loudness + spectral balance"), css="body", line_height=42),
        multiline(650, 470, ("timbre + density", "phrase alignment", "artifact + analyzer versions"), css="body", line_height=42),
        rect(1110, 445, 570, 120, css="card-teal", radius=14),
        text(1395, 490, "Dᵃᶜₙ = Σᵣ∈𝓕 wᵣ dᵣ(fᵣ(aᵗᵃⁱˡₙ), fᵣ(aʰᵉᵃᵈₙ₊₁))", css="equation", anchor="middle", attrs='style="font-size:24px"'),
        text(1395, 535, "normalized measured features · threshold requires evaluation", css="small", anchor="middle"),
        rect(45, 645, 1710, 230, css="card-gold"),
        text(95, 695, "3  WAVEFORM JOIN", css="section"),
        f'<path d="{wave_a}" fill="none" stroke="#277bc0" stroke-width="6" opacity="0.95" data-signal="deterministic-illustration-a"/>',
        f'<path d="{wave_b}" fill="none" stroke="#98245f" stroke-width="6" opacity="0.95" data-signal="deterministic-illustration-b"/>',
        rect(830, 700, 170, 112, css="card-muted", radius=8, attrs='fill="url(#hatch)"'),
        text(915, 736, "OVERLAP", css="body-strong", anchor="middle"),
        text(915, 769, "s ∈ [0,1]", css="equation", anchor="middle", attrs='style="font-size:24px"'),
        text(915, 798, "accepted window", css="tiny", anchor="middle"),
        text(1460, 703, "y(s) = cos(πs/2)aₙ(s) + sin(πs/2)aₙ₊₁(s)", css="equation", anchor="middle", attrs='style="font-size:23px"'),
        text(1460, 736, "one equal-power candidate", css="small", anchor="middle"),
        pill(1275, 770, 370, "ACCEPT OR FALL BACK", css="pill-plum", text_css="pill-text-plum"),
        text(900, 920, "ILLUSTRATIVE SYNTHETIC SIGNAL · SMOOTH SAMPLES DO NOT PROVE MUSICAL COHERENCE, SEMANTIC FIT, SAFETY, OR BENEFIT", css="footer", anchor="middle"),
    ]
    return shell(visual, "\n  ".join(body))


def provenance_export(visual: dict[str, object]) -> str:
    """Render provenance inputs and the fail-closed export gate."""
    body: list[str] = [
        text(850, 58, "PROVENANCE + PRIVACY-REVIEWED EXPORT", css="title", anchor="middle"),
        text(850, 96, "Integrity records become shareable only after four explicit human-governed gates", css="subtitle", anchor="middle"),
        rect(45, 140, 360, 720, css="card-blue"),
        text(225, 194, "SESSION LINEAGE", css="section-blue", anchor="middle"),
        multiline(90, 260, ("event IDs + versions", "consent + projection", "plan + specification hash", "model + adapter identity", "artifact + feature report", "exposure + interruption", "response + correction"), css="body", line_height=64),
        pill(95, 760, 260, "EXPORT CANDIDATE", css="pill-violet", text_css="pill-text-violet"),
        rect(465, 140, 770, 720, css="card-gold"),
        text(850, 194, "FAIL-CLOSED REVIEW PIPELINE", css="section", anchor="middle"),
    ]
    gates = (
        (225, "1", "PURPOSE + CONSENT", "destination and action allowed"),
        (365, "2", "MINIMIZE + REDACT", "exclude sensitive payloads"),
        (505, "3", "PRIVACY REVIEW", "re-identification unresolved?"),
        (645, "4", "HUMAN APPROVAL", "exact files and destination"),
    )
    for y, number, heading, note in gates:
        body.extend(
            (
                rect(530, y, 640, 92, css="card-gold", radius=16, attrs=f'data-gate="{number}"'),
                f'<circle cx="575" cy="{y + 46}" r="27" fill="#aa6c00"/>',
                text(575, y + 56, number, css="body-strong", anchor="middle", attrs='style="fill:#fffaf6"'),
                text(625, y + 39, heading, css="head", attrs='style="font-size:27px"'),
                text(625, y + 72, note, css="small"),
                text(1118, y + 55, "PASS / FAIL / UNRESOLVED", css="tiny", anchor="end"),
            )
        )
        if number != "4":
            body.append(arrow(f"M850 {y + 92} V{y + 128}", css="flow-gold", marker="arrow-gold", attrs=f'data-flow="gate-{number}-next"'))
        body.append(arrow(f"M1170 {y + 46} H1265", css="flow-plum", marker="arrow-plum", attrs=f'data-flow="gate-{number}-blocked"'))
    body.extend(
        (
            arrow("M405 800 H453", attrs='data-flow="candidate-to-review"'),
            rect(1280, 185, 360, 430, css="card-plum"),
            text(1460, 238, "BLOCKED EXPORT", css="section", anchor="middle"),
            multiline(1325, 305, ("no partial release", "record failed gate", "preserve review reason", "return to human", "do not infer permission"), css="body", line_height=55),
            pill(1335, 540, 250, "NO BYPASS", css="pill-plum", text_css="pill-text-plum"),
            rect(1280, 665, 360, 195, css="card-teal"),
            text(1460, 716, "APPROVED PACKAGE", css="section-blue", anchor="middle", attrs='style="font-size:27px"'),
            multiline(1325, 765, ("manifest + checksums", "declared exclusions", "provenance summary"), css="body", line_height=37),
            arrow("M1170 691 H1268", css="flow-gold", marker="arrow-gold", attrs='data-flow="approval-to-package"'),
            rect(310, 905, 1080, 90, css="card-muted", radius=18),
            text(850, 943, "HASHES SUPPORT IDENTITY + DRIFT DETECTION", css="head", anchor="middle", attrs='style="font-size:28px"'),
            text(850, 978, "They do not prove truth, authorship, consent, privacy, ownership, safety, or benefit", css="small", anchor="middle"),
        )
    )
    return shell(visual, "\n  ".join(body))


def protocol_timeline(visual: dict[str, object]) -> str:
    """Render the eight locked prospective protocol stages."""
    body: list[str] = [
        text(900, 55, "FROZEN FEASIBILITY SESSION SEQUENCE", css="title", anchor="middle"),
        text(900, 92, "ANT-PROT-FEAS-001 v1.1.0 · prospective design · collection authority = false", css="subtitle", anchor="middle"),
    ]
    stages = (
        (1, "AUTHORITY +", "READINESS", "consent · setting · choice"),
        (2, "BASELINE +", "TARGET", "state · intensity · direction"),
        (3, "REVEAL +", "PLAN REVIEW", "G / S / P · fields · approval"),
        (4, "GENERATE +", "VERIFY", "model · seed · hash · features"),
        (5, "EXPLICIT", "PLAYBACK", "separate start · stop always"),
        (6, "IMMEDIATE", "RESPONSE", "within 5 min · separated fields"),
        (7, "LATER", "AFTEREFFECT", "18–30 h · target 24 h"),
        (8, "REVIEW +", "CLOSE / PAUSE", "safety · corrections · no update"),
    )
    positions = ((70, 165), (500, 165), (930, 165), (1360, 165), (1360, 440), (930, 440), (500, 440), (70, 440))
    for (number, line_one, line_two, note), (x, y) in zip(stages, positions, strict=True):
        css = "card-gold" if number in {1, 3, 5, 8} else "card-blue"
        body.extend(
            (
                f'<g data-stage-order="{number}" data-stage="{esc(line_one.lower().replace(" +", "").replace(" ", "-"))}">',
                rect(x, y, 370, 170, css=css, radius=18),
                f'<circle cx="{x + 34}" cy="{y + 34}" r="24" fill="#17375e"/>',
                text(x + 34, y + 43, number, css="body-strong", anchor="middle", attrs='style="fill:#fffaf6"'),
                multiline(x + 185, y + 62, (line_one, line_two), css="head", anchor="middle", line_height=35, attrs='style="font-size:28px"'),
                text(x + 185, y + 142, note, css="small", anchor="middle", attrs='style="font-size:20px"'),
                "</g>",
            )
        )
    for path in (
        "M440 250 H488",
        "M870 250 H918",
        "M1300 250 H1348",
        "M1545 335 V428",
        "M1360 525 H1312",
        "M930 525 H882",
        "M500 525 H452",
    ):
        body.append(arrow(path, attrs='data-flow="next-stage"'))
    body.extend(
        (
            rect(70, 666, 1130, 78, css="card-plum", radius=16),
            text(635, 700, "INTERRUPT AT ANY EXPOSURE-RELATED STAGE", css="head", anchor="middle", attrs='style="font-size:27px"'),
            text(635, 730, "stop · revoke consent · technical failure · adverse response → silence, record minimum, review", css="small", anchor="middle"),
            arrow("M1545 610 V705 H1212", css="flow-plum", marker="arrow-plum", attrs='data-flow="interrupt"'),
            rect(1250, 666, 480, 78, css="card-violet", radius=16),
            text(1490, 700, "NEXT EXPOSURE ≥ 48 HOURS", css="head", anchor="middle", attrs='style="font-size:26px"'),
            text(1490, 730, "later window must close first", css="small", anchor="middle"),
            text(900, 790, "ORDERED DESIGN ≠ COMPLETED STUDY · NO PARTICIPANT FLOW OR OUTCOME IS SHOWN", css="footer", anchor="middle"),
        )
    )
    return shell(visual, "\n  ".join(body))


def equation_card(
    x: int,
    y: int,
    heading: str,
    ids: str,
    formula_lines: tuple[str, ...],
    classification: str,
    status: str,
    css: str,
) -> list[str]:
    """Return one equation-family card."""
    equation_ids: list[str] = []
    for group in ids.split(","):
        normalized = group.strip()
        if "–" not in normalized:
            equation_ids.append(normalized)
            continue
        left, right = normalized.split("–", 1)
        prefix, start = left.rsplit("-", 1)
        stop = int(right)
        equation_ids.extend(
            f"{prefix}-{number:03d}" for number in range(int(start), stop + 1)
        )
    return [
        rect(
            x,
            y,
            760,
            220,
            css=css,
            radius=20,
            attrs=f'data-equations="{esc(" ".join(equation_ids))}"',
        ),
        text(x + 38, y + 42, heading, css="head", attrs='style="font-size:25px"'),
        text(x + 720, y + 39, ids, css="small", anchor="end", attrs='style="font-size:17px"'),
        multiline(x + 380, y + 88, formula_lines, css="equation", anchor="middle", line_height=38, attrs='style="font-size:21px"'),
        pill(
            x + 38,
            y + 158,
            310,
            classification,
            css="pill-violet",
            text_css="pill-text-violet",
            text_attrs='style="font-size:16px"',
        ),
        pill(
            x + 372,
            y + 158,
            350,
            status,
            css="pill-gold" if "mock" in status else "pill-plum",
            text_css="pill-text-gold" if "mock" in status else "pill-text-plum",
            text_attrs='style="font-size:16px"',
        ),
    ]


def equation_map(visual: dict[str, object]) -> str:
    """Render the equation registry as six connected, class-labeled families."""
    body: list[str] = [
        text(900, 58, "MOMENT → JOURNEY → REALIZATION → RESPONSE", css="title", anchor="middle"),
        text(900, 96, "A map of definitions and proposed models — arrows show record dependencies, not established causality", css="subtitle", anchor="middle"),
    ]
    cards = (
        (70, 135, "MOMENT + AUTHORIZED CONTEXT", "ANT-EQ-001–003", ("zᵢ,ₜ = (oᵘˢʳᵢ,ₜ, oᵒᵖᵗᵢ,ₜ, cʷᵒʳᵏᵢ,ₜ, gᵢ,ₜ, kᵘˢʳᵢ,ₜ, ℋᵢ,<ₜ)", "cʷᵒʳᵏᵢ,ₜ = π(Sᶜᵗˣᵢ,ₜ ; Aᵢ,ₜ)"), "DEFINITION + OPERATION", "implemented mock slice", "card-gold"),
        (970, 135, "SEMANTIC MIXER + ADAPTER", "ANT-EQ-004–007", ("kᵉᶠᶠ → αⱼ,ₜ → qᵢ,ₙ", "Jᵢ,ₜ → Compileₐ(·, 𝒦ₐ) → γ⁽ᵃ⁾ᵢ,ₙ → φ⁽ᵃ⁾ᵢ,ₙ"), "DEFINITION + OPERATION", "formalized / unavailable", "card-violet"),
        (70, 420, "BELIEF + NEGOTIATED HORIZON", "ANT-EQ-008–009", ("bᵢ,ₜ(x) = Pr(Xᵢ,ₜ=x | oᵢ,₁:ₜ, uᵢ,₁:ₜ₋₁)", "U* ∈ arg min [mismatch + change + risk + burden]"), "ESTIMATOR + CONCEPT", "unavailable", "card-violet"),
        (970, 420, "BUFFER + CONTINUITY", "ANT-EQ-010–013", ("Bᵢ,ₜ ≥ Σ ℓ + Mᵢ,ₜ", "Dˢᵉᵐₙ ; Dᵃᶜₙ ; y(s)=cos(πs/2)aₙ+sin(πs/2)aₙ₊₁"), "PROPOSED OPERATION", "unavailable", "card-blue"),
        (70, 705, "EXPOSURE-LINKED RESPONSE", "ANT-EQ-014", ("eᵢ,ₜ = what was actually heard", "𝒀ᵢ,ₜ = (perceived, felt, intensity, helpfulness, harm, aftereffect)"), "DEFINITION", "implemented mock subset", "card-teal"),
        (970, 705, "FUTURE WITHIN-PERSON UPDATE", "ANT-EQ-015–016", ("pθᵢ(𝒀ᵢ,ₜ | eᵢ,ₜ, zᵢ,ₜ)", "p(θᵢ | 𝒟ᵢ,₁:ₜ) ∝ likelihood × prior"), "FUTURE EMPIRICAL MODEL", "unavailable · approval required", "card-plum"),
    )
    for card in cards:
        body.extend(equation_card(*card))
    for path, label, y in (
        ("M830 258 H958", "compile only after approval", 238),
        ("M450 365 V408", "authorized observations", 393),
        ("M1350 365 V408", "accepted controls", 393),
        ("M450 650 V693", "actual exposure", 678),
        ("M1350 650 V693", "qualifying records", 678),
        ("M830 828 H958", "human-reviewed proposal", 808),
    ):
        body.append(arrow(path, css="flow-violet", marker="arrow-violet", attrs='data-relation="record-dependency"'))
        body.append(text(900 if "H" in path else (480 if "450" in path else 1380), y, label, css="tiny", anchor="middle", attrs='style="font-size:14px"'))
    body.extend(
        (
            pill(480, 990, 260, "DEFINITION", css="pill-gold", text_css="pill-text-gold"),
            pill(770, 990, 260, "PROPOSED MODEL", css="pill-violet", text_css="pill-text-violet"),
            pill(1060, 990, 260, "UNAVAILABLE", css="pill-plum", text_css="pill-text-plum"),
            text(900, 1068, "NO EQUATION IS A VALIDATED LAW OF AFFECT, AN OPTIMAL POLICY, OR AN AUTHORIZATION FOR AUTONOMOUS LEARNING", css="footer", anchor="middle"),
        )
    )
    return shell(visual, "\n  ".join(body))


RENDERERS = {
    "ANT-FIG-001": person_moment_loop,
    "ANT-FIG-003": consent_projection,
    "ANT-FIG-004": semantic_mixer,
    "ANT-FIG-005": predictive_horizon,
    "ANT-FIG-006": continuity_renderer,
    "ANT-FIG-007": provenance_export,
    "ANT-FIG-008": protocol_timeline,
    "ANT-FIG-009": equation_map,
}


def expected_assets(project: Path = ROOT) -> dict[Path, str]:
    """Return the exact generated publication-figure paths and contents."""
    manifest = json.loads((project / MANIFEST_PATH).read_text(encoding="utf-8"))
    by_id = {
        visual["id"]: visual
        for visual in manifest["visuals"]
        if isinstance(visual, dict) and visual.get("kind") == "figure"
    }
    missing = sorted(set(GENERATED_IDS) - set(by_id))
    if missing:
        raise ValueError(f"publication figure IDs missing from manifest: {missing}")
    assets: dict[Path, str] = {}
    for visual_id in GENERATED_IDS:
        visual = by_id[visual_id]
        if visual.get("state") != "final" or visual.get("status") != "active":
            raise ValueError(f"{visual_id} must be active and final")
        assets[Path(str(visual["filename"]))] = RENDERERS[visual_id](visual)
    return assets


def main() -> int:
    """Write or verify the generated publication figures."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=str(ROOT))
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    project = Path(arguments.project).expanduser().resolve()
    stale: list[str] = []
    try:
        assets = expected_assets(project)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"ERROR publication figures cannot be generated: {error}", file=sys.stderr)
        return 1
    for relative, expected in assets.items():
        destination = project / relative
        if arguments.write:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(expected, encoding="utf-8")
        elif not destination.is_file() or destination.read_text(encoding="utf-8") != expected:
            stale.append(str(relative))
    if stale:
        for relative in stale:
            print(f"ERROR generated publication figure is stale or missing: {relative}", file=sys.stderr)
        return 1
    action = "wrote" if arguments.write else "verified"
    print(f"PASS {action} {len(assets)} deterministic publication figures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
