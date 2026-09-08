# Pass 167Z10 — Development normalization report

## Outcome

Havenwild now has one supported root launcher, one internal build lane, one current validation registry, domain-owned automation, Windows-safe paths, and an explicit separation between current development tooling and historical pass checks.

## Root contract

The only root files are:

- `.gitignore`
- `Cargo.lock`
- `Cargo.toml`
- `HavenwildTools.cmd`
- `README.md`

`HavenwildTools.cmd` is the only human-facing root launcher.

## Tooling layout

- `tools/build/` — internal build and run implementation.
- `tools/control/` — the Windows project control center.
- `tools/automation/<domain>/` — generators and maintenance scripts owned by a specific domain.
- `tools/automation/validation/` — current validation framework and active entrypoints only.
- `tools/automation/validation/checks/<domain>/` — historical/pass-specific diagnostic checks.
- `tools/archive/legacy_pass_tools/` — retired command wrappers.
- `archive/source/legacy_cpp_shell/` — unreferenced legacy C++ shell source.

Automation file counts:

- `archive/`: 3
- `assets/`: 17
- `characters/`: 13
- `common/`: 1
- `dependencies/`: 1
- `packaging/`: 2
- `project/`: 4
- `release/`: 2
- `reports/`: 4
- `terrain/`: 24
- `validation/`: 356
- `worldgen/`: 12

## Validation normalization

- Active V3 validators: **19**.
- Compatibility tasks: **20**.
- Historical pre-normalization registry and manifest are retained under `manifests/validation/legacy/`.
- Current profiles are `quick`, `source`, and `full`.
- `full` adds Cargo format, check, Clippy, and tests.
- Generated-output/source-rollup Pass 146 checks that depend on the inherited missing cave source are no longer ordinary build gates.
- Direct LPC terrain authority replaced obsolete mapped-atlas performance/structural-rock checks in the current terrain contract.

## Known development debt

- Twelve large Rust modules remain under explicit size allowances with lower extraction targets in `docs/audits/PASS167Z10_ARCHITECTURE_DEBT_MATRIX.md`.
- Rich editor command execution metadata is declared but not yet represented as Rust types; the command bus is marked transitional instead of falsely certified complete.
- `assets/source/original/cave_entrance_96.png` remains absent from the inherited baseline. Current active validation does not pretend the file exists.
- Rust compilation still requires the local Windows Rust toolchain.

## Packaging rule

Pass 167Z10 complete source is the authoritative cumulative baseline. Future patches should target this baseline and preserve the machine-readable lineage under `manifests/`.
