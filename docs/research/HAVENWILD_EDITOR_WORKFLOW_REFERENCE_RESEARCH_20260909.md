# Havenwild Editor Workflow Reference Research — 2026-09-09

This document records workflow references used by `HW-EDITOR-GAP-AUDIT-02`. Havenwild remains an original editor and does not copy protected UI/assets.

## GameMaker

Primary references:
- https://manual.gamemaker.io/lts/en/The_Asset_Editors/Rooms.htm
- https://manual.gamemaker.io/lts/en/The_Asset_Editors/Room_Properties/Layer_Properties.htm
- https://manual.gamemaker.io/lts/en/The_Asset_Editors/Tile_Set_Editors/Brush_Builder.htm
- https://manual.gamemaker.io/lts/en/The_Asset_Editors/Tile_Sets.htm

Adopt conceptually:
- one primary room/game canvas;
- layer-driven tool context;
- direct browser-to-canvas placement;
- separate tileset/atlas view available while editing the room;
- temporary multi-tile selections and persistent brushes;
- tile transform tools.

Do not copy:
- proprietary visual layout, icons or exact window chrome;
- GameMaker-specific runtime layer model where it conflicts with Havenwild semantic layers.

## LDtk

Primary references:
- https://ldtk.io/docs/general/editor-components/
- https://ldtk.io/docs/general/editor-components/layers/
- https://ldtk.io/docs/general/editor-components/entities/
- https://ldtk.io/docs/general/auto-layers/
- https://ldtk.io/docs/general/auto-layers/auto-layer-rules/
- https://ldtk.io/docs/general/world/

Adopt conceptually:
- Definitions vs Instances;
- active layer drives contextual palette;
- semantic IntGrid-like source data separated from generated visual output;
- entity fields and constraints, including unique Player Start;
- rule authoring/debug visibility;
- world/level navigation.

Do not copy:
- literal LDtk project format as Havenwild authority;
- infinite-world assumptions; Havenwild remains a finite enormous seeded archipelago.

## Tiled

Primary references:
- https://doc.mapeditor.org/en/latest/manual/layers/
- https://doc.mapeditor.org/en/latest/manual/objects/
- https://doc.mapeditor.org/en/latest/manual/using-templates/
- https://doc.mapeditor.org/en/latest/manual/editing-tilesets/
- https://doc.mapeditor.org/en/latest/manual/automapping/
- https://doc.mapeditor.org/en/latest/manual/custom-properties/

Adopt conceptually:
- tile layers for dense visuals and object/entity layers for richer metadata;
- templates/prefabs with inherited defaults;
- custom typed properties/classes;
- stamp brush/terrain brush workflows;
- Wang/terrain metadata;
- pattern-based automapping for structures such as cliff faces;
- chunked editing model for very large maps.

Do not copy:
- TMX/TMJ as Havenwild's canonical save format;
- expose every low-level layer as a creator-facing layer.

## Godot

Primary references:
- https://docs.godotengine.org/en/stable/tutorials/2d/using_tilesets.html
- https://docs.godotengine.org/en/stable/tutorials/2d/using_tilemaps.html
- https://docs.godotengine.org/en/stable/classes/class_tilesetscenescollectionsource.html

Adopt conceptually:
- TileSet per-tile physics/navigation/occlusion/custom-data authority;
- terrain Connect, Path and manual/specific tile placement modes;
- alternative tile/variant identities;
- rich scene-backed placements only when behavior warrants it;
- stable tile remapping/proxy concept for catalog migrations.

Do not copy:
- Godot node/scene runtime architecture wholesale;
- scene-backed tiles for ordinary static world decoration where atlas placement is cheaper.

## RPG Maker MZ

Primary references:
- https://rpgmakerofficial.com/product/MZ_help-en/01_03.html
- https://rpgmakerofficial.com/product/MZ_help-en/01_09.html
- https://rpgmakerofficial.com/product/MZ_help-en/01_09_03.html

Adopt conceptually:
- gameplay markers/events authored in map context;
- map/region/event authoring remains spatially understandable.

Do not copy:
- a second map-event scripting language. Havenwild uses the shared Logic/Behavior system;
- a separate Spawn editor mode.

## Resulting Havenwild direction

The common high-value pattern is not a specific editor's UI. It is a consistent authoring loop:

`active layer -> contextual palette -> direct canvas manipulation -> contextual inspector`

Havenwild extends that with shared Native/F3/automation command parity, semantic terrain plus exact manual atlas overrides, PCG exemplars, provenance-aware assets, and a finite whole-world authoring model.
