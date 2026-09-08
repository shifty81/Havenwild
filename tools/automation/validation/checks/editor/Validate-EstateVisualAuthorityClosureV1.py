#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def text(rel: str) -> str:
    p = ROOT / rel
    if not p.is_file():
        raise SystemExit(f"FAIL W43C Estate visual authority: missing {rel}")
    return p.read_text(encoding="utf-8")


def data(rel: str):
    return json.loads(text(rel))


def need(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(f"FAIL W43C Estate visual authority: {message}")

scene_types = text("crates/haven_core/src/scene_types.rs")
starter = text("crates/haven_core/src/foundation/starter_generation.rs")
atlas_render = text("apps/haven_editor_native/src/app/atlas_render.rs")
region_graph = text("crates/haven_world/src/region_graph.rs")
editor_mod = text("apps/haven_editor_native/src/app/mod.rs")
nav = data("content/worldgen/home_island_navigation_graph_v0_4.json")
island = data("content/worldgen/island_region_graph.json")
fixture = data("content/worldgen/scenes/home_island/farmstead_scene_v0_3.json")
active_world = data("WORKSPACE/development/active_world.json")
live_command = data("WORKSPACE/development/live_command.json")

# User-facing identity changes; compatibility code intentionally does not.
need('SceneId::Farmstead => "Estate"' in scene_types, "legacy scene does not display as Estate")
need('SceneId::Farmstead => "farmstead"' in scene_types, "legacy farmstead scene code was destructively renamed")
need('"farmstead" => Some(SceneId::Farmstead)' in scene_types, "farmstead compatibility alias was removed")
need('label: "Estate".to_string()' in region_graph, "region graph still presents Farmstead")
need("canonical Estate" in editor_mod, "native editor fallback messages still present Farmstead to the user")
need(active_world.get("default_scene") == "farmstead", "development compatibility scene ID changed")
need(live_command.get("command", {}).get("scene_id") == "farmstead", "live development compatibility scene ID changed")

nav_estate = next((n for n in nav.get("nodes", []) if n.get("sceneId") == "farmstead"), None)
need(nav_estate is not None and nav_estate.get("title") == "Estate", "navigation graph does not present Estate")
island_estate = next((n for n in island.get("nodes", []) if n.get("scene_id") == "farmstead"), None)
need(island_estate is not None and island_estate.get("label") == "Estate", "island graph does not present Estate")
need("Estate Terrain Fixture" in fixture.get("title", ""), "quarantined authored fixture still uses Farmstead title")

# The procedural compatibility fixture is allowed temporarily, but it must no
# longer manufacture fake exterior structures from unsupported terrain kinds.
need("fn generate_estate_development_layout" in starter, "Estate compatibility fixture is not explicit")
match = re.search(r"fn generate_estate_development_layout\(&mut self, seed: u32\) \{(?P<body>.*?)\n    \}\n\n    pub\(super\) fn generate_tavern_interior", starter, re.S)
need(match is not None, "could not inspect Estate development layout")
body = match.group("body")
for forbidden in (
    "TileKind::Wall",
    "TileKind::WoodFloor",
    "TileKind::GreenhouseZone",
    "ObjectKind::GreenhouseMarker",
    "ObjectKind::Door",
    "ObjectKind::CaveEntrance",
):
    need(forbidden not in body, f"Estate fixture still emits legacy structure placeholder {forbidden}")
need("TileKind::Road" in body and "TileKind::TilledSoil" in body, "Estate fixture lost safe terrain development content")
need("TileKind::DeepWater" in body and "TileKind::ShallowWater" in body, "Estate fixture lost semantic creek")

# The blue/cyan H/L/T blocks in the screenshot were the generated live-autotile
# cache leaking into ordinary Scene Editor presentation. Keep that atlas as
# diagnostics infrastructure only; normal Scene Editor base drawing must not use it.
need("live_autotile_atlas_entry" not in atlas_render, "native editor still renders live autotile atlas as replacement art")
need("LIVE_AUTOTILE_ATLAS_PATH" not in atlas_render, "native editor still loads live autotile atlas as production base art")
need("W43C fail-closed production rule" in atlas_render, "fail-closed presentation rule is not documented in code")

print("PASS W43C Estate visual authority closure")
print("- user-facing Farmstead is normalized to Estate while scene code farmstead remains compatible")
print("- legacy Estate fixture no longer paints exterior Wall/WoodFloor/Greenhouse placeholders")
print("- native Scene Editor no longer displays live_autotile_16_32 as production fallback artwork")
