#!/usr/bin/env python3
"""Validate the additive W81R18-R28 LPC ecosystem intake authority."""
from __future__ import annotations

import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]

REQUIRED = [
    "content/assets/lpc/lpc_ecosystem_discovery_seed_r18_v1.json",
    "content/assets/lpc/lpc_ecosystem_intake_authority_r18_r28_v1.json",
    "content/assets/lpc/lpc_ecosystem_intake_snapshot_r18_r28_v1.json",
    "content/editor/assets/universal_asset_browser_v2_r19_v1.json",
    "content/editor/assets/lpc_ecosystem_browser_projection_r19_v1.json",
    "content/editor/character/character_lpc_catalog_exposure_r20_v1.json",
    "content/editor/world/world_lpc_terrain_nature_exposure_r21_v1.json",
    "content/gameplay/lpc_intake/farming_food_animals_r22_v1.json",
    "content/gameplay/lpc_intake/mining_forge_sawmill_r23_v1.json",
    "content/gameplay/lpc_intake/tavern_interiors_storage_r24_v1.json",
    "content/gameplay/lpc_intake/creatures_combat_weapons_fx_r25_v1.json",
    "content/gameplay/lpc_intake/ships_fishing_water_r26_v1.json",
    "content/legal/open_assets/lpc_release_license_policy_r27_v1.json",
    "content/editor/acceptance/lpc_visual_gameplay_acceptance_world_r28_v1.json",
    "docs/handoffs/HAVENWILD_W81R18_R28_LPC_ECOSYSTEM_INTAKE_HANDOFF.md",
]


def load(rel: str):
    path = ROOT / rel
    if not path.is_file():
        raise AssertionError(f"missing required R18-R28 file: {rel}")
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return path.read_text(encoding="utf-8")


def main() -> int:
    loaded = {rel: load(rel) for rel in REQUIRED}
    authority = loaded["content/assets/lpc/lpc_ecosystem_intake_authority_r18_r28_v1.json"]
    snapshot = loaded["content/assets/lpc/lpc_ecosystem_intake_snapshot_r18_r28_v1.json"]
    discovery = loaded["content/assets/lpc/lpc_ecosystem_discovery_seed_r18_v1.json"]
    browser = loaded["content/editor/assets/universal_asset_browser_v2_r19_v1.json"]
    projection = loaded["content/editor/assets/lpc_ecosystem_browser_projection_r19_v1.json"]
    character = loaded["content/editor/character/character_lpc_catalog_exposure_r20_v1.json"]
    terrain = loaded["content/editor/world/world_lpc_terrain_nature_exposure_r21_v1.json"]
    legal = loaded["content/legal/open_assets/lpc_release_license_policy_r27_v1.json"]
    acceptance = loaded["content/editor/acceptance/lpc_visual_gameplay_acceptance_world_r28_v1.json"]

    expected_passes = [f"W81R{i}" for i in range(18, 29)]
    assert authority.get("passes") == expected_passes, authority.get("passes")
    assert authority.get("baseline") == "W81R17"
    assert set(authority.get("licenseTiers", {}).keys()) >= {"green", "green_conditional", "yellow", "red"}
    assert len(discovery.get("packs", [])) >= 25, "R18 discovery must materially broaden the old OGA queue"

    headline = snapshot.get("headline", {})
    assert headline.get("elizawyRawFilesExpected", 0) >= 64000
    assert headline.get("ulpcSpritesheetPngFiles", 0) >= 88000
    assert headline.get("ulpcEquipmentRecords", 0) >= 37000
    assert headline.get("ulpcCreditRecords", 0) >= 13000
    assert headline.get("r18DiscoverySeedPacks", 0) >= 25

    assert browser.get("presentation") == "virtualized_scrolling_thumbnail_grid"
    assert browser.get("forbidPrimaryPagination") is True
    assert projection.get("presentation", {}).get("sourceVisibleBeforeRuntimeBinding") is True

    assert character.get("sharedAuthority") == "CharacterEquipmentAuthority"
    mirrored = " ".join(character.get("mirroredSurfaces", []))
    assert "Character Studio" in mirrored
    assert "game Character/Inventory" in mirrored
    assert len(character.get("toolBeltSlots", [])) >= 9

    assert terrain.get("terrainRule", "").startswith("Paint semantic materials")
    assert "Cliff/ramp/stair" in terrain.get("structuralRule", "")

    assert "proprietary" in legal.get("intent", "")
    assert legal.get("policies", {}).get("GPL-only") == "blocked by default"
    assert "ShareAlike" in legal.get("policies", {}).get("CC-BY-SA-4.0", "")
    assert len(legal.get("releaseGate", [])) >= 4

    boards = acceptance.get("boards", [])
    ids = {board.get("id") for board in boards}
    assert {"terrain", "characters", "resource_interaction", "water_travel", "combat_creatures"}.issubset(ids)
    assert "existing selected-Scene Play flow" in acceptance.get("runtimeEntry", "")

    # Cross-check committed ULPC indexes are still present and coherent.
    with gzip.open(ROOT / "content/assets/lpc/universal_lpc_commercial_catalog_v0_1.json.gz", "rt", encoding="utf-8") as handle:
        commercial = json.load(handle)
    with gzip.open(ROOT / "content/assets/lpc/universal_lpc_sharealike_catalog_v0_1.json.gz", "rt", encoding="utf-8") as handle:
        sharealike = json.load(handle)
    assert len(commercial.get("records", [])) > 10000
    assert len(sharealike.get("records", [])) > 1000

    print("PASS: W81R18-R28 LPC ecosystem intake + exposure authority")
    print(f"- discovery packs: {len(discovery.get('packs', []))}")
    print(f"- ULPC catalog: {headline['ulpcSpritesheetPngFiles']:,} spritesheets / {headline['ulpcEquipmentRecords']:,} equipment records")
    print("- Character Studio and Game Client share CharacterEquipmentAuthority contract")
    print("- terrain paints semantic materials; cliffs remain structural")
    print("- release licensing is fail-closed and code/editor license remains isolated from third-party artwork")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
