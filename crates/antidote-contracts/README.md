# antidote-contracts

Executable Rust projection of Antidote's canonical JSON Schemas.

`scripts/generate_contracts.py` owns `src/generated.rs`; edit the schemas or
manifest and regenerate rather than changing that file directly. The crate
embeds canonical schema source at compile time, validates JSON Schema Draft
2020-12 formats, and runs the same synthetic fixture suite as TypeScript and
Python.

This crate owns interoperability shape, not consent policy, session behavior,
model semantics, or scientific interpretation.
