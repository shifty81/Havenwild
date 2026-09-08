# Editor And Asset Pipeline Plan

Date: 2026-05-24

## Goal

Build a game-aware creation environment beside the Rust game:

- map/construction editor
- tile/object palette editor
- pixel-art import and preview tools
- animation/tag importer
- content-pack editor
- script/event editor
- validation and logging

This should become an in-game overlay plus a standalone tool, not a general-purpose art program at first.

## Recommended External Tools To Support

### Pixel Art

- Pixelorama: free/open-source pixel-art editor with animation, onion skinning, tags, layers, masks, effects, and import support.
- LibreSprite: free/open-source Aseprite-family editor for animated sprites.
- Aseprite: strong commercial/source-available pixel-art workflow with CLI, layers, frame tags, and scripting. Useful if you own it, but not open-source-distributable.

### Maps

- Tiled: free/open-source map editor with tile layers, object layers, custom properties, and JSON export.
- LDtk: modern 2D level editor with entities and custom fields. Good model for our own in-game editor concepts.

### Scripting

- Rhai: Rust-native embedded scripting language, good candidate for safe in-game scripts and content-pack hooks.

## Internal Editor Architecture

```text
crates/haven_editor
  palette model
  validators
  content-pack schema helpers
  import/export adapters

crates/haven_game
  in-game editor overlay
  construction mode
  live preview

content/
  packs/
  schemas/

assets/
  raw/
    pixelorama/
    libresprite/
    aseprite/
    tiled/
    ldtk/
  processed/
    atlases/
    sprites/
    maps/
```

## Asset Manifest

Every asset should have metadata:

```json
{
  "id": "wood_floor_basic",
  "source": "assets/raw/pixelorama/tiles/tavern_tiles.pxo",
  "output": "assets/processed/sprites/tavern_tiles.png",
  "license": "CC0",
  "author": "Shifty",
  "tags": ["floor", "wood", "tavern"],
  "tileSize": [32, 32],
  "animations": []
}
```

## Sprite Import Requirements

- Import PNG spritesheets.
- Import frame metadata JSON from Aseprite-compatible workflows.
- Support animation tags: idle, walk, carry, serve, clean, build, sleep.
- Support layered character parts: hair, head, torso, arms, legs, outfit, tool.
- Generate a runtime atlas manifest.

## Tile/Object Editor Requirements

- Paint tile layers.
- Paint object layers.
- Place room/zone markers.
- Validate walkability and customer paths.
- Validate tavern objects: table must have reachable chairs; bed must be in guest room; keg must be in production/storage area.
- Validate greenhouse zone: connected region, allowed floor conversion, crop bed count, irrigation objects.

## Pixel Editor Scope

Do not build a full Aseprite replacement first.

Build these focused tools first:

- palette swatch manager
- tile variant preview
- 3x3 autotile preview
- object footprint editor
- sprite slicing grid
- animation tag preview
- character paper-doll layer preview
- export/import buttons for Pixelorama/Aseprite/LibreSprite/Tiled/LDtk

Later, add actual pixel editing:

- pencil/eraser/fill
- layers
- onion skin
- frame timeline
- palette remap
- normal/emissive mask painting for lighting

## Scripting Requirements

Use scripts for behavior that benefits from iteration:

- customer archetype spawn rules
- daily event triggers
- recipe effects
- crop growth modifiers
- staff behavior tweaks
- tutorial/quest steps

Keep hard simulation rules in Rust first. Expose a small safe API to scripts.

## Validation Checklist

- Every asset has a license and source path.
- Every sprite has declared dimensions and tags.
- Every object has footprint, collision, category, comfort/utility values.
- Every map has a spawn point, road/customer entry, reachable tavern service path, and no orphan zones.
- Every content pack logs load success/failure.
- Editor changes write backups before overwriting content files.

## First Buildable Milestone

1. Add `assets/manifest.json`.
2. Add runtime atlas loader.
3. Add tile/object manifest structs in `haven_core`.
4. Add editor inspector for selected tile/object.
5. Add map save/load to JSON.
6. Add import folder conventions for Pixelorama/Aseprite/Tiled/LDtk.
