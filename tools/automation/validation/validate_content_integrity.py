#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
PINNED_LPC_COMMIT = "f07f7f5892e67c932c68f70bb04472f2c64e46bc"


def load_json(relative: str):
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(f"missing required content file: {relative}")
    return json.loads(path.read_text(encoding="utf-8"))


def require_file(relative: str) -> Path:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(f"missing required file: {relative}")
    return path


def validate_lpc_source_lock() -> None:
    lock = load_json("content/assets/intake/lpc_source_lock_v0_1.json")
    if lock.get("schema") != "havenwild.lpc_source_lock.v0_1":
        raise ValueError("unexpected LPC source-lock schema")
    if lock.get("commit") != PINNED_LPC_COMMIT:
        raise ValueError("LPC source lock does not use the pinned production commit")
    if lock.get("tileSize") != 32:
        raise ValueError("LPC source lock must preserve the 32x32 tile contract")
    required_terrain = lock.get("requiredTerrainFiles", [])
    if len(required_terrain) < 30 or "Terrain/cliff_summer.png" not in required_terrain or "Terrain/trees_summer.png" not in required_terrain:
        raise ValueError("LPC source lock does not preserve the complete reviewed Terrain folder")
    source_root = ROOT / lock["fullSourceProjectPath"]
    if source_root.exists():
        for item in lock.get("lockedFiles", []):
            path = require_file(item["projectPath"])
            with Image.open(path) as image:
                if image.size != (item["width"], item["height"]):
                    raise ValueError(f"locked LPC dimensions changed: {item['projectPath']}")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != item["sha256"]:
                raise ValueError(f"locked LPC checksum changed: {item['projectPath']}")
    else:
        print("INFO LPC source mount absent; lock metadata validated, mounted files deferred")


def validate_complete_map() -> None:
    contract = load_json("content/assets/intake/lpc_terrain_summer_complete_map_v0_1.json")
    ledger_path = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_terrain_summer_complete_map_32.json"
    if not ledger_path.is_file():
        print("INFO generated summer terrain ledger deferred until asset-generation stage")
        return
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    summary = ledger.get("summary", {})
    if summary.get("totalCells") != 416:
        raise ValueError("summer terrain ledger must contain 416 cells")
    if summary.get("nonTransparentCells") != 305:
        raise ValueError("summer terrain ledger must contain 305 non-transparent cells")
    if summary.get("mappedNonTransparentCells") != 305:
        raise ValueError("all non-transparent summer cells must be mapped")
    if not summary.get("allNonTransparentCellsMapped"):
        raise ValueError("summer terrain map reports incomplete coverage")
    if not summary.get("noPrimaryGroupOverlap"):
        raise ValueError("summer terrain map reports overlapping primary groups")
    cells = ledger.get("cells", [])
    coords = {tuple(record["cell"]) for record in cells}
    if coords != {(x, y) for y in range(26) for x in range(16)}:
        raise ValueError("summer terrain ledger does not cover the full 16x26 grid")
    group_ids = {
        item["id"]
        for section in ("fillFamilies", "transitionFamilies", "modularStrips", "decorations")
        for item in contract.get(section, [])
    }
    required = {
        "summer_grass_over_dirt",
        "summer_grass_over_sand",
        "summer_sand_over_wet_sand",
        "summer_sand_bank_pond",
        "summer_deep_water_basin",
        "summer_water_fill",
    }
    if not required.issubset(group_ids):
        raise ValueError(f"missing required LPC mapping groups: {sorted(required - group_ids)}")


def validate_seasonal_topology() -> None:
    manifest = load_json("content/assets/lpc/lpc_seasonal_terrain_topology_v0_1.json")
    if manifest.get("cellSize") != 32 or manifest.get("grid") != [16, 26]:
        raise ValueError("seasonal topology grid contract changed")
    seasons = manifest.get("seasons", [])
    if len(seasons) != 5:
        raise ValueError("seasonal topology must define five terrain sheets")
    source_root = ROOT / "assets/source/licensed/lpc_revised"
    if source_root.exists():
        for season in seasons:
            require_file(season["source"])
    else:
        print("INFO seasonal LPC source sheets deferred until dependency mount")
    families = manifest.get("families", [])
    if len(families) != 20:
        raise ValueError("seasonal topology must define 20 terrain families")


def validate_transition_atlas() -> None:
    manifest_path = ROOT / "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.json"
    atlas_path = ROOT / "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.png"
    if not manifest_path.is_file() or not atlas_path.is_file():
        print("INFO generated transition atlas deferred until asset-generation stage")
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    with Image.open(atlas_path) as image:
        atlas = image.convert("RGBA")
    width, height = atlas.size
    variants = manifest.get("variants", [])
    inner = manifest.get("innerCornerVariants", [])
    if len(variants) != 144 or len(inner) != 32:
        raise ValueError("transition atlas variant counts changed")
    for entry in [*variants, *inner]:
        x, y, w, h = entry["rect"]
        if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > width or y + h > height:
            raise ValueError(f"transition rect is outside atlas bounds: {entry['id']}")
        tile = atlas.crop((x, y, x + w, y + h))
        if entry in inner and tile.getchannel("A").getbbox() is None:
            raise ValueError(f"inner-corner transition is empty: {entry['id']}")


def validate_worldgen_preset() -> None:
    preset = load_json("content/worldgen/havenwild_open_world_preset_v1.json")
    load_json("content/schemas/havenwild_open_world_preset.schema.v1.json")
    overworld = preset.get("overworld", {})
    if overworld.get("world_size_tiles") != [1024, 1024]:
        raise ValueError("open-world preset must remain 1024x1024 tiles")
    if overworld.get("chunk_size_tiles") != [64, 64]:
        raise ValueError("open-world preset must remain 64x64 chunks")
    anchors = preset.get("required_anchors", [])
    if len(anchors) != 9:
        raise ValueError("open-world preset must define nine required anchors")
    required = {"starter_tavern_plot", "town_center", "harbor", "starter_cave_entrance"}
    if not required.issubset(anchors):
        raise ValueError(f"open-world preset is missing anchors: {sorted(required - set(anchors))}")


def validate_generated_registry() -> None:
    registry = load_json("content/build/generated_output_registry_v2.json")
    if registry.get("schema") != "havenwild.generated_output_registry.v2":
        raise ValueError("unexpected generated-output registry schema")
    for item in registry.get("outputs", []):
        require_file(item["generator"])
        for source in item.get("inputs", []):
            source_path = ROOT / source
            if source_path.is_file():
                continue
            if source.startswith("assets/source/"):
                continue
            if source.startswith("assets/generated/"):
                continue
            raise FileNotFoundError(f"missing generated-output input: {source}")
        if not item.get("output") or not item.get("provenance"):
            raise ValueError("generated-output registry entry lacks output/provenance metadata")



