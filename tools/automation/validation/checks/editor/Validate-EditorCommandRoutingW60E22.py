#!/usr/bin/env python3
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[5]; errors=[]
def t(p): return (R/p).read_text(encoding='utf-8') if (R/p).is_file() else ''
try:
 d=json.loads(t('content/editor/ui/editor_command_routing_w60e22_v1.json'))
 if d.get('schema')!='havenwild.editor_command_routing.w60e22.v1': errors.append('E22 schema mismatch')
except Exception as e: errors.append('E22 contract invalid: '+str(e))
menu=t('apps/haven_editor_native/src/app/editor_menu.rs'); registry=t('apps/haven_editor_native/src/app/command_registry.rs')
for marker in ['Self::File','Self::Edit','Self::View','Self::World','Self::Scene','Self::Asset','Self::Build','Self::Tools','Self::Help','copy_contextual_selection','cut_contextual_selection','paste_contextual_selection','duplicate_contextual_selection','mirror_contextual_selection','promote_contextual_selection']:
 if marker not in menu: errors.append('command routing marker missing '+marker)
for marker in ['FILE_COMMANDS','EDIT_COMMANDS','VIEW_COMMANDS','WORLD_COMMANDS','SCENE_COMMANDS','ASSET_COMMANDS','BUILD_COMMANDS','TOOLS_COMMANDS','HELP_COMMANDS','nine_menu_groups_are_registered']:
 if marker not in registry: errors.append('canonical command registry missing '+marker)
if 'HAVENWILD NATIVE EDITOR' in menu: errors.append('redundant internal application title returned to menu shell')
if errors:
 print('FAIL: W60E22 editor command routing'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: W60E22 editor command routing (nine-menu command registry)')
