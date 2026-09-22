//! Primary-window GPU atlas compositor for the read-only ElizaWy river fixture.
//! This draws exact, pre-verified source pixels through Bevy's egui texture upload.
//! The result is not source mapping approval, native renderer parity, or PIE.
use bevy_egui::egui;
use crate::{SOURCE_H, SOURCE_W};

const TILE_PX: u32 = 32;

fn source_uv(cell: [u32; 2]) -> Option<egui::Rect> {
    if cell[0] >= SOURCE_W / TILE_PX || cell[1] >= SOURCE_H / TILE_PX {
        return None;
    }
    let x = cell[0] as f32 * TILE_PX as f32;
    let y = cell[1] as f32 * TILE_PX as f32;
    Some(egui::Rect::from_min_max(
        egui::pos2(x / SOURCE_W as f32, y / SOURCE_H as f32),
        egui::pos2((x + TILE_PX as f32) / SOURCE_W as f32,
                   (y + TILE_PX as f32) / SOURCE_H as f32),
    ))
}

/// Submit atlas-sampled image rectangles to the primary egui GPU render pass.
/// Coordinate arithmetic derives independently from each cell to avoid drift
/// during fractional zoom. The clipping rectangle comes from the *canvas*, not
/// the full desktop, so floating panels retain correct input/drawing ownership.
pub(crate) fn draw_tiles(
    painter: &egui::Painter,
    texture: egui::TextureId,
    image_rect: egui::Rect,
    viewport: egui::Rect,
    scene_size: [usize; 2],
    cells: &[[u32; 2]],
) {
    let [width, height] = scene_size;
    if width == 0 || height == 0 || cells.len() != width.saturating_mul(height) {
        return;
    }
    let step_x = image_rect.width() / width as f32;
    let step_y = image_rect.height() / height as f32;
    for (index, &source) in cells.iter().enumerate() {
        let x = index % width;
        let y = index / width;
        let min = image_rect.min + egui::vec2(x as f32 * step_x, y as f32 * step_y);
        let max = image_rect.min + egui::vec2((x + 1) as f32 * step_x, (y + 1) as f32 * step_y);
        let tile_rect = egui::Rect::from_min_max(min, max);
        if !viewport.intersects(tile_rect) {
            continue;
        }
        if let Some(uv) = source_uv(source) {
            painter.image(texture, tile_rect, uv, egui::Color32::WHITE);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn source_crop_matches_original_32_pixel_cells() {
        let uv = source_uv([3, 5]).expect("valid source tile");
        assert!((uv.min.x - 96.0 / 512.0).abs() < 0.000001);
        assert!((uv.min.y - 160.0 / 832.0).abs() < 0.000001);
        assert!((uv.max.x - 128.0 / 512.0).abs() < 0.000001);
        assert!((uv.max.y - 192.0 / 832.0).abs() < 0.000001);
    }

    #[test]
    fn out_of_bounds_tiles_never_sample_another_image() {
        assert!(source_uv([15, 25]).is_some());
        assert!(source_uv([16, 0]).is_none());
        assert!(source_uv([0, 26]).is_none());
    }
}
