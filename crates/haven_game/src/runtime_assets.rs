use std::collections::HashMap;

use haven_assets::{
    asset_pack::AssetCategory,
    asset_registry::{OBJECT_ATLAS_PATH, PROTOTYPE_TERRAIN_ATLAS_PATH},
    autotile::{transition_atlas_texture_path, TERRAIN_AUTOTILE_ATLAS_PATH},
    live_autotile_atlas::LIVE_AUTOTILE_ATLAS_PATH,
    lpc_cliff_ramp_provider::LPC_CLIFF_RAMP_GRASS_SOURCE_PATH,
    lpc_mapped_terrain::{lpc_mapped_terrain_atlas_path, LPC_MAPPED_TERRAIN_ATLAS_PATH},
    placeable_asset_registry::PublishedWorldAssetRegistry,
    runtime_asset_cache::RuntimeAssetSession,
    semantic_resource_bindings::SemanticResourceRegistry,
    stamp_registry::StampRegistry,
};
use haven_save::CharacterId;
use macroquad::prelude::Texture2D;
use serde::Deserialize;

use crate::bridge_render::LPC_WOOD_BRIDGE_SOURCE_PATH;
use crate::character_visual_policy::SOURCE_BACKED_PLAYER_COMPATIBILITY_ID;
use crate::runtime_config::{runtime_asset_path, runtime_root, WORLD_PAINT_TEST_ATLAS_PATH};
use crate::runtime_render_bindings::{RenderTextureRole, StableRenderBindingRegistry};
use haven_render::structural_cliff_visual::{
    ELIZAWY_SUMMER_CLIFF_SOURCE_PATH, ELIZAWY_WATERFALL_SOURCE_PATH,
};
use crate::runtime_texture_cache::StableTextureCache;
use crate::terrain_render::{LPC_SUMMER_TERRAIN_SOURCE_PATH, LPC_TERRAIN_V7_SOURCE_PATH};