def validate_external_or_local_asset(source_rel: str, expected_sha256: str | None = None, expected_size: list[int] | None = None) -> None:
    """Validate a production asset without confusing governed external source with committed source."""
    source_path = ROOT / source_rel
    if source_path.is_file():
        if expected_size is not None:
            with Image.open(source_path) as image:
                if list(image.size) != expected_size:
                    raise ValueError(f"asset dimensions changed: {source_rel}")
        if expected_sha256:
            import hashlib
            digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
            if digest != expected_sha256:
                raise ValueError(f"asset checksum changed: {source_rel}")
        return

    filename = Path(source_rel).name
    index_root = ROOT / "content/assets/intake/external_pack_indexes"
    matches = []
    for index_path in sorted(index_root.glob("*.json")):
        payload = json.loads(index_path.read_text(encoding="utf-8"))
        pack = payload.get("pack", {})
        if pack.get("rawFilesCommitted") is True:
            continue
        for record in payload.get("records", []):
            if record.get("relativePath") == filename:
                matches.append((index_path, record, pack))
    if len(matches) != 1:
        raise FileNotFoundError(f"missing governed production asset and unique external-pack record: {source_rel}")
    _, record, pack = matches[0]
    if expected_sha256 and record.get("sha256") != expected_sha256:
        raise ValueError(f"external-pack checksum mismatch: {source_rel}")
    if expected_size is not None and [record.get("width"), record.get("height")] != expected_size:
        raise ValueError(f"external-pack dimensions mismatch: {source_rel}")
    if not pack.get("sourceUrl") or not pack.get("licenseStatus"):
        raise ValueError(f"external-pack provenance incomplete: {source_rel}")


def validate_lpc_production_assets() -> None:
    animals = load_json("content/assets/oga_lpc/manifests/oga_lpc_farm_animals_runtime_catalog_v0_1.json")
    livestock = load_json("content/gameplay/livestock/livestock_species_v0_1.json")
    registry = load_json("content/assets/lpc/lpc_production_visual_registry_v0_2.json")
    bindings = load_json("content/editor/world_asset_edit_bindings_v0_2.json")
    gallery = load_json("content/worldgen/editor_test_world_asset_galleries_v0_1.json")
    species = {entry["species_id"] for entry in animals.get("species", [])}
    if species != {"chicken", "cow", "llama", "pig", "sheep"}:
        raise ValueError(f"unexpected LPC livestock set: {sorted(species)}")
    if {entry["id"] for entry in livestock.get("species", [])} != species:
        raise ValueError("livestock gameplay definitions do not match the LPC visual catalog")
    for entry in animals.get("species", []):
        for state in ("walk", "eat"):
            animation = entry.get("animations", {}).get(state)
            if animation is None:
                raise ValueError(f"{entry['species_id']} is missing {state} animation")
            validate_external_or_local_asset(
                animation["source"],
                expected_sha256=animation.get("sha256"),
                expected_size=animation["sheet_size"],
            )
    terrain_types = registry.get("terrain_v7", {}).get("terrain_types", [])
    if len(terrain_types) < 30:
        raise ValueError("LPC production terrain registry is incomplete")
    terrain_authority = load_json("content/assets/lpc/lpc_revised_terrain_family_authority_v0_1.json")
    if terrain_authority.get("runtimePolicy", {}).get("authoredSheetsAreSourceOfTruth") is not True:
        raise ValueError("LPC Terrain-folder authored sheets are not runtime source authority")
    family_ids = {family.get("id") for family in terrain_authority.get("families", [])}
    required_families = {"seasonal_ground_water", "structural_cliffs", "rocks", "trees", "plants_and_foraging", "farm_ground", "water_features"}
    if not required_families.issubset(family_ids):
        raise ValueError(f"LPC Terrain-folder authority is missing families: {sorted(required_families - family_ids)}")
    brush_catalog = load_json("content/editor/lpc_terrain_feature_brush_catalog_v0_1.json")
    brush_ids = {group.get("id") for group in brush_catalog.get("brushGroups", [])}
    required_brushes = {"ground_and_water", "levels_and_cliff_recipes", "trees", "plants_flowers_and_foraging", "rocks", "farm_ground", "water_features"}
    if brush_ids != required_brushes:
        raise ValueError("editor LPC Terrain-folder brush catalog is incomplete")
    binding_ids = [entry["semantic_id"] for entry in bindings.get("bindings", [])]
    if len(binding_ids) != len(set(binding_ids)):
        raise ValueError("world asset edit bindings contain duplicate IDs")
    if gallery.get("world_id") != "havenwild_editor_test_world":
        raise ValueError("LPC asset gallery must target the client-loaded editor test world")




def validate_character_creation_clothing_policy() -> None:
    catalog = load_json("content/characters/character_creation_catalog_v0_1.json")
    policy = load_json("content/characters/starter_creator_policy_v0_1.json")
    acquisition = load_json("content/characters/character_clothing_acquisition_policy_v0_1.json")
    bindings = load_json("content/characters/starter_clothing_source_bindings_v0_1.json")
    slots = {item.get("slot") for item in catalog.get("starter_clothing", [])}
    if slots != {"top", "bottom", "feet"}:
        raise ValueError(f"character creation clothing slots changed: {sorted(slots)}")
    if len(catalog.get("starter_clothing", [])) > 32:
        raise ValueError("character creation starter wardrobe exceeds the bounded generic pool")
    if len(catalog.get("starter_clothing", [])) < 24:
        raise ValueError("character creation starter wardrobe has not promoted the expanded generic pool")
    if "headwear" not in catalog.get("prohibited_initial_categories", []):
        raise ValueError("character creation must reserve headwear for gameplay acquisition")
    eligibility = policy.get("clothingEligibility", {})
    if eligibility.get("sexRestricted") is not False:
        raise ValueError("generic starter clothing must not be sex-restricted")
    creator = acquisition.get("creator", {})
    if creator.get("allowedSlots") != ["clothing_torso", "clothing_legs", "clothing_feet"]:
        raise ValueError("clothing acquisition policy must limit creation to torso, legs, and feet")
    if creator.get("headwearAllowed") is not False:
        raise ValueError("headwear must remain crafting/loot/shop/quest gameplay content")
    starter_ids = {entry.get("variantId") for entry in bindings.get("bindings", [])}
    expected_ids = {
        "starter_tshirt", "starter_vneck_tshirt", "starter_scoop_tshirt",
        "starter_buttoned_tshirt", "starter_long_shirt", "starter_vneck_long_shirt",
        "starter_scoop_long_shirt", "starter_buttoned_long_shirt", "starter_polo",
        "starter_tunic", "starter_vest", "starter_apron", "starter_pants",
        "starter_hose", "starter_leggings", "starter_cuffed_pants", "starter_overalls",
        "starter_shorts", "starter_short_shorts", "starter_skirt", "starter_long_skirt",
        "starter_boots", "starter_shoes", "starter_ankle_socks", "starter_high_socks",
        "starter_sandals", "none"
    }
    if starter_ids != expected_ids:
        raise ValueError("starter clothing source bindings do not match the creator wardrobe")
    exception = acquisition.get("identityException", {})
    if exception.get("channel") != "facial_hair" or exception.get("allowedSex") != ["Male"]:
        raise ValueError("facial-hair Male-only policy changed")


def validate_optional_generated_evidence(path_value, label):
    """Validate generated evidence when present without making it source authority."""
    if not path_value:
        return None
    candidate = ROOT / path_value
    if candidate.exists():
        if not candidate.is_file():
            fail(f"{label} exists but is not a file: {path_value}")
        return candidate
    normalized = str(path_value).replace("\\", "/").lower()
    generated_markers = (
        "/generated/",
        "docs/audits/generated/",
        "docs/screenshots/",
        "artifacts/",
    )
    if any(marker in normalized for marker in generated_markers):
        return None
    fail(f"missing required non-generated evidence file: {path_value}")


