# Pass 148A — Universal Asset-Pack Core Foundation

Havenwild content is mounted through open-ended asset packs. Terrain is only one category. Stable identity is `pack + category + asset + source + variant`; source atlas coordinates remain local to their pack.

Initial categories include terrain, objects, buildings, walls, floors, doors, furniture, crops, trees, foliage, characters, clothing, armor, tools, weapons, animals, NPCs, animations, effects, UI, audio, music, items, recipes, biomes, world generation, scenes, interiors, caves, dungeons, and editor templates.

The core registry permits multiple packs to provide the same semantic asset. Selection is priority-based today and will later include project, biome, season, explicit-user, compatibility, and license policies.

`havenwild_core` and `lpc_revised` are registered as initial package manifests. The LPC Revised manifest is intentionally unmapped until its source/license inventory is imported through the generic adapter layer.
