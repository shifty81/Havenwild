#!/usr/bin/env python3
from pathlib import Path
import json
import re
root = Path(__file__).resolve().parents[5]
issues = []
required = [
    'crates/haven_world/src/world_paint_render_cache.rs',
    'content/assets/world_paint/world_paint_render_cache_contract_v0_1.json',
    'content/schemas/world_paint_render_cache_contract.schema.v0_1.json',
    'docs/assets/WORLD_PAINT_RENDER_CACHE_PASS38.md',
]
for rel in required:
    if not (root / rel).exists():
        issues.append(f'missing {rel}')
rs = (root / 'crates/haven_world/src/world_paint_render_cache.rs').read_text(encoding='utf-8')
for token in [
    'WorldPaintRenderCacheDocument',
    'WorldPaintRenderCacheScene',
    'WorldPaintRenderCacheEntry',
    'refresh_world_paint_render_cache_scene',
    'load_world_paint_render_cache_scene',
    'validate_world_paint_render_cache_document',
    'atlas_rect[2] != 32 || entry.atlas_rect[3] != 32',
]:
    if token not in rs:
        issues.append(f'missing rust token {token}')
lib = (root / 'crates/haven_world/src/lib.rs').read_text(encoding='utf-8')
if 'pub mod world_paint_render_cache;' not in lib or 'pub use world_paint_render_cache::*;' not in lib:
    issues.append('world_paint_render_cache not exported from haven_world')
config = (root / 'crates/haven_game/src/runtime_config.rs').read_text(encoding='utf-8')
if 'WORLD_PAINT_RENDER_CACHE_PATH' not in config:
    issues.append('WORLD_PAINT_RENDER_CACHE_PATH missing')
binding = (root / 'crates/haven_game/src/world_paint_render_binding.rs').read_text(encoding='utf-8')
for token in ['refresh_world_paint_render_cache_scene', 'WORLD_PAINT_RENDER_CACHE_PATH', 'cache persisted']:
    if token not in binding:
        issues.append(f'render binding missing {token}')
contract = json.loads((root / 'content/assets/world_paint/world_paint_render_cache_contract_v0_1.json').read_text(encoding='utf-8'))
if contract.get('schema') != 'havenwild.world_paint_render_cache_contract.v0.1':
    issues.append('bad contract schema')
if 'WORKSPACE/generated/world_paint/world_paint_render_cache_v0_1.json' != contract.get('cacheDocument'):
    issues.append('bad cache document path')
if issues:
    print('Validate-WorldPaintRenderCacheV45 FAILED')
    for issue in issues:
        print(' -', issue)
    raise SystemExit(1)
print('Validate-WorldPaintRenderCacheV45 OK')
