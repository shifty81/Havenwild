# Pass 158A — Validator Consolidation

## Active build gates

1. `cargo fmt --all -- --check`
2. `cargo check --workspace --all-targets`
3. `cargo clippy --workspace --all-targets -- -D warnings`
4. `cargo test --workspace`
5. `tools/automation/validation/validate_content_integrity.py`

## Content-integrity scope

The Python validator checks only facts Rust compilation cannot establish:

- pinned LPC source lock, dimensions, and checksums;
- complete 32x32 LPC summer atlas inventory;
- seasonal source-sheet availability and topology counts;
- generated transition-atlas bounds and non-empty authored inner corners;
- open-world preset dimensions and semantic anchors;
- generated-output registry inputs, generators, and provenance sidecars.

## Historical validators

Older `Validate-*.py` and `Validate-*.ps1` files remain as archived implementation history. They are no longer active build gates. In particular, source-token checks for function names, enum variants, exact branch values, pass labels, and deleted renderer architecture are intentionally inactive.

## Policy

A new Python build gate must validate content, licensing, file integrity, or cross-file data relationships. Compiler behavior, API shape, runtime algorithms, and implementation details belong in Rust tests and Clippy.
