use super::*;
use haven_core::{
    pending_dev_bridge_commands, unix_time_ms, write_dev_bridge_status, DevBridgeClientStatus,
    DevBridgeCommand,
};
use std::path::{Path, PathBuf};

const DEV_BRIDGE_ENV: &str = "HAVENWILD_DEV_BRIDGE";
const HEARTBEAT_INTERVAL_MS: u64 = 500;
const EDITOR_WORLD_PATH: &str = "content/worldgen/dev_worlds/core_dev_001/world.tworld";

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum DevBridgeFrameAction {
    None,
    ReloadAssets,
    Quit,
}

pub(crate) struct DevBridgeClientSession {
    enabled: bool,
    repo_root: PathBuf,
    started_unix_ms: u64,
    next_heartbeat_unix_ms: u64,
    last_command_sequence: u64,
    desired_reveal_all: bool,
    pending_editor_world: bool,
    pending_asset_reload: bool,
    last_message: String,
}

impl DevBridgeClientSession {
    pub(crate) fn from_runtime_root(root: &Path) -> Self {
        let enabled = std::env::var(DEV_BRIDGE_ENV)
            .map(|value| matches!(value.trim().to_ascii_lowercase().as_str(), "1" | "true" | "on" | "yes"))
            .unwrap_or(false);
        let now = unix_time_ms();
        Self {
            enabled,
            repo_root: root.to_path_buf(),
            started_unix_ms: now,
            next_heartbeat_unix_ms: now,
            last_command_sequence: 0,
            // Keep reveal-all enabled during development acceptance. Release
            // builds can restore exploration fog after worldgen is certified.
            desired_reveal_all: true,
            pending_editor_world: false,
            pending_asset_reload: false,
            last_message: if enabled {
                "Development bridge enabled".to_string()
            } else {
                "Development bridge disabled".to_string()
            },
        }
    }

    pub(crate) fn enabled(&self) -> bool {
        self.enabled
    }

    pub(crate) fn poll_frontend(&mut self) -> bool {
        if !self.enabled {
            return false;
        }
        let mut quit = false;
        match pending_dev_bridge_commands(&self.repo_root, self.last_command_sequence) {
            Ok(commands) => {
                for envelope in commands {
                    self.last_command_sequence = envelope.sequence;
                    if envelope.issued_unix_ms.saturating_add(5_000) < self.started_unix_ms {
                        continue;
                    }
                    match envelope.command {
                        DevBridgeCommand::ReloadAssets { reason } => {
                            self.pending_asset_reload = true;
                            self.last_message = format!("Asset reload queued until gameplay: {reason}");
                        }
                        DevBridgeCommand::ReloadEditorWorld { reason } => {
                            self.pending_editor_world = true;
                            self.last_message = format!("Editor world reload queued until gameplay: {reason}");
                        }
                        DevBridgeCommand::ReloadAssetsAndWorld { reason } => {
                            self.pending_asset_reload = true;
                            self.pending_editor_world = true;
                            self.last_message = format!("Assets + editor world queued until gameplay: {reason}");
                        }
                        DevBridgeCommand::SetRevealAllMap { enabled } => {
                            self.desired_reveal_all = enabled;
                            self.last_message = format!(
                                "Development map reveal {}",
                                if enabled { "enabled" } else { "disabled" }
                            );
                        }
                        DevBridgeCommand::QuitClient => {
                            self.last_message = "Editor requested client shutdown".to_string();
                            quit = true;
                        }
                    }
                }
            }
            Err(error) => self.last_message = format!("Dev bridge command poll failed: {error}"),
        }
        if unix_time_ms() >= self.next_heartbeat_unix_ms || quit {
            let _ = self.write_status(None, "frontend");
        }
        quit
    }

    pub(crate) fn apply_pending_to_game(&mut self, game: &mut Game) {
        if !self.enabled {
            return;
        }
        game.world_map.development_reveal_all = self.desired_reveal_all;
        if self.pending_editor_world {
            self.last_message = game.reload_editor_world_from_dev_bridge("queued editor change");
            self.pending_editor_world = false;
        }
        // RuntimeAssets were loaded immediately before Game construction, so a
        // frontend-time asset request is already satisfied by the fresh load.
        self.pending_asset_reload = false;
        let _ = self.write_status(Some(game), "gameplay");
    }

