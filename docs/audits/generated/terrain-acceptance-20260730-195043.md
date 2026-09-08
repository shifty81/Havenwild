# Havenwild Terrain Acceptance Audit

- Atlas: $(@{id=lpc_mapped_terrain_v7_32; kind=lpc_mapped_terrain_corner_tileset; version=0.3.0; tileSize=System.Object[]; padding=1; atlasLayout=compact_64_column_extruded; output=assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.png; source=content/assets/lpc/source/lpc-terrains-v7/terrain-map-v7.tsx; license=OpenGameArt LPC terrain credits in content/assets/lpc/source/lpc-terrains-v7/CREDITS-terrain.txt; runtimePolicy=complete replacement tile for covered pure and mixed terrain corner tuples; dedicated structural and wet-sand paths remain fallback lanes; tileKindTerrainMap=; coverage=; entries=System.Object[]}.output)
- Atlas SHA-256: $hash
- Manifest entries: $(@(@{id=lpc_mapped_terrain_v7_32; kind=lpc_mapped_terrain_corner_tileset; version=0.3.0; tileSize=System.Object[]; padding=1; atlasLayout=compact_64_column_extruded; output=assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.png; source=content/assets/lpc/source/lpc-terrains-v7/terrain-map-v7.tsx; license=OpenGameArt LPC terrain credits in content/assets/lpc/source/lpc-terrains-v7/CREDITS-terrain.txt; runtimePolicy=complete replacement tile for covered pure and mixed terrain corner tuples; dedicated structural and wet-sand paths remain fallback lanes; tileKindTerrainMap=; coverage=; entries=System.Object[]}.entries).Count)
- Exact/mixed entries: $exact
- Fill entries: $fills
- Acceptance scenarios: $(@(@{schema=havenwild.terrain_acceptance.v1; version=1; authority=Havenwild Terrain Standard v1 exact mapped LPC tuple atlas; editorAtlas=assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.png; editorManifest=assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json; renderRules=System.Object[]; scenarios=System.Object[]; fixtureManifest=content/worldgen/scenes/terrain_acceptance/terrain_acceptance_scene_manifest_v1.json; fixturePolicy=}.scenarios).Count)
- Runtime policy: $(@{id=lpc_mapped_terrain_v7_32; kind=lpc_mapped_terrain_corner_tileset; version=0.3.0; tileSize=System.Object[]; padding=1; atlasLayout=compact_64_column_extruded; output=assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.png; source=content/assets/lpc/source/lpc-terrains-v7/terrain-map-v7.tsx; license=OpenGameArt LPC terrain credits in content/assets/lpc/source/lpc-terrains-v7/CREDITS-terrain.txt; runtimePolicy=complete replacement tile for covered pure and mixed terrain corner tuples; dedicated structural and wet-sand paths remain fallback lanes; tileKindTerrainMap=; coverage=; entries=System.Object[]}.runtimePolicy)

## Required scenarios
- **coastline** - continuous authored shoreline curves
- **river** - connected narrow and wide channel turns
- **farm_soil** - clean cultivated-ground boundary
- **mountain** - connected mountain/path boundary
- **snow_ice** - continuous frozen-biome boundary
- **wrapped_world_seam** - left/right tuple parity across world wrap

This audit is diagnostic and does not add a mandatory build gate.
