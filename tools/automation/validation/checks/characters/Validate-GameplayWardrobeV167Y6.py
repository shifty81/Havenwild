#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
def load(relative: str):
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(relative)
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    catalog = load("content/characters/gameplay_clothing_item_catalog_v0_1.json")
    loot = load("content/loot/clothing_loot_tables_v0_1.json")
    npc = load("content/characters/npc_outfit_catalog_v0_1.json")
    crafting = load("content/crafting/havenwild_crafting_catalog_v0_1.json")

    assert catalog["schema"] == "havenwild.character.gameplay_clothing_item_catalog.v0_1"
    assert catalog["rules"]["starterCreationUsesItems"] is True
    assert catalog["rules"]["headwearIsGameplayOnly"] is True
    items = catalog["items"]
    assert len(items) >= 14
    item_ids = {item["itemId"] for item in items}
    assert len(item_ids) == len(items)
    assert {item["equipmentSlot"] for item in items} >= {"head", "torso", "legs", "feet"}
    assert all(item["stackLimit"] == 1 for item in items)
    assert all(item["runtimeReady"] is True for item in items)
    assert all(item["acquisitionKinds"] for item in items)
    assert all("starter" not in item["acquisitionKinds"] for item in items)
    required_asset_ref_keys = {"pack_id", "category", "asset_id", "source_id", "variant_id"}
    forbidden_asset_ref_keys = {"packId", "assetId", "sourceId", "variantId"}
    for item in items:
        asset_ref = item["assetRef"]
        assert required_asset_ref_keys <= set(asset_ref), item["itemId"]
        assert not (forbidden_asset_ref_keys & set(asset_ref)), item["itemId"]
        assert asset_ref["variant_id"] == item["variantId"], item["itemId"]
    creation_items = [item for item in items if item["equipmentSlot"] in {"torso", "legs", "feet"}]
    assert creation_items
    assert all("character_creation" in item["acquisitionKinds"] for item in creation_items)
    headwear = [item for item in items if item["equipmentSlot"] == "head"]
    assert headwear
    assert all("character_creation" not in item["acquisitionKinds"] for item in headwear)
    assert any(item["itemId"] == "headwear_felt_hat" for item in items)
    assert any(item["itemId"] == "headwear_travel_hood" for item in items)

    loot_refs = {
        entry["itemId"]
        for table in loot["tables"]
        for entry in table["entries"]
    }
    assert loot_refs <= item_ids
    assert len(loot["tables"]) >= 4

    npc_refs = {
        item_id
        for outfit in npc["outfits"]
        for values in outfit["weightedItems"].values()
        for item_id in values
    }
    assert npc_refs <= item_ids
    assert any("farmer" in outfit["roles"] for outfit in npc["outfits"])
    assert any("sailor" in outfit["roles"] for outfit in npc["outfits"])

    stations = {station["id"] for station in crafting["stations"]}
    assert "tailor_bench" in stations
    recipe_ids = {recipe["id"] for recipe in crafting["recipes"]}
    assert len(recipe_ids) == len(crafting["recipes"])
    tailored_outputs = {
        recipe["output"][0]
        for recipe in crafting["recipes"]
        if recipe["station_id"] == "tailor_bench"
    }
    expected = {
        "clothing_linen_tshirt",
        "clothing_long_work_shirt",
        "clothing_traveler_tunic",
        "clothing_plain_trousers",
        "clothing_plain_skirt",
        "clothing_simple_sandals",
        "headwear_felt_hat",
        "headwear_travel_hood",
    }
    assert expected <= tailored_outputs

    required_files = [
        "crates/haven_game/src/character_equipment_runtime.rs",
        "crates/haven_game/src/clothing_loot_runtime.rs",
        "tools/automation/characters/Build-UniversalLpcGameplayWardrobeV167Y6.py",
        "tools/automation/characters/Build-UniversalLpcGameplayWardrobe.cmd",
    ]
    for relative in required_files:
        assert (ROOT / relative).is_file(), relative

    player_inventory = (ROOT / "crates/haven_game/src/player_inventory_ui.rs").read_text(encoding="utf-8")
    assert "havenwild.player_inventory.v0_12" in player_inventory
    assert "equip_selected_item" in player_inventory
    assert '"tailor_bench_kit" => "tailor_bench"' in player_inventory

    interactions = (ROOT / "crates/haven_game/src/runtime_interactions.rs").read_text(encoding="utf-8")
    assert "loot_clothing_container" in interactions

    print("Pass 167Y6 gameplay wardrobe, crafting, loot, equipment, and NPC outfit contracts validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
