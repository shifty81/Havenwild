use super::*;
impl Game {
    pub(super) fn draw_world_paint_editor_tab(&self, panel_x: f32) {
        draw_text(
            "World Paint Brush Backend",
            panel_x + 18.0,
            104.0,
            19.0,
            Color::from_rgba(255, 232, 144, 255),
        );
        for (label, x, y, w) in [
            ("Family", panel_x + 18.0, 126.0, 92.0),
            ("Layer", panel_x + 118.0, 126.0, 82.0),
            ("Subcell", panel_x + 208.0, 126.0, 92.0),
            ("Str-", panel_x + 308.0, 126.0, 62.0),
            ("Str+", panel_x + 378.0, 126.0, 62.0),
            ("Auto", panel_x + 18.0, 164.0, 82.0),
            ("MirrorH", panel_x + 108.0, 164.0, 82.0),
            ("MirrorV", panel_x + 198.0, 164.0, 82.0),
            ("Match", panel_x + 288.0, 164.0, 82.0),
            ("Water", panel_x + 18.0, 202.0, 76.0),
            ("Sand", panel_x + 102.0, 202.0, 72.0),
            ("Cave", panel_x + 182.0, 202.0, 72.0),
            ("Brick", panel_x + 262.0, 202.0, 76.0),
            ("Wood", panel_x + 346.0, 202.0, 76.0),
            ("Replay", panel_x + 18.0, 240.0, 94.0),
            ("ReplayAll", panel_x + 120.0, 240.0, 106.0),
            ("Inspect", panel_x + 234.0, 240.0, 94.0),
            ("Adj", panel_x + 336.0, 240.0, 64.0),
            ("SceneAdj", panel_x + 408.0, 240.0, 94.0),
            ("Tile", panel_x + 18.0, 278.0, 76.0),
            ("SceneTile", panel_x + 102.0, 278.0, 104.0),
            ("Bind", panel_x + 214.0, 278.0, 76.0),
        ] {
            draw_editor_button(label, x, y, w, 26.0);
        }
        let lines = [
            format!(
                "Family: {} ({})",
                self.world_paint_family.label(),
                self.world_paint_family.code()
            ),
            format!("Layer: {}", self.world_paint_layer.code()),
            format!("Brush radius: {} tile(s)", self.brush_size),
            format!(
                "Subcell mask: {} grid {:?}",
                self.world_paint_subcell_mode.code(),
                self.world_paint_subcell_mode.grid()
            ),
            format!(
                "Strength: {:.2}  Autotile: {}",
                self.world_paint_strength,
                if self.world_paint_autotile {
                    "ON"
                } else {
                    "OFF"
                }
            ),
            format!(
                "Mirror: horizontal {}  vertical {}",
                if self.world_paint_mirror_horizontal {
                    "ON"
                } else {
                    "OFF"
                },
                if self.world_paint_mirror_vertical {
                    "ON"
                } else {
                    "OFF"
                }
            ),
            format!(
                "Selected: {},{}",
                self.selected_cell.0, self.selected_cell.1
            ),
            format!("Last: {}", self.world_paint_last_report),
            format!("Delta: {}", self.world_paint_delta_status),
            format!("Inspector: {}", self.world_paint_inspector_status),
            format!("Adjacency: {}", self.world_paint_adjacency_status),
            format!("Tile: {}", self.world_paint_tile_resolver_status),
            format!("Render binding: {}", self.world_paint_render_status),
            format!(
                "Bound atlas layers: {} across {} cell(s)",
                self.world_paint_render_bindings.len(),
                self.world_paint_render_bindings.cell_count()
            ),
            format!("Sequence: {}", self.world_paint_edit_sequence),
        ];
        for (i, line) in lines.iter().enumerate() {
            draw_text(
                line,
                panel_x + 24.0,
                320.0 + i as f32 * 19.0,
                15.0,
                Color::from_rgba(220, 231, 236, 255),
            );
        }
        if let Some(inspection) = &self.world_paint_inspector {
            let header = format!(
                "Cell material state: {} entry(s) | adjacency {} | debris {}",
                inspection.entries.len(),
                if inspection.ready_for_adjacency {
                    "READY"
                } else {
                    "not ready"
                },
                if inspection.ready_for_debris {
                    "READY"
                } else {
                    "not ready"
                }
            );
            draw_text(
                &header,
                panel_x + 24.0,
                548.0,
                14.0,
                Color::from_rgba(255, 232, 144, 255),
            );
            for (i, entry) in inspection.entries.iter().take(4).enumerate() {
                let line = format!(
                    "{}: {} / {} / {} / weights {} / seq {}",
                    i + 1,
                    entry.family,
                    entry.layer,
                    entry.subcell_mode,
                    entry.weights_u8.len(),
                    entry.last_sequence
                );
                draw_text(
                    &line,
                    panel_x + 24.0,
                    570.0 + i as f32 * 17.0,
                    13.0,
                    Color::from_rgba(220, 231, 236, 255),
                );
            }
        }
        if let Some(adjacency) = &self.world_paint_adjacency {
            let line = format!(
                "Adjacency: {} | mask {} | role {}",
                adjacency.primary_family,
                adjacency.neighbor_mask.compact_label(),
                adjacency.transition_role_hint
            );
            draw_text(
                &line,
                panel_x + 24.0,
                638.0,
                13.0,
                Color::from_rgba(180, 255, 196, 255),
            );
        }
        if let Some(tile) = &self.world_paint_tile_resolution {
            let line = format!(
                "Tile record: {} rect {:?} kind {} bits {}",
                tile.selected_tile_id,
                tile.selected_atlas_rect,
                tile.transition_kind,
                tile.neighbor_bits
            );
            draw_text(
                &line,
                panel_x + 24.0,
                656.0,
                13.0,
                Color::from_rgba(255, 232, 144, 255),
            );
        }
        draw_text(
            "Paint on the world with LMB. Deltas -> material state -> adjacency -> strict 32x32 tile record selection.",
            panel_x + 24.0,
            704.0,
            14.0,
            Color::from_rgba(162, 228, 255, 255),
        );
        draw_text(
            "Hotkeys: J/K family  [/] subcell  P layer  A autotile  H/V mirror  T replay  I inspect  Y/U adj  O/L tile  B bind  -/+ radius",
            panel_x + 24.0,
            724.0,
            14.0,
            Color::from_rgba(162, 228, 255, 255),
        );
    }
}
