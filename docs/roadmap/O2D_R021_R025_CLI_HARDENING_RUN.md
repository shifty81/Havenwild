# O2D-R021–R025 CLI Hardening Run

Prerequisite: O2D-R020H13.

This cumulative overwrite-capable patch advances the CLI-first Cortex lane through:

- R021: canonical CLI help + quick/full doctor
- R022: LM Studio model-role routing
- R023: tool introspection/certification/safe smoke tests
- R024: durable cross-process source transactions
- R025: grounded tool evidence + persisted inspection provenance

The top-level Open2DTools menu remains compact. New operations are grouped under
the existing Cortex submenu.

This patch has not been compiled in the assistant environment. Apply it over the
working H13 source and run the existing full Cortex checkpoint. The checkpoint
will rustfmt the changed Rust files, run builds/tests/Clippy, and synchronize
SOURCE_MANIFEST.json as O2D-R025.
