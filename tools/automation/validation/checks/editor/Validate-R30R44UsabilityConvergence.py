#!/usr/bin/env python3
"""Validate Havenwild W81R30-R44 asset/character/world/help/NPC usability convergence."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def text(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        raise AssertionError(f"missing R30-R44 file: {rel}")
    return path.read_text(encoding="utf-8")


def data(rel: str):
    return json.loads(text(rel))


def require(source: str, tokens: list[str], label: str) -> None:
    for token in tokens:
        if token not in source:
            raise AssertionError(f"{label} missing {token!r}")


def enum_variants(source: str, enum_name: str) -> list[str]:
    match = re.search(rf"enum\s+{re.escape(enum_name)}\s*\{{(?P<body>.*?)\n\}}", source, re.S)
    if not match:
        raise AssertionError(f"missing enum {enum_name}")
    out: list[str] = []
    for line in match.group("body").splitlines():
        line = line.split("//", 1)[0].strip()
        found = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s*,?$", line)
        if found:
            out.append(found.group(1))
    return out


def validate_contracts() -> dict[str, int]:
    paths = {
        "r30": "content/editor/assets/asset_promotion_authority_r30_v1.json",
        "r30queue": "content/editor/assets/lpc_promotion_queue_r30_v1.json",
        "r31": "content/editor/character/character_layers_equipment_r31_v1.json",
        "r32": "content/editor/character/character_animation_coverage_r32_v1.json",
        "r32summary": "content/editor/character/character_animation_coverage_summary_r32_v1.json",
        "r33": "content/editor/assets/gameplay_pack_promotion_r33_v1.json",
        "r33inventory": "content/editor/assets/lpc_gameplay_pack_inventory_r33_v1.json",
        "r34": "content/editor/canvas/semantic_layer_authority_r34_v1.json",
        "r35": "content/editor/canvas/layer_context_sync_r35_v1.json",
        "r36": "content/editor/world/real_world_document_authority_r36_v1.json",
        "r37": "content/editor/world/entire_world_lod_canvas_r37_v1.json",
        "r38": "content/editor/world/production_world_generator_r38_v1.json",
        "r39": "content/editor/world/world_pixel_workflow_r39_v1.json",
        "r40": "content/editor/world/transition_authoring_r40_v1.json",
        "r41": "content/editor/world/world_scene_convergence_r41_v1.json",
        "r42": "content/editor/help/help_center_wiki_r42_v1.json",
        "r42coverage": "content/editor/help/help_coverage_registry_r42_v1.json",
        "r43": "content/characters/npc_generation_profiles_r43_v1.json",
        "r44": "content/characters/npc_generation_constraints_r44_v1.json",
        "r44authoring": "content/characters/npc_profile_authoring_r44_v1.json",
    }
    contracts = {key: data(path) for key, path in paths.items()}
    expected = {
        "r30": "havenwild.editor.asset_promotion_authority.r30.v1",
        "r31": "havenwild.editor.character_layers_equipment.r31.v1",
        "r32": "havenwild.editor.character_animation_coverage.r32.v1",
        "r33": "havenwild.editor.gameplay_pack_promotion.r33.v1",
        "r34": "havenwild.editor.semantic_layer_authority.r34.v1",
        "r35": "havenwild.editor.layer_context_sync.r35.v1",
        "r36": "havenwild.editor.real_world_document_authority.r36.v1",
        "r37": "havenwild.editor.entire_world_lod_canvas.r37.v1",
        "r38": "havenwild.editor.production_world_generator.r38.v1",
        "r39": "havenwild.editor.world_pixel_workflow.r39.v1",
        "r40": "havenwild.editor.transition_authoring.r40.v1",
        "r41": "havenwild.editor.world_scene_convergence.r41.v1",
        "r42": "havenwild.editor.help_center_wiki.r42.v1",
        "r42coverage": "havenwild.editor.help_coverage_registry.r42.v1",
        "r43": "havenwild.characters.npc_generation_profiles.r43.v1",
        "r44": "havenwild.characters.npc_generation_constraints.r44.v1",
        "r44authoring": "havenwild.characters.npc_profile_authoring.r44.v1",
    }
    for key, schema in expected.items():
        assert contracts[key].get("schema") == schema, (key, contracts[key].get("schema"))

    queue = contracts["r30queue"]
    queued_family_sources = sum(int(row.get("sourceCount", 0)) for row in queue.get("families", []))
    assert queue.get("entryCount", 0) >= 320
    assert queued_family_sources == queue.get("entryCount"), (queued_family_sources, queue.get("entryCount"))
    summary = contracts["r32summary"]
    assert summary.get("familyCount", 0) >= 2000
    assert summary.get("walkWithoutRunFamilyCount", 0) >= 1
    inventory = contracts["r33inventory"]
    gameplay_assets = sum(int(row.get("sourceCount", 0)) for row in inventory.get("loops", []))
    assert gameplay_assets > 300
    assert contracts["r42"].get("articleCount") == 78
    counts = contracts["r42coverage"].get("counts", {})
    assert counts.get("studios") == 9
    assert counts.get("semanticLayers") == 46
    assert counts.get("tools") == 25
    return {
        "promotion": queue["entryCount"],
        "coverage_families": summary["familyCount"],
        "walk_without_run": summary["walkWithoutRunFamilyCount"],
        "gameplay_assets": gameplay_assets,
        "help_articles": contracts["r42"]["articleCount"],
    }


def validate_character() -> None:
    core = text("apps/haven_editor_native/src/app/character_studio.rs")
    ext = text("apps/haven_editor_native/src/app/character_studio_runtime_ext.rs")
    resolver = text("crates/haven_assets/src/universal_lpc_resolver.rs")
    presentation = text("crates/haven_assets/src/universal_lpc_character_presentation.rs")
    npc = text("crates/haven_assets/src/universal_lpc_npc_generation.rs")

    require(core, [
        "character_studio_runtime_ext.rs",
        "presentation_issues",
        "preview_hidden_items",
        "draw_npc_profile_controls(c)",
        "draw_npc_profile_rule_editor(c)",
    ], "Character Studio")
    require(ext, [
        "CharacterLayerViewMode",
        "EquipmentSlots",
        "semantic_layer_rows",
        "toggle_semantic_layer_preview",
        "current_action_available",
        "npc_profile_detail_lines",
        "toggle_npc_profile_editor",
        "adjust_npc_profile_minimum",
        "adjust_npc_profile_maximum",
        "adjust_npc_profile_weight",
        "save_npc_profile_variant",
        "NPC PROFILE RULES · derived variant",
        "character_catalog_thumbnail_key",
    ], "Character Studio runtime extension")
    require(presentation, [
        "resolve_character_presentation",
        "HeadwearOcclusionProfile",
        "two-handed main-hand equipment conflicts",
        "hair remains equipped",
    ], "Character presentation resolver")
    require(resolver, ["presentation_issues", "hidden_item_ids"], "ULPC resolver")
    require(npc, [
        "resolved_profile",
        "NPC profile inheritance cycle detected",
        "plan_population_for_context",
        "UniversalLpcNpcPopulationContext::willowmere",
        "required_animations",
        "save_profile_variant_default",
        "ULPC_NPC_PROFILE_VARIANT_SCHEMA",
    ], "NPC generator")


def validate_world_scene_layers() -> None:
    layers = text("apps/haven_editor_native/src/app/canvas_layers.rs")
    tools = text("apps/haven_editor_native/src/app/tool_registry.rs")
    controller = text("apps/haven_editor_native/src/app/canvas_controller.rs")
    scene_bank = text("apps/haven_editor_native/src/app/scene_bank_workspace.rs")
    production = text("crates/haven_world/src/production_world_generation.rs")
    creation = text("crates/haven_world/src/world_creation.rs")
    skeleton = text("crates/haven_world/src/archipelago_skeleton.rs")

    require(layers, [
        '"Terrain Materials"',
        '"Derived Transitions"',
        '"Vegetation"',
        '"Resources"',
        '"Structures"',
        '"NPC / Spawn"',
        '"Collision"',
        "canvas_layer_context_override",
    ], "semantic Layers")
    require(tools, ["tool_is_applicable", "CanvasLayerKind", "PixelEdit"], "Tool Rail")
    require(controller, ["world_scene_grid_bounds_all", "world_show_entire_world"], "complete World canvas")
    require(scene_bank, [
        "Scene Browser",
        "Locate in World",
        "Validate References",
        "scene_reference_integrity_summary",
        "scene_stable_region_summary",
        "legacy_scene_rectangle_region_key",
    ], "Scene Browser")
    require(production, [
        "HAVENWILD_MAJOR_LANDMASS_MIN: u8 = 3",
        "HAVENWILD_MAJOR_LANDMASS_MAX: u8 = 15",
        "ocean_on_all_outer_boundaries",
        "willowmere_generated_first",
        "ProductionRegenerationScope",
        "ProductionWorldRegionKey",
        "authored_override_replay",
    ], "production world generation")
    require(creation, ["validate_havenwild_production"], "world creation production validation")
    require(skeleton, ["major_landmass_count.clamp(3, 15)", "requires 3-15 total major landmasses"], "archipelago skeleton")


def validate_help_coverage() -> None:
    help_source = text("apps/haven_editor_native/src/app/editor_help.rs")
    layer_source = text("apps/haven_editor_native/src/app/canvas_layers.rs")
    tool_source = text("apps/haven_editor_native/src/app/tool_registry.rs")
    viewport_source = text("apps/haven_editor_native/src/app/editor_types.rs")
    coverage = data("content/editor/help/help_coverage_registry_r42_v1.json")

    require(help_source, [
        "const HELP_ARTICLES: [HelpArticle; 78]",
        "const ALL: [Self; 78]",
        "Havenwild Editor Help / Wiki",
        "Manual Index",
        "contextual_help_page",
        "filtered_help_pages",
    ], "Help Center")
    layers = enum_variants(layer_source, "CanvasLayerKind")
    tools = enum_variants(tool_source, "UniversalTool")
    studios = enum_variants(viewport_source, "EditorViewportMode")
    assert {row["id"] for row in coverage["semanticLayers"]} == set(layers)
    assert {row["id"] for row in coverage["tools"]} == set(tools)
    assert {row["id"] for row in coverage["studios"]} == set(studios)
    help_pages = set(enum_variants(help_source, "HelpPage"))
    for group in ("semanticLayers", "tools", "studios", "majorFeatures"):
        for row in coverage[group]:
            assert row["helpPage"] in help_pages, (group, row)


def validate_handoff() -> None:
    handoff = text("docs/current/HAVENWILD_W81R30_R44_USABILITY_CONVERGENCE.md")
    require(handoff, [
        "320 source references",
        "2,315 relevant ULPC families",
        "78 searchable articles",
        "3-15 total major landmasses",
        "Compatibility boundary",
        "Windows Full Quality Gate",
    ], "R30-R44 handoff")


def validate_registry() -> None:
    registry = data("content/build/validator_registry_v3.json")
    matches = [entry for entry in registry.get("validators", []) if entry.get("id") == "editor.r30-r44-usability-convergence"]
    assert len(matches) == 1, "R30-R44 validator must be registered exactly once"
    entry = matches[0]
    assert "source" in entry.get("profiles", []) and "full" in entry.get("profiles", [])
    assert entry.get("read_only") is True


def main() -> int:
    metrics = validate_contracts()
    validate_character()
    validate_world_scene_layers()
    validate_help_coverage()
    validate_handoff()
    validate_registry()
    print("PASS: W81R30-R44 Havenwild usability convergence")
    print(f"- LPC promotion candidates: {metrics['promotion']}")
    print(f"- Character source families audited: {metrics['coverage_families']} ({metrics['walk_without_run']} Walk-without-Run)")
    print(f"- Gameplay-oriented LPC entries: {metrics['gameplay_assets']}")
    print(f"- Built-in Help/Wiki articles: {metrics['help_articles']}")
    print("- Character Layers, profile variants, semantic World/Scene Layers, complete-world identity, Scene references and Help coverage are guarded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
