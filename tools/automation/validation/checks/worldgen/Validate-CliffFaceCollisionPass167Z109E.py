from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
RUNTIME = ROOT / 'crates/haven_game/src/runtime_surface_streaming.rs'
AUTH = ROOT / 'content/worldgen/structural_collision_cliff_assembly_authority_v0_1.json'
DOC = ROOT / 'docs/archive/pass_history/PASS167Z109E_CLIFF_FACE_COLLISION_FOOTPRINT.md'

errors = []
for path in (RUNTIME, AUTH, DOC):
    if not path.exists():
        errors.append(f'missing required file: {path.relative_to(ROOT)}')

if not errors:
    runtime = RUNTIME.read_text(encoding='utf-8')
    authority = AUTH.read_text(encoding='utf-8')
    required_runtime = [
        'structural_cliff_face_occupies_tile(to)',
        'fn structural_cliff_face_occupies_tile',
        'structural_south_face_projection_depth',
        'tile_within_south_face_projection',
        'structural_connector_from_host_edge_in_manifest',
        'Some(CliffShape15::SouthWest | CliffShape15::EastSouth) => 3',
        '_ => 2',
    ]
    for token in required_runtime:
        if token not in runtime:
            errors.append(f'runtime missing collision-footprint token: {token}')
    required_authority = [
        'projectedSouthFaceCellsBlocked',
        'connectorCorridorCarvesProjectedFace',
        'z109d_only_lip_edge_collision_allowed_player_inside_visible_cliff_face',
    ]
    for token in required_authority:
        if token not in authority:
            errors.append(f'authority missing token: {token}')

if errors:
    print('Pass167Z109E cliff face collision validation FAILED')
    for error in errors:
        print(f' - {error}')
    sys.exit(1)

print('Pass167Z109E cliff face collision validation passed')
