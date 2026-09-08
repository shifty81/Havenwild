#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parents[5]
checks=[
('assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.json',(274,546),32),
('assets/generated/worldgen_v0_1/terrain/live_autotile_16_32.json',(546,240),112),
('assets/generated/worldgen_v0_1/water/water_families_animated_32.json',(138,172),5),
]
for rel,size,count in checks:
 p=ROOT/rel; d=json.loads(p.read_text()); img=ROOT/d['output'] if not Path(d['output']).is_absolute() else Path(d['output'])
 if not img.exists():
  img=p.with_suffix('.png')
 assert img.exists(), f'missing image for {rel}: {img}'
 assert Image.open(img).size==size, f'{img} size mismatch'
 values=d.get('tiles') or d.get('variants')
 assert len(values)==count, f'{rel} entry count mismatch'
 expected_version='0.4.0' if 'common_base_terrain' in rel else '0.2.0'
 assert d['version']==expected_version, f'{rel} version mismatch'
 if 'live_autotile' in rel:
  assert d.get('art_generator')=='tools/automation/terrain/Generate-HavenwildProductionTerrainPass59.py'
assert (ROOT/'tools/automation/terrain/Generate-HavenwildProductionTerrainPass59.py').exists()
assert (ROOT/'docs/assets/previews/havenwild_production_terrain_repeat_preview_pass59.png').exists()
text=(ROOT/'tools/build/Build.sh').read_text()
assert 'tiles)' in text and 'Generate-HavenwildProductionTerrainPass59.py' in text
print('Production terrain tile validation V76 passed')
