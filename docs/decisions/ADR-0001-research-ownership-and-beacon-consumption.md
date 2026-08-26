# ADR-0001: Own research source here and consume Beacon by immutable revision

- Status: Accepted
- Date: 2026-08-26
- Decision owners: Ego Hygiene / Antidote
- Related issue: `egohygiene/empathy#71`

## Context

The Antidote workspace was incubated under Empathy with a Markdown manuscript,
research notes, and two provisional local templates. Empathy is the ecosystem's
golden consumer and bounded incubator; it is not the durable owner of specialist
research source. Beacon now publishes a `research-paper` profile that owns the
generic publication contract.

## Decision

Antidote becomes the sole writable owner of its manuscript, bibliography,
figures, data, research notes, and source records. It consumes Beacon
`research-paper` `0.1.0` from the full commit recorded in
`dependencies/beacon.lock.toml`. It does not vendor or fork Beacon templates.

The repository is classified as a Holon `publication` with a `baseline`
security floor. Relay CI and Egolint quality validation are selected. A public
site and an Aether agent package are not selected. Because the current Holon
draft makes those capabilities part of the publication default or required
set, no Holon materialization manifest is checked in yet.

Empathy retains only an immutable migration pointer after this repository is
canonical. Antidote has no Empathy runtime dependency.

## Consequences

- Publication outputs are reproducible projections, not committed source.
- Beacon upgrades require an explicit lock change and review.
- Research evidence remains editable only in Antidote after migration.
- Site and agent capabilities require separate explicit decisions.
- Holon conformance is documented but not overstated until its contract can
  represent this narrower capability selection.
