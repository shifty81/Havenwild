#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
CATALOG = ROOT / "content/asset_packs/havenwild_objects/published_world_assets_v1.json"
PACK = ROOT / "content/asset_packs/havenwild_objects/pack.json"
MANIFEST = ROOT / "assets/generated/havenwild_lpc_objects_160x192_v2.json"
SCANNER = ROOT / "tools/automation/assets/Build-PublishedWorldAssetInventoryV1.py"
REGISTRY_RS = ROOT / "crates/haven_assets/src/placeable_asset_registry.rs"
AUTHORED_ENTITIES_RS = ROOT / "crates/haven_core/src/foundation/authored_entities.rs"
LOADER_RS = ROOT / "crates/haven_core/src/worldgen_loader.rs"
EXPORTER_RS = ROOT / "crates/haven_core/src/worldgen_exporter.rs"
BOOTSTRAP_RS = ROOT / "crates/haven_game/src/game_bootstrap.rs"
RUNTIME_PERSISTENCE_RS = ROOT / "crates/haven_game/src/runtime_persistence.rs"
EDITOR_RS = ROOT / "apps/haven_editor_native/src/app/mod.rs"
RUNTIME_ASSETS_RS = ROOT / "crates/haven_game/src/runtime_assets.rs"
MAIN_RS = ROOT / "crates/haven_game/src/main.rs"
OLD_CATALOG = ROOT / "content/asset_packs/havenwild_objects/placeables_v1.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def need(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL W42 published world asset authority: {message}")


def text(path: Path) -> str:
    need(path.is_file(), f"missing {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8-sig")


