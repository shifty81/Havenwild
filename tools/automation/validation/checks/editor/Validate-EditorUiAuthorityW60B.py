#!/usr/bin/env python3
from pathlib import Path
import json, sys

ROOT = Path(__file__).resolve().parents[5]
errors = []

def read(rel):
    p = ROOT / rel
    if not p.is_file():
        errors.append(f"missing {rel}"); return ""
    return p.read_text(encoding="utf-8")

def need(rel, *markers):
    s = read(rel)
    for marker in markers:
        if marker not in s:
            errors.append(f"{rel} missing marker: {marker}")

def need_any(rel, groups, label):
    s = read(rel)
    if not any(all(m in s for m in group) for group in groups):
        errors.append(f"{rel} missing {label}")

need("apps/haven_editor_native/src/app/editor_text.rs", 'DEFAULT_EDITOR_TEXT_SCALE: f32 =', 'fonts.join("segoeui.ttf")', 'prewarm_editor_font()', 'HAVENWILD_EDITOR_TEXT_SCALE')
# W79 supersedes W60B's historical 1.15 default with the compact 1.10 authority.
# W60B continues to certify the font lifecycle and scalable-text contract; the
# current exact default is owned by Validate-NativeEditorInteractionDocumentClosureW79.py.
font = read("apps/haven_editor_native/src/app/editor_text.rs")
if "HAVENWILD_EDITOR_EXPERIMENTAL_SYSTEM_FONT" in font:
    errors.append("Segoe UI must not be hidden behind an experimental opt-in")
mod = read("apps/haven_editor_native/src/app/mod.rs")
init = mod.find("editor_text::initialize_editor_font()")
prewarm = mod.find("editor_text::prewarm_editor_font()")
bootstrap = mod.find('draw_bootstrap_screen("Opening editor window...", 0.03)')
font_stage = mod.find('draw_bootstrap_screen("Preparing editor font atlas...", 0.10)')
rich_visible = mod.find('"Editor typography ready"')
first_frame = mod.find("next_frame().await;")
if min(init, prewarm, bootstrap, font_stage, rich_visible, first_frame) < 0:
    errors.append("startup font/progress lifecycle markers are incomplete")
elif not (bootstrap < first_frame < font_stage < init < prewarm < rich_visible):
    errors.append("bootstrap progress must render before Segoe prewarm; normal editor-font startup text must follow prewarm")
if "STARTUP PHASE font atlas ready" not in mod or "STARTUP COMPLETE editor interactive" not in mod:
    errors.append("startup phase timing telemetry missing")
if mod.count("initialize_editor_font()") != 1:
    errors.append("font atlas must initialize exactly once")

need("apps/haven_editor_native/src/app/canvas_layers.rs", "CANVAS_TOOL_RACK_WIDTH: f32 =", "canvas_layer_rail_expanded_width", "canvas_authoring_left_inset", "EYE_ZONE_W: f32 =", "LOCK_ZONE_W: f32 =")
# H6 widens the persisted Layers splitter range while retaining the same default width.
need("apps/haven_editor_native/src/app/workspace_shell.rs", "canvas_layer_rail_width: f32", "canvas_layer_rail_width: 174.0", "clamp(132.0, 480.0)")
need("apps/haven_editor_native/src/app/canvas_controller.rs", "canvas_authoring_left_inset", "canvas_workspace_layout")
# W76 supersedes raw host/left-inset literals with one protected CanvasWorkspace.
need_any("apps/haven_editor_native/src/app/pixel_studio_render.rs", [
    ("canvas_workspace_layout().viewport", "Tool Rail + Layers remain outside the canvas"),
    ("let left = self.canvas_authoring_left_inset();",),
], "Pixel Studio rail-safe canvas authority")
need_any("apps/haven_editor_native/src/app/scene_bank_workspace.rs", [
    ("canvas_workspace_layout().viewport", "canvas_workspace_layout().context_toolbar"),
    ("canvas_authoring_left_inset", "canvas_host_rect"),
], "Scene Bank protected CanvasWorkspace authority")
for rel in ["apps/haven_editor_native/src/app/animation_studio.rs", "apps/haven_editor_native/src/app/animation_studio_input.rs"]:
    need_any(rel, [("canvas_workspace_layout().workspace_body",), ("canvas_authoring_left_inset", "canvas_host_rect")], "Animation Studio protected workspace body")
need_any("apps/haven_editor_native/src/app/character_studio.rs", [("canvas_workspace_layout().workspace_body", "Character Wardrobe"), ("let left = self.canvas_authoring_left_inset();",)], "Character Studio protected workspace body")
need("apps/haven_editor_native/src/app/island_workspace.rs", "canvas_authoring_left_inset")
need("apps/haven_editor_native/src/app/canvas_workspace.rs", "DOCUMENT_TAB_H", "CONTEXT_TOOLBAR_H", "RULER_H", "ruler_and_canvas_never_overlap_document_tabs")

contract_path = ROOT / "content/editor/native_editor_ui_authority_w60b_v1.json"
if not contract_path.is_file():
    errors.append("missing W60B editor UI authority contract")
else:
    data = json.loads(contract_path.read_text(encoding="utf-8"))
    if data.get("font", {}).get("primary") != "Windows Segoe UI": errors.append("W60B contract must keep Segoe UI as primary")
    if data.get("canvasChrome", {}).get("overlapAuthoringViewport") is not False: errors.append("W60B contract must prohibit layer/tool overlay on authoring viewport")

if errors:
    print("FAIL: W60B editor UI authority"); [print(" -", e) for e in errors]; sys.exit(1)
print("PASS: W60B editor UI authority (W76 CanvasWorkspace-compatible)")
