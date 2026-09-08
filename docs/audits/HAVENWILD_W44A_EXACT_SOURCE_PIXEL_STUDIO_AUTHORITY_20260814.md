# Havenwild W44A — Exact-Source Pixel Studio Authority

**Pass:** Pass167Z109W44A  
**Date:** 2026-08-14  
**Baseline:** Pass167Z109W43D on the user's authoritative W40 rollup  
**Status:** Source/static validation PASS; Windows Rust runtime acceptance pending.

## Purpose

W44A closes the editor workflow gap where `Edit source in Pixel Studio` opened a complete atlas/source sheet and merely selected a region. World assets now open as an exact cropped source-region document while retaining immutable upstream provenance.

## Implemented authority

- `PixelDocumentMetadata.source_region` records the exact immutable upstream rectangle with backward-compatible `serde(default)` handling.
- `PixelDocument::load_source_region` validates and crops the requested region into a standalone editable working document.
- Save remains non-destructive: the working copy is written under the Havenwild Pixel Studio derived-output lane rather than overwriting LPC/licensed source files.
- `reset_to_source_region` rebases the derived document to the exact upstream rectangle.
- Scene right-click context now hit-tests the Objects layer independently from terrain and retains the selected `ObjectId`.
- Published object source resolution follows the canonical `PublishedWorldAssetRegistry` persistent ref/legacy adapter and requires reviewed provenance `source_path + source_rect`.
- Terrain and object editing converge on one `open_resolved_world_asset_source` path.
- Missing/rejected/unreviewed objects fail closed instead of opening generated runtime atlases as if they were source authority.
- Exact-source documents disable the atlas grid and frame only the cropped document.
- Pixel Studio keeps three distinct operations: **Save Working Copy**, **Publish Slice Draft**, and contextual **Reset Source**.
- Save/return no longer requests a runtime hot reload for an unpublished derived copy. The UI states that runtime binding remains unchanged until Publish → approve → Bake + Reload.

## Validation

`tools/automation/validation/checks/editor/Validate-ExactSourcePixelStudioAuthorityV1.py`

Registered gate: `editor.exact-source-pixel-studio-v167z109w44a`, order 342, profiles `source/full`.

Root build command:

```text
tools\build\Build.cmd exact-source
```

Project Control Center entry:

```text
36. Validate exact-source Pixel Studio authority
```

## Remaining W44 work

W44A intentionally does not silently replace a published runtime binding when a derived copy is saved. A future published-override/promote step may streamline exact-asset replacement, but it must target the exact `PublishedWorldAsset` identity rather than fall back to generic `ObjectKind` targeting.

The next production roadmap milestone remains W45 structural component certification unless W44 runtime acceptance exposes a concrete issue.
