#!/usr/bin/env python3
"""C1-C20 structural/conformance guard for Havenwild's normalized ULPC pipeline."""
from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SOURCE = ROOT / "assets/source/licensed/universal_lpc_generator"
RUNTIME = ROOT / "content/characters/universal_lpc_runtime_contract_v1.json"
LAB = ROOT / "content/characters/universal_lpc_character_conformance_lab_v1.json"
LAYER = ROOT / "content/characters/lpc_character_layer_catalog_v1.json"
EQUIPMENT = ROOT / "content/assets/lpc/universal_lpc_equipment_action_catalog_v0_1.json"
SEEDS = ROOT / "content/gameplay/universal_lpc_equipment_item_seed_catalog_v0_1.json"
CANDIDATE = ROOT / "content/assets/intake/universal_lpc_source_upgrade_candidate_v1.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def fail(message: str):
    print(f"FAIL: {message}")
    raise SystemExit(1)


def require(condition: bool, message: str):
    if not condition:
        fail(message)


def png_size(path: Path):
    with path.open("rb") as f:
        header = f.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", header[16:24])


def animation_folder(animation: str) -> str:
    return {"combat":"combat_idle", "1h_slash":"backslash", "1h_backslash":"backslash", "1h_halfslash":"halfslash", "watering":"thrust"}.get(animation, animation)


