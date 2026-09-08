#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[5]; errors=[]
def read(rel):
 p=ROOT/rel
 if not p.is_file(): errors.append(f"missing {rel}"); return ""
 return p.read_text(encoding="utf-8")
view=read("apps/haven_editor_native/src/app/canvas_view.rs")
for m in ["pub(crate) const CANVAS_RULER_THICKNESS: f32 = 24.0;", "viewport.y - CANVAS_RULER_THICKNESS", "viewport.x - CANVAS_RULER_THICKNESS", "fn adaptive_ruler_step", "fn format_ruler_value"]:
 if m not in view: errors.append("canvas ruler authority missing: "+m)
workspace=read("apps/haven_editor_native/src/app/canvas_workspace.rs")
for m in ["RULER_H", "RULER_W", "pub document_tabs: Rect", "pub context_toolbar: Rect", "pub viewport: Rect", "viewport_x = host.x + RULER_W", "viewport_y = body_y + RULER_H", "ruler_and_canvas_never_overlap_document_tabs"]:
 if m not in workspace: errors.append("W76 ruler-safe CanvasWorkspace geometry missing: "+m)
layers=read("apps/haven_editor_native/src/app/canvas_layers.rs")
for m in ["canvas_content_host_rect", "canvas_layer_rail_rect", "canvas_workspace_layout().workspace_body"]:
 if m not in layers: errors.append("layer/canvas geometry bridge missing: "+m)
scene=read("apps/haven_editor_native/src/app/draw_scene_views.rs")
if scene.count("canvas_workspace_layout().context_toolbar") < 1: errors.append("Scene/World context toolbar must use CanvasWorkspace")
if "scene_canvas_viewport_rect()" not in scene: errors.append("Scene canvas must use protected CanvasWorkspace viewport")
bank=read("apps/haven_editor_native/src/app/scene_bank_workspace.rs")
for m in ["canvas_workspace_layout().viewport", "canvas_workspace_layout().context_toolbar"]:
 if m not in bank: errors.append("Scene Bank must use protected CanvasWorkspace: "+m)
if errors:
 print("FAIL: W60D ruler-safe canvas corner layer dock"); [print(" -",e) for e in errors]; sys.exit(1)
print("PASS: W60D ruler-safe canvas corner layer dock (W76 geometry)")
