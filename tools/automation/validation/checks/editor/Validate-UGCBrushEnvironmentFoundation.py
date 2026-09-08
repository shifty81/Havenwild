#!/usr/bin/env python3
from pathlib import Path
import json, sys

ROOT = Path(__file__).resolve().parents[5]
errors=[]

def need(path, tokens=()):
    p=ROOT/path
    if not p.exists():
        errors.append(f"missing {path}")
        return ""
    text=p.read_text(encoding='utf-8')
    for token in tokens:
        if token not in text:
            errors.append(f"{path}: missing token {token!r}")
    return text

need(Path('apps/haven_editor_native/src/app/mod.rs'), [
    'mod brush_authoring;',
    'canvas_authoring_context: brush_authoring::CanvasAuthoringContext',
    'CanvasAuthoringContext::default()',
])
need(Path('apps/haven_editor_native/src/app/brush_authoring.rs'), [
    'enum BrushMode', 'TerrainElevation', 'Atmosphere', 'Weather',
    'struct CanvasAuthoringContext', 'compatible_brush_modes',
    'ElevationBrushPolicy', 'StructuralBakePolicy',
    'sync_canvas_authoring_context',
])
need(Path('apps/haven_editor_native/src/app/canvas_tool_rack.rs'), [
    'tool_shelf_height', 'active_brush_modes', 'tool_shelf_mode_rect', 'select_canvas_brush_mode',
])
need(Path('apps/haven_editor_native/src/app/canvas_layers.rs'), [
    'CanvasLayerKind::Atmosphere', 'CanvasLayerKind::Weather',
    'Layers is a dedicated panel, not text painted over the world', '+ self.canvas_layer_rail_width()',
])
need(Path('apps/haven_editor_native/src/app/shared_palette.rs'), [
    'Palette is a reserved sibling surface at the bottom of Canvas', 'shared_palette_height', 'self.draw_canvas_brush_palette(rect)',
    'EditorViewportMode::PixelStudio',
])
need(Path('apps/haven_editor_native/src/app/canvas_controller.rs'), [
    'Palette is a first-class bottom Canvas panel',
    'super::shared_palette::shared_palette_height(self)',
])
need(Path('apps/haven_editor_native/src/app/document_tabs.rs'), [
    'authoring_context: super::brush_authoring::CanvasAuthoringContext',
    'authoring_context: self.canvas_authoring_context.clone()',
])
need(Path('crates/haven_assets/src/asset_palette.rs'), [
    'enum BrushResourceClass', 'enum BrushCapability',
    'brush_resource_class', 'brush_capabilities',
])
need(Path('crates/haven_world/src/environment_system.rs'), [
    'ENVIRONMENT_SYSTEM_SCHEMA', 'enum WeatherKind', 'enum AtmosphereKind',
    'struct LightEmitterProfile', 'struct WeatherProfile', 'struct EnvironmentVolume',
])
need(Path('crates/haven_world/src/lib.rs'), ['pub mod environment_system;', 'pub use environment_system::*;'])

brush_path=ROOT/'content/editor/authoring/brush_resource_catalog_v0_1.json'
env_path=ROOT/'content/environment/environment_profiles_v0_1.json'
try:
    brush=json.loads(brush_path.read_text())
    assert brush['schema']=='havenwild.editor.brush_resource_catalog.v0_1'
    modes={m for rule in brush['rules'] for m in rule.get('brush_modes',[])}
    for m in ['autotile','terrain_elevation','lighting','atmosphere','weather']:
        if m not in modes: errors.append(f'brush catalog missing {m}')
    presets={p['id'] for p in brush['canonical_presets']}
    if 'brush.terrain.grass.level2_plateau' not in presets:
        errors.append('brush catalog missing level-2 plateau preset')
except Exception as e:
    errors.append(f'brush catalog invalid: {e}')

try:
    env=json.loads(env_path.read_text())
    atmos={x['stable_id'] for x in env['atmosphere']}
    weather={x['stable_id'] for x in env['weather']}
    lights={x['stable_id'] for x in env['lights']}
    if not {'atmosphere.clear','atmosphere.morning_mist','atmosphere.cave_dust','atmosphere.storm_haze'} <= atmos:
        errors.append('environment catalog missing baseline atmosphere profiles')
    if not {'weather.clear','weather.rain','weather.thunderstorm'} <= weather:
        errors.append('environment catalog missing baseline weather profiles')
    if not {'light.lantern.warm','light.fireplace.warm'} <= lights:
        errors.append('environment catalog missing baseline light profiles')
    for w in env['weather']:
        a=w.get('atmosphere_profile')
        if a and a not in atmos: errors.append(f"weather {w['stable_id']} references missing atmosphere {a}")
except Exception as e:
    errors.append(f'environment catalog invalid: {e}')

if errors:
    print('[FAIL] Unified Game Canvas brush/environment foundation')
    for e in errors: print(' -',e)
    sys.exit(1)
print('[PASS] Unified Game Canvas brush/environment foundation')
