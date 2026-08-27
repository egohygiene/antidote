# Antidote desktop application

## Status

Executable workspace scaffold. Tauri 2, React, TypeScript, Vite, linting,
formatting, tests, and the canonical-schema validator are pinned and built. The
visible screen reports this limited state; no session behavior is implemented.

## Ownership

This directory owns the Tauri 2 desktop host and React interaction layer. Later
issues add:

- moment check-in and desired-transition capture;
- consented-context selection and working-projection review;
- personal sonic-language editing;
- journey storyboard review and approval;
- generation capability, resource, progress, warning, and cancellation views;
- deliberate audio playback with persistent stop controls;
- immediate and later response capture;
- inspectable history, provenance, and personal-learning proposals.

It must not own canonical consent policy, session transitions, model behavior,
storage semantics, scientific claims, or personal-model update authority. Those
belong to Rust domain/application ports and versioned contracts.

## Current permission boundary

The default Tauri capability grants only `core:default`. It does not grant shell,
sidecar, filesystem, network, notification, or model permissions. Those
capabilities require explicit implementation and review in later issues.

## Commands

From the repository root, use:

```sh
make mvp-bootstrap
make mvp-check
```

Direct frontend development is available with `pnpm --filter
@egohygiene/antidote-desktop dev` after bootstrap. Browser preview falls back to
an honest `browser-preview` status when the Tauri IPC host is unavailable.

The completed bootstrap gate established:

1. reviewed architecture and ADR boundaries;
2. shared schema validation in Rust, TypeScript, and Python;
3. pinned desktop and package-manager baselines;
4. a common synthetic fixture suite; and
5. a deny-by-default Tauri capability starting point.

The provisional developer platform matrix is documented in
[`../../docs/mvp-toolchains.md`](../../docs/mvp-toolchains.md).
