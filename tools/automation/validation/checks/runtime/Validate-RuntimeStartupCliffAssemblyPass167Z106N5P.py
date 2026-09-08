#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def fail(message: str) -> None:
    raise SystemExit(f"N5P runtime startup/cliff assembly validation FAILED: {message}")


def text(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        fail(f"missing {rel}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    cliff = text("crates/haven_game/src/runtime_structural_cliff_draw.rs")
    shape_path = ROOT / "crates/haven_game/src/runtime_structural_cliff_shapes.rs"
    shape_text = shape_path.read_text(encoding="utf-8") if shape_path.is_file() else ""
    combined_cliff = cliff + "\n" + shape_text
    if "320.0" not in combined_cliff or "352.0" not in combined_cliff:
        fail("certified straight-face source cells changed unexpectedly")
    forbidden = [
        "for segment in 0..segment_count",
        "segment as f32 * SOUTH_FACE_SOURCE.h",
        "stack complete assemblies",
    ]
    for token in forbidden:
        if token in combined_cliff:
            fail(f"complete 1x3 vertical stacking returned: {token}")
    if "recipe.body" not in cliff or "recipe.foot" not in cliff:
        fail("N5Q successor must still preserve body-only extension plus one foot")

    contract_path = ROOT / "content/worldgen/elizawy_cliff_vertical_assembly_contract_v0_1.json"
    if not contract_path.is_file():
        fail("missing vertical cliff assembly contract")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    face = contract.get("straightSouthFace", {})
    if face.get("verticalRepeat") not in ("forbidden", "forbidden_complete_envelope"):
        fail("complete straight face is not explicitly forbidden as a vertical repeat unit")
    if face.get("containsLowerGrassFoot") is not True:
        fail("grass-foot ownership is not recorded")

    preview = json.loads((ROOT / "content/worldgen/elizawy_cliff_runtime_preview_certification_v0_1.json").read_text(encoding="utf-8"))
    multi_level = preview.get("certifiedRuntimeVisual", {}).get("multiLevelPolicy", "")
    if "single_complete_1x3_face_only" not in multi_level and "single_lower_grass_foot" not in multi_level:
        fail("runtime preview certification no longer protects the single grass-foot rule")

    pack = json.loads((ROOT / "content/asset_packs/lpc_revised/pack.json").read_text(encoding="utf-8"))
    if pack.get("production_enabled") is not False:
        fail("raw LPC Revised repository pack must remain production-disabled")
    license_record = pack.get("license", {})
    for key in ("production_approved", "commercial_use", "redistribution"):
        if license_record.get(key) is not False:
            fail(f"raw LPC Revised repository license gate {key} must be boolean false")

    policy = text("crates/haven_game/src/character_visual_policy.rs")
    if "load_optional_project_character_texture" not in policy:
        fail("optional generated character texture probe is missing")
    if "Path::new(&resolved).is_file()" not in policy:
        fail("optional character candidates are still sent to the texture loader before an existence check")

    frontend = text("crates/haven_game/src/client_frontend.rs")
    if 'if !id.starts_with("body_")' not in frontend:
        fail("character creator preview can again generate body_male_female/body_female_female probes")
    if "load_optional_project_character_texture" not in frontend:
        fail("character creator preview is not using silent optional probes")

    compositor = text("crates/haven_game/src/character_runtime_compositor.rs")
    if "load_optional_project_character_texture" not in compositor:
        fail("runtime compositor is not using silent optional generated-layer probes")

    print("N5P runtime startup and cliff vertical assembly regression validated")


if __name__ == "__main__":
    main()
