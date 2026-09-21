# B48R28C16R6 — Windows parallel-migration path repair

## Observed Windows result

In the `experimental` project, both the ForgePY dashboard **PCC FULL GATE** button and `HavenwildTools.cmd` call the same Havenwild-owned gate. The Windows run completed the root Rust `cargo check --workspace`, `cargo build --workspace`, `cargo test --workspace` and reached the experimental Bevy candidate infrastructure Python suite. Its `Parallel migration` group failed with `hw_parallel_migration.EvidenceError: Invalid relative path`; the full gate stopped, emitted a debug bundle and did not certify GREEN.

## Root cause and repair

`tools/architecture/parallel_migration.py` initially validates slash-delimited fixture paths using `safe_rel()`, then `compare_fixture()` converts the resulting platform-native `Path` with `str(...)`. On Windows that turns `source/asset.dat` into `source\asset.dat`. `existing_file()` deliberately rejects input containing backslashes, so a previously safe path fails revalidation. This is not a malformed original fixture.

`canonical_rel()` now validates with `safe_rel()` and uses `Path.as_posix()` for the internal receipt and subsequent `existing_file()` call. Original untrusted strings containing backslashes, `..`, absolute paths, drives or missing values remain rejected. Existing symlink/root-boundary and source-hash safeguards are unchanged. A regression mocks the Windows path representation and checks preserved rejection behavior.

## Workflow

This is a cumulative replacement of R5, NOT a full-source rollup and NOT a new PCC/ForgePY engine. Place **only R6** at the test repo root; use existing HavenwildTools.cmd root intake or the already updated R5 GUI's governed Apply via Havenwild PCC. Close/relaunch ForgePY after an update. Run **PCC FULL GATE** once; if it reaches Cargo/Bevy and fails again, send the new debug bundle. No commit/push before GREEN.

## Verification boundary

Local Python validation exercises the affected suite and additional candidate/architecture/mapper suites. ZIP manifest and predecessor preservation checks run on the delivered source. Neither the Linux environment nor the older Windows log proves the new patch compiled or passed the Windows PCC gate, GPU display, PIE, or asset/art certification.

## Architecture direction

Retain one Havenwild-owned PCC for validation, root intake and source publication. ForgePY is only a GUI/adaptor to those commands, not an independent second full gate. The native PCC CLI may be surfaced directly through the separate Cortex/Forge desktop orchestration later, avoiding project-local duplicate GUI maintenance. That architectural preference does not alter the current project's certified release rules.
