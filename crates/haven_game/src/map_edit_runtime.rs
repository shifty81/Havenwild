use super::*;

impl Game {
    pub(super) fn handle_map_tab_click(&mut self, mx: f32, my: f32, panel_x: f32) -> bool {
        for (label, x, y) in [
            ("Seed+", panel_x + 18.0, 126.0),
            ("Biome", panel_x + 98.0, 126.0),
            ("Water-", panel_x + 18.0, 162.0),
            ("Water+", panel_x + 98.0, 162.0),
            ("Highland-", panel_x + 178.0, 162.0),
            ("Highland+", panel_x + 258.0, 162.0),
            ("Raise", panel_x + 18.0, 198.0),
            ("Lower", panel_x + 98.0, 198.0),
            ("Smooth", panel_x + 178.0, 198.0),
            ("Repaint", panel_x + 258.0, 198.0),
            ("Generate", panel_x + 18.0, 238.0),
            ("Bridge", panel_x + 118.0, 238.0),
        ] {
            if mx >= x && mx <= x + 82.0 && my >= y && my <= y + 26.0 {
                match label {
                    "Seed+" => {
                        self.world_seed = self.world_seed.wrapping_add(1);
                        self.status_message = format!("Map seed {}", self.world_seed);
                    }
                    "Biome" => self.cycle_active_biome(),
                    "Water-" => {
                        self.map_water_level = (self.map_water_level - 4).max(8);
                        self.status_message = format!("Water level {}", self.map_water_level);
                    }
                    "Water+" => {
                        self.map_water_level = (self.map_water_level + 4).min(72);
                        self.status_message = format!("Water level {}", self.map_water_level);
                    }
                    "Highland-" => {
                        self.map_mountain_level = (self.map_mountain_level - 4).max(42);
                        self.status_message =
                            format!("Highland rockline {}", self.map_mountain_level);
                    }
                    "Highland+" => {
                        self.map_mountain_level = (self.map_mountain_level + 4).min(96);
                        self.status_message =
                            format!("Highland rockline {}", self.map_mountain_level);
                    }
                    "Raise" => {
                        self.map_brush = MapBrushMode::Raise;
                        self.status_message = "Height brush: Raise".to_string();
                    }
                    "Lower" => {
                        self.map_brush = MapBrushMode::Lower;
                        self.status_message = "Height brush: Lower".to_string();
                    }
                    "Smooth" => {
                        self.map_brush = MapBrushMode::Smooth;
                        self.status_message = "Height brush: Smooth".to_string();
                    }
                    "Repaint" => {
                        self.push_undo_snapshot();
                        self.rebuild_active_scene_from_heightmap();
                        self.status_message = "Repainted terrain from saved heights".to_string();
                    }
                    "Generate" => {
                        self.push_undo_snapshot();
                        self.generate_active_heightmap_scene();
                    }
                    "Bridge" => {
                        self.push_undo_snapshot();
                        self.place_bridge_at_cursor();
                    }
                    _ => {}
                }
                self.log.event(&self.status_message);
                return true;
            }
        }
        true
    }

