# ANT-FIG-006 - Semantic and waveform continuity renderer

## Scientific purpose

Keep semantic transition checks independent from measured audio-boundary continuity.

## Required content

Show adjacent conditioning states, interpolation bounds, audio segments, overlap/crossfade, measurements, acceptance, and fallback.

## Evidence and claim boundary

Governed by ANT-HYP-002 and ANT-CLM-005. Smooth waveforms do not prove semantic intent, and semantic similarity does not prove smooth audio.

## Source plan

Author deterministic SVG; any waveform example must be generated from a checked-in synthetic signal and labeled as illustrative.

## Accessibility plan

Use aligned semantic and acoustic lanes, direct boundary labels, and shapes that remain distinct in grayscale.

## Failure conditions

Reject fabricated measured traces, an unlabeled synthetic example, a seamless-audio claim, or collapsed continuity criteria.
