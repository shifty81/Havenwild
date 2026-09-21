# Havenwild B48R28C16R1 — complete source, independent Windows test folder

## What this archive actually contains

- **Complete source test rollup**, constructed from `Havenwild_FullSourceRollup_PassB48R26_20260919.zip` (SHA-256 `1aa8290ebe482ba352f493ca7f0253efbfaaa889b173081f23a261b34aa61992`) plus every validated file in cumulative `B48R28C16` (SHA-256 `63c869b2da10a0a606408c18c9984f1ded63086e7e1c51bf649737667268cf5b`). This is NOT a root-drop PCC patch. Do not drop the full-source ZIP into an existing project root for update intake.
- B48R26 base ZIP: 9,724 files; C16 patch: 51 files, all manifest SHA/lengths verified, zero declared removals; 3 pre-existing source files changed by overlay, 43 paths added, 5 identical. The union was 9,767 files **before** handoff-specific additions/exclusions.
- Excluded from this clean test handoff: 19 historic `.forgepy/state/` files and 1 `.forgepy/cache/` file from the R26 archive, to avoid copying old machine-local certification receipts or cached scans. Kept remaining project content, authoring documents and other source files. Python test-generated `__pycache__` is excluded.
- Includes the original **user-supplied** `Terrain.zip` in `tools/handoff/dependencies/`, unchanged at SHA-256 `bcf551ecdaa6c352b72668e8087ebd9934b896dc1c45b2b5252abef76c932309`, including `Terrain/Credits.txt`. It is a credited, source-exact **test input**, not an approved terrain mapping or a complete installed ElizaWy/LPC dependency checkout.
- B48R28C16R1 makes ONE source-safety correction beyond C16: `experimental` Full Quality Gate now fails if the Bevy candidate's Cargo.toml is absent, instead of silently skipping the candidate. An additional test checks this contract. **The standalone R16 cumulative patch previously delivered is not modified by this rollup.**
- Historical Git baseline for test copy: `experimental` B48R28C4 GREEN, commit `d9c01b26ec2440f97fc1f6167ee561bc6d43e86e`. This ZIP intentionally does not ship `.git` history or `.havenwild` machine-local GREEN records.

## New folder: step-by-step (recommended)

1. Close live Havenwild editor/client and leave the original `C:\Users\Shifty\Desktop\Havenwild` folder unchanged. Create a separate **empty** directory, for example `C:\Users\Shifty\Desktop\Havenwild-C16-Test`.
2. Extract THIS entire ZIP into that empty directory so `HavenwildTools.cmd`, `Cargo.toml`, `tools/`, `content/`, and `experiments/` are directly in the directory (no additional nested folder).
3. In PowerShell, run:

   ```powershell
   & 'C:\Users\Shifty\Desktop\Havenwild-C16-Test\tools\handoff\Initialize-ExperimentalTestCopy.ps1' -Root 'C:\Users\Shifty\Desktop\Havenwild-C16-Test'
   ```

   If the machine's execution policy blocks local scripts, use `powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'C:\Users\Shifty\Desktop\Havenwild-C16-Test\tools\handoff\Initialize-ExperimentalTestCopy.ps1' -Root 'C:\Users\Shifty\Desktop\Havenwild-C16-Test'`.

4. The bootstrap checks **every packaged file's hash**, verifies the included `Terrain.zip`, initializes **Git only inside the new directory**, fetches the actual remote experimental history, and sets `HEAD` to pinned C4 using **`git reset --mixed`**. It DOES NOT checkout or hard-reset the C16R1 worktree. It then stages exact source image+credits in the candidate's ignored staging directory only.
5. Run the new folder's `HavenwildTools.cmd`, select **1 FULL QUALITY GATE**. This requires project dependencies, Windows Rust/Cargo and may download many crates. It now must perform the candidate Python tests + Cargo check and block any compile failure. If FAIL, retain the generated debug ZIP and build log. Do not commit/push a failure.
6. Run **4 Run & Play → Bevy candidate** separately. A successful `cargo check` is not proof that the Bevy GUI launched, graphics are correct, or actual PIE is wired. Inspect the original atlas, *UNAPPROVED GPU DRAFT* river view, semantic view and activity diagnostics and capture a screenshot.
7. Use **2 COMMIT+PUSH only if and when you want to publish the new folder's certified result**. This script does not commit or push anything. The new directory and the original directory share the remote; do not push independently if the remote has advanced without first reconciling.

