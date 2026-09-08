#!/usr/bin/env python3
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[5]; errors=[]
def t(x): return (R/x).read_text(encoding='utf-8') if (R/x).is_file() else ''
types=t('crates/haven_pixel/src/animation/types.rs'); layers=t('apps/haven_editor_native/src/app/canvas_layers.rs'); inp=t('apps/haven_editor_native/src/app/animation_studio_input.rs')
for m in ['pub struct AnimationBounds','pub foot_anchor','pub hitboxes','pub hurtboxes']:
 if m not in types: errors.append('missing E11 metadata '+m)
for m in ['Foot / Ground Anchor','Shadow Anchor','Hitboxes','Hurtboxes']:
 if m not in layers: errors.append('missing E11 layer '+m)
for m in ['AnimationPlacementMode::Foot','AnimationPlacementMode::Hitbox','AnimationPlacementMode::Hurtbox']:
 if m not in inp: errors.append('missing E11 authoring '+m)
if errors:
 print('FAIL: W60E11 animation metadata'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: W60E11 animation metadata')