def main() -> int:
    for path in (RUNTIME, LAB, LAYER, EQUIPMENT, SEEDS, CANDIDATE):
        require(path.exists(), f"missing {path.relative_to(ROOT)}")
    runtime = load(RUNTIME)
    require(runtime.get("schema") == "havenwild.universal_lpc_runtime_contract.v1", "runtime contract schema drift")
    require(runtime.get("sourceFrameCell") == [64,64], "ULPC source frame must remain 64x64")
    require(runtime.get("runtimeFrameCell") == [64,96], "Havenwild runtime frame must remain 64x96")
    require(runtime.get("directionOrder") == ["north","west","south","east"], "ULPC direction authority must be four-direction N/W/S/E")
    require(runtime.get("bodyTypes") == ["male","female","teen","child","muscular","pregnant"], "ULPC body type authority drift")
    require(len(runtime.get("animations", [])) == 17, "all 17 normalized standard animation families are required")

    layer = load(LAYER)
    require(layer.get("schema") == "havenwild.lpc_character_layer_catalog.v2", "active layer catalog must be schema v2")
    require(layer.get("frame_cell") == [64,96], "active layer catalog runtime cell drift")
    require(layer.get("directions") == ["north","west","south","east"], "active layer catalog must not regress to eight directions")

    equipment = load(EQUIPMENT)
    require(equipment.get("schema") == "havenwild.universal_lpc.equipment_action_catalog.v0_1", "equipment action schema drift")
    records = equipment.get("records", [])
    require(len(records) == 37364, f"expected 37364 equipment-action records, got {len(records)}")
    seeds = load(SEEDS)
    seed_items = seeds.get("items", [])
    require(len(seed_items) == 105, f"expected 105 ULPC gameplay seed items, got {len(seed_items)}")

    rust_layer = (ROOT / "crates/haven_assets/src/lpc_character_pipeline.rs").read_text(encoding="utf-8")
    require('LPC_CHARACTER_LAYER_CATALOG_SCHEMA' in rust_layer and 'havenwild.lpc_character_layer_catalog.v2' in rust_layer, "Rust layer loader is not normalized to v2")
    require('ULPC_DIRECTION_ORDER' in rust_layer and 'four cardinal directions' in rust_layer, "Rust layer loader lacks four-direction authority")
    rust_equipment = (ROOT / "crates/haven_assets/src/universal_lpc_equipment_catalog.rs").read_text(encoding="utf-8")
    require('records: Vec<UniversalLpcEquipmentRecord>' in rust_equipment, "Rust equipment loader must consume records[]")
    require('havenwild.universal_lpc.equipment_action_catalog.v0_1' in rust_equipment, "Rust equipment loader schema mismatch")
    studio = (ROOT / "apps/haven_editor_native/src/app/character_studio.rs").read_text(encoding="utf-8")
    import re
    action_count = re.search(r'const CHARACTER_ACTIONS: \[\(&str, &str\); (\d+)\]', studio)
    require(action_count is not None and int(action_count.group(1)) >= 17, "Character Studio must expose all normalized ULPC standard animations")
    require('("1h_backslash", "1H Backslash")' in studio, "Character Studio standard action list is incomplete")
    require('("tool_axe", "Tool: Axe/Pickaxe")' in studio and '("slash_oversize", "Oversize Slash 192")' in studio, "Character Studio must retain certified custom equipment actions")

    game_action = (ROOT / "crates/haven_game/src/universal_lpc_gameplay_equipment.rs").read_text(encoding="utf-8")
    for marker in ('Chop','Build','Till','Mine','Fish','Dig','Water','Slash','Thrust','Shoot','Spellcast','Block'):
        require(marker in game_action, f"gameplay equipment binding missing {marker}")
    tool_runtime = (ROOT / "crates/haven_game/src/gameplay_tool_runtime.rs").read_text(encoding="utf-8")
    require('PendingGameplayToolAction' in tool_runtime and 'contact_progress' in tool_runtime, "tool gameplay must commit at normalized animation contact")
    require('equipped_items()' in tool_runtime and 'main_hand' in tool_runtime, "equipped main-hand items must drive gameplay before the fallback hotbar")
    inventory = (ROOT / "crates/haven_game/src/player_inventory_ui/interaction.rs").read_text(encoding="utf-8")
    require('equipment_slot_for_item' in inventory, "inventory must accept normalized ULPC tool/weapon item IDs")
    npc = (ROOT / "crates/haven_assets/src/universal_lpc_npc_generation.rs").read_text(encoding="utf-8")
    require('UniversalLpcCharacterRecipe' in npc, "NPC generator must emit the shared character recipe")

    # When the immutable source mount is present, run a targeted full pants/boots metadata and geometry audit.
    sheet_root = SOURCE / "sheet_definitions"
    if sheet_root.exists():
        audited = 0
        missing = []
        geometry = []
        for family in (sheet_root / "legs/pants", sheet_root / "feet/boots"):
            if not family.exists():
                fail(f"missing ULPC conformance family {family.relative_to(ROOT)}")
            for definition_path in sorted(family.rglob("*.json")):
                definition = load(definition_path)
                if not definition.get("name") or not isinstance(definition.get("layer_1"), dict):
                    continue
                animations = definition.get("animations") or []
                for layer_index in range(1, 10):
                    layer_def = definition.get(f"layer_{layer_index}")
                    if not isinstance(layer_def, dict):
                        break
                    if layer_def.get("custom_animation"):
                        continue
                    for body in runtime["bodyTypes"]:
                        base = layer_def.get(body)
                        if not isinstance(base, str) or not base:
                            continue
                        for animation in animations:
                            source_file = SOURCE / "spritesheets" / base / f"{animation_folder(animation)}.png"
                            if not source_file.exists():
                                # Variant-backed definitions may put files beneath another directory; only fail when a direct non-variant sheet is expected.
                                variants = definition.get("variants") or []
                                if not variants:
                                    missing.append(str(source_file.relative_to(ROOT)))
                                continue
                            size = png_size(source_file)
                            if size and (size[0] % 64 != 0 or size[1] % 64 != 0):
                                geometry.append(f"{source_file.relative_to(ROOT)}={size[0]}x{size[1]}")
                            audited += 1
        require(not missing, "pants/boots declared animations missing source files; first: " + ", ".join(missing[:8]))
        require(not geometry, "pants/boots standard animation geometry not aligned to 64px source cells; first: " + ", ".join(geometry[:8]))
        require(audited > 0, "pants/boots conformance audit found no standard source sheets")
        print(f"PASS: audited {audited} pants/boots body-animation source sheets")
    else:
        print("INFO: immutable ULPC source mount not present; source-corpus checks deferred to local Full quality gate")

    candidate = load(CANDIDATE)
    require(candidate.get("activationPolicy", "").startswith("Do not replace"), "C20 candidate must remain gated until local conformance passes")
    print("PASS: C1-C20 Universal LPC character/gameplay normalization contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
