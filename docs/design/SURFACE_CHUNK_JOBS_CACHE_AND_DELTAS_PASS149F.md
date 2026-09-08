# Pass 149F — Surface Chunk Jobs, Cache, and Deltas

Pass 149F removes routine procedural generation from the exterior boundary-crossing path.
A dedicated worker receives deterministic chunk requests, while the game integrates at most two
results per frame. Generated baselines are written beneath the active world save and are reused on
future visits. A player-delta snapshot takes precedence over the baseline and is saved before an
edited generated chunk loses active ownership.

The active 3×3 window remains fully resident. The 5×5 preload ring is requested or loaded from disk.
Generated chunks outside that ring are evicted from the in-memory scene registry. Authored exterior
overrides are not selected by the generated-scene eviction rule.

The current delta file is a complete replacement snapshot for correctness. A later compaction pass
may rewrite it as sparse terrain/object/state records without changing load precedence or paths.