def validate_client_test_world_materialization() -> None:
    contract = load_json("content/worldgen/client_test_world_materialization_v0_3.json")
    scene = load_json("content/worldgen/scenes/open_world/willowmere_outskirts_region_v0_1.json")
    pack = load_json("content/worldgen/packs/worldgen_open_world_test_v0_12.json")
    placement = load_json("content/worldgen/open_world_build_placement_policy_v0_1.json")
    family = load_json("content/worldgen/terrain_visual_family_authority_v0_1.json")
    candidates = load_json("content/assets/intake/lpc_open_world_terrain_candidate_registry_v0_1.json")
    require_file(contract["materializer"])
    validate_optional_generated_evidence(contract["semanticTopologyPreview"], "semanticTopologyPreview")
    if "diagnostic colors only" not in contract.get("previewPolicy", "") or "live-client screenshots remain final visual authority" not in contract.get("previewPolicy", ""):
        raise ValueError("semantic topology preview is not clearly separated from runtime evidence")
    if contract.get("enabledByDefault") is not True:
        raise ValueError("client worldgen test-world materialization must remain enabled")
    if scene.get("editor", {}).get("generationProfile") != "open_world_v7_source_pure_certification_v167z67":
        raise ValueError("default client scene is not using the current V7 source-pure open-world generation profile")
    if pack.get("defaultScene") != "willowmere_outskirts_open_world" or pack.get("requiresLegacySceneSet") is not False:
        raise ValueError("open-world test pack does not own its default scene/legacy policy")
    if scene.get("transitions"):
        raise ValueError("default open-world region must not bake outdoor portals")
    natural_assets = {str(item.get("assetId", "")) for item in scene.get("objects", [])}
    required_nature_groups = {
        "tree": any(asset.startswith("oak_tree") for asset in natural_assets),
        "bush": any(asset.startswith("berry_bush") for asset in natural_assets),
        "rock": any(asset.startswith("boulder") for asset in natural_assets),
        "mushroom": any(asset.startswith("forage_mushroom") for asset in natural_assets),
        "herb": any(asset.startswith("wild_herb") for asset in natural_assets),
        "flower": any(asset.startswith("wildflower_patch") for asset in natural_assets),
        "reed": any(asset.startswith("reed_patch") for asset in natural_assets),
    }
    missing_nature = sorted(name for name, present in required_nature_groups.items() if not present)
    if missing_nature:
        raise ValueError(f"default biome does not exercise ElizaWy nature groups: {missing_nature}")
    tree_variants = {asset for asset in natural_assets if asset.startswith("oak_tree")}
    if len(tree_variants) < 4:
        raise ValueError(f"default biome must exercise at least four ElizaWy tree variants: {sorted(tree_variants)}")
    terrain = scene.get("layers", {}).get("terrain", [])
    flat = [tile for row in terrain for tile in row]
    required = {"Grass", "Road", "Sand", "OceanShallow", "OceanDeep", "MudBank", "ShallowWater", "Water", "DeepWater"}
    missing = required - set(flat)
    if missing:
        raise ValueError(f"open-world generated scene is missing roles: {sorted(missing)}")
    forbidden = {"TilledSoil", "WateredSoil", "Crop", "MountainRock", "MountainPath", "Cliff", "PebbleShore", "Bridge", "StonePath"} & set(flat)
    if forbidden:
        raise ValueError(f"default biome reintroduced static/mixed-family terrain: {sorted(forbidden)}")
    if family.get("activeOpenWorldFamily") != "lpc_terrain_v7_island_v1":
        raise ValueError("open-world terrain is not using the source-pure V7 certification family")
    if placement.get("businessPlacement", {}).get("cityCentered") is None:
        raise ValueError("open-world city/rural business placement policy is missing")
    if len(candidates.get("candidates", [])) < 8 or candidates.get("policy", {}).get("runtimeUseBeforeAudit") is not False:
        raise ValueError("LPC open-world terrain candidate intake is incomplete or bypasses audit")


def validate_universal_lpc_character_authority() -> None:
    lock = load_json("content/assets/intake/universal_lpc_generator_source_lock_v0_1.json")
    summary = load_json("content/assets/lpc/universal_lpc_character_source_summary_v0_1.json")
    policy = load_json("content/characters/universal_lpc_character_generation_policy_v0_1.json")
    profiles = load_json("content/characters/universal_lpc_npc_generation_profiles_v0_1.json")
    require_file("content/assets/lpc/licenses/universal_lpc_credits_snapshot_0f898bb6.csv.gz")
    require_file("content/assets/lpc/universal_lpc_commercial_catalog_v0_1.json.gz")
    require_file("content/editor/character_studio_universal_lpc_source_v0_1.json")
    require_file("content/assets/lpc/universal_lpc_sharealike_catalog_v0_1.json.gz")
    share_policy = load_json("content/assets/intake/universal_lpc_sharealike_intake_v0_1.json")
    if share_policy.get("recordCount") != 2038 or share_policy.get("enabled") is not True:
        raise ValueError("Universal LPC ShareAlike intake is not enabled or has the wrong record count")
    if lock.get("commit") != "0f898bb675a1abe16ce430e82e3bf9daed278690":
        raise ValueError("Universal LPC character source lock changed")
    if summary.get("creditRecords") != 13818 or summary.get("spritesheetFiles") != 88235:
        raise ValueError("Universal LPC source audit counts changed")
    identity = policy.get("identity", {})
    if identity.get("sexValues") != ["Male", "Female"]:
        raise ValueError("Universal LPC policy must preserve Male/Female sex values")
    if identity.get("ageGroups") != ["Child", "Teen", "Adult", "Elder"]:
        raise ValueError("Universal LPC policy must preserve all four age groups")
    if identity.get("pronounFieldEnabled") is not False:
        raise ValueError("Universal LPC policy must keep pronoun fields disabled")
    if len(profiles.get("profiles", [])) < 7:
        raise ValueError("Universal LPC NPC generation profiles are incomplete")



def validate_character_studio_usage_tracking() -> None:
    require_file("crates/haven_assets/src/universal_lpc_character_authority.rs")
    require_file("apps/haven_editor_native/src/app/character_studio.rs")
    require_file("tools/automation/characters/Build-UniversalLpcUsageManifestV167X.py")
    contract = load_json("content/editor/character_studio_universal_lpc_source_v0_1.json")
    if contract.get("authorityOutput") != "WORKSPACE/generated/universal_lpc_character_authority_v167w.json":
        raise ValueError("Character Studio must consume the v167w authority")
    if contract.get("usageManifestTool") != "tools/automation/characters/Build-UniversalLpcUsageManifestV167X.py":
        raise ValueError("Character Studio usage tracking tool is not registered")



def validate_open_asset_broad_credits() -> None:
    policy = load_json("content/legal/havenwild_open_asset_credit_policy_v0_1.json")
    summary = load_json("content/legal/open_assets/UNIVERSAL_LPC_MASTER_CATALOG_SUMMARY.json")
    require_file("content/legal/HAVENWILD_OPEN_ASSET_ACKNOWLEDGEMENT.txt")
    require_file("content/legal/open_assets/UNIVERSAL_LPC_MASTER_CONTRIBUTORS.txt")
    require_file("content/legal/open_assets/UNIVERSAL_LPC_MASTER_CONTRIBUTORS.csv")
    require_file("tools/automation/release/Build-HavenwildOpenAssetCreditsV167Y.py")
    if policy.get("broadAcknowledgement", {}).get("enabled") is not True:
        raise ValueError("broad open-asset acknowledgment must remain enabled")
    if policy.get("exactBuildAttribution", {}).get("required") is not True:
        raise ValueError("exact per-build open-asset attribution must remain required")
    if summary.get("approvedSourceRecordCount") != 13818:
        raise ValueError("Universal LPC master credits do not cover the approved catalog")
    if summary.get("conditionalShareAlikeRecordCount") != 2038:
        raise ValueError("Universal LPC master credits do not cover the ShareAlike pool")



