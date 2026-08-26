# Architecture

Antidote is the durable owner of one research program and its publication
evidence. It consumes organization capabilities through versioned contracts
without depending on Empathy or Beacon at runtime.

```text
Empathy migration history
          |
          v
Antidote-owned research source
  |       |        |        |
paper   sources   notes    data
  |
  v
Antidote-owned publication build kit
  |
  +--> PDF
  +--> accessible HTML
  +--> arXiv source archive
  +--> provenance record
  +--> GitHub Pages publication hub
         |--> paper (available)
         |--> magazine (planned)
         +--> downloads and integrity evidence

Beacon pin --> inspect / upgrade / validate / package (optional)

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
| Site | Antidote-owned GitHub Pages workflow with explicit activation gate |
| Agent package | Deferred; no Aether package selected |

Holon's current draft `publication` manifest makes agent and documentation-site
capabilities mandatory. Issue 71 requires both to remain opt-in, so this
repository records the class selection but deliberately does not materialize a
Holon manifest until that contract can express the narrower selection.

## Ownership boundaries

- Antidote owns manuscript text, bibliography records, figures, data schemas,
  research notes, and source assessments.
- Antidote owns the local renderer, checks, themes, web template, Pages staging,
  and Make/Task interfaces required for independent builds.
- Beacon owns the upstream research-paper profile and optional control-plane
  behavior for initialization, upgrade coordination, planning, validation, and
  checksummed packaging.
- Relay owns reusable workflow implementation. Antidote owns caller policy and
  final publication approval.
- Egolint owns lint semantics and normalized quality evidence.
- Empathy retains only migration history and a pointer after extraction.

Generated artifacts are disposable projections of committed source. No build
output is canonical, and no automated workflow publishes a claim or submits a
paper. Pages deployment publishes only a draft projection and remains disabled
until a maintainer explicitly activates it.

## Publication hub contract

The custom-domain site is a catalog over product-owned projections, not a
second source of truth. `site.json` is the machine-readable catalog and
`publication.json` remains the current paper manifest.

| Route | Owner | State in issue #4 |
| --- | --- | --- |
| `/` | Antidote site projection | Available |
| `/paper/` | Antidote paper build | Available |
| `/antidote.pdf` | Antidote paper build | Available |
| `/magazine/` | Antidote site projection | Planned |
| `/downloads/` | Antidote site projection | Available |
| `/publication.json` | Antidote paper staging | Available |
| `/site.json` | Antidote hub staging | Available |
| `/SHA256SUMS` | Antidote hub staging | Available |

A planned slot has no stage, manifest, or artifacts. It becomes available only
in the same deterministic build that supplies real, verified outputs. The
first edition is therefore separate work in
[issue #5](https://github.com/egohygiene/antidote/issues/5); reserving its route
does not publish a magazine or imply evidence.

The canonical base is `https://antidote.egohygiene.io/`. GitHub's project URL
is retained only as a technical fallback. Pull requests build and validate the
entire hub without deployment; `main` can deploy only through the explicit
Pages gate.
