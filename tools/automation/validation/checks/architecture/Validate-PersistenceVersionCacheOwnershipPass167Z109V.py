#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def main() -> int:
    domain = load("content/architecture/master_domain_registry_v0_1.json")
    require(domain["revision"].startswith("167Z109V"), "master domain registry is not V authority")
    require(domain["policy"]["domainCount"] == 7, "normalization must stay at seven foundations")
    require(domain["policy"]["noFeatureSpecificFrameworks"] is True, "scope guard regressed")
    persistence = next(item for item in domain["domains"] if item["id"] == "persistence")
    for token in [
        "persistent_entity_identity_boundary",
        "typed_domain_deltas",
        "cache_persistence_policy",
    ]:
        require(token in persistence["owns"], f"persistence domain missing V ownership: {token}")

    authority = load("content/architecture/persistence_version_cache_authority_v0_1.json")
    require(authority["revision"].startswith("167Z109V"), "V persistence authority revision missing")
    require(authority["behaviorPreserving"] is True, "V must remain a parity pass")
    require(authority["authority"]["persistentEntityIdType"] == "haven_core::PersistentEntityId", "wrong durable identity authority")
    require(authority["authority"]["runtimeEntityIdType"] == "haven_ecs::EntityId", "wrong runtime identity authority")
    require(authority["identityBoundary"]["runtimeEntityIdsAreNeverSaveAuthority"] is True, "ECS handles may not become save authority")
    require(authority["versionBoundary"]["existingSaveSchemasUnchanged"] is True, "V may not force a save schema migration")
    require(authority["typedDeltaBoundary"]["opaqueEcsComponentSerializationForbidden"] is True, "opaque ECS serialization guard missing")
    require(authority["cacheRules"]["cacheNeverOwnsGameplayTruth"] is True, "cache authority guard missing")

    core = text("crates/haven_core/src/persistent_identity.rs")
    core_lib = text("crates/haven_core/src/lib.rs")
    require("pub struct PersistentEntityId(pub String);" in core, "PersistentEntityId type missing")
    require("#[serde(transparent)]" in core, "PersistentEntityId must preserve string wire shape")
    require("pub use persistent_identity::*;" in core_lib, "persistent identity is not exported")

    ecs_manifest = text("crates/haven_ecs/Cargo.toml")
    require("serde" not in ecs_manifest, "runtime ECS crate must not gain serialization authority")
    ecs = text("crates/haven_ecs/src/lib.rs")
    require("pub struct EntityId" in ecs, "runtime EntityId missing")
    require("Serialize" not in ecs and "Deserialize" not in ecs, "EntityId must remain non-serializable")

    character = text("crates/haven_sim/src/character_runtime.rs")
    require("pub stable_id: PersistentEntityId" in character, "runtime identity still uses untyped durable ID")
    require("PersistentEntityId::from_domain_id" in character, "runtime identity does not bridge domain ID explicitly")

    save_lib = text("crates/haven_save/src/lib.rs")
    contract = text("crates/haven_save/src/persistence_contract.rs")
    require("pub mod persistence_contract;" in save_lib, "persistence contract is not exported")
    for token in [
        "pub struct DomainVersion(pub u32);",
        "pub struct PersistenceDomainVersions",
        "from_legacy_generation_version",
        "TerrainOverrideDelta",
        "TerrainPlayerDelta",
        "NpcStateDelta",
    ]:
        require(token in contract, f"typed persistence token missing: {token}")
    require(save_lib.count("pub fn domain_versions(&self) -> PersistenceDomainVersions") == 2, "legacy and dynamic world metadata do not expose the same domain-version view")

    chunk = text("crates/haven_save/src/chunk_persistence.rs")
    for token in [
        "pub generator_version: DomainVersion",
        "pub terrain_overrides: Vec<TerrainOverrideDelta>",
        "pub terrain_deltas: Vec<TerrainPlayerDelta>",
        "pub npc_state: Vec<NpcStateDelta>",
    ]:
        require(token in chunk, f"chunk persistence still has untyped ownership: {token}")
    require(not (ROOT / "crates/haven_save/src/foundation_persistence.rs").exists(), "retired duplicate persistence source still exists")

    cache = text("crates/haven_game/src/runtime_cache_contract.rs")
    for token in [
        "base_terrain_chunk_cache",
        "visible_terrain_plan_cache",
        "terrain_scene_surface_cache",
        "chunk_surface_descriptor_cache",
        "scene_backdrop_height_cache",
        "stable_asset_source_cache",
        "stable_texture_cache",
        "world_paint_render_cache",
        "RebuildableSaveSidecar",
    ]:
        require(token in cache, f"retained-cache ownership token missing: {token}")
    bootstrap = text("crates/haven_game/src/game_bootstrap.rs")
    require("runtime_cache_ownership_summary" in bootstrap, "runtime cache ownership is not surfaced at startup")

    # V is a bridge over U/T/R/S, not a gameplay rewrite.
    runtime_authority = load("content/architecture/runtime_character_ecs_authority_v0_1.json")
    world_plan = load("content/architecture/world_plan_compatibility_bridge_v0_1.json")
    terrain = load("content/architecture/world_terrain_authority_bridge_v0_1.json")
    canvas = load("content/architecture/native_canvas_authoring_authority_v0_1.json")
    require(runtime_authority["revision"].startswith("167Z109U"), "U runtime authority unexpectedly changed")
    require(world_plan["revision"].startswith("167Z109T"), "T WorldPlan authority unexpectedly changed")
    require(terrain["revision"].startswith("167Z109R"), "R terrain authority unexpectedly changed")
    require(canvas["revision"].startswith("167Z109S"), "S canvas authority unexpectedly changed")

    registry = load("content/build/validator_registry_v3.json")
    source = [entry for entry in registry["validators"] if "source" in entry.get("profiles", [])]
    require(len(source) == 10, f"source validation profile must remain 10 current-authority checks, got {len(source)}")
    current_ids = {entry["id"] for entry in source}
    require(
        "architecture.persistence-version-cache-v167z109v" in current_ids
        or "worldgen.cliff-contour-turns-v167z109w1" in current_ids,
        "source authority must be V or a later checkpoint layered over V",
    )
    require("architecture.runtime-character-ecs-v167z109u" not in current_ids, "U validator should move to historical/full certification")

    handoff = text("docs/current/CURRENT_SOURCE_HANDOFF.md")
    roadmap = text("docs/current/ROADMAP.md")
    require(
        "Pass167Z109V" in handoff or "Pass167Z109W1" in handoff,
        "current source handoff predates the V persistence foundation",
    )
    require("V — Persistence/version/caching normalization**: current pass" in roadmap or "V — Persistence/version/caching normalization**: complete" in roadmap, "roadmap lost V checkpoint")
    diagnostic = text("crates/haven_game/src/runtime_diagnostics.rs")
    require(
        "Pass 167Z109V" in diagnostic or "Pass 167Z109W1" in diagnostic,
        "runtime diagnostic checkpoint predates V",
    )

    print("Pass167Z109V persistence/version/cache ownership validated")
    print("- persistent gameplay IDs are distinct from runtime-local ECS EntityId handles")
    print("- existing save JSON shapes remain compatible while versions/deltas gain typed ownership")
    print("- duplicate inactive save authority is retired")
    print("- retained caches are explicitly transient or rebuildable and never gameplay truth")
    print("- U character, T WorldPlan, R terrain and S canvas parity foundations remain intact")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Pass167Z109V validation FAILED: {exc}")
        raise SystemExit(1)
