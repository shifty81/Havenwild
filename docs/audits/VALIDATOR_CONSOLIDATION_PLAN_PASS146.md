# Validator Consolidation Plan — Pass 146

## Objective

Replace the Pass 145 hotfix chain with durable behavior and build-contract validation. A validator may protect a public contract, structured manifest, migration path, generated-output dependency, or executable behavior. It must not permanently freeze private helper names, atlas coordinates, incidental source strings, or one historical build version.

## Decisions

- Keep current domain validators that protect live contracts.
- Move all generator tasks into the explicit `generation` profile.
- Remove Pass 145A–145O compatibility validators from active profiles and archive their manifest records.
- Add seven consolidated Pass 146 validators covering packaging, generated assets, Windows portability, save migration, shoreline behavior, Rust workspace structure, and validator quality.
- Require clean source archive extraction validation before a release rollup is promoted.

## Build profiles

- `quick`: contract-only architecture/content/world checks.
- `generate`: required derived asset generation.
- `validate-source`: validators only; no generators.
- `validate-generation`: explicit manifest-registered generators.
- `test`: Rust workspace tests.
- `all`: generation, source validation, formatting, check, Clippy, tests, smoke build, catalog, web checks, and packaged applications.
- `clean-rollup`: create, extract, and validate the actual archive.
- `catalog-lpc`: explicit full LPC catalog rebuild.

## Completion gate

Pass 146 is complete only when the produced archive passes `Validate-CleanSourceBuildV146.py` and a Windows extraction passes `tools/build/Build.sh all` without manual source repair.
