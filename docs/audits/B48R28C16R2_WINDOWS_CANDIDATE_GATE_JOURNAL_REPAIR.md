# Havenwild B48R28C16R2 — Windows experimental candidate gate repair

## Evidence and exact failure

Input: `Havenwild_DebugBundle_20260920-004653_MANUAL.zip`, containing the failed Full Quality Gate session `20260920-003752` and candidate contract test log `20260920-004041`.

The main client/editor Cargo build completed successfully, the main Cargo test log reported passing results, and the unified source validation report recorded ten passes, zero failures and zero skips. The *overall PCC Full Quality Gate failed*: experimental Bevy candidate infrastructure tests ran 86 tests and reported one failure, seven skips. The failed test `test_replay_tamper_rejected` expected `Journal replay mismatch`; `verified_session` raised `Session document hash changed without a command` instead. The log does NOT establish a real Bevy launch, visual parity, or an independently successful candidate Cargo check: reported temporary Cargo exit values are test fixtures, not a production candidate run.

## Repair and safeguards

`experiments/haven_bevy_candidate/tools/experiment_spine.py`: after structural validation and command-ID checking, replay the journal *before* comparing document SHA-256, then compare the hash, then compare document to replayed state. Neither check is removed or relaxed. Corrupt journal history produces a stable chronology diagnostic even when the document hash also disagrees.

`experiments/haven_bevy_candidate/tests/test_experiment_spine.py`: preserve the original journal-tamper test and add independent checks for a corrupted journal plus corrupted hash, hash-only tampering, and a forged modified document with a recomputed matching hash. All cases must be rejected.

No renderer, source sheet, approvals, scene fixture, production saves, Macroquad systems, or published game systems are changed. The protected main gate is unchanged. The C16R1 fail-closed mandatory-candidate check is retained in the full-source handoff and carried into the cumulative patch's PCC file.

## How to use

- Existing experimental folder: apply the **C16R2 cumulative PCC patch** through the existing PCC instead of older C16/C16R1 artifacts. Run the Full Quality Gate again. Commit + Push only after its new GREEN result; no bypass of governed source fingerprints.
- Separate fresh test folder: extract the **C16R2 complete-source test archive** into a *new empty folder* and run `tools/handoff/Initialize-ExperimentalTestCopy.ps1`. Never root-drop the full source archive into PCC update intake.
- The R2 ZIP is source-verified only. A Windows rerun of C16R2, its mandatory candidate Cargo check, GPU preview, visual review, and PIE are not claimed here.

## Residual findings from the supplied bundle

- The manual debug-bundle STATUS recorded `Baseline: Missing` and `Git: Modified`; these are distinct from the journal-test failure and not repaired by this narrow change. Keep the previous C4 GREEN as the historical checkpoint until the current source passes a new gate.
- The candidate `Cargo.lock` was absent in temporary test fixtures; a generated ignored lockfile is not a committed reproducible dependency lock.
- An unapproved 1,120-cell historical ElizaWy draft is not an approved recipe or runtime parity result.
