#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parents[5]
required=[
 'content/assets/intake/asset_intake_catalog_v0_1.json',
 'content/editor/assets/asset_intake_atlas_authoring_contract_v0_1.json',
 'assets/source/original/cave_entrance_96.png',
 'tools/automation/assets/Bake-AssetIntakeAtlasV66.py',
]
missing=[p for p in required if not (ROOT/p).is_file()]
if missing:
 raise SystemExit('Pass 145E missing asset-intake bootstrap files:\n- '+'\n- '.join(missing))
catalog=json.loads((ROOT/required[0]).read_text(encoding='utf-8'))
assert catalog.get('schema')=='havenwild.asset_intake_catalog.v0_1'
recipes=catalog.get('recipes',[])
assert recipes, 'asset intake catalog must contain at least one proof recipe'
for recipe in recipes:
 source=ROOT/recipe['sourcePath']
 assert source.is_file(), f'missing intake source {recipe["sourcePath"]}'
 with Image.open(source) as im:
  rect=recipe['slice']; assert rect['x']+rect['width']<=im.width and rect['y']+rect['height']<=im.height
completed=subprocess.run([sys.executable,str(ROOT/'tools/automation/assets/Bake-AssetIntakeAtlasV66.py'),'--validate-only'],cwd=ROOT,capture_output=True,text=True)
if completed.returncode:
 raise SystemExit(completed.stderr or completed.stdout)
for script in ['tools/automation/packaging/Create-SourceOnlyRollup.py','tools/automation/packaging/Create-ChatGPTSourceRollup.py','tools/automation/validation/checks/build/Validate-SourceRollupBootstrapV145A.py']:
 text=(ROOT/script).read_text(encoding='utf-8')
 for item in required[:3]:
  assert item in text, f'{script} does not protect {item}'
print(f'Pass 145E asset-intake bootstrap validated ({len(recipes)} recipe(s))')