def validate_gameplay_wardrobe_pipeline() -> None:
    catalog = load_json("content/characters/gameplay_clothing_item_catalog_v0_1.json")
    loot = load_json("content/loot/clothing_loot_tables_v0_1.json")
    npc = load_json("content/characters/npc_outfit_catalog_v0_1.json")
    crafting = load_json("content/crafting/havenwild_crafting_catalog_v0_1.json")
    items = catalog.get("items", [])
    item_ids = {item.get("itemId") for item in items}
    if len(items) < 14 or len(item_ids) != len(items):
        raise ValueError("gameplay clothing item catalog is incomplete or contains duplicates")
    if any(item.get("stackLimit") != 1 for item in items):
        raise ValueError("wearable clothing must remain non-stackable")
    if any(not item.get("runtimeReady") for item in items):
        raise ValueError("current embedded gameplay clothing items must be runtime-ready")
    required_asset_ref_keys = {"pack_id", "category", "asset_id", "source_id", "variant_id"}
    forbidden_asset_ref_keys = {"packId", "assetId", "sourceId", "variantId"}
    for item in items:
        asset_ref = item.get("assetRef")
        if not isinstance(asset_ref, dict):
            raise ValueError(f"clothing item {item.get('itemId')} has no portable asset reference")
        missing = required_asset_ref_keys - set(asset_ref)
        if missing:
            raise ValueError(
                f"clothing item {item.get('itemId')} assetRef is missing Rust PortableAssetRef fields: {sorted(missing)}"
            )
        legacy = forbidden_asset_ref_keys & set(asset_ref)
        if legacy:
            raise ValueError(
                f"clothing item {item.get('itemId')} assetRef uses unsupported camelCase fields: {sorted(legacy)}"
            )
        if asset_ref.get("variant_id") != item.get("variantId"):
            raise ValueError(
                f"clothing item {item.get('itemId')} assetRef variant does not match its item variant"
            )
    for table in loot.get("tables", []):
        for entry in table.get("entries", []):
            if entry.get("itemId") not in item_ids:
                raise ValueError(f"clothing loot table references unknown item {entry.get('itemId')}")
    for outfit in npc.get("outfits", []):
        for values in outfit.get("weightedItems", {}).values():
            for item_id in values:
                if item_id not in item_ids:
                    raise ValueError(f"NPC outfit references unknown item {item_id}")
    stations = {station.get("id") for station in crafting.get("stations", [])}
    if "tailor_bench" not in stations:
        raise ValueError("tailor bench crafting station is missing")
    require_file("crates/haven_game/src/character_equipment_runtime.rs")
    require_file("crates/haven_game/src/clothing_loot_runtime.rs")
    require_file("tools/automation/characters/Build-UniversalLpcGameplayWardrobeV167Y6.py")


def validate_terrain_topology_certification() -> None:
    contract = load_json("content/worldgen/terrain_topology_contract_v0_2.json")
    manifest = load_json(
        "content/worldgen/scenes/terrain_acceptance/terrain_acceptance_scene_manifest_v1.json"
    )
    metrics = load_json(
        "docs/audits/generated/havenwild_open_world_biome_v167z38_metrics.json"
    )
    test_pack = load_json("content/worldgen/packs/worldgen_open_world_test_v0_12.json")
    if contract.get("schema") != "havenwild.terrain_topology_contract.v0_2":
        raise ValueError("terrain topology contract schema changed")
    if manifest.get("version") != 5 or len(manifest.get("scenes", [])) != 9:
        raise ValueError("terrain acceptance scene coverage or exact-V7/workbench evidence version is incomplete")
    if metrics.get("transition_band_violations") != 0:
        raise ValueError("client test-world terrain topology has violations")
    required = {
        "coastline", "river", "pond_bridge", "farm_soil", "mountain",
        "junctions", "snow_ice", "wrapped_world_seam", "terrain_gallery",
    }
    scene_ids = {entry.get("id") for entry in manifest.get("scenes", [])}
    if scene_ids != required:
        raise ValueError("terrain acceptance manifest does not cover all required scenarios")
    acceptance_paths = {entry["path"] for entry in manifest.get("scenes", [])}
    for entry in manifest.get("scenes", []):
        require_file(entry["path"])
        validate_optional_generated_evidence(entry["semanticTopologyPreview"], "semanticTopologyPreview")
        validate_optional_generated_evidence(entry["lpcMappedPreview"], "lpcMappedPreview")
        validate_optional_generated_evidence(entry["comparisonPreview"], "comparisonPreview")
    report = load_json("docs/audits/generated/havenwild_terrain_lpc_certification_report_v167z5a.json")
    if report.get("missingBindings"):
        raise ValueError(f"LPC terrain evidence has missing bindings: {report['missingBindings']}")
    aggregate = report.get("aggregateCounts", {})
    for field in ("invalid_rect_cells", "transparent_source_cells", "missing_binding_cells"):
        if aggregate.get(field, 0):
            raise ValueError(f"LPC terrain evidence has {field}: {aggregate[field]}")
    if report.get("schema") != "havenwild.terrain_lpc_certification_report.v167z27":
        raise ValueError("direct-LPC terrain certification report is stale")
    if report.get("renderContract") != "exact_v7_presentation_authority_w77":
        raise ValueError("terrain certification report does not use W77 exact presentation authority")
    unresolved = aggregate.get("unresolved_transition_cells", 0)
    rules = report.get("certificationRules", {})
    if unresolved and rules.get("unresolvedTransitionCellsAreWorkbenchCandidates") is not True:
        raise ValueError("unresolved terrain contacts are not routed to the workbench")
    if unresolved and rules.get("workbenchRequiredForUnresolvedContacts") is not True:
        raise ValueError("unresolved terrain contacts do not require hand-author repair")
    evidence = manifest.get("evidencePolicy", {})
    if evidence.get("unresolvedTransitionCellsAreWorkbenchCandidates") is not True:
        raise ValueError("acceptance manifest does not recognize unresolved contacts as workbench candidates")
    workbench_path = evidence.get("workbench")
    if not workbench_path:
        raise ValueError("acceptance manifest does not declare the transition workbench")
    workbench = load_json(workbench_path)
    if workbench.get("materialCount") != 15 or workbench.get("completeDirectPairCount") != 48 or workbench.get("missingPairCount") != 57:
        raise ValueError("transition workbench coverage is not the certified 15/48/57 authority")
    if not acceptance_paths.issubset(set(test_pack.get("sceneFiles", []))):
        raise ValueError("client terrain test pack does not load every acceptance scene")
    require_file("tools/automation/validation/validate_terrain_topology_v167z5.py")