**Alternative (already familiar):** `git clone --branch experimental https://github.com/shifty81/Havenwild.git Havenwild-C16-Test` into an empty folder, then extract this full-source ZIP **over that new clone**. Do not run `Initialize-ExperimentalTestCopy.ps1` in an existing clone. The ZIP includes the original test Terrain archive in `tools/handoff/dependencies`; for manual cloning, stage it with `python experiments/haven_bevy_candidate/tools/prepare_source.py --terrain-zip tools/handoff/dependencies/Terrain.zip` before candidate Verify or use the PCC Build/Run with `HAVENWILD_BEVY_TERRAIN_ZIP` pointed at that archive.

## Verification performed in the authoring environment

- Both input archives passed ZIP integrity; cumulative patch manifest paths were safe, unique and SHA-256/byte-length exact; no Windows-case-insensitive collisions in the merged files; original B48R26 archive SHA matched the previously recorded rebase receipt.
- `experiments/haven_bevy_candidate/tests`: **86 passed** after the one-line Full Gate safety repair. The three architecture suites (`test_elizawy_draw_plan_boundary`, `test_engine_convergence_contract`, `test_parallel_migration`) also passed. Mapper B48R26/B48R27 unit tests: **7 passed**. Python bytecode compilation passed.
- The actual `tools/validation/Validate-HavenwildBevyCandidate.py` entrypoint correctly **refused the extracted archive without Git lineage**. That is why a real new-folder Git bootstrap is included rather than weakening candidate lineage verification.
- No Rust toolchain, PowerShell runtime, Windows D3D/WGPU device or project dependency mounts were available for a real local build here. **NOT verified:** full Windows PCC gate for C16R1, Rust compile, Bevy GPU execution/GUI, certified source-exact ElizaWy recipes, true PIE, multiplayer, Macroquad retirement or end-to-end asset/editor parity. Historical river atlas assignments remain explicitly UNAPPROVED; no source art was regenerated.
- The published C4 commit's 3-commit Git ancestry from B48R26 was checked through GitHub; all its *added* paths were present in the overlay, and its modified PCC files were overlaid. A complete Git tree/blob equality comparison against the ZIP was not performed; content produced from full R26 rollup plus cumulative changes is a **full source reconstruction**, not a dump of a clean C16 Git tree.

## Interpreting the user's current PCC error

`FAIL: Governed source changed after the last GREEN Full Quality Gate` is a correctly enforced certification safeguard. It is expected when C16 modifies source after the C4 green marker. Do **Full Quality Gate** before Commit+Push; do not reset or bypass fingerprints. If the gate fails, use the debug bundle. The new test folder starts from pinned C4 ancestry with C16R1 as uncommitted working tree and must pass its own fresh gate. Neither source packaging nor manifest verification grants GREEN status.

## Remaining concrete issues

Candidate's `Cargo.lock` is intentionally Git-ignored and missing from the ZIP; Cargo will resolve its dependencies on the first Windows run. The actual resolved lock must be reviewed and incorporated into a governed dependency policy before fully reproducible builds are claimed. Existing project-owned ElizaWy mapping approval is still incomplete; the candidate's 1,120 original-pixel river cells are historical unapproved draft assignments. The root Full Gate now checks the candidate's Cargo check, but does not replace a GPU/runtime screenshot/PIE check. The `tools/handoff/dependencies/Terrain.zip` test input does **not** replace the rest of the pinned LPC corpus needed by the original game's full build; hydrate that through Havenwild's existing dependency/Vault workflow as required.
