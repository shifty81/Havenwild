#!/usr/bin/env python3
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[5]; errors=[]
try:
 data=json.loads((R/'content/editor/logic/logic_node_editor_contract_w60e18_v1.json').read_text(encoding='utf-8'))
 if data.get('schema')!='havenwild.logic_node_editor_contract.w60e18.v1': errors.append('E18 schema mismatch')
 for key in ['select','pan','place','move','link','rectangle']:
  if key not in data.get('sharedTools',{}): errors.append('node shared tool map missing '+key)
except Exception as e: errors.append('E18 contract invalid: '+str(e))
# E18 was an architecture lock before exposure. Later W62/W76 work legitimately exposed a
# deterministic graph editor. Validate the superseding implementation instead of rejecting it.
logic=(R/'apps/haven_editor_native/src/app/logic_studio.rs').read_text(encoding='utf-8') if (R/'apps/haven_editor_native/src/app/logic_studio.rs').is_file() else ''
mod=(R/'apps/haven_editor_native/src/app/mod.rs').read_text(encoding='utf-8')
tabs=(R/'apps/haven_editor_native/src/app/document_tabs.rs').read_text(encoding='utf-8') if (R/'apps/haven_editor_native/src/app/document_tabs.rs').is_file() else ''
for m in ['LogicGraph','validate()','compile()','LogicNodeKind','UniversalTool::Place','UniversalTool::Link','UniversalTool::Move','deterministic Havenwild instructions']:
 if m not in logic: errors.append('Logic Studio supersession missing '+m)
for m in ['mod logic_studio;','EditorViewportMode::LogicStudio']:
 if m not in mod: errors.append('Logic Studio module/exposure missing '+m)
if 'EditorViewportMode::LogicStudio' not in tabs: errors.append('Logic Studio missing protected document-tab host')
if errors:
 print('FAIL: W60E18 Logic Node Editor architecture lock'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: W60E18 architecture lock superseded by deterministic Logic Studio implementation')