def validate_direct_lpc_terrain_authority() -> None:
    terrain_render = require_file(
        "crates/haven_game/src/terrain_render.rs"
    ).read_text(encoding="utf-8")
    runtime_assets = require_file(
        "crates/haven_game/src/runtime_assets.rs"
    ).read_text(encoding="utf-8")
    terrain_pass = require_file(
        "crates/haven_game/src/runtime_terrain_pass.rs"
    ).read_text(encoding="utf-8")
    terrain_base_draw = require_file(
        "crates/haven_game/src/runtime_terrain_base_draw.rs"
    ).read_text(encoding="utf-8")
    retained = require_file(
        "crates/haven_game/src/terrain_scene_surface.rs"
    ).read_text(encoding="utf-8")
    mapped = require_file(
        "crates/haven_assets/src/lpc_mapped_terrain.rs"
    ).read_text(encoding="utf-8")
    editor_atlas = require_file(
        "apps/haven_editor_native/src/app/atlas_render.rs"
    ).read_text(encoding="utf-8")
    main = require_file("crates/haven_game/src/main.rs").read_text(encoding="utf-8")
    bridge = require_file(
        "crates/haven_game/src/bridge_render.rs"
    ).read_text(encoding="utf-8")
    save_lib = require_file("crates/haven_save/src/lib.rs").read_text(encoding="utf-8")
    palette = require_file(
        "crates/haven_editor/src/palette_defaults.rs"
    ).read_text(encoding="utf-8")

    v7_png = require_file(
        "content/assets/lpc/source/lpc-terrains-v7/terrain-v7.png"
    )
    v7_tsx = require_file(
        "content/assets/lpc/source/lpc-terrains-v7/terrain-v7.tsx"
    )
    with Image.open(v7_png) as image:
        if image.size != (1024, 2048):
            raise ValueError(f"terrain-v7 source must remain 1024x2048, found {image.size}")

    tsx_root = ET.parse(v7_tsx).getroot()
    if tsx_root.get("tilewidth") != "32" or tsx_root.get("tileheight") != "32":
        raise ValueError("terrain-v7 TSX must preserve native 32x32 source cells")
    terrain_ids = {
        entry.get("name"): int(entry.get("tile", "-1"))
        for entry in tsx_root.findall("./terraintypes/terrain")
    }
    required_source_ids = {
        "Dirt_Tan": 97,
        "Dirt_Brown": 100,
        "Dirt_Dark": 103,
        "Rock_Gray": 109,
        "Rock_Dark": 112,
        "Rock_Black": 115,
        "Mud_Brown": 124,
        "Grass": 321,
        "Soil": 333,
        "Sand": 336,
        "Gravel_1": 345,
        "Dirt_Roots": 348,
        "Water_Shallows_Dirt": 545,
        "Water": 548,
        "Water_Deep": 551,
        "Stone_Tan": 790,
        "Mudstone_Brown": 796,
        "Water_Shallows_Sand": 837,
    }
    for name, tile_id in required_source_ids.items():
        if terrain_ids.get(name) != tile_id:
            raise ValueError(
                f"terrain-v7 source mapping changed for {name}: "
                f"expected {tile_id}, found {terrain_ids.get(name)}"
            )

    required_render_tokens = (
        "LPC_TERRAIN_V7_SOURCE_PATH",
        "direct_lpc_v7_base_rect",
        "TileKind::Grass | TileKind::TallGrass",
        "TileKind::Sand | TileKind::WetSand",
        "TileKind::PebbleShore",
        "TileKind::MountainPath",
        "TileKind::MountainRock",
        "TileKind::CaveFloor",
        "TileKind::OceanShallow | TileKind::ShoreFoam",
        "TileKind::DeepWater | TileKind::OceanDeep",
    )
    if any(token not in terrain_render for token in required_render_tokens):
        raise ValueError("source-pure direct terrain-v7 fallback coverage is incomplete")

    required_mapped_tokens = (
        "lpc_mapped_terrain_owner_fill_entry_for_map",
        "lpc_mapped_terrain_transition_entry_for_map",
        ".filter(|entry| entry.is_mixed)",
        "lpc_mapped_terrain_quiet_entry",
        'if material != "Grass"',
        "atomic objects/stamps",
    )
    if any(token not in mapped for token in required_mapped_tokens):
        raise ValueError("V7 normalized atlas or atomic-detail policy is incomplete")

    combined_active_renderers = terrain_pass + terrain_base_draw + retained + editor_atlas + main
    forbidden_active_tokens = (
        "draw_direct_water_depth_rim",
        "draw_tile_transition_overlays",
        "mod terrain_transition_draw;",
        "resolve_transition_atlas_requests",
        "resolve_transition_inner_corner_requests",
    )
    if any(token in combined_active_renderers for token in forbidden_active_tokens):
        raise ValueError("active V7 renderers still permit generic or cross-style overlays")
    if "direct_lpc_base_rect" in terrain_base_draw:
        raise ValueError("active V7 terrain base can still fall through to ElizaWy terrain cells")
    if "self.lpc_mapped_terrain_atlas.as_ref()" not in terrain_base_draw:
        raise ValueError("runtime does not prioritize the source-pure normalized V7 atlas")
    if "self.draw_mapped_terrain_tuple_overlay(entry, screen)" not in terrain_pass:
        raise ValueError("runtime does not submit exact authored V7 tuple overlays")
    if "self.draw_mapped_terrain_tuple_overlay" not in retained:
        raise ValueError("retained terrain surface omits exact V7 tuple overlays")
    if "terrain_tuple_render_origin_tiles(x, y)" not in editor_atlas:
        raise ValueError("native editor does not use the shared tuple intersection origin")
    if "self.lpc_mapped_terrain.as_ref()" not in editor_atlas:
        raise ValueError("native editor palette/runtime does not use the normalized V7 atlas")
    if "lpc_mapped_terrain_quiet_entry(underlay)" not in bridge:
        raise ValueError("bridge water underlay can still borrow a non-V7 terrain source")
    if "BuildTool::Floor(TileKind::WetSand)" in palette:
        raise ValueError("WetSand is still exposed as an active editor brush")
    generation = re.search(r"CURRENT_CLIENT_GENERATION_VERSION:\s*u32\s*=\s*(\d+)", save_lib)
    if generation is None or int(generation.group(1)) < 10:
        raise ValueError("client generation version predates the V7 source-pure migration baseline 10")
    if "lpc_mapped_terrain_atlas" not in runtime_assets:
        raise ValueError("normalized V7 atlas is not loaded through runtime assets")
    if "draw_direct_transition_composite" in terrain_render:
        raise ValueError("runtime still synthesizes transition pixels")

