#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[5]; errors=[]
def read(rel):
 p=ROOT/rel
 if not p.is_file(): errors.append(f"missing {rel}"); return ""
 return p.read_text(encoding="utf-8")
layers=read("apps/haven_editor_native/src/app/canvas_layers.rs")
for m in ["canvas_content_host_rect","canvas_layer_context_override","active_canvas_layer_locked","canvas_workspace_layout().workspace_body","self.set_scene_layer_mode(mode)","self.set_world_layer_mode(WorldLayerMode::Terrain)"]:
 if m not in layers: errors.append("CanvasWorkspace layer authority missing: "+m)
scene=read("apps/haven_editor_native/src/app/scene_authoring.rs"); world=read("apps/haven_editor_native/src/app/world_surface_authoring.rs")
if "self.scene_edit_tool = SceneEditTool::Select" not in scene: errors.append("scene layer changes must return to Select")
if "self.world_edit_tool = WorldEditTool::Select" not in world: errors.append("world layer changes must return to Select")
if "self.canvas_layer_context_override = None" not in scene or "self.canvas_layer_context_override = None" not in world: errors.append("canonical semantic layer switches must clear synthetic layer context")
rack=read("apps/haven_editor_native/src/app/canvas_tool_rack.rs")
for m in ["universal_tool_available","active_canvas_layer_locked","tool.mutates_document()"]:
 if m not in rack: errors.append("tool rack availability missing: "+m)
registry=read("apps/haven_editor_native/src/app/tool_registry.rs")
# R30-R44 semantic-layer convergence split Building behavior by canvas authority.
# SceneMap owns the complete wired building/structure/furniture/prop adapter set,
# while the complete-world SceneRectangles canvas advertises only Pixel Edit for
# Buildings until transform/place adapters are genuinely world-surface aware.
scene_building_semantics = (
    "Some(L::Buildings) | Some(L::Structures) | Some(L::Furniture) | Some(L::Props)" in registry
    and "Some(L::Lighting) | Some(L::Effects) => matches!(tool, T::Select | T::Place | T::Move | T::Pick | T::Erase | T::PixelEdit)" in registry
)
world_building_semantics = "Some(L::Buildings) => matches!(tool, T::PixelEdit)" in registry
if not scene_building_semantics:
 errors.append("scene building semantic layers must expose the truthful wired adapter set")
if not world_building_semantics:
 errors.append("complete-world building layer must remain fail-closed to its currently wired Pixel Edit adapter")
pixel=read("apps/haven_editor_native/src/app/pixel_studio.rs")
segment=pixel[pixel.find("enum PixelInspectorTab"):pixel.find("enum PixelSelectionMode")]
if "Layers," in segment: errors.append("Pixel Inspector must not retain duplicate Layers tab")
render=read("apps/haven_editor_native/src/app/pixel_studio_render.rs"); color=read("apps/haven_editor_native/src/app/pixel_color_panel.rs"); shared=read("apps/haven_editor_native/src/app/shared_palette.rs")
if '"Properties"' not in render or "PixelInspectorTab::Animation" not in render: errors.append("Pixel Inspector normalized core tabs missing")
if not ("color_wheel_center" in color and "pixel_color_popup_open" in shared): errors.append("Pixel color editing surface missing")
scene_draw=read("apps/haven_editor_native/src/app/draw_scene_views.rs")
if "canvas_workspace_layout().context_toolbar" not in scene_draw: errors.append("Scene/World toolbars must use CanvasWorkspace context toolbar")
workspace=read("apps/haven_editor_native/src/app/canvas_workspace.rs")
for m in ["document_tabs", "context_toolbar", "viewport", "ruler_and_canvas_never_overlap_document_tabs"]:
 if m not in workspace: errors.append("W76 CanvasWorkspace missing: "+m)
contract=ROOT/"content/editor/canvas_workspace_authority_w60e3_v1.json"
if not contract.is_file(): errors.append("missing W60E3 CanvasWorkspace contract")
else:
 data=json.loads(contract.read_text(encoding="utf-8"))
 if data.get("schema")!="havenwild.canvas_workspace_authority.w60e3.v1": errors.append("W60E3 contract schema mismatch")
 if data.get("interaction",{}).get("defaultModifyingToolOnLayerSelect") is not False: errors.append("layer selection must be non-destructive")
 if data.get("canvasChrome",{}).get("rightInspectorMayDuplicateLayers") is not False: errors.append("right Inspector must not duplicate layers")
if errors:
 print("FAIL: W60E3 CanvasWorkspace authority"); [print(" -",e) for e in errors]; sys.exit(1)
print("PASS: W60E3 CanvasWorkspace authority (W76 protected-layout compatible)")
