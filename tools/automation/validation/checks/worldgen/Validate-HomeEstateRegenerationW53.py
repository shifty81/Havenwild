#!/usr/bin/env python3
from collections import deque
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[5]


def load(rel):
    p = ROOT / rel
    if not p.exists():
        raise AssertionError(f"missing {rel}")
    return json.loads(p.read_text(encoding="utf-8-sig"))


def req(condition, message):
    if not condition:
        raise AssertionError(message)


def published_assets():
    published = {}
    aliases = {}
    for path in sorted((ROOT / "content/asset_packs/havenwild_objects").glob("published_*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        if data.get("schema") != "havenwild.published_world_asset_catalog.v1":
            continue
        for entry in data.get("entries", []):
            asset_id = entry["id"]
            req(asset_id not in published, f"duplicate published world asset id {asset_id}")
            published[asset_id] = entry
            for alias in list(entry.get("aliases", [])) + [entry.get("semantic_id")]:
                if alias:
                    aliases[alias] = asset_id
    return published, aliases


def find_catalog_entry(catalog, entry_id):
    for entry in catalog.get("entries", []):
        if entry.get("id") == entry_id:
            return entry
    return None


def reachable(terrain, start, blocked):
    height = len(terrain)
    width = len(terrain[0]) if height else 0
    walkable = {"Grass", "TallGrass", "Dirt", "StonePath", "MountainPath"}
    start = tuple(start)
    req(0 <= start[0] < width and 0 <= start[1] < height, f"route start out of bounds: {start}")
    req(terrain[start[1]][start[0]] in walkable, f"route start is not walkable: {start}={terrain[start[1]][start[0]]}")
    queue = deque([start])
    seen = {start}
    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            point = (nx, ny)
            if point in seen or point in blocked:
                continue
            if 0 <= nx < width and 0 <= ny < height and terrain[ny][nx] in walkable:
                seen.add(point)
                queue.append(point)
    return seen


try:
    contract = load("content/estates/home_estate_contract_v1.json")
    profile = load("content/estates/estate_generation_profile_v1.json")
    scene = load("content/worldgen/scenes/home_island/farmstead_scene_v0_3.json")
    recipe_catalog = load("content/buildings/building_recipe_catalog_v1.json")
    instance_catalog = load("content/buildings/building_instance_catalog_v1.json")
    recipe = load("content/buildings/recipes/estate_starter_cottage_v1.json")
    instance = load("content/buildings/instances/estate_starter_cottage_v1.json")
    certification = load("content/assets/world_visual_certification_v1.json")
    dev_pack = load("content/worldgen/packs/worldgen_home_island_test_v0_11.json")
    published, aliases = published_assets()

    req(str(contract.get("pass", "")).startswith(("167Z109W53", "167Z109W54")), "W53 Estate contract pass lineage mismatch")
    req(str(profile.get("pass", "")).startswith(("167Z109W53", "167Z109W54", "167Z109W57")), "W53 Estate generation profile pass lineage mismatch")
    req(contract.get("displayName") == "Estate", "Home Estate display name must be Estate")
    req(contract.get("legacySceneCompatibilityId") == "farmstead", "internal farmstead compatibility id must remain explicit")
    instance_policy = contract["instancePolicy"]
    for key in ("oneCanonicalEstatePerPlayer", "portableAcrossSingleAndMultiplayer", "serverAuthoritativeDuringSession", "sameEstateInstanceIdAcrossServers", "serverReplicaNeverBecomesSeparateAuthority"):
        req(instance_policy.get(key) is True, f"Estate canonical persistence policy regressed: {key}")
    property_policy = contract["propertyPolicy"]
    req(property_policy.get("fixedEntranceSide") == "south", "Estate fixed entrance side must remain south")
    req(property_policy.get("expandThroughEntranceSide") is False, "Estate must not expand through its fixed entrance side")
    req(set(property_policy.get("expandableDirections", [])) == {"north", "east", "west"}, "Estate expansion directions drifted")
    req(contract["progressionPolicy"].get("fullyEstablishedStartingBase") is False, "Estate may not become a fully established starting base")
    req(contract["progressionPolicy"].get("estateUnlockedAfterFieldSurvivalPhase") is True, "Estate field-survival progression rule regressed")

    req(scene.get("sceneId") == "farmstead" and scene.get("legacySceneId") == "farmstead", "W53 must retain internal farmstead scene compatibility")
    req(scene.get("title") == "Estate" and scene.get("canonicalDisplayName") == "Estate", "W53 user-facing Farmstead -> Estate normalization regressed")
    req(scene.get("role") == "player_home_estate", "W53 scene role must be player_home_estate")
    req(any(tag in str(scene.get("version", "")) for tag in ("w53", "w54")), "W53 Estate scene lineage mismatch")
    req(scene.get("sceneSize") == [96, 64] and scene.get("tileSize") == [32, 32], "Estate scene dimensions/tile size drifted")
    edge = scene["edgePolicy"]
    req(edge.get("boundedEstate") is True and edge.get("fixedEntranceSide") == "south" and edge.get("expandThroughEntranceSide") is False, "Estate edge policy drifted")
    req(scene["editor"].get("displayName") == "Estate" and scene["editor"].get("allowBuildingInstanceAuthoring") is True, "native editor Estate identity/building lane regressed")
    req(scene["editor"].get("legacyReferenceOnly") is False, "W53 Estate may not be treated as a legacy reference-only scene")

    terrain = scene["layers"]["terrain"]
    zones = scene["layers"]["zones"]
    width, height = scene["sceneSize"]
    req(len(terrain) == height and all(len(row) == width for row in terrain), "Estate terrain layer dimensions mismatch")
    req(len(zones) == height and all(len(row) == width for row in zones), "Estate zone layer dimensions mismatch")

    entrance = profile["fixedEntrance"]
    req(entrance["side"] == "south" and entrance["transitionId"] == "to_north_road", "Estate generation profile fixed entrance drifted")
    for y in range(60, 64):
        for x in range(46, 51):
            req(terrain[y][x] == "StonePath", f"fixed south Estate gate obstructed at {(x, y)}")
    # Structural border remains bounded by Level-2 authority. W54F normalizes the
    # plateau surface to Grass so the cliff resolver owns the vertical face instead
    # of displaying a MountainRock top plate.
    border_surface = "Grass" if profile.get("pass") in {"167Z109W54F", "167Z109W57K8"} else "MountainRock"
    req(all(terrain[0][x] == border_surface for x in range(width)), "north highland border regressed")
    req(all(terrain[y][0] == border_surface for y in range(height)), "west highland border regressed")
    req(all(terrain[y][width - 1] == border_surface for y in range(height)), "east highland border regressed")
    for x in list(range(0, 46)) + list(range(51, width)):
        req(terrain[height - 1][x] == border_surface, f"south highland border regressed outside gate at x={x}")

    transitions = {t["id"]: t for t in scene.get("transitions", [])}
    req(set(transitions) == {"to_north_road", "to_cave_mouth"}, "W53 Estate must expose only shared-world gate and cave transitions")
    req(transitions["to_north_road"]["rect"] == [46, 62, 5, 2] and transitions["to_north_road"]["toScene"] == "north_road", "Estate shared-world gate transition drifted")
    req(transitions["to_cave_mouth"]["rect"] in ([78, 8, 1, 1], [78, 9, 1, 1], [78, 10, 1, 1]) and transitions["to_cave_mouth"]["toScene"] == "cave_mouth", "Estate cave transition drifted")
    req(all(t.get("toScene") != "tavern_interior" for t in scene.get("transitions", [])), "legacy separate Tavern interior transition must not return to Estate")

    quarantine = set(contract["visualPolicy"]["quarantinedLegacyKindsNeverGenerated"])
    req(quarantine == {"well", "scarecrow", "bench", "log", "greenhouse_marker", "sign"}, "Estate visual quarantine set drifted")
    req(certification.get("status") == "CERTIFIED_WITH_EXPLICIT_QUARANTINES", "W52 visual certification must precede W53")
    certified_quarantine = {x["objectKind"] for x in certification.get("quarantinedOptionalLegacyKinds", [])}
    req(quarantine == certified_quarantine, "W52/W53 quarantine policies disagree")

    cave_obj = None
    blocked = set()
    for obj in scene.get("objects", []):
        asset_id = obj.get("assetId")
        req(asset_id in published, f"Estate object does not resolve through PublishedWorldAssetRegistry: {obj.get('id')} -> {asset_id}")
        status = published[asset_id].get("certification")
        req(status not in {"rejected", "missing", "placeholder"}, f"Estate object uses unusable visual: {obj.get('id')} -> {asset_id} ({status})")
        req(asset_id not in quarantine and aliases.get(asset_id, asset_id) not in quarantine, f"Estate generated quarantined visual {asset_id}")
        if obj.get("blocksMovement"):
            x, y, w, h = obj.get("collisionRect", [0, 0, 0, 0])
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    blocked.add((xx, yy))
        if obj.get("id") == "estate_cave_mouth":
            cave_obj = obj
    req(cave_obj is not None, "Estate exact cave-mouth object missing")
    req(cave_obj["assetId"] == "cave_entrance_default" and cave_obj.get("state") == "open", "Estate cave mouth must use exact open published connector")
    req(cave_obj["visualRect"] == [78, 6, 1, 3] and cave_obj["collisionRect"] == [78, 8, 1, 1], "Estate cave mouth 1x3 placement drifted")
    req(profile["caveMouth"]["tile"] == [78, 8] and profile["caveMouth"]["assetId"] == "cave_entrance_default", "Estate profile/scene cave mouth disagreement")

    recipe_entry = find_catalog_entry(recipe_catalog, "havenwild.estate.starter_cottage")
    instance_entry = find_catalog_entry(instance_catalog, "havenwild.estate.dev.starter_cottage")
    req(recipe_entry and recipe_entry["path"] == "content/buildings/recipes/estate_starter_cottage_v1.json", "Estate cottage recipe missing from BuildingRecipe catalog")
    req(instance_entry and instance_entry["path"] == "content/buildings/instances/estate_starter_cottage_v1.json", "Estate cottage instance missing from BuildingInstance catalog")
    req(recipe.get("id") == "havenwild.estate.starter_cottage" and recipe.get("classification", {}).get("diagnosticOnly") is False, "Estate starter cottage recipe identity drifted")
    req(instance.get("id") == "havenwild.estate.dev.starter_cottage" and instance.get("recipeId") == recipe["id"], "Estate starter cottage BuildingInstance identity drifted")
    req(instance.get("sceneId") == "farmstead" and instance.get("placementSpace") == "scene_local" and instance.get("anchorTile") in ([54, 29], [55, 29], [57, 29], [55, 28]), "Estate cottage placement drifted")
    req(scene["estate"].get("starterCottageBuildingInstanceId") == instance["id"], "Estate scene does not reference starter cottage BuildingInstance")
    req(scene["estate"].get("starterCottagePolicy") in {"development_fixture_or_progression_unlock", "deferred_until_complete_exterior_certified"}, "Estate cottage must remain optional/deferred rather than a starting entitlement")

    furnishings = [f for level in recipe.get("levels", []) for f in level.get("furnishings", [])]
    req(len(furnishings) in {4, 6}, "Estate starter cottage furnishing count must match W53/W53B certified layouts")
    for furnishing in furnishings:
        asset_id = furnishing.get("assetId")
        req(asset_id in published, f"Estate cottage furnishing unresolved: {furnishing.get('id')} -> {asset_id}")
        req(published[asset_id].get("certification") not in {"rejected", "missing", "placeholder"}, f"Estate cottage furnishing unusable: {asset_id}")
    # Structural walls keep collision; visual-only interior finish runs may be explicitly non-blocking.
    for level in recipe.get("levels", []):
        for wall in level.get("wallRuns", []):
            visual_only = wall.get("id") == "rear_interior_finish" or wall.get("id", "").startswith("gable_fill_")
            if not visual_only:
                req(wall.get("blocksMovement") is True, f"Estate cottage structural wall lost authoritative collision: {wall.get('id')}")
            else:
                req(wall.get("blocksMovement") is False and wall.get("visualAssetId") is not None, f"visual-only wall layer drifted: {wall.get('id')}")
            if wall.get("visualStatus") == "deferred_exact_facing":
                req(wall.get("visualAssetId") is None, f"deferred wall must fail closed instead of substituting artwork: {wall.get('id')}")
    roof = recipe.get("roof", {})
    req(roof.get("cameraLocalOcclusion") is True, "Estate cottage roof/cutaway policy drifted")
    if roof.get("mode") == "flat_nine_slice":
        for asset_id in roof.get("components", {}).values():
            req(asset_id in published, f"Estate cottage roof component unresolved: {asset_id}")
    else:
        req(roof.get("mode") == "authored_module", "Estate cottage roof must be flat nine-slice or exact authored module")
        modules = roof.get("authoredModules", [])
        if modules:
            for module in modules:
                roof_asset = module.get("assetId")
                req(roof_asset in published, f"Estate cottage authored roof unresolved: {roof_asset}")
        else:
            roof_asset = roof.get("authoredModuleAssetId")
            req(roof_asset in published, f"Estate cottage authored roof unresolved: {roof_asset}")

    spawn = next(s for s in scene["spawns"] if s["id"] == "player_default")["tile"]
    # The cave mouth's collision/interaction cell is a valid transition target; do not count that one target as a generic obstacle.
    blocked.discard((78, 8))
    seen = reachable(terrain, spawn, blocked)
    for label, point in {
        "fixed south gate": (48, 62),
        "starter cottage front approach": (59, 35),
        "cave approach/threshold": (78, 9),
        "cave interaction approach": (78, 10),
    }.items():
        req(point in seen, f"Estate critical route unreachable from player spawn: {label} {point}")

    farm_path = "content/worldgen/scenes/home_island/farmstead_scene_v0_3.json"
    req(farm_path in dev_pack.get("sceneFiles", []), "W53 Estate scene must remain registered in development pack")
    req(farm_path in dev_pack.get("smokeTests", []), "W53 Estate scene must remain a smoke-test scene")
    req(dev_pack.get("editor", {}).get("defaultScene") == "farmstead", "native editor development pack must continue opening the Estate compatibility scene")
    test_world = dev_pack.get("testWorld", {})
    req(test_world.get("homeEstateSceneId") == "farmstead" and test_world.get("homeEstateDisplayName") == "Estate", "development pack Estate identity pointers drifted")
    req(test_world.get("homeEstateScene") == farm_path and test_world.get("homeEstateBuildingInstanceId") == instance["id"], "development pack Estate scene/BuildingInstance pointers drifted")

    print("PASS W53 Home Estate regeneration authority")
    print("- user-facing Farmstead is normalized to Estate while internal sceneId=farmstead compatibility is retained")
    print("- canonical portable Estate, fixed south entrance and N/E/W expansion rules are locked")
    print(f"- Estate scene contains {len(scene.get('objects', []))} published object instances and no quarantined legacy substitutions")
    print("- exact cave mouth, fixed gate, cottage approach and cave route are reachable from the default spawn")
    print("- starter cottage source remains available, with W53C allowed to fail closed until its complete exact exterior shell is certified")
except Exception as exc:
    print(f"FAIL W53 Home Estate regeneration authority: {exc}", file=sys.stderr)
    sys.exit(1)
