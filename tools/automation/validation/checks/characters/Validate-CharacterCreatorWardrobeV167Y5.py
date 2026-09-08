#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
def load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def main() -> int:
    catalog = load("content/characters/character_creation_catalog_v0_1.json")
    starter = load("content/characters/starter_creator_policy_v0_1.json")
    acquisition = load("content/characters/character_clothing_acquisition_policy_v0_1.json")
    bindings = load("content/characters/starter_clothing_source_bindings_v0_1.json")
    equipment = load("content/characters/gameplay_character_equipment_policy_v0_1.json")

    clothing = catalog["starter_clothing"]
    slots = {item["slot"] for item in clothing}
    assert slots == {"top", "bottom", "feet"}, slots
    assert 24 <= len(clothing) <= 32, len(clothing)
    assert "headwear" in catalog["prohibited_initial_categories"]
    assert starter["clothingEligibility"]["sexRestricted"] is False
    assert acquisition["creator"]["headwearAllowed"] is False
    assert acquisition["identityException"] == {
        "channel": "facial_hair",
        "allowedSex": ["Male"],
        "appliesTo": ["player_creation", "saved_profiles", "npc_generation"],
    }

    binding_ids = {entry["variantId"] for entry in bindings["bindings"]}
    assert len(binding_ids) == len(clothing)
    assert "none" in binding_ids
    assert all(entry["availability"] == "starter" for entry in bindings["bindings"])

    slots_by_id = {entry["id"]: entry for entry in equipment["slots"]}
    assert slots_by_id["head"]["allowAtCreation"] is False
    assert slots_by_id["head"]["creatorChannels"] == []
    assert slots_by_id["torso"]["creatorChannels"] == ["clothing_torso"]
    assert slots_by_id["legs"]["creatorChannels"] == ["clothing_legs"]
    assert "armor_torso" not in slots_by_id["torso"]["creatorChannels"]
    assert "armor_legs" not in slots_by_id["legs"]["creatorChannels"]
    assert "armor_feet" not in slots_by_id["feet"]["creatorChannels"]

    print("Expanded character-creator wardrobe policy validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
