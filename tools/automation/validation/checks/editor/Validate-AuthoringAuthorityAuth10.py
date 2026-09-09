#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[5]
def read(p): return (root/p).read_text(encoding='utf-8')
s=read('apps/haven_editor_native/src/app/authoring_session.rs')
t=read('apps/haven_editor_native/src/app/tool_registry.rs')
l=read('apps/haven_editor_native/src/app/canvas_layers.rs')
m=read('apps/haven_editor_native/src/app/mod.rs')
checks={
 'WorkspaceId canonical set': all(x in s for x in ['GameCanvas','Assets','Pixel','Animation','Character','Data','Logic','Sound']),
 'Data reserved unavailable': 'Self::Data' in s and 'available' in s,
 'GameCanvasView contextual': all(x in s for x in ['World','Scene(','SceneLibrary','Routes','Ui(']),
 'AuthoringSession spine': 'struct AuthoringSession' in s and 'active_document' in s and 'active_layer' in s and 'active_tool' in s and 'edit_scope' in s,
 'EditorContextSnapshot read model': 'struct EditorContextSnapshot' in s,
 'Palette provider authority': 'enum PaletteProviderId' in s and 'for_context' in s,
 'UniversalTool preserved': 'enum UniversalTool' in t,
 'Disabled tool explanation': 'struct ToolAvailability' in t and 'reason:' in t,
 'Layer authority flags': all(x in l for x in ['pub generated: bool','pub derived: bool','pub diagnostic: bool','pub writable: bool']),
 'Session registered once': m.count('mod authoring_session;') == 1,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('[PASS] ' if v else '[FAIL] ')+k)
if failed: sys.exit(1)
print('PASS HW-AUTHORITY-10 static authority contract')
