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
    require(domain["revision"].startswith("167Z109T"), "master domain registry is not T authority")
    require(domain["policy"]["domainCount"] == 7, "normalization must stay at seven foundations")
    require(domain["policy"]["noFeatureSpecificFrameworks"] is True, "scope guard regressed")
    world = next(item for item in domain["domains"] if item["id"] == "world")
    require("world_plan" in world["owns"], "world domain no longer owns WorldPlan")

    bridge = load("content/architecture/world_plan_compatibility_bridge_v0_1.json")
    require(bridge["revision"].startswith("167Z109T"), "WorldPlan bridge contract is not T authority")
    require(bridge["behaviorPreserving"] is True, "T must remain a visual-parity pass")
    require(bridge["authority"]["planType"] == "haven_world::SurfaceWorldPlanV1", "wrong WorldPlan authority")
    require(bridge["authority"]["materializationMode"] == "LegacyVisualParity", "T may not switch visible materializers")
    target = bridge["mainlandTargetCarriedByPlan"]
    require(target["primaryCities"] == ["WesternHarborCapital", "MountainCity", "SouthernSandyCity"], "three-city target drifted")
    require(target["tradeTriangleRequired"] is True, "trade triangle target missing")
    require(target["materializedInThisPass"] is False, "T must not silently replace mainland visuals")

    lib = text("crates/haven_world/src/lib.rs")
    plan = text("crates/haven_world/src/surface_world_plan.rs")
    require("pub mod surface_world_plan;" in lib, "surface WorldPlan module is not exported")
    for token in [
        "pub struct SurfaceWorldPlanV1",
        "pub struct SurfaceWorldBounds",
        "LegacyVisualParity",
        "pub fn materialize_mainland_world_plan_compatibility",
        "target_mainland: Option<MainlandPlanV1>",
        "MainlandCityRole::WesternHarborCapital",
        "MainlandCityRole::MountainCity",
        "MainlandCityRole::SouthernSandyCity",
        "compatibility_landmass_seed",
    ]:
        require(token in plan, f"WorldPlan bridge token missing: {token}")
    require(len(plan.splitlines()) <= 500, "WorldPlan bridge became oversized")

    island = text("crates/haven_world/src/island_pcg.rs")
    require("SurfaceWorldPlanV1::build(" in island, "fresh PCG does not construct WorldPlan before materialization")
    require("materialize_mainland_world_plan_compatibility(" in island, "fresh mainland bypasses WorldPlan materialization bridge")
    require("world_plan.compatibility_landmass_seed()" in island, "structural/ecology compatibility seed is not plan-owned")
    require("pub world_plan: SurfaceWorldPlanV1" in island, "GeneratedIsland does not expose its WorldPlan")
    require("apply_mainland_surface_features" not in island, "fresh PCG still calls mainland feature implementation directly")

    migration = text("crates/haven_world/src/surface_population.rs")
    require("SurfaceWorldPlanV1::build(" in migration, "existing-save mainland migration bypasses WorldPlan")
    require("materialize_mainland_world_plan_compatibility(" in migration, "existing-save mainland migration bypasses plan materializer")
    require("apply_mainland_surface_features" not in migration, "save migration still reaches directly into mainland implementation")

    # Previous parity foundations remain present; T is a bridge, not a rewrite.
    terrain_bridge = load("content/architecture/world_terrain_authority_bridge_v0_1.json")
    canvas_bridge = load("content/architecture/native_canvas_authoring_authority_v0_1.json")
    require(terrain_bridge["revision"].startswith("167Z109R"), "R terrain authority unexpectedly changed")
    require(canvas_bridge["revision"].startswith("167Z109S"), "S canvas authority unexpectedly changed")

    registry = load("content/build/validator_registry_v3.json")
    source = [entry for entry in registry["validators"] if "source" in entry.get("profiles", [])]
    require(len(source) == 10, f"source validation profile must remain 10 current-authority checks, got {len(source)}")
    current_ids = {entry["id"] for entry in source}
    require("architecture.world-plan-compatibility-v167z109t" in current_ids, "T validator is not current source authority")
    require("architecture.native-canvas-authoring-v167z109s" not in current_ids, "S validator should move to historical/full certification")

    handoff = text("docs/current/CURRENT_SOURCE_HANDOFF.md")
    require("Pass167Z109T" in handoff, "current source handoff not advanced to T")
    roadmap = text("docs/current/ROADMAP.md")
    require("T — WorldPlan compatibility bridge**: current pass" in roadmap, "roadmap does not mark T current")

    diagnostic = text("crates/haven_game/src/runtime_diagnostics.rs")
    require("Pass 167Z109T" in diagnostic or "Pass 167Z109U" in diagnostic, "runtime diagnostic checkpoint predates T")

    print("Pass167Z109T WorldPlan compatibility bridge validated")
    print("- current PCG builds one SurfaceWorldPlanV1 before materialization")
    print("- fresh and migrated mainland features route through the same plan bridge")
    print("- existing surface/structural/ecology seed expressions remain parity-compatible")
    print("- target mainland carries three cities/trade/massif requirements without changing visuals")
    print("- R terrain and S canvas authorities remain intact")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Pass167Z109T validation FAILED: {exc}")
        raise SystemExit(1)
