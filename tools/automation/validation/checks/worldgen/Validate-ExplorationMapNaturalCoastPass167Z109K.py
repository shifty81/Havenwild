#!/usr/bin/env python3
from pathlib import Path
import json
import sys

root = Path(__file__).resolve().parents[5]
errors = []

def require(path, token):
    text = (root / path).read_text(encoding='utf-8')
    if token not in text:
        errors.append(f"{path}: missing {token!r}")
    return text

world_map = require('crates/haven_game/src/runtime_world_map.rs', 'WORLD_MAP_EXPLORATION_SCHEMA')
for token in [
    'world_map_exploration.json',
    'capture_active_world_map_chunk',
    'explored_world_map_bounds',
    'TileKind::Road',
    'map expands as you explore',
]:
    if token not in world_map:
        errors.append(f'runtime_world_map.rs missing {token}')
if 'sample_geographic_surface(' in world_map.split('pub(super) fn rebuild_world_map_geographic_overview', 1)[1].split('pub(super) fn handle_world_map_input', 1)[0]:
    errors.append('player world map still pre-samples unrevealed geographic surface')

stream = require('crates/haven_game/src/runtime_surface_streaming.rs', 'capture_active_world_map_chunk')
if stream.count('capture_active_world_map_chunk') < 2:
    errors.append('surface streaming must snapshot both departure/arrival or active discovery')

geo = require('crates/haven_world/src/geographic_surface.rs', 'COAST_WARP_BROAD_DOMAIN')
for token in ['COAST_WARP_DETAIL_DOMAIN', 'north_west', 'north_east', 'lobe_a', 'lobe_b', 'lobe_c', 'starter_mainland_southern_coast_is_not_a_single_ellipse_arc']:
    if token not in geo:
        errors.append(f'geographic_surface.rs missing {token}')

map_authority = json.loads((root / 'content/worldgen/global_map_minimap_flora_authority_v0_1.json').read_text(encoding='utf-8'))
if not (map_authority['revision'].startswith('167Z109K') or map_authority['revision'].startswith('167Z109L')):
    errors.append('map authority revision predates Z109K')
if map_authority['worldMap'].get('explorationPersistence') != 'worldgen/world_map_exploration.json':
    errors.append('map exploration persistence path mismatch')

geo_authority = json.loads((root / 'content/worldgen/geographic_world_authority_v0_1.json').read_text(encoding='utf-8'))
if not geo_authority['revision'].startswith('167Z109K'):
    errors.append('geographic authority revision not advanced to Z109K')

diag = (root / 'crates/haven_game/src/runtime_diagnostics.rs').read_text(encoding='utf-8')
if not any(tag in diag for tag in ['Pass 167Z109K', 'Pass 167Z109L', 'Pass 167Z109M', 'Pass 167Z109N', 'Pass 167Z109O']):
    errors.append('runtime diagnostic predates Z109K')

if errors:
    print('Pass167Z109K validation FAILED')
    for error in errors:
        print(' -', error)
    sys.exit(1)
print('Pass167Z109K exploration map + natural coast validation passed')
