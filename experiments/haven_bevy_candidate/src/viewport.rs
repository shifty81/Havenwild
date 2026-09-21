//! Candidate viewport *presentation* geometry. Uses one immutable Bevy draft texture.
//! This is not a scene camera, dynamic render target, renderer parity or game PIE.
use bevy_egui::egui;

#[derive(Clone, Debug)]
pub(crate) struct WorldViewport {
    pub zoom: f32,
    pub pan: egui::Vec2,
    pub show_grid: bool,
}

impl Default for WorldViewport {
    fn default() -> Self { Self { zoom: 1.0, pan: egui::Vec2::ZERO, show_grid: false } }
}

impl WorldViewport {
    pub fn reset(&mut self) { self.zoom = 1.0; self.pan = egui::Vec2::ZERO; }
    pub fn zoom_by(&mut self, factor: f32, pointer_from_center: Option<egui::Vec2>) {
        if !factor.is_finite() || factor <= 0.0 { return; }
        let next = (self.zoom * factor).clamp(0.25, 16.0);
        let ratio = next / self.zoom;
        if let Some(pointer) = pointer_from_center {
            self.pan = pointer - (pointer - self.pan) * ratio;
        }
        self.zoom = next;
    }
    pub fn scale(&self, viewport: egui::Vec2, native: egui::Vec2) -> f32 {
        let fit = (viewport.x / native.x.max(1.0))
            .min(viewport.y / native.y.max(1.0)).max(0.00001);
        fit * self.zoom
    }
    pub fn clamp_pan(&mut self, viewport: egui::Vec2, native: egui::Vec2) {
        let draw = native * self.scale(viewport, native);
        let extent = egui::vec2(((draw.x - viewport.x) * 0.5).max(0.0),
                                ((draw.y - viewport.y) * 0.5).max(0.0));
        self.pan.x = self.pan.x.clamp(-extent.x, extent.x);
        self.pan.y = self.pan.y.clamp(-extent.y, extent.y);
    }
    pub fn image_rect(&self, viewport: egui::Rect, native: egui::Vec2) -> egui::Rect {
        let draw = native * self.scale(viewport.size(), native);
        egui::Rect::from_center_size(viewport.center() + self.pan, draw)
    }
    pub fn cell_at(&self, point: egui::Pos2, image: egui::Rect, cells: [usize; 2]) -> Option<[usize; 2]> {
        if cells.contains(&0) || !image.contains(point) || image.width() <= 0.0 || image.height() <= 0.0 {
            return None;
        }
        let x = ((point.x - image.min.x) / image.width() * cells[0] as f32).floor() as usize;
        let y = ((point.y - image.min.y) / image.height() * cells[1] as f32).floor() as usize;
        Some([x.min(cells[0] - 1), y.min(cells[1] - 1)])
    }
    pub fn cell_rect(&self, image: egui::Rect, cell: [usize; 2], cells: [usize; 2]) -> egui::Rect {
        let scale = egui::vec2(image.width() / cells[0].max(1) as f32,
                               image.height() / cells[1].max(1) as f32);
        egui::Rect::from_min_size(image.min + egui::vec2(cell[0] as f32 * scale.x,
            cell[1] as f32 * scale.y), scale)
    }
    pub fn paint_grid(&self, painter: &egui::Painter, image: egui::Rect, cells: [usize; 2]) {
        let sx = image.width() / cells[0].max(1) as f32;
        let sy = image.height() / cells[1].max(1) as f32;
        // Fine lines are counterproductive below 5 physical pixels/tile.
        if sx < 5.0 || sy < 5.0 { return; }
        let stroke = egui::Stroke::new(0.6, egui::Color32::from_rgba_unmultiplied(180, 190, 195, 70));
        for x in 0..=cells[0] {
            let x = image.left() + x as f32 * sx;
            painter.line_segment([egui::pos2(x, image.top()), egui::pos2(x, image.bottom())], stroke);
        }
        for y in 0..=cells[1] {
            let y = image.top() + y as f32 * sy;
            painter.line_segment([egui::pos2(image.left(), y), egui::pos2(image.right(), y)], stroke);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn center_and_coordinates_remain_exact_after_zoom_and_pan() {
        let mut view = WorldViewport::default();
        let viewport = egui::Rect::from_min_size(egui::pos2(100.0, 80.0), egui::vec2(1000.0, 700.0));
        let native = egui::vec2(1280.0, 896.0);
        let rect = view.image_rect(viewport, native);
        assert_eq!(view.cell_at(rect.min + egui::vec2(16.0, 16.0), rect, [40, 28]), Some([0, 0]));
        view.zoom_by(2.0, Some(egui::Vec2::ZERO));
        view.pan = egui::vec2(100.0, -80.0);
        view.clamp_pan(viewport.size(), native);
        let rect = view.image_rect(viewport, native);
        let c = view.cell_rect(rect, [12, 16], [40, 28]);
        assert_eq!(view.cell_at(c.center(), rect, [40, 28]), Some([12, 16]));
        assert_eq!(view.cell_at(rect.min - egui::vec2(1.0, 1.0), rect, [40, 28]), None);
    }
    #[test]
    fn fit_and_zoom_are_bounded_and_grid_is_non_authoritative() {
        let mut view = WorldViewport::default();
        view.zoom_by(100000.0, None);
        assert_eq!(view.zoom, 16.0);
        view.zoom_by(0.00001, None);
        assert_eq!(view.zoom, 0.25);
        view.reset();
        assert_eq!(view.zoom, 1.0);
        assert_eq!(view.pan, egui::Vec2::ZERO);
    }
}
