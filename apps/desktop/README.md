# Antidote desktop application

## Status

Executable synthetic session interface. Tauri 2 and React now compose the Rust
session authority, SQLite event log, Level-1 planner, supervised mock worker,
deliberate playback, response capture, safety halt, and restart recovery. This
is a developer research instrument: it uses synthetic test audio, makes no
clinical claim, and does not update a personal model.

## Ownership

This directory owns the Tauri 2 desktop host and React interaction layer. The
current mock session implements:

- moment check-in and desired-transition capture;
- consented-context selection and working-projection review;
- personal sonic-language editing;
- journey storyboard review and approval;
- generation capability, resource, progress, warning, and cancellation views;
- deliberate audio playback with persistent stop controls;
- immediate and later response capture;
- canonical restart recovery and an explicit later-aftereffect capture intent.

Inspectable history, provenance export, personal-learning proposals, packaged
worker discovery, and real-model generation remain later issues.

It must not own canonical consent policy, session transitions, model behavior,
storage semantics, scientific claims, or personal-model update authority. Those
belong to Rust domain/application ports and versioned contracts.

## Current permission boundary

The default Tauri capability grants only `core:default`. It does not grant shell,
sidecar, filesystem, network, notification, or model permissions. JavaScript
can call only the named Tauri commands registered by the Rust host. Rust opens
the local event store and launches the deterministic worker with a cleared,
explicit environment; packaged worker discovery and operating-system sandboxing
still require explicit implementation and review.

## Commands

From the repository root, use:

```sh
make mvp-bootstrap
make mvp-check
```

Run the complete desktop host after bootstrap with:

```sh
pnpm --filter @egohygiene/antidote-desktop tauri dev
```

Direct browser development remains available with `pnpm --filter
@egohygiene/antidote-desktop dev`, but the screen correctly reports that Tauri
is required because the webview never owns canonical session state.

The current desktop evidence establishes:

1. reviewed architecture and ADR boundaries;
2. shared schema validation in Rust, TypeScript, and Python;
3. pinned desktop and package-manager baselines;
4. a common synthetic fixture suite; and
5. a deny-by-default Tauri capability boundary;
6. keyboard-readable consent, journey, generation, playback, response, and
   adverse-event controls; and
7. refresh/restart recovery from the SQLite event record.

The provisional developer platform matrix is documented in
[`../../docs/mvp-toolchains.md`](../../docs/mvp-toolchains.md).
