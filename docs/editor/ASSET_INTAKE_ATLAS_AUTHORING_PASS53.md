# Pass 53 — Asset Intake and Atlas Authoring

Pass 53 turns the Pass 52 warning-only asset lane into a project-owned authoring pipeline.

## Intake locations

- `assets/source/intake/` is the editor-scanned inbox for reviewed source images.
- `assets/source/original/` stores original Havenwild-owned source art.
- `assets/reference_quarantine/third_party/` remains isolated and is never scanned or promoted automatically.

The native editor's **Intake** tab scans the inbox and creates draft recipes in:

`content/assets/intake/asset_intake_catalog_v0_1.json`

## Recipe authoring

Each recipe owns a stable import ID, source rectangle, runtime target, pivot, visual/collision/interaction footprints, license declaration, acceptance flag, and promotion state. Runtime targets currently bind to canonical `TileKind` or `ObjectKind` entries, which removes the need to edit Rust atlas lookup tables for replacement or missing sprites.

## Promotion gate

A recipe cannot become Approved unless:

- its source stays under the approved source roots;
- the source file exists;
- the source slice and footprint sizes are valid;
- the runtime target exists;
- the license is project-owned, CC0, CC-BY, or explicitly approved third party;
- the user explicitly confirms license acceptance;
- CC-BY attribution is present;
- no other approved recipe owns the same runtime target.

Unverified and blocked records remain visible but cannot enter a runtime atlas.

## Deterministic bake

Run:

```powershell
.\tools/build/Build.cmd asset-bake
```

or use **Bake + Reload** in the Intake tab. The Python/Pillow baker sorts approved recipes by stable ID, crops their source rectangles, packs a deterministic shelf atlas with padding and edge extrusion, and writes:

- `assets/generated/user_imports/havenwild_intake_atlas_v0_1.png`
- `assets/generated/user_imports/havenwild_intake_atlas_v0_1.json`

The editor watches the manifest timestamp and hot reloads the generated texture, binding registry, and searchable palette. The included project-owned cave entrance recipe proves the path and resolves the previous Cave Entrance missing-binding warning.

## Current boundary

Pass 53 binds imported art to existing canonical tile/object gameplay kinds. Creating entirely new gameplay kinds remains a later schema/compiler task; source slicing and runtime binding no longer require hand-edited atlas coordinates.
