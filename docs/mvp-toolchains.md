# MVP toolchains and support boundary

## Status

This document records the reproducible developer baseline established through
issues #9–#15. It does not resolve the open decision about end-user
operating-system or GPU support and does not claim a distributable application.

## Pinned toolchains

| Boundary | Baseline | Authoritative pin |
| --- | --- | --- |
| Rust | `1.97.1`, edition 2024, Clippy, rustfmt | `rust-toolchain.toml`, `Cargo.lock` |
| Node | `24.19.x` | `.node-version`, package `engines` |
| pnpm | `11.19.x` | root `packageManager`, `pnpm-lock.yaml` |
| Python | `3.12.13` | worker `.python-version`, `pyproject.toml` |
| uv | `0.11.33` | CI workflow; worker `uv.lock` pins packages |
| Tauri | Tauri 2 Rust/JavaScript packages | Cargo and pnpm lockfiles |

All direct language dependencies use exact or bounded versions and all three
package graphs are committed as lockfiles. Bootstrap does not select or
download an audio model.

## Developer platform matrix

| Platform | Foundation status | Boundary |
| --- | --- | --- |
| Ubuntu 24.04 x86_64 | CI validation platform | Rust crates, Tauri host compilation, frontend build/tests, Python tests |
| macOS 14+ on Apple silicon | Provisional maintainer development target | Requires the standard Tauri prerequisites and local validation before release evidence |
| Windows | Not yet verified | No support claim until a checked workflow and recovery evidence exist |
| GPU or model-specific hardware | Out of scope for this foundation | Issue #19 owns measured candidate evaluation |

The matrix describes development evidence only. Minimum end-user OS versions,
packaging, signing, GPU/CPU tiers, and audio-device behavior remain open
decisions.

## Desktop and process capability baseline

The default capability still grants only `core:default` to the main window. The
webview does not launch the worker, so it receives no shell, sidecar,
filesystem, URL, notification, network, or model permission. The implemented
Rust adapter owns the explicit executable, argument vector, cleared
environment, working directory, output-root grants, message bounds,
cancellation, timeout, stderr draining, cleanup, and restart policy.

This is process supervision, not an operating-system sandbox or a packaged
Tauri sidecar. Desktop command composition and release packaging must preserve
the Rust-owned boundary without granting general process execution to the
webview.

## Bootstrap and recovery

Use `make mvp-bootstrap` to restore lockfile-backed dependencies and
`make mvp-check` to run the complete gate. Task provides equivalent
`mvp:bootstrap` and `mvp:check` commands.

If dependency restoration is interrupted, remove only the generated local
directories below and rerun bootstrap:

- `target/`;
- `node_modules/`;
- `apps/desktop/dist/`; and
- `workers/generation/.venv/`.

Do not delete or regenerate canonical schemas, fixtures, manifests, architecture
documents, research source, or lockfiles as a recovery shortcut.

## Explicit exclusions

- no PyTorch or model-specific dependency;
- no model weights, network inference, or telemetry;
- no private journal, therapy, participant, health, credential, or generated
  audio data;
- no database access from the worker, personal history, desktop composition,
  packaged sidecar, playback, or adaptation; and
- no clinical, efficacy, mechanism, CPU-only, or GPU support claim.
