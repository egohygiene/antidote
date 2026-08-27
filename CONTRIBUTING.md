# Contributing

Thank you for helping Antidote investigate personalized generative audio with
care, technical clarity, and scientific restraint.

Start with [`docs/getting-started.md`](docs/getting-started.md) and read
[`AGENTS.md`](AGENTS.md) before changing research claims, architecture,
personal-context behavior, model adapters, or publication workflows.

## Repository boundaries

Antidote contains four related but distinct surfaces:

| Surface | Canonical locations |
| --- | --- |
| Architecture and decisions | Root architecture corpus, `docs/decisions/`, and `contracts/` |
| Prototype | `apps/`, `crates/`, `workers/`, and `experiments/` |
| Research | `research/`, `data/`, `paper/`, and the claim/source ledgers |
| Publication | `scripts/`, `latex/`, `themes/`, `web/`, `docs/`, and workflows |

Do not move a concern across these boundaries merely because a framework makes
it convenient. Sibling Ego Hygiene repositories integrate through released or
immutably pinned contracts, not copied source trees.

## Current development state

The research and publication system is implemented. The runtime prototype has
architecture, ADR, directory, protocol, and JSON Schema scaffolds but no Tauri,
React, Rust, Python worker, model, or study implementation yet. Contributions
must not present a target directory or contract as shipped behavior.

## Build and validate

The current repository-wide interfaces are:

```sh
make check-all
task check-all
```

Both delegate to `scripts/tasks.py`. Beacon remains optional through
`scripts/beacon.py`. Generated files belong in `build/`, `dist/`, and `_site/`
and must not be committed.

When the prototype workspaces land, their language-specific checks must be
composed behind these existing project-owned interfaces rather than introduce a
second top-level truth.

## Research contributions

- Verify bibliographic metadata against primary records.
- Record source type, peer-review state, exact supported claims, limitations,
  and conflicts where relevant.
- Keep source, hypothesis, observation, interpretation, and claim distinct.
- Treat lived experience as meaningful context without presenting it as general
  efficacy evidence.
- Do not commit private personal records or formal study data before protocol,
  consent, privacy, and publication classifications are accepted.

## Architecture and contract changes

- Update the owning architecture document or ADR when a durable boundary changes.
- Preserve stable IDs and the dependency graph in `META.md`.
- Version breaking schema semantics and document migration.
- Validate every cross-process and storage boundary.
- Record model license, revision, integrity, remote-code, hardware, control, and
  output-rights evidence before adding a real adapter.

## Commit messages

Use Conventional Commits with a meaningful scope when useful:

```text
docs(architecture): define moment-specific consent boundary
spec(contracts): add journey plan schema
feat(core): record generation cancellation events
research(sources): verify adaptive audio comparator
fix(publication): preserve canonical artifact hashes
```

## Pull requests

Describe the problem, owned boundary, evidence, implementation status, tests,
privacy/safety implications, migration impact, and remaining uncertainty. Link
the relevant roadmap step or issue when one exists. A pull request may propose a
decision; it does not silently make the decision accepted.

## License

Repository automation and non-manuscript documentation are MIT-licensed unless
otherwise identified. The draft manuscript remains governed by
[`paper/LICENSE.md`](paper/LICENSE.md). Model code and weights retain their own
licenses and must not be redistributed without review.
