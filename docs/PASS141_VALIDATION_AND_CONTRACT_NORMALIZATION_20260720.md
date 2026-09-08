# Pass 141 — Validation and Contract Normalization

## Decision

Havenwild now uses a manifest-driven validation system as the permanent project structure.
New passes must register validators and prerequisite generators in:

`content/validation/validation_manifest_v1.json`

Directly appending long validator lists to `tools/build/Build.sh`, `tools/build/Build.ps1`, or `tools/automation/validation/validate.py` is deprecated.

## Authoritative entry points

- `./tools/build/Build.sh validate-quick`
- `./tools/build/Build.sh validate-source`
- `./tools/build/Build.sh validate-full`
- `python tools/automation/validation/validation_runner.py source`
- Legacy `./tools/build/Build.sh validate [domain]` remains compatible.

## Profiles

- **quick**: architecture, content, and world contract validators.
- **source**: all manifest-registered validators and prerequisite generators.
- **full**: source profile plus Cargo format, check, Clippy, and workspace tests.

## Required registration fields

Every task requires a stable ID, name, domain, phase, kind, command, required flag, enabled flag, and unique order.
Optional dependencies must be declared through `requires` and `required: false`; required production contracts must never be silently skipped.

## Reports

Every run writes:

- timestamped JSON report;
- timestamped Markdown report;
- `logs/validation/latest.json`;
- `logs/validation/latest.md`.

Reports use `havenwild.validation.report.v1` and normalize passed, failed, and skipped states.

## Contract restoration

The production tile-extraction workbench contract was restored from the project crate pack:

`content/assets/tile_extraction/tile_extraction_workbench_contract_v0_1.json`

It remains required because active GUI and LPC authored-role validators reference it.

## Future-pass rule

A pass is not complete until its validator is registered in the manifest and the Pass 141 normalization validator passes.
