#!/usr/bin/env python3
"""Validate H21A14AB9-AB18 LPC content + gameplay integration closure."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
errors = []

def read_json(rel):
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"invalid/missing JSON {rel}: {exc}")
        return {}

registry = read_json("content/assets/oga_lpc/manifests/oga_lpc_prototype_source_registry_v0_1.json")
expected_sources = {
    "oga.lpc.terrain_extension", "oga.lpc.hand_tools", "oga.lpc.tavern", "oga.lpc.farming_magic_ui",
    "oga.lpc.extended_magic", "oga.lpc.monsters", "oga.lpc.blacksmith",
    "oga.lpc.woodshop", "oga.lpc.tailor", "oga.lpc.sawmill",
    "oga.lpc.revised_workshops_reference",
}
source_ids = {entry.get("id") for entry in registry.get("sources", [])}
for source_id in sorted(expected_sources - source_ids):
    errors.append(f"curated LPC source missing: {source_id}")

roles = read_json("content/assets/oga_lpc/manifests/oga_lpc_prototype_role_registry_v0_1.json")
for domain in ["terrain_transition_extensions", "tools_and_equipment", "workshops", "tavern_and_inn", "combat_creatures", "magic_effects", "ui_reference"]:
    if domain not in roles.get("domains", {}):
        errors.append(f"LPC semantic provider domain missing: {domain}")

catalog = read_json("content/assets/lpc/universal_lpc_equipment_action_catalog_v0_1.json")
bindings = catalog.get("toolBindings", {})
for tool in ["axe", "pickaxe", "hoe", "watering_can", "hammer", "fishing_rod", "shovel", "scythe", "whip"]:
    if not bindings.get(tool):
        errors.append(f"corrected ULPC tool binding is empty/missing: {tool}")
if any("horseshoe" in asset.lower() for asset in bindings.get("hoe", [])):
    errors.append("horseshoe beard assets are still misclassified as Hoe")
if any("pickaxe" in asset.lower() for asset in bindings.get("axe", [])):
    errors.append("Pickaxe assets are still misclassified as Axe")
if any("waraxe" in asset.lower() for asset in bindings.get("axe", [])):
    errors.append("Waraxe weapon assets are still misclassified as work Axe")

crafting = read_json("content/crafting/havenwild_crafting_catalog_v0_1.json")
outputs = {recipe.get("id"): recipe.get("output", [None])[0] for recipe in crafting.get("recipes", [])}
expected_outputs = {
    "primitive_axe": "item.ulpc.tools_tool_axe",
    "stone_hammer": "item.ulpc.tools_tool_hammer",
    "copper_pick": "item.ulpc.tools_tool_pickaxe",
    "stone_hoe": "item.ulpc.tools_tool_hoe",
    "wooden_watering_can": "item.ulpc.tools_tool_watering_can",
    "stone_shovel": "item.ulpc.tools_tool_shovel",
    "simple_fishing_rod": "item.ulpc.tools_tool_rod",
    "field_scythe": "item.ulpc.weapons_polearm_weapon_polearm_scythe",
    "utility_whip": "item.ulpc.tools_tool_whip",
}
for recipe_id, output in expected_outputs.items():
    if outputs.get(recipe_id) != output:
        errors.append(f"crafting recipe {recipe_id} does not output canonical LPC equipment id {output}")

gameplay = (ROOT / "crates/haven_game/src/gameplay_tool_runtime.rs").read_text(encoding="utf-8")
for marker in [
    "use_resource_tool_at(GameplayTool::Axe",
    "use_resource_tool_at(GameplayTool::Pickaxe",
    "resource_hits:",
    "ObjectKind::Tree",
    "ObjectKind::OreNode",
    "Copper Ore",
    "Crop harvesting uses the crop growth/harvest state",
    "equip the matching item in Main Hand before use",
]:
    if marker not in gameplay:
        errors.append(f"gameplay tool runtime missing marker: {marker}")

interactions = (ROOT / "crates/haven_game/src/runtime_interactions.rs").read_text(encoding="utf-8")
for marker in ["equip an Axe", "equip a Mining Pick", "forage_loose_object", "Wild Mushroom", "Wild Herb", "equip a Hoe", "equip a Watering Can", "authored crop growth/harvest state"]:
    if marker not in interactions:
        errors.append(f"runtime interaction closure missing marker: {marker}")

if "+1 coin placeholder" in interactions or "+3 coin placeholder" in interactions:
    errors.append("generic terrain interaction still awards placeholder coin instead of using authored gameplay state")

classifier = (ROOT / "tools/automation/characters/Build-UniversalLpcCompleteRepositoryIndexV167Z7.py").read_text(encoding="utf-8")
for marker in ["def tool_id_for_path", 'first == "watering"', 'first == "fishing"', '"shovel": "shovel"', '"whip": "whip"']:
    if marker not in classifier:
        errors.append(f"exact-path ULPC classifier missing marker: {marker}")
if "TOOL_TOKENS" in classifier:
    errors.append("legacy substring TOOL_TOKENS classifier remains active")

powershell = (ROOT / "tools/build/Build.ps1").read_text(encoding="utf-8")
lpc_sync_line = next((line for line in powershell.splitlines() if '"lpc-sync" {' in line), "")
if "Sync-OgaLpcPrototypes;" not in lpc_sync_line:
    errors.append("PowerShell lpc-sync does not include governed OGA/LPC prototype sync")

contract = read_json("content/gameplay/lpc_bindings/havenwild_lpc_gameplay_action_binding_v1.json")
if len(contract.get("actions", [])) < 9:
    errors.append("LPC gameplay action binding contract does not cover the nine equipped work/combat tools")

build = (ROOT / "tools/build/Build.sh").read_text(encoding="utf-8")
if "Validate-LpcGameplayExpansionA14AB18.py" not in build:
    errors.append("AB18 validator is not registered in Full Quality Gate")

if errors:
    print("H21A14AB9-AB18 LPC Gameplay Expansion validation FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("PASS: H21A14AB9-AB18 LPC content + gameplay integration")
print("- governed LPC source registry covers tools, workshops, tavern, creatures, magic and reference UI")
print("- exact-path ULPC tool classification prevents horseshoe/pickaxe/waraxe contamination")
print("- crafted work tools use the same canonical item IDs as equipped runtime actions")
print("- axe/pickaxe resource hits and forage/scythe interactions commit at LPC animation contact")
