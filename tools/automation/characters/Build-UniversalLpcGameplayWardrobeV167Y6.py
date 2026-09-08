#!/usr/bin/env python3
"""Build gameplay wardrobe and NPC outfit pools from the mounted Universal LPC authority."""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AUTHORITY = ROOT / "WORKSPACE/generated/universal_lpc_character_authority_v167w.json"
OUTPUT = ROOT / "WORKSPACE/generated/universal_lpc_gameplay_wardrobe_catalog_v167y6.json"
NPC_OUTPUT = ROOT / "WORKSPACE/generated/universal_lpc_npc_outfit_pool_v167y6.json"

EXCLUDED_TERMS = (
    "body/", "heads/", "eyes/", "eyebrows/", "beards/", "facial", "hair/",
    "nose/", "ears/", "skin/", "expressions/",
)

SLOT_RULES = (
    ("off_hand", ("shield", "offhand", "off_hand")),
    ("hands", ("glove", "gauntlet", "weapon", "sword", "axe", "bow", "tool")),
    ("back", ("cape", "cloak", "backpack", "quiver", "wings", "back/")),
    ("head", ("hat", "hood", "helmet", "crown", "headwear", "mask")),
    ("feet", ("feet", "foot", "shoe", "boot", "sandal", "slipper")),
    ("legs", ("legs", "pants", "trouser", "shorts", "skirt", "greaves")),
    ("torso", ("torso", "shirt", "tunic", "vest", "apron", "robe", "jacket", "coat", "armor", "chest")),
)

ROLE_KEYWORDS = {
    "farmer": ("apron", "straw", "farmer", "overalls"),
    "blacksmith": ("smith", "apron", "forge", "leather"),
    "merchant": ("merchant", "fancy", "formal", "robe"),
    "guard": ("armor", "helmet", "shield", "guard"),
    "sailor": ("sailor", "pirate", "navy", "coast", "fisher"),
    "adventurer": ("armor", "cape", "cloak", "quiver", "weapon"),
    "mage": ("wizard", "mage", "robe", "staff"),
    "festival": ("fancy", "formal", "crown", "festival"),
}


def slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return value[:72] or "asset"


def classify_slot(source: str) -> str | None:
    low = source.lower().replace("\\", "/")
    if any(term in low for term in EXCLUDED_TERMS):
        return None
    for slot, terms in SLOT_RULES:
        if any(term in low for term in terms):
            return slot
    return None


def acquisition_for(source: str, slot: str) -> list[str]:
    low = source.lower()
    routes = {"looted", "purchased"}
    if slot in {"torso", "legs", "feet", "head", "back"}:
        routes.add("crafted")
    if any(term in low for term in ("armor", "helmet", "shield", "weapon", "gauntlet")):
        routes.update(("dungeon_reward", "quest_reward"))
    if any(term in low for term in ("uniform", "apron", "smith", "farmer", "sailor")):
        routes.add("profession_unlock")
    if any(term in low for term in ("crown", "fancy", "formal", "festival")):
        routes.update(("festival_reward", "quest_reward"))
    return sorted(routes)


def rarity_for(source: str) -> str:
    low = source.lower()
    if any(term in low for term in ("legendary", "royal", "crown", "dragon", "demon")):
        return "rare"
    if any(term in low for term in ("armor", "fancy", "formal", "robe", "cape", "cloak")):
        return "uncommon"
    return "common"


def role_tags(source: str) -> list[str]:
    low = source.lower()
    roles = [role for role, terms in ROLE_KEYWORDS.items() if any(term in low for term in terms)]
    return sorted(roles or ["resident"])


def main() -> int:
    if not AUTHORITY.is_file():
        raise SystemExit("Universal LPC authority missing; run tools/automation/characters/Bootstrap-UniversalLpcGenerator.cmd")
    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    items = []
    seen = set()
    slot_counts = Counter()
    role_pools: dict[str, list[str]] = defaultdict(list)

    for record in authority.get("records", []):
        if record.get("license_tier") not in {"preferred", "conditional"}:
            continue
        source = str(record.get("source", ""))
        slot = classify_slot(source)
        if slot is None:
            continue
        digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:10]
        item_id = f"ulpc_{slot}_{slug(Path(source).stem)}_{digest}"
        if item_id in seen:
            continue
        seen.add(item_id)
        roles = role_tags(source)
        entry = {
            "itemId": item_id,
            "displayName": Path(source).stem.replace("_", " ").replace("-", " ").title(),
            "equipmentSlot": slot,
            "source": source,
            "sourceRecordCategory": record.get("category"),
            "authors": record.get("authors", []),
            "selectedLicense": record.get("selected_license"),
            "shareAlikeRequired": bool(record.get("share_alike_required")),
            "sourceUrls": record.get("urls", []),
            "acquisitionKinds": acquisition_for(source, slot),
            "rarity": rarity_for(source),
            "npcRoleTags": roles,
            "runtimeReady": False,
            "runtimeReadinessReason": "Requires reviewed idle/walk layer bake and body compatibility mapping",
        }
        items.append(entry)
        slot_counts[slot] += 1
        for role in roles:
            role_pools[role].append(item_id)

    items.sort(key=lambda item: (item["equipmentSlot"], item["displayName"], item["itemId"]))
    output = {
        "schema": "havenwild.universal_lpc.gameplay_wardrobe_catalog.v167y6",
        "sourceAuthority": str(AUTHORITY.relative_to(ROOT)).replace("\\", "/"),
        "itemCount": len(items),
        "slotCounts": dict(sorted(slot_counts.items())),
        "policy": {
            "creationUsesOnlyCuratedGenericSubset": True,
            "allOtherValidatedItemsRouteToGameplayAcquisition": True,
            "runtimeReadyRequiresReviewedIdleAndWalkBake": True,
            "shareAlikeItemsRemainSelectableWithExactTracking": True,
            "clothingIsNotSexRestricted": True,
            "facialHairIsExcludedFromEquipment": True,
        },
        "items": items,
    }
    npc_output = {
        "schema": "havenwild.universal_lpc.npc_outfit_pool.v167y6",
        "sourceCatalog": str(OUTPUT.relative_to(ROOT)).replace("\\", "/"),
        "rules": {
            "deterministicPerNpcIdentity": True,
            "contextOutfitsSupported": ["Everyday", "Work", "Rain", "Winter", "Travel", "Festival", "Formal", "Combat"],
            "authoredNpcLocksOverrideGeneratedPools": True,
            "onlyRuntimeReadyItemsMayRenderInClient": True,
        },
        "rolePools": {role: sorted(ids) for role, ids in sorted(role_pools.items())},
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    NPC_OUTPUT.write_text(json.dumps(npc_output, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(items):,} gameplay wardrobe candidates")
    print(f"Wrote {NPC_OUTPUT} with {len(role_pools):,} NPC role pools")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