    pub(crate) fn heartbeat_frontend(&mut self) {
        if !self.enabled || unix_time_ms() < self.next_heartbeat_unix_ms {
            return;
        }
        let _ = self.write_status(None, "frontend");
    }

    pub(crate) fn poll_game(&mut self, game: &mut Game) -> DevBridgeFrameAction {
        if !self.enabled {
            return DevBridgeFrameAction::None;
        }
        let mut action = DevBridgeFrameAction::None;
        match pending_dev_bridge_commands(&self.repo_root, self.last_command_sequence) {
            Ok(commands) => {
                for envelope in commands {
                    self.last_command_sequence = envelope.sequence;
                    if envelope.issued_unix_ms.saturating_add(5_000) < self.started_unix_ms {
                        continue;
                    }
                    match envelope.command {
                        DevBridgeCommand::ReloadAssets { reason } => {
                            self.last_message = format!("Reload assets: {reason}");
                            action = DevBridgeFrameAction::ReloadAssets;
                        }
                        DevBridgeCommand::ReloadEditorWorld { reason } => {
                            self.last_message = game.reload_editor_world_from_dev_bridge(&reason);
                        }
                        DevBridgeCommand::ReloadAssetsAndWorld { reason } => {
                            self.last_message = game.reload_editor_world_from_dev_bridge(&reason);
                            action = DevBridgeFrameAction::ReloadAssets;
                        }
                        DevBridgeCommand::SetRevealAllMap { enabled } => {
                            self.desired_reveal_all = enabled;
                            game.world_map.development_reveal_all = enabled;
                            self.last_message = format!(
                                "Development map reveal {}",
                                if enabled { "enabled" } else { "disabled" }
                            );
                        }
                        DevBridgeCommand::QuitClient => {
                            self.last_message = "Editor requested client shutdown".to_string();
                            action = DevBridgeFrameAction::Quit;
                        }
                    }
                }
            }
            Err(error) => {
                self.last_message = format!("Dev bridge command poll failed: {error}");
            }
        }
        let now = unix_time_ms();
        if now >= self.next_heartbeat_unix_ms || action != DevBridgeFrameAction::None {
            let _ = self.write_status(Some(game), "gameplay");
        }
        action
    }

    pub(crate) fn note_asset_reload(&mut self, game: &Game, result: &str) {
        if !self.enabled {
            return;
        }
        self.last_message.clear();
        self.last_message.push_str(result);
        let _ = self.write_status(Some(game), "gameplay");
    }

    fn write_status(&mut self, game: Option<&Game>, phase: &str) -> Result<(), String> {
        let now = unix_time_ms();
        self.next_heartbeat_unix_ms = now.saturating_add(HEARTBEAT_INTERVAL_MS);
        let (world_id, character_id, active_scene, player_tile, reveal_all_map) = game.map_or(
            (None, None, None, None, false),
            |game| {
                let tile_x = (game.player.x / TILE_SIZE).floor() as i32;
                let tile_y = (game.player.y / TILE_SIZE).floor() as i32;
                (
                    Some(game.world_id.0.clone()),
                    Some(game.character_id.0.clone()),
                    Some(game.world.active_scene.code().to_string()),
                    Some([tile_x, tile_y]),
                    game.world_map.development_reveal_all,
                )
            },
        );
        write_dev_bridge_status(
            &self.repo_root,
            &DevBridgeClientStatus {
                schema: haven_core::DEV_BRIDGE_SCHEMA.to_string(),
                process_id: std::process::id(),
                started_unix_ms: self.started_unix_ms,
                heartbeat_unix_ms: now,
                phase: phase.to_string(),
                world_id,
                character_id,
                active_scene,
                player_tile,
                last_command_sequence: self.last_command_sequence,
                reveal_all_map,
                message: self.last_message.clone(),
            },
        )
    }
}

