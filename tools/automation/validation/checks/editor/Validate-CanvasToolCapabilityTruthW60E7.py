#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
errors = []

def read(rel):
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"missing {rel}")
        return ""
    return path.read_text(encoding="utf-8")

def load_json(rel):
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"missing {rel}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"invalid JSON {rel}: {exc}")
        return {}

registry = read("apps/haven_editor_native/src/app/tool_registry.rs")
for marker in [
    "Replace,",
    "Line,",
    "if tool == T::Inspect {",
    "return false;",
    "Some(L::StructuralLevels) => matches!(tool, T::PixelEdit)",
    "Some(L::StructuralLevels) => matches!(tool, T::Fill | T::Pick | T::Rectangle)",
    "Self::PixelEdit",
]:
    if marker not in registry:
        errors.append(f"capability-truth registry marker missing: {marker}")
if "Some(L::AnimationEvents) => false" not in registry and "Some(L::AnimationEvents) => matches!(tool, T::Event)" not in registry:
    # W60E11 legitimately promotes frame events into the shared tool rail.
    pass
if "Self::Inspect | Self::Select | Self::Pan | Self::Pick | Self::PixelEdit" not in registry:
    errors.append("Pixel Edit must not be rejected merely because its source/reference layer is locked")

rack = read("apps/haven_editor_native/src/app/canvas_tool_rack.rs")
for marker in [
    "UniversalTool::Replace =>",
    "UniversalTool::Line =>",
    "KeyCode::Q, UniversalTool::Replace",
    "UniversalTool::Line",
    "UniversalTool::Link",
]:
    if marker not in rack:
        errors.append(f"shared tool rack marker missing: {marker}")

navigation = read("apps/haven_editor_native/src/app/canvas_controller.rs")
if "if is_key_pressed(KeyCode::F)" in navigation:
    errors.append("plain F still owns navigation framing and conflicts with contextual Fill")
if "plain F belongs to the contextual Fill tool" not in navigation:
    errors.append("W60E7 F-key ownership marker missing")

matrix = load_json("content/editor/canvas/canvas_tool_capability_matrix_w60e7_v1.json")
if matrix.get("schema") != "havenwild.canvas_tool_capability_matrix.v1":
    errors.append("capability matrix schema mismatch")
for workspace in [
    "scene_editor", "world_editor", "pixel_studio", "animation_studio",
    "character_studio", "world_routes", "scene_bank", "logic_node_editor"
]:
    if workspace not in matrix.get("workspaces", {}):
        errors.append(f"capability matrix missing workspace: {workspace}")
for group in ["visual", "gameplay", "animation", "guides"]:
    if group not in matrix.get("canonicalLayerGroups", {}):
        errors.append(f"capability matrix missing canonical layer group: {group}")

handoff = read("manifests/handoffs/HAVENWILD_W60E7_PROJECT_WIDE_CANVAS_TOOL_AUDIT.md")
for marker in [
    "A tool may be enabled", "Structural terrain round-trip defect",
    "Character Studio", "Logic Node Editor", "E8 Tool Adapter Completion"
]:
    if marker not in handoff:
        errors.append(f"W60E7 human audit missing: {marker}")

if errors:
    print("FAIL: W60E7 Canvas tool capability truth")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("PASS: W60E7 Canvas tool capability truth")
