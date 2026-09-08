# Havenwild validation

Havenwild validation v4 separates current development gates from historical certification so old pass machinery cannot silently become a normal build dependency.

## Current authority

- Registry: `content/build/validator_registry_v4.json`
- Profile policy: `content/build/validation_profiles_v4.json`
- Aliases/deprecations: `content/validation/validator_aliases_v1.json`
- Runner: `tools/automation/validation/validation_runner.py`
- Stable local/CI wrapper: `tools/automation/validation/check_current.py`

The v4 registry is a thin overlay over `validator_registry_v3.json`. The v3 registry remains preserved as historical/full-certification evidence; v4 strips its `build`, `quick`, `source`, and `framework` memberships and explicitly assigns current authorities. New validators therefore do not require rewriting or deleting the historical registry.

## Profiles

- `build` / `quick` — **2 lightweight gates**: repository/development layout and Havenwild-owned content parsing.
- `source` — **10 current-authority gates**. This is intentionally bounded and clean-checkout reproducible.
- `framework` — **4 current framework gates**.
- `full` — explicit historical/subsystem certification plus Cargo fmt/check/Clippy/tests. It is never an implicit normal build gate.

## Source authority checks

The ten source checks cover repository layout, architecture, owned content parsing, content integrity, the validation framework contract, required runtime-media publication, evidence/receipt policy, transactional root patch intake, CI/check entrypoints, and validation documentation/legacy quarantine.

## Historical checks

Pass-specific validators remain under `tools/automation/validation/checks/` and historical manifests/evidence remain in their existing archive/manifests locations. They are preserved for diagnosis and explicit `full` certification but are not live build/source/framework authorities.
