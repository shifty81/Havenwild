#!/usr/bin/env python3
"""Build the R42 Help coverage registry from native editor enum authorities."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "content/editor/help/help_coverage_registry_r42_v1.json"

LAYER_HELP = {
    "Terrain": "TerrainMaterials",
    "TerrainTransitions": "Transitions",
    "Water": "WaterHydrology",
    "RoadsPaths": "RoadsPaths",
    "Vegetation": "Vegetation",
    "Resources": "Resources",
    "Structures": "Structures",
    "Furniture": "FurnitureProps",
    "Props": "FurnitureProps",
    "Characters": "SceneNpcEditing",
    "Triggers": "TriggersInteractions",
    "Lighting": "LightingFx",
    "SoundEmitters": "SoundEmitters",
    "Effects": "LightingFx",
    "Buildings": "Structures",
    "Objects": "FurnitureProps",
    "AuthoredPixels": "WorldPixelMode",
    "Collision": "WorldCollision",
    "Navigation": "WorldCollision",
    "Zones": "SceneLogic",
    "Links": "SceneLogic",
    "Shelter": "Structures",
    "WaterSwim": "WaterHydrology",
    "SpawnPopulation": "WorldNpcSpawns",
    "BuildabilityFarming": "TerrainMaterials",
    "LogicBindings": "SceneLogic",
    "StructuralLevels": "ElevationCliffs",
    "SourceReference": "AssetStatus",
    "AnimationFrames": "FramesCels",
    "AnimationAnchors": "AnchorsSockets",
    "AnimationFootAnchor": "AnchorsSockets",
    "AnimationShadowAnchor": "AnchorsSockets",
    "AnimationSockets": "AnchorsSockets",
    "AnimationHitboxes": "HitboxesHurtboxes",
    "AnimationHurtboxes": "HitboxesHurtboxes",
    "AnimationEvents": "AnimationEvents",
    "CharacterParts": "CharacterLayers",
    "PixelLayer": "PixelLayers",
    "Interaction": "TriggersInteractions",
    "Occlusion": "CharacterOcclusion",
    "LogicNodes": "LogicStudio",
    "LogicConnections": "LogicStudio",
    "SoundNodes": "SoundStudio",
    "SoundConnections": "SoundStudio",
    "SoundTimeline": "SoundStudio",
    "Guides": "Canvas",
}

TOOL_HELP = {
    "Inspect": "ToolRail",
    "Select": "ToolRail",
    "Pan": "Canvas",
    "Paint": "PixelDrawingTools",
    "Erase": "PixelDrawingTools",
    "Fill": "PixelDrawingTools",
    "Replace": "PixelDrawingTools",
    "Pick": "PixelDrawingTools",
    "MagicSelect": "PixelSelectionTransform",
    "Rectangle": "PixelDrawingTools",
    "Ellipse": "PixelDrawingTools",
    "Line": "PixelDrawingTools",
    "Gradient": "PixelDrawingTools",
    "Blur": "PixelDrawingTools",
    "Smudge": "PixelDrawingTools",
    "Lighten": "PixelDrawingTools",
    "Darken": "PixelDrawingTools",
    "Place": "AssetBrowser",
    "Move": "ToolRail",
    "Link": "SceneLogic",
    "Collision": "WorldCollision",
    "PixelEdit": "WorldPixelMode",
    "Anchor": "AnchorsSockets",
    "Socket": "AnchorsSockets",
    "Event": "AnimationEvents",
}

STUDIO_HELP = {
    "RegionGraph": "WorldRoutes",
    "SceneRectangles": "WorldStudio",
    "SceneBank": "SceneBrowser",
    "SceneMap": "SceneStudio",
    "PixelStudio": "PixelAuthoring",
    "AnimationStudio": "AnimationStudio",
    "CharacterStudio": "CharacterStudio",
    "LogicStudio": "LogicStudio",
    "SoundStudio": "SoundStudio",
}

FEATURES = {
    "project_home": "ProjectHome",
    "document_tabs": "DocumentTabs",
    "tool_rail": "ToolRail",
    "layer_rail": "LayerRail",
    "inspector": "Inspector",
    "right_dock": "RightDock",
    "undo_redo": "UndoRedo",
    "validation": "Validation",
    "settings_activity": "SettingsActivity",
    "asset_browser": "AssetBrowser",
    "asset_promotion": "AssetPromotion",
    "batch_promotion": "BatchPromotion",
    "where_used": "WhereUsed",
    "licensing": "Licensing",
    "entire_world_canvas": "EntireWorldCanvas",
    "world_generation": "WorldGeneration",
    "regeneration_scopes": "RegenerationScopes",
    "authored_overrides": "AuthoredOverrides",
    "transition_repair": "TransitionRepair",
    "character_create": "CharacterCreate",
    "wardrobe_gear": "WardrobeGear",
    "equipment_slots": "EquipmentSlots",
    "character_layers": "CharacterLayers",
    "character_occlusion": "CharacterOcclusion",
    "animation_coverage": "AnimationCoverage",
    "npc_generator": "NpcGenerator",
    "npc_profiles": "NpcProfiles",
    "profile_inheritance": "ProfileInheritance",
    "population_generation": "PopulationGeneration",
    "play_testing": "PlayTesting",
    "save_recovery": "SaveRecovery",
    "troubleshooting": "Troubleshooting",
}


def enum_variants(path: Path, enum_name: str) -> list[str]:
    source = path.read_text(encoding="utf-8")
    match = re.search(rf"enum\s+{re.escape(enum_name)}\s*\{{(?P<body>.*?)\n\}}", source, re.S)
    if not match:
        raise SystemExit(f"could not find enum {enum_name} in {path}")
    variants: list[str] = []
    for line in match.group("body").splitlines():
        line = line.split("//", 1)[0].strip()
        found = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s*,?$", line)
        if found:
            variants.append(found.group(1))
    return variants


def mapped_rows(values: list[str], mapping: dict[str, str], kind: str) -> list[dict[str, str]]:
    missing = [value for value in values if value not in mapping]
    extra = sorted(set(mapping) - set(values))
    if missing or extra:
        raise SystemExit(f"{kind} help mapping drift; missing={missing}, extra={extra}")
    return [{"id": value, "helpPage": mapping[value]} for value in values]


def main() -> int:
    layers = enum_variants(ROOT / "apps/haven_editor_native/src/app/canvas_layers.rs", "CanvasLayerKind")
    tools = enum_variants(ROOT / "apps/haven_editor_native/src/app/tool_registry.rs", "UniversalTool")
    studios = enum_variants(ROOT / "apps/haven_editor_native/src/app/editor_types.rs", "EditorViewportMode")
    payload = {
        "schema": "havenwild.editor.help_coverage_registry.r42.v1",
        "pass": "167Z109W81R42",
        "policy": "Every registered Studio, semantic Canvas layer, universal tool and major workflow surface must resolve to searchable Help. New enum variants fail validation until mapped.",
        "studios": mapped_rows(studios, STUDIO_HELP, "studio"),
        "semanticLayers": mapped_rows(layers, LAYER_HELP, "layer"),
        "tools": mapped_rows(tools, TOOL_HELP, "tool"),
        "majorFeatures": [{"id": key, "helpPage": value} for key, value in FEATURES.items()],
        "counts": {
            "studios": len(studios),
            "semanticLayers": len(layers),
            "tools": len(tools),
            "majorFeatures": len(FEATURES),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(payload["counts"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
