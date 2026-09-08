use macroquad::prelude::{load_texture, FilterMode, Texture2D};

use crate::runtime_config::runtime_path;
use std::path::Path;

pub(crate) const LPC_RUNTIME_FRAME_WIDTH: f32 = 64.0;
pub(crate) const LPC_RUNTIME_FRAME_HEIGHT: f32 = 96.0;
pub(crate) const SOURCE_BACKED_PLAYER_COMPATIBILITY_ID: &str = "character.player.base";

pub(crate) fn enforce_nearest_character_filter(texture: &Texture2D) {
    texture.set_filter(FilterMode::Nearest);
}

pub(crate) async fn load_optional_project_character_texture(path: &str) -> Option<Texture2D> {
    let resolved = runtime_path(path);
    if !Path::new(&resolved).is_file() {
        return None;
    }
    match load_texture(&resolved).await {
        Ok(texture) => {
            enforce_nearest_character_filter(&texture);
            Some(texture)
        }
        Err(error) => {
            println!("Could not load existing optional character texture {path}: {error}");
            None
        }
    }
}
