use haven_assets::lpc_mapped_terrain::lpc_mapped_terrain_quiet_entry;
use haven_core::{TavernMap, TileKind, TILE_SIZE};
use haven_render::atlas_rect;
use macroquad::prelude::*;

pub(crate) const LPC_WOOD_BRIDGE_SOURCE_PATH: &str =
    "assets/source/licensed/lpc_revised/Structure/Bridges/Wood Bridge A - No Rails.png";

const SOURCE_CELL_SIZE: f32 = 32.0;

pub(crate) fn bridge_underlay_tile(map: &TavernMap, x: i32, y: i32) -> Option<TileKind> {
    let neighbors = [
        map.get(x, y - 1),
        map.get(x + 1, y),
        map.get(x, y + 1),
        map.get(x - 1, y),
    ];
    [
        TileKind::OceanShallow,
        TileKind::ShallowWater,
        TileKind::Water,
        TileKind::OceanDeep,
        TileKind::DeepWater,
        TileKind::RiverWater,
    ]
    .into_iter()
    .find(|candidate| neighbors.contains(candidate))
}

#[allow(clippy::too_many_arguments)]
pub(crate) fn draw_bridge_base(
    map: &TavernMap,
    x: i32,
    y: i32,
    px: f32,
    py: f32,
    bridge_texture: Option<&Texture2D>,
    mapped_terrain_texture: Option<&Texture2D>,
) -> bool {
    let Some(bridge_texture) = bridge_texture else {
        return false;
    };
    if let Some(underlay) = bridge_underlay_tile(map, x, y) {
        if let (Some(texture), Some(entry)) = (
            mapped_terrain_texture,
            lpc_mapped_terrain_quiet_entry(underlay),
        ) {
            draw_source(texture, atlas_rect(entry.rect), px, py);
        }
    }
    draw_bridge_tile(bridge_texture, map, x, y, px, py);
    true
}

fn draw_source(texture: &Texture2D, source: Rect, px: f32, py: f32) {
    draw_texture_ex(
        texture,
        px,
        py,
        WHITE,
        DrawTextureParams {
            dest_size: Some(vec2(TILE_SIZE + 0.20, TILE_SIZE + 0.20)),
            source: Some(source),
            ..Default::default()
        },
    );
}

pub(crate) fn draw_bridge_tile(
    texture: &Texture2D,
    map: &TavernMap,
    x: i32,
    y: i32,
    px: f32,
    py: f32,
) {
    let north = map.get(x, y - 1) == TileKind::Bridge;
    let east = map.get(x + 1, y) == TileKind::Bridge;
    let south = map.get(x, y + 1) == TileKind::Bridge;
    let west = map.get(x - 1, y) == TileKind::Bridge;
    let horizontal = east || west || (!north && !south);

    let (column, row) = if horizontal {
        match (west, east) {
            (false, true) => (7, 1),
            (true, false) => (9, 1),
            _ => (8, 1),
        }
    } else {
        match (north, south) {
            (false, true) => (1, 0),
            (true, false) => (1, 2),
            _ => (1, 1),
        }
    };

    draw_texture_ex(
        texture,
        px,
        py,
        WHITE,
        DrawTextureParams {
            dest_size: Some(vec2(TILE_SIZE, TILE_SIZE)),
            source: Some(Rect::new(
                column as f32 * SOURCE_CELL_SIZE,
                row as f32 * SOURCE_CELL_SIZE,
                SOURCE_CELL_SIZE,
                SOURCE_CELL_SIZE,
            )),
            ..Default::default()
        },
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bridge_source_is_a_project_owned_runtime_path() {
        assert!(LPC_WOOD_BRIDGE_SOURCE_PATH.starts_with("assets/source/licensed/"));
        assert!(LPC_WOOD_BRIDGE_SOURCE_PATH.ends_with(".png"));
    }
}
