from pathlib import Path

root = Path(__file__).resolve().parents[5]
mask = (root / 'crates/haven_world/src/water_render_mask.rs').read_text(encoding='utf-8')
render = (root / 'crates/haven_game/src/terrain_render.rs').read_text(encoding='utf-8')
lib = (root / 'crates/haven_world/src/lib.rs').read_text(encoding='utf-8')

required = {
    'water mask module exported': 'pub mod water_render_mask;' in lib,
    'deep water owns the depth edge': 'is_deep(tile) && is_shallow(neighbor)' in mask,
    'shader-ready mask record exists': 'pub struct WaterRenderMask' in mask,
    'depth atlas requests are bypassed': 'request.material == TransitionMaterial::ShallowWaterEdge' in render,
    'legacy circular depth corners are bypassed': 'corner.material != TransitionMaterial::ShallowWaterEdge' in render,
    'mask renderer is active': 'draw_water_depth_mask(' in render and 'water_mask.depth_edges' in render and 'water_mask.depth_corners' in render,
}
missing = [name for name, ok in required.items() if not ok]
if missing:
    raise SystemExit('Pass 153A V7 water-mask validation failed:\n- ' + '\n- '.join(missing))
print('Pass 153A OK: V7 water topology emits shader-ready masks and legacy circular depth stamps are disabled')
