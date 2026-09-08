# Pass 52 — Asset Palette and Atlas Binding

Pass 52 replaces the Scene Map's diagnostic-only tile presentation with project-owned atlas rendering and turns the right dock into a production asset-selection surface.

## Locked editor behavior

- The **Assets** dock is separate from Tools and Inspector.
- Search, category filters, favorites, and recent assets operate on stable palette IDs.
- Clicking a tile arms **Terrain / Paint**.
- Clicking an object arms **Objects / Place**.
- Dragging an asset card onto the permanent canvas resolves through the same clipped canvas transform and snapped cell used by all other authoring tools.
- Palette placement uses the existing typed transaction path; it must not introduce serialized-world snapshot history.
- Favorites and recent assets persist under `.local/editor/asset_palette_state.json` and are machine-local rather than canonical project content.

## Atlas ownership

The editor loads four project-owned textures with nearest-neighbor filtering:

1. canonical generated base terrain atlas;
2. canonical generated object atlas;
3. the new 112-cell live-autotile atlas;
4. the terrain-transition atlas already resolved by the world/runtime autotile layer.

`LiveAutotileAtlasRegistry` validates all seven supported terrain families and every cardinal mask from 0 through 15. The Scene Map asks `LiveAutotileCache` for the resolved group/mask and draws the matching atlas cell. Terrain transitions use the shared `resolve_transition_atlas_requests` path, preventing editor-only topology rules.

## Missing assets and provenance

A palette record remains searchable when its runtime sprite binding is unavailable. The card shows a warning and a fallback preview rather than silently hiding the content. This currently exposes missing bindings such as Cave Entrance as explicit asset-pipeline work.

All Pass 52 source art is project-generated. Future imported assets must carry provenance and promotion/licensing metadata before they can become runtime-ready palette entries.

## Generated live-autotile atlas

- Manifest: `assets/generated/worldgen_v0_1/terrain/live_autotile_16_32.json`
- Texture: `assets/generated/worldgen_v0_1/terrain/live_autotile_16_32.png`
- Families: 7
- Cardinal masks per family: 16
- Required bindings: 112
- Cell size: 32×32
- Filtering: nearest
- Deterministic generator: `tools/automation/terrain/Generate-LiveAutotileAtlas.py`

Regenerate it with:

```powershell
.\tools\automation\terrain\Generate-LiveAutotileAtlas.ps1
```

## Validation

Run:

```powershell
.\tools\automation\validation\checks\assets\Validate-AssetPaletteAtlasBindingV65.ps1
```

or:

```bash
python tools/automation/validation/checks/assets/Validate-AssetPaletteAtlasBindingV65.py
```
