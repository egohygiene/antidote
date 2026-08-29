# Web Audio source record

## Verified metadata

| Field | Value |
| --- | --- |
| Title | Web Audio API 1.1 |
| Editor | Paul Adenot; Hongchan Choi |
| Publisher | World Wide Web Consortium |
| Version reviewed | First Public Working Draft, 2024-11-05; latest published URL checked 2026-08-29 |
| Primary source | https://www.w3.org/TR/webaudio-1.1/ |
| Source type | Normative technical specification in development |
| Reviewed | 2026-08-29 |

## Source claims assessed

- Web Audio defines a graph-based audio-processing model, scheduled sources,
  time-based `AudioParam` automation, and audio-worklet processing.
- It distinguishes audio-rate and control-rate parameter handling.
- The specification warns that some cancellation patterns can cause
  discontinuities, making explicit scheduling behavior material.

## Limitations and unresolved questions

- Version 1.1 is a Working Draft rather than a W3C Recommendation.
- Antidote currently uses a Tauri/Rust target and need not implement Web Audio.
- The specification defines technical behavior, not musical quality, affective
  continuity, or safety.

## Allowed manuscript use

Use as a normative engineering anchor for sample-accurate scheduling,
automation curves, render-thread separation, and the distinction between
control-rate and audio-rate work.

## Prohibited manuscript use

Do not claim W3C conformance, seamless music, improved response, or that the
specification selects Antidote's playback implementation.
