# Pass 148O — Stable Placeable Runtime Dispatch

Generic placeables now use their persisted provider identity as the first runtime lookup key.

## Rendering

The runtime resolves `StablePlaceableAssetRef` through `PlaceableAssetRegistry`, loads each provider source through the shared texture cache, selects the saved object state, and draws the pack-defined source rectangle and foot anchor. `ObjectKind` atlas lookup remains an explicit compatibility fallback for old saves or missing providers.

## Interaction

Catalog entries define an action, message, and optional target. The first supported actions are inspect, sit, sleep, harvest, open, and enter-scene. Runtime interaction dispatch checks stable asset metadata before the legacy `ObjectKind` match.

## Persistence correction

The persisted asset ID now identifies the individual catalog entry rather than the shared catalog manifest. Object state is stored through `object_state` records. Existing saves without these records remain readable.

## Current boundary

State transitions are now persistable and renderable, but full behavior-node binding and authoritative multiplayer replication of state changes remain later work.