def validate_character_render_and_frame_performance() -> None:
    generator = require_file("tools/automation/characters/Build-UniversalLpcPlayerRuntimeCachesV167Z7.py").read_text(encoding="utf-8")
    build_script = require_file("tools/build/Build.sh").read_text(encoding="utf-8")
    compositor = require_file(
        "crates/haven_game/src/character_runtime_compositor.rs"
    ).read_text(encoding="utf-8")
    character_visual_policy = require_file(
        "crates/haven_game/src/character_visual_policy.rs"
    ).read_text(encoding="utf-8")
    runtime_character_authority = json.loads(require_file(
        "content/characters/runtime_character_visual_authority_v0_1.json"
    ).read_text(encoding="utf-8"))
    terrain_pass = require_file(
        "crates/haven_game/src/runtime_terrain_pass.rs"
    ).read_text(encoding="utf-8")
    terrain_base_draw = require_file(
        "crates/haven_game/src/runtime_terrain_base_draw.rs"
    ).read_text(encoding="utf-8")
    chunk_cache = require_file(
        "crates/haven_game/src/chunk_surface_cache.rs"
    ).read_text(encoding="utf-8")
    frontend = require_file("crates/haven_game/src/client_frontend.rs").read_text(
        encoding="utf-8"
    )
    runtime_assets = require_file(
        "crates/haven_game/src/runtime_assets.rs"
    ).read_text(encoding="utf-8")
    base_cache = require_file(
        "crates/haven_game/src/base_terrain_cache.rs"
    ).read_text(encoding="utf-8")
    runtime_draw = require_file(
        "crates/haven_game/src/runtime_draw.rs"
    ).read_text(encoding="utf-8")
    terrain_render = require_file(
        "crates/haven_game/src/terrain_render.rs"
    ).read_text(encoding="utf-8")
    revision = "167Z109V1-authored-action-alias-and-directional-coverage-v1"
    if revision not in generator or revision not in build_script:
        raise ValueError("tools/build/Build.sh and the Universal LPC runtime-cache generator revision differ")
    required_generator_tokens = (
        "RUNTIME_H = 96",
        "sourcePixelsPreservedAtOneToOne",
        "build_component",
        "assets/source/licensed/universal_lpc_generator",
        "head/heads/human/heads_human_male.json",
        "head/heads/human/heads_human_female.json",
    )
    if any(token not in generator for token in required_generator_tokens):
        raise ValueError("LPC native 64x96 frame normalization is incomplete")
    if "dest_size: Some(vec2(64.0, source.h))" not in compositor:
        raise ValueError("runtime compositor no longer preserves the normalized 64px LPC runtime frame width")
    creator_model = require_file("crates/haven_game/src/character_creator_model.rs").read_text(encoding="utf-8")
    if 'pack_id: "havenwild_starter_character".to_string()' not in creator_model:
        raise ValueError("character creator no longer targets the curated starter runtime pack")
    if "FilterMode::Nearest" not in character_visual_policy or "set_filter" not in character_visual_policy:
        raise ValueError("runtime character texture policy must enforce nearest filtering")
    texture_policy_tokens = (
        "load_project_character_texture",
        "load_optional_project_character_texture",
    )
    if not any(token in compositor for token in texture_policy_tokens):
        raise ValueError("runtime compositor bypasses the normalized character texture policy")
    if not any(token in frontend for token in texture_policy_tokens):
        raise ValueError("frontend character previews bypass the normalized character texture policy")
    if runtime_character_authority.get("proceduralCharacterArtworkFallback") is not False:
        raise ValueError("runtime character authority must disable procedural character artwork fallback")
    if "draw_procedural_fallback" in compositor:
        raise ValueError("production character compositor still contains non-LPC fallback artwork")
    if "production character appearance has no resolved body/base LPC layer" not in compositor:
        raise ValueError("layered character runtime does not require a resolved body/base LPC layer")
    if "No production character visual resolved; procedural character fallback is disabled" not in runtime_assets:
        raise ValueError("runtime asset startup does not report complete character visual resolution failure")
    if "row as f32 * 96.0" not in runtime_draw or "dest_size: Some(vec2(64.0, 96.0))" not in runtime_draw:
        raise ValueError("source-backed player compatibility atlas does not use the normalized 64x96 frame geometry")
    if "let bob = self.walk_phase.sin()" in runtime_draw:
        raise ValueError("production player draw still contains procedural character body fallback geometry")

    for body_cache in (
        "assets/generated/lpc/characters/layers/havenwild_player_body_male_walk_64.png",
        "assets/generated/lpc/characters/layers/havenwild_player_body_female_walk_64.png",
    ):
        body_path = require_file(body_cache)
        with Image.open(body_path).convert("RGBA") as image:
            if image.size != (576, 384):
                raise ValueError(f"Universal LPC body cache geometry changed: {body_cache}")
            for row in range(4):
                head_band = image.crop((16, row * 96 + 32, 48, row * 96 + 64))
                if head_band.getbbox() is None:
                    raise ValueError(
                        f"Universal LPC body cache is missing its human head layer: {body_cache}, row {row}"
                    )
    if 'std::env::var("HAVENWILD_RETAINED_CHUNK_COMMANDS")' in chunk_cache:
        raise ValueError("legacy CPU retained-command override is still active")
    if "HAVENWILD_EXPERIMENTAL_CPU_RETAINED_CHUNK_COMMANDS" not in chunk_cache:
        raise ValueError("experimental retained-command lane is not explicitly isolated")
    if "VisibleTerrainPlanCache" not in terrain_pass or "water_spans" not in terrain_pass:
        raise ValueError("retained visible terrain frame plan is not active")
    if "Credits [C]" not in frontend or "credits_button_rect_for_viewport" not in frontend:
        raise ValueError("small bottom-right credits control is not registered")
    direct_source = "assets/source/licensed/lpc_revised/Terrain/terrain_summer.png"
    if direct_source not in terrain_render or "lpc_terrain_source" not in runtime_assets:
        raise ValueError("direct LPC summer terrain source is not registered")
    if "load_authored_tuple_atlas: true" not in runtime_assets:
        raise ValueError("authored terrain-map-v7 tuple atlas is not mandatory in normal runtime")
    if '"terrain.sand"' not in runtime_assets or "lpc_mapped_terrain" not in runtime_assets:
        raise ValueError("authored terrain-map-v7 tuple atlas is not loaded through the runtime asset session")
    if "(None, None)" in runtime_assets and "direct_lpc_sources_ready" in runtime_assets:
        raise ValueError("licensed LPC source mounts still disable the authored tuple atlas")
    if "terrain_transition" not in runtime_assets:
        raise ValueError("exact-pair compatibility transition atlas is unavailable for compound masks")
    if (
        "lpc_mapped_terrain_runtime_entry_for_map(map, x, y)" not in base_cache
        and "resolve_authored_v7_surface_for_map(map, x, y)" not in base_cache
    ):
        raise ValueError(
            "chunk cache is not using the authored runtime tuple policy for rounded water depth contours"
        )
    if "lpc_mapped_terrain_exact_entry_for_map(map, x, y)" in base_cache:
        raise ValueError("chunk cache can still cache hard rectangular mapped water-depth tuples")
    if "mapped_entry: None" in base_cache:
        raise ValueError("chunk cache reintroduced the mapped-terrain bypass")
    if "unwrap_or_else(|| resolve_terrain_transitions(map, x, y))" not in base_cache:
        raise ValueError("non-autotiled grass/farm terrain still loses LPC boundary transitions")
    if "lpc_mapped_terrain_atlas" not in terrain_base_draw:
        raise ValueError("runtime terrain base drawer does not use the normalized V7 atlas")
    bridge_render = require_file(
        "crates/haven_game/src/bridge_render.rs"
    ).read_text(encoding="utf-8")
    licensed_lpc_root = ROOT / "assets/source/licensed/lpc_revised"
    if licensed_lpc_root.exists():
        require_file(
            "assets/source/licensed/lpc_revised/Structure/Bridges/Wood Bridge A - No Rails.png"
        )
    else:
        print("INFO LPC bridge source deferred until dependency mount")
    if "draw_direct_source_piece" in terrain_render:
        raise ValueError("runtime still synthesizes compound LPC transitions from opaque tile fragments")
    if "draw_tile_transition_overlays" in terrain_render:
        raise ValueError("active terrain renderer still includes generic compatibility overlays")
    if "draw_bridge_base" not in terrain_base_draw or "bridge_underlay_tile" not in bridge_render:
        raise ValueError("bridges are not rendered as LPC structures over a water underlay")
    if "direct_lpc_v7_map_base_rect" not in terrain_base_draw:
        raise ValueError("farm-soil compatibility cells are not selected from V7 adjacency")
    if "if !self.dev_mode" not in runtime_draw:
        raise ValueError("developer status panel can still cover the production vitals HUD")

    atlas = ROOT / "assets/generated/lpc/characters/havenwild_player_walk_64.png"
    manifest = ROOT / "assets/generated/lpc/characters/havenwild_player_walk_64.json"
    if atlas.is_file():
        with Image.open(atlas) as image:
            if image.size != (576, 384):
                raise ValueError(f"runtime player atlas must be 576x384, found {image.size}")
    if manifest.is_file():
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        if payload.get("cellSize") != [64, 96]:
            raise ValueError("runtime player manifest must advertise 64x96 cells")
        if payload.get("generatorRevision") != revision:
            universal_lpc_root = ROOT / "assets/source/licensed/universal_lpc_generator"
            if universal_lpc_root.is_dir():
                raise ValueError(
                    "runtime player manifest revision is stale; run Build development (fast) "
                    "to rebuild the authored Universal LPC action caches"
                )
            print(
                "INFO runtime player cache revision predates current generator; "
                "fast build will rebuild after the Universal LPC dependency is mounted"
            )