    pub(super) fn generate_active_heightmap_scene(&mut self) {
        let scene_kind = self.world.active().kind;
        let scene_biome = self.world.active().biome;
        let seed = self.world_seed as u32;
        let water_level = self.map_water_level;
        let mountain_level = self.map_mountain_level;
        let scene = self.world.active_mut();
        scene.map.objects.clear();
        for y in 0..MAP_H as i32 {
            for x in 0..MAP_W as i32 {
                let edge = x.min(y).min(MAP_W as i32 - 1 - x).min(MAP_H as i32 - 1 - y);
                let ridge = if edge < 3 { 18 - edge * 4 } else { 0 };
                let river_x = MAP_W as i32 / 2
                    + (((y * 17 + seed as i32 * 3) as f32 * 0.17).sin() * 8.0) as i32;
                let river = (x - river_x).abs() <= 1;
                let lake_dx = x - 12;
                let lake_dy = y - 23;
                let lake = lake_dx * lake_dx + lake_dy * lake_dy < 34;
                let coast_pull = if matches!(scene_biome, SceneBiome::Coastal) {
                    ((y - (MAP_H as i32 / 2)) * 3).max(0)
                } else {
                    0
                };
                let uplands = if matches!(scene_biome, SceneBiome::Highlands) {
                    ((x - MAP_W as i32 / 2).abs() / 2) + edge.max(0) * 2
                } else {
                    0
                };
                let cave_bias = if matches!(scene_kind, SceneKind::Cave) {
                    12
                } else {
                    0
                };
                let mut height = terrain_height(seed, x, y) as i32 + ridge + uplands + cave_bias;
                if river {
                    height -= 18;
                }
                if lake {
                    height -= 24;
                }
                if coast_pull > 0 {
                    height -= coast_pull;
                }
                scene.map.set_height(x, y, height.clamp(0, 100) as u8);
            }
        }
        self.rebuild_active_scene_from_heightmap();
        let scene = self.world.active_mut();
        for transition in scene.transitions.clone() {
            for y in transition.y - 1..transition.y + transition.h + 1 {
                for x in transition.x - 1..transition.x + transition.w + 1 {
                    scene.map.set(x, y, TileKind::Road);
                    scene.map.set_height(
                        x,
                        y,
                        (water_level + 8).clamp(0, mountain_level - 2) as u8,
                    );
                }
            }
        }
        let _ = scene.map.place_object(ObjectKind::Tree, 7, 8);
        let _ = scene.map.place_object(ObjectKind::Tree, 39, 22);
        if matches!(scene_kind, SceneKind::Cave) {
            let _ = scene.map.place_object(ObjectKind::OreNode, 26, 16);
        }
        self.status_message = format!(
            "Generated {} {} terrain seed {} water {} highland rockline {}",
            scene.name,
            scene_biome.label(),
            seed,
            water_level,
            mountain_level
        );
    }

    pub(super) fn place_bridge_at_cursor(&mut self) {
        let (cx, cy) = self.selected_cell;
        let scene = self.world.active_mut();
        for x in cx - 2..=cx + 2 {
            scene.map.set(x, cy, TileKind::Bridge);
            scene.map.set(x, cy - 1, TileKind::Bridge);
            scene
                .map
                .set_height(x, cy, (self.map_water_level + 10).clamp(0, 100) as u8);
            scene
                .map
                .set_height(x, cy - 1, (self.map_water_level + 10).clamp(0, 100) as u8);
        }
        self.status_message = format!("Placed bridge at {},{}", cx, cy);
    }

    pub(super) fn cycle_active_biome(&mut self) {
        let scene = self.world.active_mut();
        scene.biome = match scene.kind {
            SceneKind::Cave => SceneBiome::Cave,
            SceneKind::Interior => SceneBiome::Temperate,
            SceneKind::Exterior => match scene.biome {
                SceneBiome::Temperate => SceneBiome::Coastal,
                SceneBiome::Coastal => SceneBiome::Highlands,
                SceneBiome::Highlands | SceneBiome::Cave => SceneBiome::Temperate,
            },
        };
        self.status_message = format!("Scene biome: {}", scene.biome.label());
    }

    pub(super) fn apply_map_brush(&mut self, tx: i32, ty: i32) {
        let brush = self.map_brush;
        let min_y = self.brush_min(ty);
        let max_y = self.brush_max(ty, MAP_H as i32);
        let min_x = self.brush_min(tx);
        let max_x = self.brush_max(tx, MAP_W as i32);
        let scene = self.world.active_mut();
        for y in min_y..=max_y {
            for x in min_x..=max_x {
                match brush {
                    MapBrushMode::Raise => scene.map.add_height(x, y, 6),
                    MapBrushMode::Lower => scene.map.add_height(x, y, -6),
                    MapBrushMode::Smooth => {
                        let mut total = 0i32;
                        let mut count = 0i32;
                        for sy in y - 1..=y + 1 {
                            for sx in x - 1..=x + 1 {
                                if TavernMap::idx(sx, sy).is_some() {
                                    total += scene.map.get_height(sx, sy) as i32;
                                    count += 1;
                                }
                            }
                        }
                        if count > 0 {
                            scene.map.set_height(x, y, (total / count) as u8);
                        }
                    }
                }
            }
        }
        self.rebuild_active_scene_from_heightmap();
        self.status_message = format!("{} heights around {},{}", brush.label(), tx, ty);
    }

