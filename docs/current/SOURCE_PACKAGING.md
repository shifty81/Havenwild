# Havenwild Source Packaging Authority

## Packageable project outputs

`assets/generated/` contains reviewed runtime/editor generated assets and remains packageable when needed for exact visual/runtime reconstruction.

## Reproducible machine-local output

The following are not source authority and are excluded from future complete-source/ChatGPT rollups:

- `WORKSPACE/generated/`
- `WORKSPACE/test-output/`
- `WORKSPACE/saves/`
- `WORKSPACE/recovery/`

They are regenerated or recreated by dependency sync, asset-catalog, promotion, validation, test, editor, and save workflows.

The machine-readable contract is `content/architecture/generated_data_ownership_v0_1.json`.

## Cumulative patches and removals

A cumulative patch may need to normalize/remove paths that existed in the Pass167Z59 baseline or a later applied patch. Such packages include:

- `manifests/removals/PATCH_REMOVALS.txt`
- `APPLY_HAVENWILD_PATCH.cmd`

After extracting a cumulative patch, launch `HavenwildTools.cmd`. It attempts the guarded removal manifest automatically, but cleanup is deliberately nonfatal: if Windows refuses a removal or a helper is unavailable, the control center still opens and reports a startup warning. The manifest is retained for retry. `APPLY_HAVENWILD_PATCH.cmd` is the explicit retry path.

## External dependencies

Large pinned LPC dependency repositories remain reconstructable external dependencies and must not be duplicated in every source handoff.

## Cumulative patch removals

Cumulative patches may retire or relocate files.  Such packages carry a package-only
`manifests/removals/PATCH_REMOVALS.txt`.  On the next launch, `HavenwildTools.cmd`
attempts that manifest before opening the control center. Successful cleanup removes the
transport manifest and root-level helpers; failed cleanup leaves them in place and surfaces
a warning without terminating the control center.  This preserves the normal
five-file repository-root contract while allowing cumulative patches to converge an
older source tree without requiring users to chain historical incremental patches.



## Bootstrap files in patches

Every patch forcibly carries `HavenwildTools.cmd`, `tools/control/HavenwildTools.ps1`,
`tools/control/ApplyPatchRemovals.ps1`, and `tools/control/ProjectCommandRegistry.ps1`
even when those files are byte-identical to the captured baseline. A patch must always
carry the bootstrap chain required to apply and diagnose itself.
