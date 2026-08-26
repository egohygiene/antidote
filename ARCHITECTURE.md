# Architecture

Antidote is the durable owner of one research program and its publication
evidence. It consumes organization capabilities through versioned contracts;
it does not copy their implementation or depend on Empathy at runtime.

```text
Empathy migration history
          |
          v
Antidote-owned research source
  |       |        |        |
paper   sources   notes    data
  |
  v
Beacon research-paper profile (immutable revision)
  |
  +--> PDF
  +--> accessible HTML
  +--> arXiv source archive
  +--> provenance record

Relay --> reviewable repository-intelligence artifact
Egolint --> repository portability and policy validation
```

## Foundation selection

| Concern | Selection |
| --- | --- |
| Holon repository class | `publication` |
| Security floor | `baseline` |
| Publication profile | Beacon `research-paper` `0.1.0` |
| Identity projection | Beacon `egohygiene` theme |
| CI orchestration | Repository paper gate plus pinned Relay workflow |
| Quality | Egolint native validation from a pinned source revision |
| Site | Deferred; no Pages deployment selected |
| Agent package | Deferred; no Aether package selected |

Holon's current draft `publication` manifest makes agent and documentation-site
capabilities mandatory. Issue 71 requires both to remain opt-in, so this
repository records the class selection but deliberately does not materialize a
Holon manifest until that contract can express the narrower selection.

## Ownership boundaries

- Antidote owns manuscript text, bibliography records, figures, data schemas,
  research notes, and source assessments.
- Beacon owns publication templates, rendering conventions, validation, and
  source packaging.
- Relay owns reusable workflow implementation. Antidote owns caller policy and
  final publication approval.
- Egolint owns lint semantics and normalized quality evidence.
- Empathy retains only migration history and a pointer after extraction.

Generated artifacts are disposable projections of committed source. No build
output is canonical, and no automated workflow publishes a claim or submits a
paper.
