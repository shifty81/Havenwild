#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL {message}")


def main() -> None:
    authority = load("content/worldgen/unified_terrain_world_lane_authority_v0_1.json")
    sources = load("content/assets/oga_lpc/manifests/oga_lpc_prototype_source_registry_v0_1.json")
    roles = load("content/assets/oga_lpc/manifests/oga_lpc_prototype_role_registry_v0_1.json")
    gameplay = load("content/assets/oga_lpc/manifests/oga_lpc_gameplay_intake_v0_2.json")
    commercial = load("content/assets/oga_lpc/manifests/oga_lpc_commercial_intake_v0_1.json")
    queue = load("content/assets/oga_lpc/manifests/oga_lpc_audit_queue_v0_1.json")
    pack = load("content/asset_packs/oga_lpc_prototypes/pack.json")
    external = load("content/assets/external_sources/external_asset_sources_v0_1.json")
    binding = load("content/gameplay/lpc_bindings/oga_lpc_gameplay_binding_contract_v0_1.json")

    require(authority.get("revision", "").startswith("167Z109"), "unified terrain authority revision")
    require(authority.get("tileSize") == 32, "unified terrain authority must keep 32px tile scale")
    for invariant in (
        "ordinary structural authoring is discrete Level 0/2/3/4; Level 1 is reserved for certified 2→1→0 ramp transition cells; no freeform numeric elevation painting",
        "canonical semantics and topology are resolved before visual providers",
        "details may decorate a host recipe but may not silently alter host topology",
    ):
        require(invariant in authority.get("invariants", []), f"missing invariant: {invariant}")

    expected_seed_domains = {"geography", "geology", "climate", "hydrology", "structure", "settlement", "road", "cave", "ecology", "tree_stands", "forage", "resource", "detail", "landmark", "wildlife"}
    require(expected_seed_domains.issubset(set(authority.get("seedDomains", []))), "domain-separated seed coverage incomplete")
    require(authority.get("structural", {}).get("levels") == [0, 2, 3, 4], "ordinary structural authoring levels changed")
    require(authority.get("structural", {}).get("reservedTransitionLevels", {}).get("1") is not None, "Level 1 ramp-only reservation missing")
    require(authority.get("caves", {}).get("graphFirst") is True, "cave graph must precede local geometry")
    require(authority.get("settlements", {}).get("willowmere", {}).get("alwaysPresent") is True, "Willowmere permanent-capital rule missing")
    require(authority.get("settlements", {}).get("willowmere", {}).get("authoredCoreInvariant") is True, "Willowmere authored core must remain invariant")
    require("waterfall_without_downstream_water" in authority.get("validationFailures", []), "waterfall validation coverage missing")
    require("season_geometry_mismatch" in authority.get("validationFailures", []), "season provider geometry validation missing")

    source_records = sources.get("sources", [])
    source_ids = {entry.get("id") for entry in source_records}
    require(len(source_records) >= 18, "prototype source registry is unexpectedly small")
    for source_id in ("elizawy.4_season_terrain", "oga.lpc.caves", "oga.lpc.cave_openings", "oga.lpc.mine", "oga.lpc.farm", "oga.lpc.animated_water", "oga.lpc.trees", "oga.lpc.city_outside", "oga.lpc.dock"):
        require(source_id in source_ids, f"missing prototype source {source_id}")
    require(any(e.get("id") == "oga.lpc.caves" and e.get("selectedLicense") == "CC0-1.0" for e in source_records), "CC0 cave intake not recorded")
    require(any(e.get("id") == "oga.lpc.mine" and e.get("selectedLicense") == "CC-BY-4.0" for e in source_records), "mine intake license not recorded")

    expected_role_domains = {"terrain.surface", "terrain.details", "structural.cliffs", "hydrology", "shoreline", "caves", "ecology", "farming", "routes", "settlements"}
    require(expected_role_domains.issubset(set(roles.get("domains", {}).keys())), "prototype role-domain coverage incomplete")
    require(roles.get("providerContract", {}).get("seasonSwapChangesTopology") is False, "season swap must not change topology")
    require(roles.get("providerContract", {}).get("seasonSwapChangesCollision") is False, "season swap must not change collision")

    require(gameplay.get("revision") == "167Z109M", "gameplay intake not restored/advanced")
    require(len(gameplay.get("entries", [])) >= 17, "gameplay intake entries incomplete")
    require(commercial.get("revision") == "167Z109M", "commercial intake not restored/advanced")
    require(queue.get("revision") == "167Z109M", "OGA/LPC audit queue not restored/advanced")
    require(binding.get("revision") == "167Z109M", "gameplay binding contract not unified")
    for domain in ("terrain_surface", "structural_cliffs", "hydrology", "caves", "trees", "forage", "settlements"):
        require(domain in binding.get("domains", {}), f"binding contract missing {domain}")

    require(pack.get("production_enabled") is False, "prototype pack must stay authoring-only")
    require(pack.get("authority") == "content/worldgen/unified_terrain_world_lane_authority_v0_1.json", "prototype pack authority mismatch")
    require(any(e.get("id") == "third_party.oga_lpc.curated_prototype_lane" for e in external.get("sources", [])), "external-source registry missing curated OGA/LPC lane")

    acquire = (ROOT / "tools/automation/assets/Acquire-OgaLpcGameplayBatchV167S.py").read_text(encoding="utf-8")
    require("oga_lpc_prototype_source_registry_v0_1.json" in acquire, "acquire tool does not consume canonical source registry")
    require("assets/source/licensed/oga_lpc_prototypes" in acquire, "acquire tool does not use excluded licensed-source mount")
    require("runtimePromoted\": False" in acquire, "acquire tool must not auto-promote runtime assets")

    build_sh = (ROOT / "tools/build/Build.sh").read_text(encoding="utf-8")
    build_ps1 = (ROOT / "tools/build/Build.ps1").read_text(encoding="utf-8")
    for text, label in ((build_sh, "Build.sh"), (build_ps1, "Build.ps1")):
        require("Acquire-OgaLpcGameplayBatchV167S.py" in text, f"{label} does not sync OGA/LPC prototypes")
        require("oga-prototypes" in text, f"{label} lacks focused OGA/LPC command")

    diagnostics = (ROOT / "crates/haven_game/src/runtime_diagnostics.rs").read_text(encoding="utf-8")
    require(any(marker in diagnostics for marker in ("Pass 167Z109M", "Pass 167Z109N", "Pass 167Z109O", "Pass 167Z109P", "Pass 167Z109W15B")), "runtime diagnostics marker not advanced")

    for rel in (
        "content/assets/oga_lpc/manifests/oga_lpc_farm_animals_runtime_catalog_v0_1.json",
        "content/gameplay/livestock/livestock_species_v0_1.json",
        "docs/archive/pass_history/PASS167Z109M_UNIFIED_TERRAIN_WORLD_LANE_OGA_LPC_PROTOTYPE_INTAKE.md",
        "manifests/patches/Pass167Z109M-unified-terrain-world-lane-oga-lpc-prototype-intake.json",
    ):
        require((ROOT / rel).is_file(), f"missing restored/pass file {rel}")

    print("Pass167Z109M unified terrain/world lane validation passed")
    print(f"  prototype source records: {len(source_records)}")
    print(f"  provider role domains: {len(roles.get('domains', {}))}")
    print("  OGA/LPC source sync tooling wired into asset-sources")
    print("  terrain/hydrology/cave/ecology/settlement authority is unified and provider-neutral")


if __name__ == "__main__":
    main()
