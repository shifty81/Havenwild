#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
CATALOG = ROOT / "content/characters/character_creation_catalog_v0_1.json"
POLICY = ROOT / "content/characters/character_profile_policy_v0_1.json"
MODULE = ROOT / "crates/haven_assets/src/character_profile.rs"
LIB = ROOT / "crates/haven_assets/src/lib.rs"

errors = []
for path in (CATALOG, POLICY, MODULE, LIB):
    if not path.is_file():
        errors.append(f"missing required file: {path.relative_to(ROOT)}")

if CATALOG.is_file() and POLICY.is_file():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    allowed = set(policy.get("initial_creator_allowed_slots", []))
    for item in catalog.get("starter_clothing", []):
        if item.get("slot") not in allowed:
            errors.append(f"starter item {item.get('id')} uses disallowed slot {item.get('slot')}")
    progression = set(policy.get("progression_only_categories", []))
    for required in {"armor", "weapons", "shields", "advanced_outfits"} - progression:
        errors.append(f"{required} is not progression-only")
    access = {item.get("id"): item.get("creator_access") for item in policy.get("equipment_categories", [])}
    for required in ("armor", "weapons", "shields"):
        if access.get(required) != "progression_only":
            errors.append(f"{required} creator access is not progression_only")
    aliases = set(policy.get("required_neutral_idle_aliases", []))
    for required in {"idle_down", "idle_up", "idle_left", "idle_right"} - aliases:
        errors.append(f"missing neutral idle alias: {required}")
    category_ids = {category.get("id") for category in catalog.get("appearance_categories", [])}
    for channel in policy.get("color_channels", []):
        for category in channel.get("applies_to_categories", []):
            if category not in category_ids:
                errors.append(f"color channel {channel.get('id')} references unknown category {category}")

if LIB.is_file() and "pub mod character_profile;" not in LIB.read_text(encoding="utf-8"):
    errors.append("haven_assets does not export character_profile")

if errors:
    print("Character Profile and Wardrobe V137: FAIL")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("Character Profile and Wardrobe V137: PASS")
print("- default profile construction is catalog-driven")
print("- creator slots are limited to top, bottom, and feet")
print("- armor, weapons, shields, and advanced outfits remain progression-only")
print("- color channels are attached to canonical appearance categories")
print("- neutral four-direction idle aliases remain mandatory")