def main() -> int:
    need(CATALOG.is_file(), "published world asset catalog missing")
    need(not OLD_CATALOG.exists(), "legacy placeables_v1.json still exists as a competing catalog")
    catalog = load(CATALOG)
    need(catalog.get("schema") == "havenwild.published_world_asset_catalog.v1", "catalog schema mismatch")
    entries = catalog.get("entries", [])
    need(len(entries) >= 35, f"expected at least 35 published records, got {len(entries)}")

    ids = [str(entry.get("id", "")) for entry in entries]
    need(len(ids) == len(set(ids)), "duplicate canonical published IDs")
    aliases: dict[str, dict] = {}
    for entry in entries:
        need(entry.get("role") in {
            "placeable", "structure_component", "structural_connector", "building_recipe",
            "terrain_detail", "stamp", "legacy_adapter"
        }, f"{entry.get('id')} has invalid role")
        need(entry.get("certification") in {
            "certified", "candidate", "provisional", "placeholder", "missing", "legacy_alias", "rejected"
        }, f"{entry.get('id')} has invalid certification")
        for alias in entry.get("aliases", []):
            need(alias not in aliases, f"duplicate alias {alias}")
            aliases[alias] = entry

    need(SCANNER.is_file(), "W41 Asset Truth scanner missing")
    spec = importlib.util.spec_from_file_location("havenwild_w42_asset_truth", SCANNER)
    need(spec is not None and spec.loader is not None, "could not load W41 Asset Truth scanner")
    scanner = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = scanner
    spec.loader.exec_module(scanner)
    queue = scanner.build(ROOT)["migrationQueue"]
    expected = queue["sceneCandidates"]
    blockers = set(queue["sceneBlockers"])
    need(len(expected) == 29, f"W41 scene candidate count changed unexpectedly: {len(expected)}")
    need(all(alias in aliases for alias in expected), "not all 29 W41 scene candidates are published aliases")
    need(not (blockers & aliases.keys()), "W42 incorrectly published a scene blocker as an alias")

    manifest = load(MANIFEST)
    manifest_by_id = {entry["id"]: entry for entry in manifest["objects"]}
    for alias in expected:
        source = manifest_by_id[alias]
        entry = aliases[alias]
        need(entry.get("certification") == "candidate", f"{alias} must remain candidate until W43 visual certification")
        provenance = entry.get("provenance", {})
        need(provenance.get("authority") == "lpc_revised_manifest", f"{alias} provenance authority mismatch")
        need(provenance.get("source_path") == source.get("source"), f"{alias} source path mismatch")
        need(provenance.get("source_rect") == source.get("sourceRect"), f"{alias} exact source rect mismatch")
        need(provenance.get("source_mode") == source.get("sourceMode"), f"{alias} source mode mismatch")
        visual = entry.get("visual", {})
        frames = visual.get("frames", [])
        need(len(frames) == 1, f"{alias} must have one W42 cache frame")
        need(frames[0].get("source_rect") == source.get("rect"), f"{alias} runtime cache rect mismatch")
        need(visual.get("foot_anchor") == source.get("footAnchor"), f"{alias} foot anchor mismatch")

    primaries = [entry for entry in entries if entry.get("legacy_object_kind_primary")]
    primary_kinds = [entry.get("legacy_object_kind") for entry in primaries if entry.get("legacy_object_kind")]
    need(len(primary_kinds) == len(set(primary_kinds)), "duplicate primary legacy ObjectKind adapters")
    for required in ("tree", "bush", "boulder", "mushroom", "herb", "log", "table", "chair", "bed", "door", "cave_entrance"):
        need(required in primary_kinds, f"missing primary legacy adapter for {required}")

    pack = load(PACK)
    # W42 owns the authority contract, not a historical content-pack revision.
    # Later asset passes may legitimately advance the pack while retaining the
    # same PublishedWorldAsset source/semantic bindings.
    version = str(pack.get("version", ""))
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:[-+][A-Za-z0-9_.-]+)?", version)
    need(match is not None, f"havenwild_objects pack version is not semver-like: {version!r}")
    major, minor = int(match.group(1)), int(match.group(2))
    need(major == 0 and minor >= 2, f"havenwild_objects pack predates W42 authority: {version}")
    need(any(s.get("id") == "published_world_asset_catalog" and s.get("path", "").endswith("published_world_assets_v1.json") for s in pack.get("sources", [])), "pack does not mount published catalog source")
    need(any(a.get("semantic_id") == "world_asset.catalog.default" and a.get("source_id") == "published_world_asset_catalog" for a in pack.get("assets", [])), "pack does not expose world_asset.catalog.default")

    registry = text(REGISTRY_RS)
    for token in (
        "pub struct PublishedWorldAssetDefinition",
        "pub struct PublishedWorldAssetRegistry",
        "pub type PlaceableAssetRegistry = PublishedWorldAssetRegistry",
        "by_alias: BTreeMap<String, usize>",
        "pub fn resolve_alias",
        "pub fn canonical_ref_for_alias",
        "pub fn canonicalize_scene_aliases",
        "pub fn canonicalize_world_aliases",
        "havenwild.published_world_asset_catalog.v1",
        "legacy_object_kind_primary",
    ):
        need(token in registry, f"registry missing W42 token: {token}")

    core_ref = text(AUTHORED_ENTITIES_RS)
    need("from_scene_asset_alias" in core_ref and "scene_asset_alias_id" in core_ref, "StablePlaceableAssetRef scene alias adapter missing")
    loader = text(LOADER_RS)
    need("StablePlaceableAssetRef::from_scene_asset_alias" in loader, "worldgen loader does not preserve authored assetId")
    need("asset_id.to_string()" in loader, "worldgen loader does not return assetId alias")
    exporter = text(EXPORTER_RS)
    need("scene.map.object_asset_ref(object.id)" in exporter, "worldgen exporter ignores canonical object asset refs")
    need("scene_asset_alias_id()" in exporter, "worldgen exporter does not preserve unresolved scene aliases")
    need("canonicalize_world_aliases(&mut world)" in text(BOOTSTRAP_RS), "startup does not canonicalize authored aliases")
    need("canonicalize_world_aliases(&mut world)" in text(RUNTIME_PERSISTENCE_RS), "runtime worldgen reload does not canonicalize aliases")
    need("canonicalize_world_aliases(&mut model.world)" in text(EDITOR_RS), "native editor startup does not canonicalize aliases")
    need("PublishedWorldAssetRegistry" in text(EDITOR_RS), "native editor still names the legacy registry as primary authority")
    need("PublishedWorldAssetRegistry" in text(RUNTIME_ASSETS_RS), "runtime assets still names the legacy registry as primary authority")
    need("PublishedWorldAssetRegistry" in text(MAIN_RS), "game state still names the legacy registry as primary authority")

    rejected_aliases = {"stairs_up", "bench", "signboard", "well_pump", "construction_tape"}
    need(not (rejected_aliases & aliases.keys()), "known rejected/placeholder atlas IDs were promoted as canonical aliases")

    print("PASS W42 PublishedWorldAsset authority + first 29 authored-scene aliases")
    print(json.dumps({
        "publishedRecords": len(entries),
        "publishedAliases": len(aliases),
        "migratedSceneCandidates": len(expected),
        "remainingSceneBlockers": len(blockers),
        "primaryLegacyAdapters": len(primary_kinds),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