    pub(super) fn rebuild_active_scene_from_heightmap(&mut self) {
        let scene_kind = self.world.active().kind;
        let scene_biome = self.world.active().biome;
        let water_level = self.map_water_level;
        let mountain_level = self.map_mountain_level;
        let preserved_transitions = self.world.active().transitions.clone();
        let scene = self.world.active_mut();
        for y in 0..MAP_H as i32 {
            for x in 0..MAP_W as i32 {
                let height = scene.map.get_height(x, y) as i32;
                let edge = x.min(y).min(MAP_W as i32 - 1 - x).min(MAP_H as i32 - 1 - y);
                let tile = classify_height_tile(TerrainClassificationInput {
                    scene_kind,
                    biome: scene_biome,
                    height,
                    edge,
                    x,
                    y,
                    water_level,
                    mountain_level,
                });
                scene.map.set(x, y, tile);
            }
        }
        if scene_kind == SceneKind::Exterior {
            apply_coastline_tile_pass(&mut scene.map, scene_biome);
        }
        for transition in preserved_transitions {
            for y in transition.y - 1..transition.y + transition.h + 1 {
                for x in transition.x - 1..transition.x + transition.w + 1 {
                    scene.map.set(x, y, TileKind::Road);
                }
            }
        }
    }

    pub(super) fn draw_map_editor_tab(&self, panel_x: f32) {
        draw_text(
            "Elevation + Structural Cliff Editor",
            panel_x + 18.0,
            104.0,
            17.0,
            Color::from_rgba(162, 228, 255, 255),
        );
        draw_text(
            &format!(
                "Biome {} | Brush {} | Cursor h{}",
                self.world.active().biome.label(),
                self.map_brush.label(),
                self.world
                    .active()
                    .map
                    .get_height(self.selected_cell.0, self.selected_cell.1)
            ),
            panel_x + 18.0,
            154.0,
            15.0,
            Color::from_rgba(244, 238, 201, 255),
        );
        draw_text(
            &format!(
                "Seed {} | Waterline {} | Highland rockline {} | Face step Δ2",
                self.world_seed, self.map_water_level, self.map_mountain_level
            ),
            panel_x + 18.0,
            174.0,
            15.0,
            Color::from_rgba(244, 238, 201, 255),
        );
        for (label, x, y, w) in [
            ("Seed+", panel_x + 18.0, 126.0, 72.0),
            ("Biome", panel_x + 98.0, 126.0, 72.0),
            ("Water-", panel_x + 18.0, 162.0, 72.0),
            ("Water+", panel_x + 98.0, 162.0, 72.0),
            ("Highland-", panel_x + 178.0, 162.0, 76.0),
            ("Highland+", panel_x + 258.0, 162.0, 76.0),
            ("Raise", panel_x + 18.0, 198.0, 72.0),
            ("Lower", panel_x + 98.0, 198.0, 72.0),
            ("Smooth", panel_x + 178.0, 198.0, 72.0),
            ("Repaint", panel_x + 258.0, 198.0, 72.0),
            ("Generate", panel_x + 18.0, 238.0, 92.0),
            ("Bridge", panel_x + 118.0, 238.0, 82.0),
        ] {
            draw_editor_button(label, x, y, w, 26.0);
        }
        draw_text(
            "Paint saved elevation here; do not paint Cliff as a flat ground tile.",
            panel_x + 18.0,
            274.0,
            14.0,
            Color::from_rgba(208, 224, 232, 255),
        );
        draw_text(
            "Generate classifies exposed faces, plateau tops, shores, and mountain ground.",
            panel_x + 18.0,
            296.0,
            14.0,
            Color::from_rgba(208, 224, 232, 255),
        );
        draw_text(
            "Repaint preserves ground material and rebuilds faces from neighboring height deltas.",
            panel_x + 18.0,
            318.0,
            14.0,
            Color::from_rgba(208, 224, 232, 255),
        );
        draw_text(
            "Bridge stamps a walkable span over water without removing depth data.",
            panel_x + 18.0,
            340.0,
            14.0,
            Color::from_rgba(208, 224, 232, 255),
        );
        draw_text(
            "Cliff art: ElizaWy seasonal faces audited; exact runtime recipes still gated.",
            panel_x + 18.0,
            362.0,
            14.0,
            Color::from_rgba(255, 232, 144, 255),
        );
        draw_text(
            "V7 supplies rock, stone, mudstone, pits, and plateau tops—not vertical faces.",
            panel_x + 18.0,
            384.0,
            14.0,
            Color::from_rgba(208, 224, 232, 255),
        );
    }
}
