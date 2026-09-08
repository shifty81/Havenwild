#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
CATALOG = ROOT / "content/characters/character_creation_catalog_v0_1.json"
MODULE = ROOT / "crates/haven_assets/src/character_creation.rs"
LIB = ROOT / "crates/haven_assets/src/lib.rs"

errors = []
for path in (CATALOG, MODULE, LIB):
    if not path.is_file():
        errors.append(f"missing required file: {path.relative_to(ROOT)}")

if CATALOG.is_file():
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    if len(data.get("starter_clothing", [])) > 32:
        errors.append("starter clothing exceeds maximum of 32")
    prohibited = set(data.get("prohibited_initial_categories", []))
    for required in {"armor", "weapons", "shields", "advanced_outfits"} - prohibited:
        errors.append(f"missing prohibited initial category: {required}")
    aliases = set(data.get("required_animation_aliases", []))
    for required in {"idle_down", "idle_up", "idle_left", "idle_right", "walk_8dir"} - aliases:
        errors.append(f"missing required animation alias: {required}")
    for item in data.get("starter_clothing", []):
        slot = item.get("slot", "").lower()
        if any(token in slot for token in ("armor", "weapon", "shield")):
            errors.append(f"combat equipment leaked into creator: {item.get('id')}")

if LIB.is_file() and "pub mod character_creation;" not in LIB.read_text(encoding="utf-8"):
    errors.append("haven_assets does not export character_creation")

if errors:
    print("Character Creation Foundation V136: FAIL")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("Character Creation Foundation V136: PASS")
print("- appearance-first creator contract present")
print("- ordinary starter clothing remains intentionally bounded to the expanded generic pool")
print("- armor, weapons, shields, and advanced outfits are excluded")
print("- four-direction idle aliases and 8-direction walk alias are required")
