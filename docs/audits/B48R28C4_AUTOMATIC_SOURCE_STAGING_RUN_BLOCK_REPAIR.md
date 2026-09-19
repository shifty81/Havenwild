# B48R28C4 — Repair candidate Run BLOCKED: original source not staged

**Scope:** experimental lane only. Cumulative overwrite from GitHub B48R28B GREEN (`78ff838499015ff434dbd935ae5daf9cbd11a02e`), retaining all earlier series changes through C3. This is a patch, **not** a complete source rollup. Do not apply C1/C2/C3 in addition to this package.

## Reproduced user symptom

The PCC Full Quality Gate passed, then Run & Play → Bevy candidate: run isolated preview exited code 2: `Original source/credits/receipt are missing; stage Terrain.zip through prepare_source.py`. That gate runs on tracked source; this candidate's original source PNG, credits and receipt are deliberately untracked/ignored and were never hydrated by the Run command. The error occurred in Python preflight before Cargo or GPU startup; it does not establish a Bevy renderer failure.

## Source-verified correction

- `experiments/haven_bevy_candidate/tools/candidate_gate.py`: Run and Build alone now call `prepare_missing_inputs` ahead of `verify`. Status/Verify remain read-only; the candidate's existing scene/draft compiler and Cargo path remain unchanged.
- Source discovery is **bounded**: first the existing project-owned `assets/source/licensed/lpc_revised/Terrain`, then explicit `HAVENWILD_BEVY_TERRAIN_ZIP`, then a `Terrain.zip` already at the project root. No broad Downloads searches, silent network checkout, or second project authority.
- `experiments/haven_bevy_candidate/tools/prepare_source.py`: accept the existing project-owned original without requiring another ZIP, and pin both the summer PNG SHA-256 `1251a6ea556330190ccb1e3af166eb69fbec4b7a3f7d51c1f54728abd75bd752` and Terrain/Credits.txt SHA-256 `955d40a17e361fa2837d2af83917b07043ca078da096bd48c5b4a8c7004eebbf`. Before any staging writes, enforce Git experimental ancestry from B48R28B and reject symlink destinations. Preserve prior valid receipt provenance; refuse a conflicting/damaged receipt. Writes are candidate-local in ignored `assets/source` and `evidence` paths, never the original mount, canonical game saves, source authority, or user’s Terrain.zip.
- Add regression tests for automatic candidate Run preparation, read-only Verify, lane protection, missing-with-receipt, source tamper, verified installed source and credits tamper.

## PCC workflow after applying

1. Keep the current `experimental` branch. Drop **this unextracted cumulative C4 ZIP** into the Havenwild root, allow the existing PCC to apply it, and run Full Quality Gate. The patch retains the previous cumulative source paths rather than assuming C3 was published.
2. Run & Play → Bevy candidate: run isolated preview. When the project source dependency is installed, its original files will be staged transparently. Do not run the previous manual preparation step in that case.
3. If both installed source and root `Terrain.zip` are absent, the new error gives the exact missing location. Restore the existing ElizaWy dependency or explicitly run `py -3 experiments/haven_bevy_candidate/tools/prepare_source.py --terrain-zip "C:\\your\\original\\Terrain.zip"`. Do not use a generated atlas or unaudited lookalike.
4. If Rust/Cargo subsequently errors, provide the resulting **new** debug bundle: reaching Cargo proves the initial missing-stage blocker was cleared but does not prove a GPU launch.

## Claims and next gate

Only Python validation, original-byte/source-receipt staging, archive integrity and cumulative manifest checks can be performed in this environment. A GitHub commit named B48R28B GREEN exists; C4 has not passed Windows build, GPU, standalone Cargo, or PCC Full Gate here. C3 remains an **unapproved GPU draft**; no terrain art approval, world parity, PIE or Macroquad retirement is implied. Next work remains source-exact mapper recipe certification and shared draw-plan wiring, after a real candidate launch succeeds.
