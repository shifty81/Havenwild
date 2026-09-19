#!/usr/bin/env python3
"""Fail-closed B48R11 source identity and audit schema guard; NOT a visual/runtime certification."""
import hashlib, json, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[5]
MAP=ROOT/'content/assets/lpc/elizawy_cliff_water_role_audit_b48r11_v0_1.json'
BLOB=ROOT/'content/assets/lpc/source_blobs/elizawy_mountain_waterfall_transitions_summer.png.source'
SOURCE=ROOT/'assets/source/licensed/lpc_revised/Terrain/Mountain, Waterfall Transitions (Summer).png'
PREDECESSOR=ROOT/'content/assets/lpc/elizawy_mountain_waterfall_transition_source_b48r8_v0_1.json'
W14=ROOT/'content/worldgen/elizawy_cliff_source_grammar_authority_v0_1.json'
def digest(b):return hashlib.sha256(b).hexdigest()
def check():
 m=json.loads(MAP.read_text(encoding='utf8'))
 assert m['schema']=='havenwild.elizawy.cliff_water_mapping_audit.b48r11.v0_1'
 assert m['productionEnabled'] is False and m['editorClientRecipeEnabled'] is False and m['validForWorldgenPlacement'] is False
 p=json.loads(PREDECESSOR.read_text(encoding='utf8'))
 assert p['productionEnabled'] is False
 assert m['source']['sha256']==p['authority']['sourceSha256']
 assert digest(BLOB.read_bytes())==m['source']['sha256']
 assert SOURCE.read_bytes()==BLOB.read_bytes()
 assert json.loads(W14.read_text(encoding='utf8'))['ordinarySouthRoles']['straight']['crest']==[2,7]
 cells=m['transitionCells']; assert len(cells)==42
 assert len({(x['col'],x['row']) for x in cells})==42
 assert all(x['runtimeEligible'] is False and x['opaquePx']+x['transparentPx']+x['partialAlphaPx']==1024 for x in cells)
 assert {(x['col'],x['row']) for x in cells if x['function']=='transparent_not_a_tile'}=={(4,6),(5,6)}
 assert sum(x['function']!='transparent_not_a_tile' for x in cells)==40
 groups=m['sourceLayoutWindows'];assert len(groups)==6
 assert m['measurements']['b48r10RecoveredTransitionPlacements']==0
 assert m['measurements']['b48r10VisualApproval'] is False
 print('PASS B48R11 source SHA, retained mount, W14 ownership, 42 distinct addresses, 40 artwork/2 empty, disabled runtime')
if __name__=='__main__':
 try: check()
 except Exception as e: print('FAIL B48R11:',e,file=sys.stderr);sys.exit(1)
