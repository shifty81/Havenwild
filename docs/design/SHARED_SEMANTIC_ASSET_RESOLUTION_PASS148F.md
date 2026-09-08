# Pass 148F — Shared Semantic Asset Resolution

All runtime/editor consumers request semantic assets through one discovered `AssetPackRegistry`.
The resolver is category-neutral and preserves stable pack/source/asset/variant identity.

Default production resolution excludes disabled/reference-only packs. Explicit inspection or authoring tools may opt in.
Resolution order is explicit provider, biome/season preference, project pack priority, required tags, then stable tie-break.

Initial consumers: PCG, F3 editor, runtime rendering, object placement, animation, audio, UI, and inventory.
Legacy category-specific registries remain compatibility adapters until migrated; they must not add new pack-name branches.
