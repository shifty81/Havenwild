# Project control

PowerShell control-center implementation and command registry.

## Root-drop incremental update authority

Havenwild uses one normal incremental-update workflow:

1. Place an unextracted `Havenwild_IncrementalPatch_*.zip` in the repository root.
2. Run **Build & Verify > Full quality gate**.
3. The quality gate validates the patch manifest and hashes, transactionally backs up overwritten/removed files, applies the patch, verifies the resulting files, archives the consumed transport under `artifacts/updates/applied`, and only then continues into root audit, build, tests, and the debug bundle.

`AuditRoot.ps1` is intentionally side-effect free. Packaging, baseline capture, and standalone diagnostics may call it without applying patches.

`PackageProject.ps1 -Mode patch` emits the same root-drop `havenwild.root_patch.v1` transport format. Complete source rollups and other packages use the reliable Python ZIP staging helper rather than Windows PowerShell `Compress-Archive`.

## GitHub / source-control authority

`HavenwildTools.cmd` exposes **GitHub / source control** as a first-class menu. `tools/control/GitSourceControl.ps1` owns the project-specific Git operations for `https://github.com/shifty81/Havenwild.git`.

The intended workflow is:

1. Use **GitHub / source control > Initialize / connect this working folder** once. This initializes Git in the existing Havenwild folder; it never reclones over or moves the local project.
2. Continue using the normal root-drop patch workflow.
3. Run **Full quality gate**. A successful gate writes `.havenwild/last-green-quality-gate.json` with a fingerprint of the exact Git working tree that passed.
4. The control center offers **Commit and push this verified checkpoint to GitHub now?**. The protected Git actions refuse to commit if the working tree changed after the green gate.
5. The GitHub Core policy rejects heavy art/audio/model/font/source-asset payloads, local history, builds, logs, saves, and other external-pack content even if someone accidentally tries to stage it.

Pulls are `--ff-only`; the control center never auto-stashes, force-pushes, rebases, resets over local work, or silently resolves diverged history.
