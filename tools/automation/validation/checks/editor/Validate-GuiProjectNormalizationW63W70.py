#!/usr/bin/env python3
from pathlib import Path
import json, sys, tomllib
ROOT=Path(__file__).resolve().parents[5]
errors=[]
def text(path):
    p=ROOT/path
    if not p.exists(): errors.append(f"missing {path}"); return ''
    return p.read_text(encoding='utf-8')
def require(path,*markers):
    s=text(path)
    for marker in markers:
        if marker not in s: errors.append(f"{path} missing marker: {marker}")

def json_ok(path,schema):
    p=ROOT/path
    if not p.exists(): errors.append(f"missing {path}"); return
    try: d=json.loads(p.read_text(encoding='utf-8'))
    except Exception as e: errors.append(f"{path} invalid JSON: {e}"); return
    if d.get('schema')!=schema: errors.append(f"{path} schema mismatch: {d.get('schema')}")

for path,schema in [
 ('content/editor/gui/gui_normalization_w63_v1.json','havenwild.editor.gui_normalization.w63.v1'),
 ('content/editor/gui/document_host_w64_v1.json','havenwild.editor.document_host.w64.v1'),
 ('content/editor/gui/palette_tray_unified_assets_w65_v1.json','havenwild.editor.palette_assets.w65.v1'),
 ('content/editor/canvas/infinite_canvas_w66_v1.json','havenwild.editor.infinite_canvas.w66.v1'),
 ('content/architecture/oss_ui_foundation_w67_v1.json','havenwild.architecture.oss_ui_foundation.w67.v1'),
 ('content/architecture/project_scale_foundation_w68_v1.json','havenwild.architecture.project_scale_foundation.w68.v1'),
 ('content/architecture/diagnostics_hot_reload_w69_v1.json','havenwild.architecture.diagnostics_hot_reload.w69.v1'),
 ('content/architecture/project_normalization_w70_v1.json','havenwild.architecture.project_normalization.w70.v1')]: json_ok(path,schema)

require('apps/haven_editor_native/src/app/workspace_shell.rs','RightDockTab','DocumentSplitMode','workspace_layout.v0_4','self.left_panel_visible = false','self.asset_shelf_open = false')
require('apps/haven_editor_native/src/app/right_dock.rs','Properties','Assets','Outliner','Validation','contextual_asset_browser_rect','focus_right_dock')
require('apps/haven_editor_native/src/app/draw.rs','draw_right_dock(&validation)')
if not (ROOT/'content/editor/gui/canvas_chrome_alignment_w72d_v1.json').exists():
    require('apps/haven_editor_native/src/app/draw.rs','draw_panel(layout.center_panel, "Canvas")')
if 'draw_universal_asset_shelf();' in text('apps/haven_editor_native/src/app/draw.rs'): errors.append('draw.rs still renders legacy Asset Shelf')
if 'draw_scene_dock(inspector_rect)' in text('apps/haven_editor_native/src/app/draw.rs'): errors.append('draw.rs still renders nested Scene dock authority')
require('apps/haven_editor_native/src/app/pixel_studio_layout.rs','pixel_document_new_rect','pixel_document_split_rect')
require('apps/haven_editor_native/src/app/pixel_studio_render.rs','pixel_canvas_full_rect','pixel_secondary_canvas_rect','draw_pixel_secondary_preview','DocumentSplitMode::Vertical')
require('apps/haven_editor_native/src/app/pixel_studio_input.rs','pixel_document_new_rect','activate_secondary_document')
require('apps/haven_editor_native/src/app/pixel_color_panel.rs','pixel_color_popup_panel(app: &EditorApp)','Palette Color','anchor.y - height - 8.0')
require('apps/haven_editor_native/src/app/transform_gizmo.rs','draw_transform_gizmo(bounds: Rect, pivot: Vec2, active: bool, clip: Rect)','if !transform.canvas.contains(point)','clipped_rect')
require('crates/haven_ui/src/lib.rs','Havenwild-owned native-editor UI boundary','mature_backend_names','canvas_first')
try:
    root=tomllib.loads(text('Cargo.toml'))
    members=root.get('workspace',{}).get('members',[])
    if 'crates/haven_ui' not in members: errors.append('Cargo workspace missing crates/haven_ui')
    deps=root.get('workspace',{}).get('dependencies',{})
    for dep in ['taffy','cosmic-text','accesskit','rfd','arboard']:
        if dep not in deps: errors.append(f'workspace dependency missing {dep}')
    meta=root.get('workspace',{}).get('metadata',{}).get('havenwild',{}).get('mature_oss',{})
    for dep in ['tracing','notify','uuid','rstar','petgraph','parry2d']:
        if dep not in meta: errors.append(f'mature OSS intake metadata missing {dep}')
except Exception as e: errors.append(f'Cargo.toml parse failed: {e}')

if errors:
    print('FAIL: W63-W70 GUI/project normalization')
    for e in errors: print(' -',e)
    sys.exit(1)
print('PASS: W63-W70 GUI/project normalization')
