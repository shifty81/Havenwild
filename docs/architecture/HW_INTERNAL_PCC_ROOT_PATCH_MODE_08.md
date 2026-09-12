# HW-INTERNAL-PCC-ROOT-PATCH-MODE-08

This pass restores Havenwild-first standalone project control while ForgePY/Cortex integration is being normalized externally.

## Temporary operating model

Havenwild owns its local Project Control Center again as the active day-to-day authority:

1. Drop pending Havenwild patch transports into the repository root.
2. Launch `HavenwildTools.cmd`.
3. The internal PCC scans the root and prompts before applying each pending patch.
4. Option `1` runs the Full Quality Gate and certifies GREEN.
5. After runtime/editor testing, option `2` commits and pushes the last certified GREEN state to GitHub.

ForgePY remains a future universal front end, but Havenwild must stay independently buildable, patchable, certifiable, and publishable through its project-owned PCC.

## Supported root transports

The internal PCC recognizes the legacy root ZIP transports plus text Git unified diff `.patch` transports:

- `Havenwild_IncrementalPatch_*.zip`
- `Havenwild_Patch_*.zip`
- `Havenwild_Handoff_*.zip`
- `Havenwild__*.patch`
- `HW-*.patch`

ZIP transports keep the existing `PATCH_MANIFEST.json` overwrite authority. Text `.patch` transports are checked with `git apply --check` before they are applied.

## Cumulative payload

This bootstrap also plants the current Assets Studio recovery patch in the repository root so the updated internal PCC can apply it on the restarted gate pass.

Included cumulative patch:

- `Havenwild__20260912__HW-ASSET-STUDIO-RECOVERY-07.patch`

That patch keeps Assets Studio honest and recoverable when `artifacts/asset-intake/asset-catalog.json` is malformed, without inventing replacement assets.