impl Game {
    pub(crate) fn replace_runtime_assets_from_dev_bridge(&mut self, assets: RuntimeAssets) {
        let RuntimeAssets {
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
            terrain_transition: _,
            lpc_mapped_terrain,
            live_autotile,
            objects,
            world_tiles,
            player_walk,
            hud_vitals_frame,
            hud_hotbar_frame,
            hud_minimap_frame,
            resource_bindings,
            stamp_registry,
            placeable_registry,
            stamp_textures,
            placeable_textures,
            character_appearance,
        } = assets;

        self.terrain_atlas = terrain;
        self.lpc_terrain_source = lpc_terrain_source;
        self.lpc_terrain_v7_source = lpc_terrain_v7_source;
        self.lpc_bridge_source = lpc_bridge_source;
        self.lpc_cliff_source = lpc_cliff_source;
        self.lpc_waterfall_source = lpc_waterfall_source;
        self.oga_cliff_source = oga_cliff_source;
        self.lpc_mapped_terrain_atlas = lpc_mapped_terrain;
        self.live_autotile_atlas = live_autotile;
        self.object_atlas = objects;
        self.world_tile_atlas = world_tiles;
        self.player_walk_atlas = player_walk;
        self.hud_vitals_frame = hud_vitals_frame;
        self.hud_hotbar_frame = hud_hotbar_frame;
        self.hud_minimap_frame = hud_minimap_frame;
        self.runtime_character_appearance = character_appearance;
        self.stamp_registry = stamp_registry;
        self.placeable_registry = placeable_registry;
        self.stamp_textures = stamp_textures;
        self.placeable_textures = placeable_textures;
        self.asset_binding_counts = (
            render_bindings.len(),
            render_bindings.fallback_count(),
            resource_bindings.len(),
        );
        self.asset_session = asset_session;
        self._texture_cache = texture_cache;
        self.invalidate_dev_bridge_presentation_caches("Dev bridge asset reload");
        self.log.event("Dev bridge reloaded runtime assets without restarting the client");
    }

    fn reload_editor_world_from_dev_bridge(&mut self, reason: &str) -> String {
        let path = runtime_root().join(EDITOR_WORLD_PATH);
        let path_text = path.to_string_lossy().into_owned();
        let mut editor_world = match load_world_from_path(&path_text) {
            Ok(world) => world,
            Err(error) => return format!("Editor world reload failed: {error}"),
        };
        let previous_scene = self.world.active_scene.clone();
        if editor_world.scene_by_reference(&previous_scene).is_some() {
            let _ = editor_world.set_active_scene(previous_scene);
        }
        self.world = editor_world;
        self.rebuild_active_surface_structures();
        self.repair_exterior_player_spawn_if_unsafe();
        self.invalidate_dev_bridge_presentation_caches("Dev bridge world reload");
        self.selected_cell = (
            (self.player.x / TILE_SIZE).floor() as i32,
            (self.player.y / TILE_SIZE).floor() as i32,
        );
        self.inspector = inspect_scene_cell(self.world.active(), self.selected_cell.0, self.selected_cell.1);
        let message = format!("Reloaded saved editor world live: {reason}");
        self.status_message = message.clone();
        self.log.event(&message);
        message
    }

    fn invalidate_dev_bridge_presentation_caches(&mut self, reason: &str) {
        self.terrain_cache = LiveAutotileCache::new(self.world.active());
        self.terrain_cache.synchronize(self.world.active());
        *self.base_terrain_cache.borrow_mut() = base_terrain_cache::BaseTerrainChunkCache::default();
        *self.chunk_surface_cache.borrow_mut() = chunk_surface_cache::ChunkSurfaceDescriptorCache::default();
        *self.visible_terrain_plan.borrow_mut() = runtime_terrain_pass::VisibleTerrainPlanCache::default();
        *self.terrain_scene_surface.borrow_mut() = terrain_scene_surface::TerrainSceneSurfaceCache::default();
        *self.scene_backdrop_height_cache.borrow_mut() = runtime_terrain_pass::SceneBackdropHeightCache::default();
        self.surface_chunks = runtime_surface_streaming::SurfaceChunkRuntime::default();
        self.rebuild_active_surface_structures();
        self.refresh_world_paint_render_bindings_for_active_scene(reason);
        self.terrain_cache_next_sync_at = get_time() + 0.35;
    }
}
