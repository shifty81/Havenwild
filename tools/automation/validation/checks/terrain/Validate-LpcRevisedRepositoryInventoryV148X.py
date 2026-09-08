#!/usr/bin/env python3
from pathlib import Path
import json, subprocess, sys
ROOT = Path(__file__).resolve().parents[5]
errors=[]
def req(path,tokens=()):
 p=ROOT/path
 if not p.is_file(): errors.append(f'missing {path}'); return ''
 text=p.read_text(encoding='utf-8')
 for token in tokens:
  if token not in text: errors.append(f'{path} missing {token}')
 return text
req('crates/haven_assets/src/lpc_revised_inventory.rs',['LpcRepositoryInventory','classify_lpc_path','AssetCategory::Terrain','AssetCategory::Character','AssetCategory::Building','AssetCategory::Animal'])
req('crates/haven_assets/src/lib.rs',['pub mod lpc_revised_inventory;'])
req('tools/automation/project/Build-LpcRevisedInventoryV148X.py',['complete mounted LPC Revised repository','category_counts','nearby_license_files','frame_cell'])
contract=ROOT/'content/asset_packs/lpc_revised/lpc_revised_inventory_contract_v1.json'
profile=ROOT/'content/import_profiles/lpc_revised_full_repository_v1.json'
coverage=ROOT/'content/asset_packs/lpc_revised/lpc_revised_category_coverage_v1.json'
pack=ROOT/'content/asset_packs/lpc_revised/pack.json'
try:
 c=json.loads(contract.read_text()); cats=set(c['categories'])
 required={'terrain','tile_object','building','wall','floor','door','furniture','crop','tree','foliage','character','clothing','armor','tool','weapon','animal','npc','animation','effect','ui','item','interior','cave','dungeon','editor_template','other'}
 if not required.issubset(cats): errors.append('inventory contract does not cover full LPC category breadth')
 if c.get('scope')!='entire_repository': errors.append('inventory scope is not entire_repository')
 if c['production_policy'].get('technical_inventory_allowed_before_license_approval') is not True: errors.append('technical and license readiness are not separated')
 if c['production_policy'].get('no_gpl_production_assets') is not True: errors.append('no-GPL production rule missing')
except Exception as e: errors.append(f'inventory contract invalid: {e}')
try:
 p=json.loads(profile.read_text())
 if not p.get('recursive'): errors.append('LPC inventory profile is not recursive')
 if len(p.get('recognized_extensions',[]))<12: errors.append('LPC inventory extension coverage too narrow')
except Exception as e: errors.append(f'import profile invalid: {e}')
try:
 cv=json.loads(coverage.read_text())
 if len(cv.get('families',{}))<5: errors.append('category coverage lacks repository families')
 if cv.get('rules',{}).get('do_not_flatten_repository') is not True: errors.append('repository flattening prohibition missing')
except Exception as e: errors.append(f'coverage invalid: {e}')
try:
 m=json.loads(pack.read_text()); sem={a['semantic_id'] for a in m.get('assets',[])}
 for s in ('lpc.repository.inventory.contract','lpc.repository.import.profile','lpc.repository.external.root'):
  if s not in sem: errors.append(f'LPC pack missing {s}')
 if m.get('production_enabled') is not False: errors.append('LPC Revised must remain production-disabled pending source review')
except Exception as e: errors.append(f'LPC pack invalid: {e}')
# Run scanner against an empty temporary mount to prove graceful missing-source behavior.
out=ROOT/'WORKSPACE/generated/validator_lpc_revised_inventory_v148x.json'
proc=subprocess.run([sys.executable,str(ROOT/'tools/automation/project/Build-LpcRevisedInventoryV148X.py'),'--source','WORKSPACE/missing_lpc_revised_for_validator','--output',str(out)],capture_output=True,text=True)
if proc.returncode!=0: errors.append('inventory scanner failed graceful missing-source run: '+proc.stderr)
else:
 try:
  inv=json.loads(out.read_text())
  if inv.get('schema')!='havenwild.lpc_revised_repository_inventory.v1': errors.append('generated inventory schema mismatch')
  if not inv.get('diagnostics'): errors.append('missing source was not reported diagnostically')
 except Exception as e: errors.append(f'generated inventory invalid: {e}')
try: out.unlink()
except OSError: pass
if errors:
 print('Pass 148X FAILED')
 for e in errors: print('-',e)
 sys.exit(1)
print(f'Pass 148X LPC Revised full-repository inventory validated ({len(required)} categories)')
