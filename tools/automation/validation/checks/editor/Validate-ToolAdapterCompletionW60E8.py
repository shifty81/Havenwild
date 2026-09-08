#!/usr/bin/env python3
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[5]; errors=[]
def t(x):
 p=R/x
 if not p.is_file(): errors.append('missing '+x); return ''
 return p.read_text(encoding='utf-8')
reg=t('apps/haven_editor_native/src/app/tool_registry.rs'); rack=t('apps/haven_editor_native/src/app/canvas_tool_rack.rs'); prod=t('apps/haven_editor_native/src/app/production_tools.rs'); dock=t('apps/haven_editor_native/src/app/object_inspector.rs'); routes=t('apps/haven_editor_native/src/app/island_workspace.rs')
for m in ['T::Select | T::Place | T::Move | T::Pick | T::Erase | T::PixelEdit','V::RegionGraph','V::SceneBank']:
 if m not in reg: errors.append('missing E8 registry '+m)
for m in ['canvas_active_tool = tool','EditorViewportMode::RegionGraph','EditorViewportMode::SceneBank']:
 if m not in rack: errors.append('missing E8 rack '+m)
if 'UniversalTool::Move' not in prod: errors.append('explicit Move adapter missing')
# W76 removed the legacy Scene Dock. If it still exists, it must not expose Tools.
if 'pub(crate) fn draw_scene_dock' in dock:
 section=dock.split('pub(crate) fn draw_scene_dock',1)[1].split('fn draw_terrain_tuple_inspector',1)[0]
 if '"Tools"' in section: errors.append('duplicate visible Scene Tools tab remains')
if 'connect_harbor_route_to_selected' not in routes: errors.append('route Link adapter missing')
scene=t('apps/haven_editor_native/src/app/scene_authoring.rs')
for m in ['self.place_building_instance_at_scene_cursor();','self.delete_building_instance_at_scene_cursor();']:
 if m not in scene: errors.append('building adapter missing '+m)
if errors:
 print('FAIL: W60E8 tool adapter completion'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: W60E8 tool adapter completion (legacy Scene Dock optional/retired)')
