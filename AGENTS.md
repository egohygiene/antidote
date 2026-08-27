# Agent instructions

Antidote is a research publication and an emerging local research instrument,
not a clinical product. Preserve the distinction between implemented,
scaffolded, proposed, and unavailable behavior.

## Required context

Before changing claims, methods, results, or conclusions, read:

- `EPISTEMOLOGY.md`;
- `research/bootstrap/03-scientific-boundaries.md`;
- `research/notes/CLAIM_LEDGER.md`;
- the relevant primary-source record under `research/sources/`.

Before changing domain language, personal-context behavior, runtime structure,
or model integration, read:

- `ONTOLOGY.md`;
- `PERSONAL_MODEL.md`;
- `AI_CONSTITUTION.md`;
- `SYSTEM.md` and `ARCHITECTURE.md`;
- `DECISIONS.md` and the relevant record under `docs/decisions/`;
- the affected schema or protocol under `contracts/`.

## Scientific and human boundaries

- Keep source, hypothesis, observation, interpretation, and claim distinct.
- The originating N-of-1 experience is hypothesis-generating only.
- Do not introduce efficacy, treatment, diagnostic, entrainment, or
  neurological-mechanism claims without adequate evidence and review.
- Separate intended controls, realized acoustics, expressed emotion, felt
  response, immediate usefulness or harm, and later aftereffect.
- Treat intense emotion as a response requiring the person's interpretation,
  not an automatic success metric.
- Never place private journal, therapy, health, participant, credential, or
  model-token data in the public repository or synthetic fixtures.

## Prototype boundaries

- The Rust core owns consent, session transitions, orchestration, events,
  provenance, safety policy, and adaptation authority.
- React/Tauri owns presentation and desktop capabilities, not domain truth.
- The Python worker owns replaceable model execution and analysis, not personal
  history, database access, adaptation, or scientific interpretation.
- A worker receives only the approved semantic projection, accepted journey
  plan, and immutable generation specification.
- v0 is rule-guided. Do not add autonomous optimization, bandits, or hidden
  personal-model updates.
- Target scaffold directories do not prove implementation. Update status tables
  only from checked-in, validated evidence.
- Cross-repository integration uses versioned contracts or immutable revisions,
  never sibling source copies or mutable default-branch assumptions.

## Publication boundaries

The canonical manuscript is `paper/paper.tex` and its `paper/sections/` inputs.
Do not add a second Markdown manuscript. Antidote owns the standalone build kit
generated from Beacon's pinned profile; native builds do not reach into a
Beacon or Reflector checkout.

Generated outputs belong in `build/`, `dist/`, and `_site/` and must not be
committed. No automation submits a manuscript, activates a planned publication,
or creates a scientific claim.

## Validation

Use the project-owned interfaces:

```sh
make check-all
task check-all
```

Keep Make and Task equivalent through `scripts/tasks.py`. New language-specific
prototype checks must compose behind these interfaces. Run `make inventory`
after changing preserved migration artifacts.

When a durable boundary changes, update the owning architecture document or ADR,
its downstream links, relevant schemas, tests, roadmap evidence, and
documentation in the same reviewable change.
