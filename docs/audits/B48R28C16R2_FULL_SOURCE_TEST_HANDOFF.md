# Havenwild B48R28C16R2 — full-source independent test handoff

This archive supersedes the C16R1 full-source TEST archive for fresh-folder testing. It is a complete source reconstruction and **not** a root-drop PCC patch. It is assembled from the earlier verified B48R26 source and cumulative C16 development plus R1 mandatory experimental gate and R2 journal validation repair. The source has not been Windows-built or PCC-certified in this authoring environment.

## What was fixed after the actual Windows debug bundle

The user's `Havenwild_DebugBundle_20260920-004653_MANUAL.zip` documents a Full Gate failure: 86 experimental candidate tests ran with one failed assertion (`test_replay_tamper_rejected`) and seven skipped; source validation separately passed 10/10 and the normal client/editor build completed. The tamper test expected a journal-specific diagnostic but hit the document hash diagnostic first. R2 checks replay chronology first and *also* always checks document hash and replayed content before accepting a session. Three additional independent tamper tests guard that sequence. See `docs/audits/B48R28C16R2_WINDOWS_CANDIDATE_GATE_JOURNAL_REPAIR.md`.

## Fresh-folder setup

1. Choose a **new empty** folder (for example `C:\Users\Shifty\Desktop\Havenwild-C16R2-Test`) and extract this full-source archive into it. The root must directly contain `HavenwildTools.cmd`.
2. Run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\Shifty\Desktop\Havenwild-C16R2-Test\tools\handoff\Initialize-ExperimentalTestCopy.ps1" -Root "C:\Users\Shifty\Desktop\Havenwild-C16R2-Test"`.
3. The bootstrap checks the R2 full-source manifest, checks the included original Terrain ZIP, creates Git history from the pinned C4 experimental commit using `git reset --mixed` **without overwriting the R2 working files**, and stages the original art only into ignored candidate space.
4. Run `HavenwildTools.cmd` in **that folder** → 1 FULL QUALITY GATE. If PASS, try 4 Run & Play → Bevy candidate (listed under Run & Play). Do not commit/push until the new folder has a current GREEN gate and you deliberately intend to publish it.
5. If any new Rust compile, environment, or GPU issue occurs, retain the PCC-generated debug ZIP. Do not assume the earlier one-test failure was the only remaining issue.

## Existing Havenwild folder instead

Use the **B48R28C16R2 cumulative PCC patch**, not this complete-source archive. It preserves C16, carries forward the R1 fail-closed missing-candidate guard, and applies the R2 journal/test fix through normal PCC intake. Do not apply the older C16 patch over R2.

## Source and certification boundary

This test archive retains the previously included, attributed original `Terrain.zip`, preserves the earlier documentation, and records its own SHA-256 per-file manifest. The archived C16R1 manifest describes the historical prior source snapshot and is not the authority for R2 verification. The active verifier is `tools/handoff/Verify-FullSource.py`, bound to `B48R28C16R2_FULL_SOURCE_FILE_MANIFEST.json`.

This package is **source-integrity checked only**. There is no verified C16R2 Windows Full Quality Gate, Bevy GPU screenshot/renderer parity, approved ElizaWy river assignment, true PIE or Macroquad retirement. The candidate Cargo.lock is currently an ignored machine-local output, not a published dependency lock. `Terrain.zip` is only the original terrain test input, not the entire dependency corpus for all game systems.
