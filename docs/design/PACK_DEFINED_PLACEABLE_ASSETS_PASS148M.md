# Pass 148M — Pack-Defined Placeable Assets

Havenwild placeable content is discovered from every mounted production asset pack through
`placeable.catalog.*` providers. A catalog may describe buildings, furniture, doors, walls,
trees, crops, foliage, caves, dungeon pieces, scene entrances, props, or future categories.

The catalog owns stable identity, semantic identity, source provider, footprint, anchor,
collision and interaction rectangles, legal placement surfaces, states, and placement tags.
The runtime and native editor consume the same `PlaceableAssetRegistry`. Legacy `ObjectKind`
default footprints remain compatibility fallback data only.

Pack-defined placement does not require a new global validator for each object family. The
single generic validator checks catalog schema, source resolution, pack-qualified identity,
consumer wiring, and shared placement rules.
