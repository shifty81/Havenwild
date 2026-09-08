# Pass 148X — LPC Revised Full Repository Inventory

Pass 148X broadens the LPC work from character sheets to the complete mounted LPC Revised dependency. The repository is treated as a source library that can produce many independent Havenwild packs rather than one flattened atlas.

## Covered families

World assets include terrain, objects, structures, walls, floors, doors, furniture, interiors, caves, and dungeons. Nature assets include crops, trees, foliage, and animals. Character assets include bodies, NPC parts, clothing, armor, tools, weapons, effects, portraits, and animation families. UI, icons, item art, metadata, Tiled files, audio, and documentation are inventoried as well.

## Inventory generation

`tools/automation/project/Build-LpcRevisedInventoryV148X.py` recursively scans `assets/source/licensed/lpc_revised` and writes `WORKSPACE/generated/lpc_revised_inventory_v1.json`. Generated inventory is local build output and is intentionally excluded from source archives.

Every supported source receives its original relative path, source kind, proposed category, proposed stable asset and semantic IDs, tags, image dimensions when available, possible frame-cell profile, animation-family hint, nearby license evidence, and readiness status.

## Licensing boundary

Technical discoverability does not imply permission to ship. LPC Revised remains reference-only and production-disabled. Each promotable source family must have compatible commercial redistribution terms verified independently. GPL material must not be promoted into the closed-source production asset set.

## Next integration

The generated inventory should feed the Content Library, category-specific mapping queues, character compositor, semantic autotile mapper, generic placeable catalog builder, animation mapper, and license-review dashboard.
