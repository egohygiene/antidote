# ANT-FIG-011 — Technical benchmark and failure panels

## Scientific purpose

Reserve a data-backed technical view that reports timing, continuity,
adherence, interruption, recovery, and failure evidence together rather than
showing only favorable runs.

## Required content

- Generation latency and verified generate-ahead margin.
- Requested-versus-measured acoustic control adherence.
- Semantic and waveform continuity measurements as separate panels.
- Cancellation, interruption, fallback, recovery, and failed-run counts.
- Denominators, uncertainty, missingness, hardware, model, and revision labels.
- Direct links to structured observations and analysis code.

## Evidence and claim boundary

No panel may exist until a frozen technical protocol produces qualifying
machine-readable observations. Synthetic contract fixtures are not benchmark
results. Technical performance does not establish felt response or benefit.

## Source plan

Issue #41 freezes the reporting and promotion rule. Generate the final SVG or
PDF deterministically from versioned structured data and analysis code; record
environment, exclusions, checksums, and provenance. Issue #46 owns styling.

## Accessibility plan

Use direct labels, redundant symbols or line styles, visible denominators, and
color-blind-safe contrast. Provide alt text and a long description that states
direction, uncertainty, failures, and missing observations.

## Failure conditions

- Any value is manually invented or copied without provenance.
- Failed or missing runs disappear from denominators.
- Hardware, model, protocol, or source revisions are absent.
- The visual implies subjective or therapeutic performance.
