from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[5]

masks = ROOT / 'crates/haven_world/src/structural_landform_masks.rs'
gen = ROOT / 'crates/haven_world/src/structural_landform_generation.rs'
diag = ROOT / 'crates/haven_game/src/runtime_diagnostics.rs'
authority = ROOT / 'content/worldgen/structural_contour_quality_authority_v0_1.json'

errors = []

def require_text(path: Path, token: str):
    text = path.read_text(encoding='utf-8')
    if token not in text:
        errors.append(f'{path.relative_to(ROOT)} missing token: {token}')

require_text(masks, 'pub(crate) fn normalize_structural_contours(')
require_text(masks, 'if support <= 1')
require_text(masks, 'else if support >= 3')
require_text(masks, 'generated_single_cell_south_spur_is_removed')
require_text(masks, 'generated_single_cell_notch_is_filled')
require_text(masks, 'two_neighbor_diagonal_staircase_corner_is_preserved')
require_text(masks, 'level_two_terminal_falls_back_to_level_one')
require_text(gen, 'normalize_structural_contours(&mut levels, &land, &protected, width, height);')

text = diag.read_text(encoding='utf-8')
if not any(marker in text for marker in ['Pass 167Z109I', 'Pass 167Z109J', 'Pass 167Z109K', 'Pass 167Z109L', 'Pass 167Z109M', 'Pass 167Z109N', 'Pass 167Z109O']):
    errors.append('runtime diagnostics missing Z109I-or-newer pass marker')

obj = json.loads(authority.read_text(encoding='utf-8'))
if obj.get('pass') != '167Z109I':
    errors.append('structural contour authority pass mismatch')
if obj.get('authority', {}).get('iterations') != 2:
    errors.append('structural contour authority must lock two cleanup iterations')
if obj.get('authority', {}).get('thresholds') != [1, 2]:
    errors.append('structural contour authority must lock Level 1/2 thresholds')
if obj.get('collisionContract', {}).get('visualAndCollisionShareResult') is not True:
    errors.append('visual/collision shared normalized structural result must be explicit')

if errors:
    print('Pass167Z109I generated cliff contour normalization validation FAILED')
    for error in errors:
        print(f' - {error}')
    sys.exit(1)

print('Pass167Z109I generated cliff contour normalization validation passed')
