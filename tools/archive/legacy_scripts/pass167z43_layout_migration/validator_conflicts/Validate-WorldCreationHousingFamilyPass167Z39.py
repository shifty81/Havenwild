#!/usr/bin/env python3
"""Focused source/data validation for Havenwild Pass 167Z39."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_JSON = {
    "content/worldgen/havenwild_world_creation_spec_v1.json": [
        "continuous_chunk_streamed_overworld",
        "freshwater",
        "marine",
        "willowmere",
        "staticPlayerFarmsteadGenerated",
    ],
    "content/worldgen/settlement_housing_generation_v0_1.json": [
        "targetAvailableProperties",
        "rent_or_purchase",
        "lease_to_own",
        "village",
    ],
    "content/social/relationship_family_household_contract_v0_1.json": [
        "playerWithNpcRomanceAndMarriage",
        "playerWithPlayerPartnershipAndMarriage",
        "pregnancy",
        "adoption",
    ],
    "content/characters/elizawy_pregnancy_body_policy_v0_1.json": [
        "elizawy_lpc.character.body.pregnancy",
        "adultCharactersOnly",
        "clothingCompatibilityMustBeValidated",
    ],
    "content/ui/world_creation_wizard_v0_1.json": [
        "relationships_and_family",
        "generate_world",
        "world_creation_settings.json",
    ],
}

REQUIRED_SOURCE_MARKERS = {
    "crates/haven_world/src/world_creation.rs": [
        "WorldCreationSettings",
        "LandformPreset",
        "HydrologyGenerationSettings",
        "city_available_homes_target",
        "player_npc_marriage_enabled",
    ],
    "crates/haven_save/src/social_world.rs": [
        "WorldSocialState",
        "HousingPropertyState",
        "RelationshipRecord",
        "HouseholdState",
        "PregnancyState",
    ],
    "crates/haven_game/src/world_creation_wizard.rs": [
        "CREATE WORLD",
        "Relationships & Family",
        "GENERATE WORLD",
    ],
    "crates/haven_game/src/client_frontend.rs": [
        "FrontendScreen::WorldCreator",
        "create_seeded_world_save_with_settings",
    ],
    "crates/haven_game/src/client_save_generation.rs": [
        "save_world_creation_settings",
        "save_world_topology_to_path",
        "load_or_create_world_social_state",
    ],
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for relative, markers in REQUIRED_JSON.items():
        path = ROOT / relative
        if not path.is_file():
            fail(f"missing required JSON: {relative}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:  # noqa: BLE001
            fail(f"invalid JSON {relative}: {error}")
        raw = json.dumps(data, sort_keys=True)
        for marker in markers:
            if marker not in raw:
                fail(f"{relative} is missing marker {marker!r}")

    for relative, markers in REQUIRED_SOURCE_MARKERS.items():
        path = ROOT / relative
        if not path.is_file():
            fail(f"missing required source: {relative}")
        raw = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in raw:
                fail(f"{relative} is missing marker {marker!r}")

    world_creation = json.loads(
        (ROOT / "content/worldgen/havenwild_world_creation_spec_v1.json").read_text(encoding="utf-8")
    )
    if world_creation["outdoorWorld"]["staticPlayerFarmsteadGenerated"] is not False:
        fail("world generation must not restore a mandatory static player farmstead")

    housing = json.loads(
        (ROOT / "content/worldgen/settlement_housing_generation_v0_1.json").read_text(encoding="utf-8")
    )
    city_target = housing["housingAvailability"]["willowmereAndCities"]["targetAvailableProperties"]
    village_target = housing["housingAvailability"]["villages"]["targetAvailableProperties"]
    if city_target <= 1:
        fail("cities must expose multiple housing opportunities")
    if village_target != 1:
        fail("villages must normally expose one housing opportunity")

    print("Pass 167Z39 world creation, housing, relationships, and family foundation validated.")


if __name__ == "__main__":
    main()
