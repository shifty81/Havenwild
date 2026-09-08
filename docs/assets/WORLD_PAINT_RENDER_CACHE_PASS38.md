# World Paint Render Cache Document Pass 38

This pass adds a derived render-cache document for the world-paint pipeline.

The cache is intentionally **not authoritative gameplay state**. Paint deltas and material-state cells remain the source of truth. The cache stores resolved, client-friendly atlas binding data so the runtime/editor can redraw painted world cells without recomputing every resolver step constantly.

## Pipeline

```text
paint delta
-> material state
-> adjacency
-> transition tile resolver
-> render cache document
-> runtime atlas draw
```

## Cache path

```text
WORKSPACE/generated/world_paint/world_paint_render_cache_v0_1.json
```

## Cached entry fields

- scene id
- tile coordinate
- family
- layer
- transition kind
- neighbor bits
- selected tile id
- selected atlas rect
- atlas source
- source resolver status

## Rules

- The cache can be deleted and regenerated.
- Atlas rects must remain strict `32x32` cells.
- Duplicated scene/x/y entries are invalid.
- Server/host authority should sync paint deltas or material-state data, not this cache.
- Clients may rebuild this cache deterministically from the same manifests.

## Current runtime behavior

The runtime refreshes and persists the active-scene render cache when paint bindings are refreshed. The Paint tab still uses the in-memory binding cache for drawing, now backed by the disposable JSON cache document.
