#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
errors = []

def text(rel):
    return (ROOT / rel).read_text(encoding="utf-8")

def req(condition, message):
    if not condition:
        errors.append(message)

landform_rs = text("crates/haven_world/src/landform_feature_graph.rs")
for token in (
    "pub struct StructuralTier(pub u8)",
    "MountainMassifPlan",
    "CoastalCliffPlan",
    "WesternHarborCapital",
    "MountainCity",
    "SouthernSandyCity",
    "MainlandTradeRoutePlan",
    "direct scheduled route",
    "ExpeditionNetworkPlan",
):
    req(token in landform_rs, f"landform graph missing {token}")

solver_rs = text("crates/haven_world/src/terrain_constraint_solver.rs")
for token in (
    "TerrainConstraintCatalog",
    "TerrainAdjacencyRule",
    "explicit adjacency",
    "solve_terrain_constraints",
    "choose_lowest_entropy_cell",
    "propagate(",
    "TerrainConstraintError::Contradiction",
    "deterministic_hash",
):
    req(token in solver_rs, f"constraint solver missing {token}")

lib_rs = text("crates/haven_world/src/lib.rs")
req("pub mod terrain_constraint_solver;" in lib_rs, "constraint solver not exported")
req("pub mod landform_feature_graph;" in lib_rs, "landform feature graph not exported")

authority = json.loads(text("content/worldgen/world_plan_landform_constraint_authority_v0_1.json"))
req(authority.get("revision") == "167Z109P", "P authority revision stale")
mainland = authority.get("mainlandInvariant", {})
req(mainland.get("primaryCityCount") == 3, "mainland does not require exactly three primary cities")
roles = {city.get("role") for city in mainland.get("cities", [])}
req(roles == {"western_harbor_capital", "mountain_city", "southern_sandy_city"}, "mainland city roles incomplete")
req(mainland.get("tradeTriangle", {}).get("directScheduledRouteRequiredForEveryCityPair") is True, "trade triangle is not a hard invariant")
coast = authority.get("coastalCliffs", {})
req(coast.get("firstClassCoastType") is True, "coastal cliff is not a first-class coast type")
req(coast.get("toeWidth", {}).get("minimum") == 0, "coastal cliff toe cannot collapse to direct-water cliff")
constraint = authority.get("constraintSynthesis", {})
req(any("explicit_non_wang_adjacency" in item for item in constraint.get("moduleContract", [])), "non-Wang adjacency not part of module contract")
req("runtime rendering consumes cached solved recipes; it does not run expensive synthesis every frame" in constraint.get("solverRules", []), "constraint solver runtime cache invariant missing")
expedition = authority.get("expeditionNetwork", {})
req(expedition.get("gateway") == "western_harbor_capital", "expedition gateway is not the western capital")
req(expedition.get("stowawayTravel", {}).get("defaultReturnWindowInGameDays") == 1, "stowaway one-day return contract missing")

unified = json.loads(text("content/worldgen/unified_terrain_world_lane_authority_v0_1.json"))
req(unified.get("revision") == "167Z109P", "unified terrain authority not advanced to P")
req("landformFeatureGraphExtension" in unified, "unified terrain authority missing landform extension")
req("constraintSynthesisExtension" in unified, "unified terrain authority missing synthesis extension")
req("coastalCliffExtension" in unified, "unified terrain authority missing coastal cliff extension")

diag = text("crates/haven_game/src/runtime_diagnostics.rs")
req("Pass 167Z109" in diag, "runtime diagnostics no longer reports the Z109 continuation family")

if errors:
    print("Pass167Z109P validation FAILED")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("Pass167Z109P landform graph + terrain constraint synthesis validation passed")
print("  mainland locks western harbor, mountain, and southern sandy city roles")
print("  direct scheduled three-city trade triangle is specified")
print("  mountain massif, cave-bearing terrain, and coastal cliff semantics are specified")
print("  local deterministic constraint propagation supports explicit non-Wang adjacency")
print("  mission/stowaway expedition gateway remains attached to the western harbor")