const UNIVERSAL_LPC_ITEM_ICON_MANIFEST_PATH: &str =
    "assets/generated/lpc/item_icons/universal_lpc_item_icons_v1.json";

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RuntimeItemIconManifest {
    atlas: String,
    #[serde(default)]
    entries: Vec<RuntimeItemIconEntry>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RuntimeItemIconEntry {
    item_id: String,
    rect: [f32; 4],
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct TerrainTexturePolicy {
    load_authored_tuple_atlas: bool,
    load_generated_same_family_autotile: bool,
}

fn terrain_texture_policy(direct_lpc_sources_ready: bool) -> TerrainTexturePolicy {
    TerrainTexturePolicy {
        // The tuple atlas is a packed projection of authored LPC cells, not
        // substitute artwork. It remains mandatory with or without source mounts.
        load_authored_tuple_atlas: true,
        load_generated_same_family_autotile: !direct_lpc_sources_ready,
    }
}

pub(crate) struct RuntimeAssets {
    pub asset_session: Option<RuntimeAssetSession>,
    pub texture_cache: StableTextureCache,
    pub render_bindings: StableRenderBindingRegistry,
    pub terrain: Option<Texture2D>,
    pub lpc_terrain_source: Option<Texture2D>,
    pub lpc_terrain_v7_source: Option<Texture2D>,
    pub lpc_bridge_source: Option<Texture2D>,
    pub lpc_cliff_source: Option<Texture2D>,
    pub lpc_waterfall_source: Option<Texture2D>,
    pub oga_cliff_source: Option<Texture2D>,
    pub terrain_transition: Option<Texture2D>,
    pub lpc_mapped_terrain: Option<Texture2D>,
    pub live_autotile: Option<Texture2D>,
    pub objects: Option<Texture2D>,
    pub world_tiles: Option<Texture2D>,
    pub player_walk: Option<Texture2D>,
    pub hud_vitals_frame: Option<Texture2D>,
    pub hud_hotbar_frame: Option<Texture2D>,
    pub hud_minimap_frame: Option<Texture2D>,
    pub item_icon_atlas: Option<Texture2D>,
    pub item_icon_rects: HashMap<String, [f32; 4]>,
    pub resource_bindings: SemanticResourceRegistry,
    pub stamp_registry: StampRegistry,
    pub placeable_registry: PublishedWorldAssetRegistry,
    pub stamp_textures: HashMap<String, Texture2D>,
    pub placeable_textures: HashMap<String, Texture2D>,
    pub world_visual_override_textures: HashMap<String, Texture2D>,
    pub character_appearance:
        Option<crate::character_runtime_compositor::RuntimeCharacterAppearance>,
}

impl RuntimeAssets {
    pub(crate) async fn load(character_id: &CharacterId) -> Self {
        let asset_session = match RuntimeAssetSession::discover(runtime_root()) {
            Ok(session) => {
                println!(
                    "Mounted {} production asset packs with {} stable source bindings",
                    session.registry.mounted_pack_count(),
                    session.sources.len()
                );
                Some(session)
            }
            Err(report) => {
                let session = RuntimeAssetSession::discover_tolerant(runtime_root());
                println!(
                    "Asset-pack startup discovery reported {} failure(s); continuing with {} valid production pack(s) and {} stable source binding(s)",
                    report.failed_count(),
                    session.registry.mounted_pack_count(),
                    session.sources.len()
                );
                for record in &report.records {
                    if record.diagnostics.is_empty() {
                        continue;
                    }
                    println!(
                        "Asset-pack diagnostic: {} [{:?}] {}",
                        record.manifest_path,
                        record.status,
                        record.diagnostics.join("; ")
                    );
                }
                Some(session)
            }
        };
        let mut texture_cache = StableTextureCache::default();

        let terrain = texture_cache
            .load_semantic(
                asset_session.as_ref(),
                "terrain.grass",
                AssetCategory::Terrain,
                runtime_asset_path(PROTOTYPE_TERRAIN_ATLAS_PATH),
            )
            .await;

        // Licensed LPC source sheets remain mounted for supplemental families,
        // editor inspection, seasonal assets, cliffs, plants, and object promotion.
        // Exact runtime boundaries are selected from the authored tuple atlas below.
        let lpc_terrain_source = texture_cache
            .load_path(runtime_asset_path(LPC_SUMMER_TERRAIN_SOURCE_PATH))
            .await;
        let lpc_terrain_v7_source = texture_cache
            .load_path(runtime_asset_path(LPC_TERRAIN_V7_SOURCE_PATH))
            .await;
        let lpc_bridge_source = texture_cache
            .load_path(runtime_asset_path(LPC_WOOD_BRIDGE_SOURCE_PATH))
            .await;
        let lpc_cliff_source = texture_cache
            .load_path(runtime_asset_path(ELIZAWY_SUMMER_CLIFF_SOURCE_PATH))
            .await;
        let lpc_waterfall_source = texture_cache
            .load_path(runtime_asset_path(ELIZAWY_WATERFALL_SOURCE_PATH))
            .await;
        // W7 promotes only the two complete authored 3x4 directional ramp
        // stamps from the companion LPC grass-top cliff sheet. The raw sheet is
        // loaded directly; runtime code is restricted to those certified source
        // rectangles and never treats arbitrary cells as placeable assets.
        let oga_cliff_source = texture_cache
            .load_path(runtime_asset_path(LPC_CLIFF_RAMP_GRASS_SOURCE_PATH))
            .await;

        let direct_lpc_sources_ready =
            lpc_terrain_source.is_some() && lpc_terrain_v7_source.is_some();
        let terrain_policy = terrain_texture_policy(direct_lpc_sources_ready);
        let transition_fallback = transition_atlas_texture_path()
            .unwrap_or_else(|error| {
                println!(
                    "Could not load transition atlas manifest, using hardcoded fallback: {error}"
                );
                TERRAIN_AUTOTILE_ATLAS_PATH
            })
            .to_string();
        let terrain_transition = texture_cache
            .load_semantic(
                asset_session.as_ref(),
                "terrain.transition.atlas",
                AssetCategory::Terrain,
                runtime_asset_path(&transition_fallback),
            )
            .await;

        // The mapped terrain atlas is not a replacement-art fallback. It is a
        // packed, exact-cell view of the authored LPC terrain-map-v7 sheets and
        // must remain loaded even when the original licensed source sheets are
        // mounted. The source sheets supply supplemental terrain families and
        // editor inspection; the tuple atlas supplies the reviewed edge, inner-
        // corner, outer-corner, island, hole, and junction cells used at runtime.
        let mapped_fallback = lpc_mapped_terrain_atlas_path()
            .unwrap_or(LPC_MAPPED_TERRAIN_ATLAS_PATH)
            .to_string();
        let lpc_mapped_terrain = if terrain_policy.load_authored_tuple_atlas {
            texture_cache
                .load_semantic(
                    asset_session.as_ref(),
                    "terrain.sand",
                    AssetCategory::Terrain,
                    runtime_asset_path(&mapped_fallback),
                )
                .await
        } else {
            None
        };

        // Same-family generated autotiling is only a compatibility lane when
        // the licensed LPC source sheets are unavailable. It must not displace
        // the exact authored tuple atlas above.
        let live_autotile = if terrain_policy.load_generated_same_family_autotile {
            texture_cache
                .load_semantic(
                    asset_session.as_ref(),
                    "terrain.path.road",
                    AssetCategory::Terrain,
                    runtime_asset_path(LIVE_AUTOTILE_ATLAS_PATH),
                )
                .await
        } else {
            None
        };
        let objects = texture_cache
            .load_semantic(
                asset_session.as_ref(),
                "object.catalog.runtime",
                AssetCategory::TileObject,
                runtime_asset_path(OBJECT_ATLAS_PATH),
            )
            .await;
        let world_paint_path = runtime_root().join(WORLD_PAINT_TEST_ATLAS_PATH);
        let world_tiles = if world_paint_path.is_file() {
            texture_cache.load_path(world_paint_path).await
        } else {
            None
        };
        let player_walk = texture_cache
            .load_semantic(
                asset_session.as_ref(),
                "character.player.base",
                AssetCategory::Character,
                runtime_asset_path("assets/generated/lpc/characters/havenwild_player_walk_64.png"),
            )
            .await;

        let hud_vitals_frame = texture_cache
            .load_semantic(
                asset_session.as_ref(),
                "ui.hud.vitals.frame",
                AssetCategory::Ui,
                runtime_asset_path("content/ui/hud/vitals_frame.png"),
            )
            .await;
        let hud_hotbar_frame = texture_cache
            .load_semantic(
                asset_session.as_ref(),
                "ui.hud.hotbar.frame",
                AssetCategory::Ui,
                runtime_asset_path("content/ui/hud/hotbar_frame.png"),
            )
            .await;
        let hud_minimap_frame = texture_cache
            .load_semantic(
                asset_session.as_ref(),
                "ui.hud.minimap.frame",
                AssetCategory::Ui,
                runtime_asset_path("content/ui/hud/minimap_frame.png"),
            )
            .await;

        let (item_icon_atlas, item_icon_rects) = load_runtime_item_icon_atlas(&mut texture_cache).await;

        let character_appearance =
            crate::character_runtime_compositor::RuntimeCharacterAppearance::load(
                std::path::Path::new(&crate::runtime_config::runtime_save_root()),
                character_id,
                asset_session.as_ref(),
                &mut texture_cache,
            )
            .await
            .map_err(|error| {
                println!("Character appearance load failed: {error}");
                error
            })
            .ok();
        if let Some(appearance) = &character_appearance {
            println!(
                "Loaded {} production character layer texture binding(s)",
                appearance.layers.len()
            );
        } else if player_walk.is_some() {
            println!(
                "Layered character appearance unavailable; using source-backed compatibility binding {}",
                SOURCE_BACKED_PLAYER_COMPATIBILITY_ID
            );
        } else {
            println!(
                "No production character visual resolved; procedural character fallback is disabled"
            );
        }
        let mut resource_bindings = SemanticResourceRegistry::default();
        let stamp_registry = asset_session
            .as_ref()
            .and_then(|session| StampRegistry::load_discovered(session).ok())
            .or_else(|| StampRegistry::load_default().ok())
            .unwrap_or_default();
        let placeable_registry = asset_session
            .as_ref()
            .and_then(|session| PublishedWorldAssetRegistry::load_discovered(session).ok())
            .unwrap_or_default();
        println!(
            "Discovered {} pack-defined placeable asset(s)",
            placeable_registry.entries().len()
        );
        let mut placeable_textures = HashMap::new();
        for definition in placeable_registry.entries() {
            if let Some(path) = &definition.source_path {
                if let Some(texture) = texture_cache.load_path(path).await {
                    placeable_textures.insert(definition.stable_id.clone(), texture);
                }
            }
        }
        println!(
            "Loaded {} stable placeable texture binding(s)",
            placeable_textures.len()
        );
        let mut stamp_textures = HashMap::new();
        for sheet in stamp_registry.sheets() {
            let path = std::path::PathBuf::from(&sheet);
            if let Some(texture) = texture_cache.load_path(&path).await {
                stamp_textures.insert(sheet, texture);
            }
        }

        for (semantic_id, category, fallback) in [
            (
                "animation.contract.default",
                AssetCategory::Animation,
                runtime_root().join("content/schemas/assets/category_metadata_contracts_v1.json"),
            ),
            (
                "audio.contract.events",
                AssetCategory::Audio,
                runtime_root().join("content/schemas/assets/category_metadata_contracts_v1.json"),
            ),
            (
                "music.contract.events",
                AssetCategory::Music,
                runtime_root().join("content/schemas/assets/category_metadata_contracts_v1.json"),
            ),
            (
                "ui.contract.generation",
                AssetCategory::Ui,
                runtime_root().join("content/ui/havenwild_gui_generation_contract_v0_1.json"),
            ),
            (
                "ui.contract.save_slots",
                AssetCategory::Ui,
                runtime_root().join("content/ui/client_save_slot_contract_v0_1.json"),
            ),
        ] {
            let _ = resource_bindings.resolve(
                asset_session.as_ref(),
                semantic_id,
                category,
                Some(&fallback),
            );
        }
        for diagnostic in resource_bindings.diagnostics() {
            println!("{diagnostic}");
        }
        println!(
            "Stable non-texture resources registered {} binding(s), {} fallback diagnostic(s)",
            resource_bindings.len(),
            resource_bindings.diagnostics().len()
        );

        let mut render_bindings = StableRenderBindingRegistry::default();
        for (role, semantic_id, category) in [
            (
                RenderTextureRole::BaseTerrain,
                "terrain.grass",
                AssetCategory::Terrain,
            ),
            (
                RenderTextureRole::TerrainTransition,
                "terrain.transition.atlas",
                AssetCategory::Terrain,
            ),
            (
                RenderTextureRole::MappedTerrain,
                "terrain.sand",
                AssetCategory::Terrain,
            ),
            (
                RenderTextureRole::LiveAutotile,
                "terrain.path.road",
                AssetCategory::Terrain,
            ),
            (
                RenderTextureRole::RuntimeObjects,
                "object.catalog.runtime",
                AssetCategory::TileObject,
            ),
            (
                RenderTextureRole::WorldPaintCompatibility,
                "terrain.world_paint.compatibility",
                AssetCategory::Terrain,
            ),
            (
                RenderTextureRole::PlayerWalk,
                "character.player.base",
                AssetCategory::Character,
            ),
        ] {
            let stable_ref =
                texture_cache.resolved_ref(asset_session.as_ref(), semantic_id, category);
            render_bindings.record(role, semantic_id, stable_ref);
        }
        println!(
            "Stable render bindings registered {} role(s), {} compatibility fallback(s)",
            render_bindings.len(),
            render_bindings.fallback_count()
        );
        println!(
            "Resolved {} render role(s): {}",
            render_bindings.resolved_count(),
            render_bindings
                .semantic_ids()
                .collect::<Vec<_>>()
                .join(", ")
        );

        println!(
            "Stable texture cache loaded {} source texture(s), {} stable binding(s), {} legacy fallback(s)",
            texture_cache.loaded_source_count(),
            texture_cache.stable_binding_count(),
            texture_cache.legacy_fallbacks().len()
        );

        let mut world_visual_override_textures = HashMap::new();
        let world_override_root = runtime_asset_path("assets/source/original/world_overrides");
        for path in collect_world_override_pngs(std::path::Path::new(&world_override_root)) {
            let relative = path.strip_prefix(runtime_root()).unwrap_or(&path).to_string_lossy().replace('\\', "/");
            if let Some(texture) = texture_cache.load_path(&path).await {
                world_visual_override_textures.insert(relative, texture);
            }
        }

        Self {
            asset_session,
            texture_cache,
            render_bindings,
            terrain,
            lpc_terrain_source,
            lpc_terrain_v7_source,
            lpc_bridge_source,
            lpc_cliff_source,
            lpc_waterfall_source,
            oga_cliff_source,
            terrain_transition,
            lpc_mapped_terrain,
            live_autotile,
            objects,
            world_tiles,
            player_walk,
            hud_vitals_frame,
            hud_hotbar_frame,
            hud_minimap_frame,
            item_icon_atlas,
            item_icon_rects,
            resource_bindings,
            stamp_registry,
            placeable_registry,
            stamp_textures,
            placeable_textures,
            world_visual_override_textures,
            character_appearance,
        }
    }
}

async fn load_runtime_item_icon_atlas(
    texture_cache: &mut StableTextureCache,
) -> (Option<Texture2D>, HashMap<String, [f32; 4]>) {
    let manifest_path = runtime_asset_path(UNIVERSAL_LPC_ITEM_ICON_MANIFEST_PATH);
    let Ok(text) = std::fs::read_to_string(&manifest_path) else {
        return (None, HashMap::new());
    };
    let Ok(manifest) = serde_json::from_str::<RuntimeItemIconManifest>(&text) else {
        println!("Universal LPC item icon manifest could not be parsed: {}", manifest_path);
        return (None, HashMap::new());
    };
    let rects = manifest
        .entries
        .into_iter()
        .map(|entry| (entry.item_id, entry.rect))
        .collect::<HashMap<_, _>>();
    let atlas = texture_cache
        .load_path(runtime_asset_path(&manifest.atlas))
        .await;
    if atlas.is_some() {
        println!("Universal LPC item icon atlas ready: {} item icon binding(s)", rects.len());
    }
    (atlas, rects)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn direct_sources_keep_authored_tuple_atlas_enabled() {
        let policy = terrain_texture_policy(true);
        assert!(policy.load_authored_tuple_atlas);
        assert!(!policy.load_generated_same_family_autotile);
    }

    #[test]
    fn missing_source_mount_keeps_tuple_atlas_and_compatibility_autotile() {
        let policy = terrain_texture_policy(false);
        assert!(policy.load_authored_tuple_atlas);
        assert!(policy.load_generated_same_family_autotile);
    }
}

fn collect_world_override_pngs(root: &std::path::Path) -> Vec<std::path::PathBuf> {
    let mut output = Vec::new();
    let mut pending = vec![root.to_path_buf()];
    while let Some(path) = pending.pop() {
        let Ok(entries) = std::fs::read_dir(&path) else { continue; };
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_dir() { pending.push(path); }
            else if path.extension().and_then(|value| value.to_str()).is_some_and(|ext| ext.eq_ignore_ascii_case("png")) { output.push(path); }
        }
    }
    output
}
