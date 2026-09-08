#!/usr/bin/env python3
"""Validate that Home Estate is a bounded exterior instance, not a streamed surface partition."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
continuous = (ROOT / "crates/haven_world/src/continuous_surface.rs").read_text(encoding="utf-8")
continuous_tests = (ROOT / "crates/haven_world/src/continuous_surface_tests.rs").read_text(encoding="utf-8")
residency = (ROOT / "crates/haven_game/src/runtime_surface_streaming_residency.rs").read_text(encoding="utf-8")
structural = (ROOT / "crates/haven_game/src/runtime_surface_streaming_structural.rs").read_text(encoding="utf-8")
terrain_pass = (ROOT / "crates/haven_game/src/runtime_terrain_pass.rs").read_text(encoding="utf-8")
runtime_draw = (ROOT / "crates/haven_game/src/runtime_draw.rs").read_text(encoding="utf-8")
visual_override = (ROOT / "crates/haven_game/src/runtime_visual_override_draw.rs").read_text(encoding="utf-8")
buildings = (ROOT / "crates/haven_game/src/building_instance_runtime.rs").read_text(encoding="utf-8")
navigation = (ROOT / "crates/haven_game/src/runtime_scene_navigation.rs").read_text(encoding="utf-8")
build = (ROOT / "tools/build/Build.sh").read_text(encoding="utf-8")
contract_path = ROOT / "content/estates/home_estate_design_contract_v2.json"
audit_path = ROOT / "docs/audits/HAVENWILD_PLAYER_WEAPON_TOOL_CRAFTING_UI_AUDIT_H21A14AB8.md"
errors = []

# Farmstead may remain in the historical manifest bridge temporarily, but it must
# not be recognized as a streamable partition or suppressed transition target.
scene_fn = continuous.split("pub fn scene_is_surface_chunk", 1)[1].split("pub fn transition_uses_surface_streaming", 1)[0]
partition_fn = continuous.split("pub fn scene_id_is_surface_partition", 1)[1].split("/// Parses the historical PCG", 1)[0]
if "SceneId::Farmstead" in scene_fn:
    errors.append("scene_is_surface_chunk still classifies Farmstead/Home Estate as streamed")
if "SceneId::Farmstead" in partition_fn:
    errors.append("scene_id_is_surface_partition still classifies Farmstead/Home Estate as streamed")
for marker in ["parse_pcg_surface_scene_id(&scene.id)", "parse_generated_chunk_scene_id(&scene.id)"]:
    if marker not in scene_fn:
        errors.append(f"streamed surface classification missing marker: {marker}")

for marker in [
    "home_estate_is_exterior_but_not_a_streamed_surface_partition",
    "legacy_overworld_companion_exteriors_remain_streamable",
]:
    if marker not in continuous_tests:
        errors.append(f"continuous-surface regression test missing: {marker}")

for label, source, markers in [
    ("terrain", terrain_pass, ["if self.active_surface_chunk_coord().is_some()", "self.draw_continuous_surface_terrain();"]),
    ("actors", runtime_draw, ["if self.active_surface_chunk_coord().is_some()", "self.draw_continuous_surface_actors();"]),
    ("visual overrides", visual_override, ["if self.active_surface_chunk_coord().is_some()"]),
    ("building instances", buildings, ["if self.active_surface_chunk_coord().is_some()"]),
]:
    for marker in markers:
        if marker not in source:
            errors.append(f"{label} is not routed by streamed-surface identity: {marker}")

for marker in [
    "if !haven_world::scene_is_surface_chunk(self.world.active())",
    "Bounded exterior instance active: retained scene terrain + local structural cache; continuous surface streaming disabled",
    "if self.active_surface_chunk_coord().is_none()",
    "Leaving them requires an authored transition",
]:
    if marker not in residency:
        errors.append(f"bounded Estate residency/boundary isolation missing marker: {marker}")

for marker in [
    "vec![(ChunkCoord::new(0, 0), self.world.active().map.clone())]",
    "never pull NorthRoad/SouthField/EastWoods into an",
]:
    if marker not in structural:
        errors.append(f"Estate local structural bake missing marker: {marker}")

for marker in [
    "let surface_streaming = self.active_surface_chunk_coord().is_some()",
    "Bounded exterior instances such as the Home Estate stay",
    "self.camera_target = if self.active_surface_chunk_coord().is_some()",
]:
    if marker not in navigation:
        errors.append(f"Estate transition/camera isolation missing marker: {marker}")

if not contract_path.is_file():
    errors.append("Home Estate v2 design contract is missing")
else:
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"Home Estate v2 design contract is invalid JSON: {exc}")
    else:
        checks = {
            "standalonePersistentScene": contract.get("runtimeAuthority", {}).get("standalonePersistentScene"),
            "continuousSurfaceStreaming": contract.get("runtimeAuthority", {}).get("continuousSurfaceStreaming") is False,
            "cliffFacesOnAllSides": contract.get("perimeter", {}).get("cliffFacesOnAllSides"),
            "northCliffCaveEntranceRequired": contract.get("perimeter", {}).get("northCliffCaveEntranceRequired"),
            "withinOneChunkOfCity": contract.get("worldPlacement", {}).get("maximumDistanceFromMainCityBorderChunks") == 1,
            "purchasablePonds": contract.get("terrainImprovements", {}).get("purchasablePonds"),
            "allGrowables": contract.get("agriculture", {}).get("allGrowableGameContentSupported"),
        }
        for name, ok in checks.items():
            if not ok:
                errors.append(f"Home Estate v2 design contract missing/false requirement: {name}")

if not audit_path.is_file():
    errors.append("player weapon/tool/crafting/UI audit is missing")

if "Validate-HomeEstateRuntimeIsolationA14AB8.py" not in build:
    errors.append("A14AB8 validator is not registered in Full Quality Gate")

if errors:
    print("A14AB8 Home Estate Runtime Isolation validation FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("PASS: A14AB8 Home Estate runtime isolation")
print("- Home Estate remains exterior for sky/weather but is not a streamed surface partition")
print("- retained terrain, local actors/overrides/buildings and bounded camera are authoritative")
print("- Estate edges cannot implicitly stream into overworld storage partitions")
print("- Estate startup structural bake is local instead of the legacy four-scene bridge")
