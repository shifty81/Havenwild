# Havenwild Project-Wide Normalization Audit — Pass 162H

## Repository snapshot

- Total source/package files: 1771
- Root files after cleanup: 9
- Historical validator scripts still present: 317

## KEEP

- Rust workspace and game/editor crates.
- Canonical `tools/build/Build.cmd`, `tools/build/Build.ps1`, and `tools/build/Build.sh` entry points.
- Consolidated `tools/automation/validation/validate.py` validation authority.
- Current LPC dependency acquisition and asset/catalog generation lanes.
- Native editor shared UI normalization work.

## REWRITE / CONSOLIDATE

- Remaining pass-specific validators must continue migration into domain checks under the consolidated validator.
- Root build commands should eventually route through one command registry shared by the menu and build scripts.
- Package generation needs persistent baseline manifests for non-Git incremental patches.
- Editor drawing and hit testing still need shared interactive component ownership.
- Logging paths and result summaries should be normalized across Bash and PowerShell.

## MOVE / ARCHIVE

- Pass handoffs and audit documents moved under `docs/`.
- Patch manifests, inventories, and provenance moved under `manifests/`.
- Obsolete one-off root scripts moved under `tools/archive/legacy_pass_tools/`.

## DELETE LATER

- Archived historical validators only after their meaningful checks are represented in consolidated native/domain validation.
- Duplicate historical pass documentation after retention policy and archive index are verified.

## NEXT

1. Consolidate remaining root/build command duplication.
2. Continue validator retirement by behavior, not source-string compatibility.
3. Normalize object/stamp/autotile/island editor inspectors.
4. Add package baseline manifests and explicit removal application.
5. Run `tools/build/Build.cmd all` on Windows and address the first concrete failure only.

## File types

- `.md`: 617
- `.py`: 341
- `.json`: 331
- `.rs`: 269
- `.ps1`: 66
- `.png`: 44
- `.txt`: 44
- `.pyc`: 17
- `.toml`: 14
- `.cmd`: 4
- `.csv`: 4
- `.sh`: 4
- `.tsx`: 3
- `.diff`: 2
- `.gz`: 2
- `.css`: 1
- `.html`: 1
- `.js`: 1
- `.lock`: 1
- `.log`: 1
- `.mjs`: 1
- `.tmp`: 1
- `.tmx`: 1
- `<none>`: 1