def validate_project_wide_elizawy_asset_authority() -> None:
    authority_path = "content/assets/lpc/lpc_project_asset_authority_v0_1.json"
    contract_path = "content/assets/lpc/lpc_project_asset_audit_contract_v0_1.json"
    authority = load_json(authority_path)
    contract = load_json(contract_path)
    lock = load_json("content/assets/intake/lpc_source_lock_v0_1.json")

    if authority.get("schema") != "havenwild.lpc_project_asset_authority.v0_1":
        raise ValueError("unexpected project-wide ElizaWy asset authority schema")
    source = authority.get("source", {})
    if source.get("id") != "elizawy_lpc" or source.get("commit") != PINNED_LPC_COMMIT:
        raise ValueError("project-wide visual authority is not pinned to ElizaWy/LPC")
    if source.get("tileSize") != 32 or source.get("visualRole") != "primary_project_art_foundation":
        raise ValueError("ElizaWy/LPC must remain the 32px primary project art foundation")

    required_domains = set(contract.get("requiredDomains", []))
    actual_domains = {domain.get("id") for domain in authority.get("domains", [])}
    if actual_domains != required_domains or len(actual_domains) != 10:
        raise ValueError(f"ElizaWy project domains changed: {sorted(actual_domains)}")
    policies = authority.get("projectPolicy", {})
    required_true = (
        "sourceTreeIsImmutable",
        "preserveOriginalFolderAndCreditLayout",
        "deriveCatalogsAndAtlasesFromSourceRects",
        "generatedAtlasesAreDisposableCaches",
        "worldGenerationMustUseElizaWyCatalogs",
        "nativeEditorAndRuntimeMustShareStableAssetIds",
        "generatedWorldsMustReserveInfrastructureBeforeEcology",
    )
    for key in required_true:
        if policies.get(key) is not True:
            raise ValueError(f"ElizaWy project authority must keep {key}=true")
    for key in (
        "runtimeMayUseUncataloguedSourceFiles",
        "moveRawThirdPartyFilesIntoProjectOwnedFolders",
        "runtimeNaturalObjectProceduralFallbackAllowed",
        "runtimeExistingElizaWyEquivalentReplacementAllowed",
    ):
        if policies.get(key) is not False:
            raise ValueError(f"ElizaWy project authority must keep {key}=false")

    tree_policy = authority.get("treeFirstWorldPolicy", {})
    if tree_policy.get("worldBuiltAroundTrees") is not True:
        raise ValueError("open-world generation must be built around authored ElizaWy trees")
    if tree_policy.get("genericTreeFallbackAllowed") is not False:
        raise ValueError("generic tree fallback cannot be re-enabled")
    if tree_policy.get("treeVisualFootprintTiles") != [3, 4] or tree_policy.get("treeTrunkCollisionTiles") != [1, 1]:
        raise ValueError("tree canopy/trunk footprint contract changed")
    if tree_policy.get("minimumAuthoredTreeVariantsInTestWorld", 0) < 4:
        raise ValueError("tree-first test world must retain at least four authored tree variants")

    routes_path = authority.get("projectRoutes")
    editor_library_path = authority.get("editorLibrary")
    project_catalog_path = authority.get("projectAssetCatalog")
    routes = load_json(routes_path)
    editor_library = load_json(editor_library_path)
    project_catalog = load_json(project_catalog_path)
    if {item.get("domain") for item in routes.get("routes", [])} != required_domains:
        raise ValueError("ElizaWy project routes do not cover every required domain")
    if {item.get("id") for item in editor_library.get("collections", [])} != required_domains:
        raise ValueError("ElizaWy editor library does not expose every required domain")
    if project_catalog.get("primaryAuthority") != authority_path or project_catalog.get("primarySource") != "elizawy_lpc":
        raise ValueError("project asset catalog is not rooted in ElizaWy/LPC")
    if lock.get("projectAssetAuthority") != authority_path or lock.get("projectAssetAuditContract") != contract_path:
        raise ValueError("LPC source lock is not routed through the project-wide authority/audit")
    if lock.get("sourceTreePolicy", {}).get("genericReplacementOfExistingElizaWyArtAllowed") is not False:
        raise ValueError("source lock permits generic replacement of ElizaWy art")
    require_file(contract["generator"])
    require_file("tools/automation/dependencies/Ensure-LpcDependency.py")
    require_file("tools/automation/assets/Promote-LpcRuntimeAssets.py")

    tool_registry = load_json("tools/tool_registry.json")
    registered = {entry.get("path") for entry in tool_registry.get("entries", [])}
    if contract["generator"] not in registered:
        raise ValueError("project-wide ElizaWy audit tool is not registered")

    build_sh = require_file("tools/build/Build.sh").read_text(encoding="utf-8")
    build_ps = require_file("tools/build/Build.ps1").read_text(encoding="utf-8")
    for text, label in ((build_sh, "Build.sh"), (build_ps, "Build.ps1")):
        if "Build-ElizaWyProjectAssetAuditV167Z38.py" not in text or "lpc-audit" not in text:
            raise ValueError(f"{label} does not enforce the project-wide ElizaWy audit")

    promote = require_file("tools/automation/assets/Promote-LpcRuntimeAssets.py").read_text(encoding="utf-8")
    registry = require_file("crates/haven_assets/src/asset_registry.rs").read_text(encoding="utf-8")
    runtime_draw = require_file("crates/haven_game/src/runtime_object_draw.rs").read_text(encoding="utf-8")
    worldgen = require_file("tools/automation/worldgen/Build-ClientWorldgenTestSceneV167Z.py").read_text(encoding="utf-8")
    loader = require_file("crates/haven_core/src/worldgen_loader.rs").read_text(encoding="utf-8")
    if not any(revision in promote for revision in (
        "167Z53-authored-rock-variant-selection-v1",
        "AC3R4F-tree-visible-natural-object-rebuild-v1",
    )):
        raise ValueError("ElizaWy natural-scale object atlas revision does not match current natural-object authority")
    for tree_id in ("oak_tree_variant_05", "oak_tree_variant_06", "oak_tree_variant_07", "oak_tree_variant_08"):
        if tree_id not in promote or tree_id not in registry or tree_id not in worldgen:
            raise ValueError(f"ElizaWy tree variant is not routed project-wide: {tree_id}")
    if "if object.kind == ObjectKind::CaveEntrance" not in runtime_draw:
        raise ValueError("runtime object fallback policy is not explicitly restricted to the cave-entrance compatibility case")
    if "draw_object_fallback(object, screen_origin);" in runtime_draw and "if object.kind == ObjectKind::CaveEntrance" not in runtime_draw:
        raise ValueError("generic runtime object fallback remains enabled")
    if "text.contains(\"wildflower\")" not in loader or "text.contains(\"reed_patch\")" not in loader:
        raise ValueError("worldgen loader does not recognize ElizaWy flowers/reeds")

    source_root = ROOT / lock["fullSourceProjectPath"]
    complete_source = source_root.is_dir() and all(
        (source_root / required).exists() for required in lock.get("requiredTopLevelPaths", [])
    )
    if not complete_source:
        print("INFO full ElizaWy source tree absent; generated repository audit deferred until dependency mount")
        return

    outputs = contract.get("outputs", {})
    summary_path = ROOT / outputs["summary"]
    full_audit_path = ROOT / outputs["fullAudit"]
    # These audit products intentionally live under WORKSPACE/generated and are
    # machine-local/disposable. Source validation must remain reproducible from
    # repository-owned contracts plus the pinned LPC mount; a clean checkout is
    # not invalid merely because the deep generated audit has not been rebuilt
    # on this machine yet. When both products are present, validate them fully.
    if not summary_path.is_file() or not full_audit_path.is_file():
        print(
            "INFO full ElizaWy source tree mounted; generated repository audit "
            "is absent and deferred (run the LPC audit command for deep audit evidence)"
        )
        return

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("sourceCommit") != PINNED_LPC_COMMIT or summary.get("coverageComplete") is not True:
        raise ValueError("full ElizaWy repository audit is incomplete or uses the wrong source revision")
    if summary.get("sourceRevisionVerified") is not True:
        raise ValueError("full ElizaWy repository audit lacks verified source provenance")
    domain_counts = summary.get("domainCounts", {})
    missing_domains = sorted(domain for domain in required_domains if int(domain_counts.get(domain, 0)) <= 0)
    if missing_domains:
        raise ValueError(f"full ElizaWy audit has empty required domains: {missing_domains}")
    if summary.get("unroutedFileCount") != 0 or summary.get("duplicateStableAssetIdCount") != 0:
        raise ValueError("full ElizaWy repository audit contains unrouted files or duplicate stable IDs")
    for domain in required_domains:
        catalog = load_json(f"{outputs['catalogRoot']}/{domain}.json")
        if catalog.get("domain") != domain or catalog.get("recordCount") != domain_counts[domain]:
            raise ValueError(f"ElizaWy domain catalog is stale or mismatched: {domain}")


