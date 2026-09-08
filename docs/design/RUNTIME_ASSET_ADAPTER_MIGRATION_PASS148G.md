# Pass 148G — Runtime Asset Adapter Migration

This pass introduces the shared adapter contract used by PCG, F3 editing, rendering, object placement, characters, animation, audio, UI, and inventory.

All consumers request semantic assets through `SemanticAssetResolver`. Legacy registries remain temporary explicit fallbacks while their runtime loaders are migrated. PCG and F3 use the same `terrain_semantic_id(TileKind)` mapping, and road, stone path, mountain path, and bridge retain distinct semantic identities.

The next migration slice wires startup discovery into the game/editor host and converts texture loading and placement calls to stable `StableAssetRef` results.
