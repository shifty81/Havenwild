use serde::Deserialize;
use std::path::PathBuf;
use std::time::SystemTime;

use haven_core::{ObjectFootprint, ObjectId, ObjectKind, PlacedObject, ProjectSceneId};

use crate::Game;

const LIVE_COMMAND_PATH: &str = "WORKSPACE/development/live_command.json";
const RESOURCE_CONTEXT_HEARTBEAT_MS: u64 = 250;

#[derive(Debug, Deserialize)]
struct LiveCommandEnvelope {
    schema: String,
    world_id: String,
    sequence: u64,
    command: LiveCommand,
}

#[derive(Debug, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
enum LiveCommand {
    MoveObject { scene_id: String, object_id: u64, x: i32, y: i32 },
    SpawnObject { scene_id: String, object_id: u64, kind: String, x: i32, y: i32, footprint: LiveFootprint },
    DeleteObject { scene_id: String, object_id: u64 },
}

#[derive(Debug, Deserialize)]
struct LiveFootprint {
    visual_offset_x: i32, visual_offset_y: i32, visual_w: i32, visual_h: i32,
    collision_offset_x: i32, collision_offset_y: i32, collision_w: i32, collision_h: i32,
    interaction_offset_x: i32, interaction_offset_y: i32, interaction_w: i32, interaction_h: i32,
    blocks_movement: bool, occludes_player: bool, fade_when_player_behind: bool,
}

impl From<LiveFootprint> for ObjectFootprint {
    fn from(value: LiveFootprint) -> Self {
        Self {
            visual_offset_x: value.visual_offset_x, visual_offset_y: value.visual_offset_y,
            visual_w: value.visual_w, visual_h: value.visual_h,
            collision_offset_x: value.collision_offset_x, collision_offset_y: value.collision_offset_y,
            collision_w: value.collision_w, collision_h: value.collision_h,
            interaction_offset_x: value.interaction_offset_x, interaction_offset_y: value.interaction_offset_y,
            interaction_w: value.interaction_w, interaction_h: value.interaction_h,
            blocks_movement: value.blocks_movement, occludes_player: value.occludes_player,
            fade_when_player_behind: value.fade_when_player_behind,
        }
    }
}

#[derive(Debug, Default)]
pub(crate) struct DevelopmentLiveBridge {
    enabled: bool,
    last_sequence: u64,
    last_modified: Option<SystemTime>,
    next_resource_context_unix_ms: u64,
}

impl DevelopmentLiveBridge {
    pub(crate) fn enabled() -> Self {
        Self {
            enabled: true,
            next_resource_context_unix_ms: haven_core::unix_time_ms(),
            ..Self::default()
        }
    }

    pub(crate) fn poll(&mut self, game: &mut Game) {
        if !self.enabled { return; }
        self.publish_resource_context(game);
        let path = command_path();
        let Ok(metadata) = std::fs::metadata(&path) else { return; };
        let modified = metadata.modified().ok();
        if modified.is_some() && modified == self.last_modified { return; }
        self.last_modified = modified;
        let Ok(bytes) = std::fs::read(&path) else { return; };
        let Ok(envelope) = serde_json::from_slice::<LiveCommandEnvelope>(&bytes) else { return; };
        if envelope.schema != "havenwild.development_live_command.v1"
            || envelope.world_id != game.world_id.0
            || envelope.sequence <= self.last_sequence
        { return; }
        self.last_sequence = envelope.sequence;
        if let Err(error) = apply(game, envelope.command) {
            game.status_message = format!("Live edit rejected: {error}");
        }
    }
    fn publish_resource_context(&mut self, game: &mut Game) {
        let now = haven_core::unix_time_ms();
        if now < self.next_resource_context_unix_ms {
            return;
        }
        self.next_resource_context_unix_ms = now.saturating_add(RESOURCE_CONTEXT_HEARTBEAT_MS);
        let Ok(repo_root) = std::env::current_dir() else {
            return;
        };
        let context = game.development_resource_context(now);
        if let Err(error) = haven_authoring::write_resource_context(&repo_root, &context) {
            game.log
                .event(&format!("Development Resource Context publish failed: {error}"));
        }
    }
}

fn apply(game: &mut Game, command: LiveCommand) -> Result<(), String> {
    match command {
        LiveCommand::MoveObject { scene_id, object_id, x, y } => {
            let scene_id = ProjectSceneId::new(scene_id);
            let scene = game.world.scene_mut(&scene_id).ok_or_else(|| format!("scene {} is not loaded", scene_id))?;
            scene.map.move_object(ObjectId::from_raw(object_id), x, y)
                .map_err(|issues| issues.iter().map(|issue| issue.label()).collect::<Vec<_>>().join("; "))?;
            game.status_message = format!("Live edit: moved object {} to {}, {}", object_id, x, y);
            Ok(())
        }
        LiveCommand::SpawnObject { scene_id, object_id, kind, x, y, footprint } => {
            let scene_id = ProjectSceneId::new(scene_id);
            let kind = ObjectKind::from_code(&kind).ok_or_else(|| format!("unknown object kind {kind}"))?;
            let scene = game.world.scene_mut(&scene_id).ok_or_else(|| format!("scene {} is not loaded", scene_id))?;
            if scene.map.object(ObjectId::from_raw(object_id)).is_some() { return Ok(()); }
            let mut object = PlacedObject::with_id(ObjectId::from_raw(object_id), kind, x, y);
            object.footprint = footprint.into();
            let placed_id = scene.map.place_custom_object(object).ok_or_else(|| format!("cannot live-place {} at {}, {}", kind.label(), x, y))?;
            if placed_id != ObjectId::from_raw(object_id) {
                return Err(format!("live-place stable ID mismatch: editor {} runtime {}", object_id, placed_id));
            }
            game.status_message = format!("Live edit: spawned {} ({}) at {}, {}", kind.label(), object_id, x, y);
            Ok(())
        }
        LiveCommand::DeleteObject { scene_id, object_id } => {
            let scene_id = ProjectSceneId::new(scene_id);
            let scene = game.world.scene_mut(&scene_id).ok_or_else(|| format!("scene {} is not loaded", scene_id))?;
            scene.map.remove_object(ObjectId::from_raw(object_id)).ok_or_else(|| format!("object {} is missing", object_id))?;
            game.status_message = format!("Live edit: deleted object {}", object_id);
            Ok(())
        }
    }
}

fn command_path() -> PathBuf {
    std::env::current_dir().unwrap_or_else(|_| PathBuf::from(".")).join(LIVE_COMMAND_PATH)
}
