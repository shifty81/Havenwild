#!/usr/bin/env python3
from pathlib import Path
import json, subprocess, sys, tempfile
ROOT = Path(__file__).resolve().parents[5]
errors=[]
def req(path,tokens=()):
 p=ROOT/path
 if not p.is_file(): errors.append(f'missing {path}'); return ''
 text=p.read_text(encoding='utf-8')
 for token in tokens:
  if token not in text: errors.append(f'{path} missing {token}')
 return text
req('tools/automation/project/Build-LpcMappingQueuesV148Y.py',['QUEUE_BY_CATEGORY','license_review','promotion_state','map_and_preview'])
req('crates/haven_assets/src/lpc_mapping_queue.rs',['LpcMappingQueues','LpcMappingQueueItem','stable_ref','havenwild.lpc_revised_mapping_queues.v1'])
req('crates/haven_assets/src/lib.rs',['pub mod lpc_mapping_queue;'])
req('crates/haven_assets/src/asset_browser.rs',['collect_lpc_mapping_queues','queue:','promotion:','Build-LpcMappingQueuesV148Y.py'])
contract=ROOT/'content/asset_packs/lpc_revised/lpc_mapping_queue_contract_v1.json'
try:
 c=json.loads(contract.read_text())
 if len(c.get('queues',[]))<10: errors.append('mapping queue breadth too narrow')
 rules=c.get('rules',{})
 for key in ('all_inventory_entries_must_enter_exactly_one_queue','license_review_precedes_production_promotion','content_library_must_show_reference_only_entries','mapping_is_incremental_and_category_neutral'):
  if rules.get(key) is not True: errors.append(f'queue contract missing rule {key}')
except Exception as e: errors.append(f'queue contract invalid: {e}')
fixture={
 'schema':'havenwild.lpc_revised_repository_inventory.v1','diagnostics':[],
 'files':[
  {'relative_path':'characters/body.png','source_kind':'image','category':'character','proposed_asset_id':'characters.body','proposed_semantic_id':'lpc.character.characters.body','tags':['character'],'dimensions':[832,1344],'frame_cell':[64,96],'animation_family':'walkcycle','nearby_license_files':['AUTHORS.txt'],'readiness':'manual_mapping_required'},
  {'relative_path':'terrain/grass.png','source_kind':'image','category':'terrain','proposed_asset_id':'terrain.grass','proposed_semantic_id':'lpc.terrain.terrain.grass','tags':['terrain'],'dimensions':[512,512],'frame_cell':[32,32],'animation_family':None,'nearby_license_files':[],'readiness':'license_review_required'}
 ]}
with tempfile.TemporaryDirectory() as td:
 td=Path(td); src=td/'inventory.json'; out=td/'queues.json'; src.write_text(json.dumps(fixture))
 proc=subprocess.run([sys.executable,str(ROOT/'tools/automation/project/Build-LpcMappingQueuesV148Y.py'),'--inventory',str(src),'--output',str(out)],capture_output=True,text=True)
 if proc.returncode: errors.append('queue generator failed: '+proc.stderr)
 else:
  q=json.loads(out.read_text()); total=sum(q['queue_counts'].values())
  if total!=2: errors.append('queue generator lost or duplicated inventory entries')
  if len(q['queues']['license_review'])!=1: errors.append('license review queue routing failed')
  if len(q['queues']['characters'])!=1: errors.append('character queue routing failed')
if errors:
 print('Pass 148Y FAILED')
 for e in errors: print('-',e)
 sys.exit(1)
print('Pass 148Y generated LPC mapping queues and Content Library integration validated')
