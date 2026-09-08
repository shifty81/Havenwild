# Pass 146C Native Validator Migration

## Result

The active validation registry is reduced to 16 validators. Five domain validators now return native `ValidationResult` objects and own the legacy subchecks for terrain runtime, shoreline/water, terrain promotion, editor authoring, and world foundation/persistence.

## Read-only enforcement

The runner snapshots project-owned source files before and after every validator. A validator that mutates protected source content fails with `HWV-QUALITY-001`. Generated outputs, previews, logs, Cargo target output, and Python caches are excluded from the protected source snapshot.

## Migration model

Legacy validators are retained as internal subchecks during migration. They are no longer first-class active registry tasks. This keeps behavior coverage while eliminating independent scheduling, cascading failures, and pass-number-driven registry identity.

## Active target

- Registry: `content/build/validator_registry_v3.json`
- Active validators: 16
- Native validators: 6
- Maximum allowed active validators: 25