def validate_universal_lpc_complete_repository_authority() -> None:
    lock = load_json("content/assets/intake/universal_lpc_generator_source_lock_v0_1.json")
    policy = load_json("content/assets/intake/universal_lpc_complete_visual_authority_v0_1.json")
    summary = load_json("content/assets/lpc/universal_lpc_complete_repository_summary_v0_1.json")
    expected = load_json("content/assets/lpc/universal_lpc_complete_repository_expected_summary_v0_1.json")
    equipment = load_json("content/assets/lpc/universal_lpc_equipment_action_catalog_v0_1.json")
    item_seeds = load_json("content/gameplay/universal_lpc_equipment_item_seed_catalog_v0_1.json")
    require_file("content/assets/lpc/universal_lpc_complete_repository_index_v0_1.json.gz")
    require_file("tools/automation/characters/Build-UniversalLpcCompleteRepositoryIndexV167Z7.py")
    require_file("crates/haven_assets/src/universal_lpc_equipment_catalog.rs")

    if policy.get("sourceMount") != lock.get("mountProjectPath"):
        raise ValueError("Universal LPC complete visual authority uses the wrong source mount")
    rules = policy.get("rules", {})
    for key in (
        "externalCharacterVisualsAllowed",
        "projectAuthoredCharacterPixelsAllowed",
        "creatorToolsWeaponsArmorAllowed",
    ):
        if rules.get(key) is not False:
            raise ValueError(f"Universal LPC complete visual authority must keep {key}=false")
    if rules.get("generatedAtlasesAreDisposableCaches") is not True:
        raise ValueError("Universal LPC generated atlases must remain disposable caches")

    commit = lock.get("commit")
    if summary.get("sourceCommit") != commit or expected.get("commit") != commit:
        raise ValueError("Universal LPC complete repository summary revision changed")
    if summary.get("strictCertified") is not True:
        raise ValueError("Universal LPC complete repository summary is not strict-certified")

    counts = summary.get("counts", {})
    expected_counts = expected.get("counts", {})
    for summary_key, expected_key in (
        ("spritesheetPngFiles", "spritesheetPngFiles"),
        ("sheetDefinitionJsonFiles", "sheetDefinitionJsonFiles"),
        ("creditRecords", "creditRecords"),
    ):
        if counts.get(summary_key) != expected_counts.get(expected_key):
            raise ValueError(f"Universal LPC complete repository count mismatch: {summary_key}")

    records = equipment.get("records", [])
    if equipment.get("sourceCommit") != commit:
        raise ValueError("Universal LPC equipment/action catalog revision changed")
    if len(records) != summary.get("equipmentRecords"):
        raise ValueError("Universal LPC equipment/action source-record catalog count is stale")
    if not records or any(not record.get("stableId") or not record.get("sourcePath") for record in records):
        raise ValueError("Universal LPC equipment/action source records require stable IDs and source paths")

    expected_gameplay_items = expected_counts.get("equipmentDefinitions")
    if item_seeds.get("itemCount") != expected_gameplay_items:
        raise ValueError("Universal LPC gameplay equipment seed count changed")
    if len(item_seeds.get("items", [])) != item_seeds.get("itemCount"):
        raise ValueError("Universal LPC gameplay item seed count does not match records")


def main() -> int:
    checks = [
        ("LPC source lock", validate_lpc_source_lock),
        ("Project-wide ElizaWy asset authority", validate_project_wide_elizawy_asset_authority),
        ("complete LPC summer map", validate_complete_map),
        ("seasonal terrain topology", validate_seasonal_topology),
        ("transition atlas integrity", validate_transition_atlas),
        ("open-world preset", validate_worldgen_preset),
        ("generated-output registry", validate_generated_registry),
        ("LPC production assets", validate_lpc_production_assets),
        ("Character creation clothing policy", validate_character_creation_clothing_policy),
        ("Client generated test world", validate_client_test_world_materialization),
        ("Terrain topology certification", validate_terrain_topology_certification),
        ("Universal LPC character authority", validate_universal_lpc_character_authority),
        ("Universal LPC complete repository authority", validate_universal_lpc_complete_repository_authority),
        ("Character Studio usage tracking", validate_character_studio_usage_tracking),
        ("Open-asset broad credits", validate_open_asset_broad_credits),
        ("Gameplay wardrobe pipeline", validate_gameplay_wardrobe_pipeline),
        ("Direct LPC terrain authority", validate_direct_lpc_terrain_authority),
        ("Character rendering and frame performance", validate_character_render_and_frame_performance),
    ]
    for name, check in checks:
        check()
        print(f"OK {name}")
    print(f"Content integrity passed: {len(checks)} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
