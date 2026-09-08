use super::*;
use haven_assets::autotile::transition_atlas_manifest;
use haven_world::{
    mask_code, resolve_terrain_transitions, resolve_transition_atlas_requests, terrain_debug_cell,
    terrain_transition_rule_manifest, CardinalDirection, DiagonalDirection, TerrainFamily,
    TransitionMaterial,
};

impl Game {
    pub(super) fn draw_terrain_debug_overlay(&self) {
        if !self.dev_mode || !self.show_terrain_debug_overlay {
            return;
        }

        let scene = self.world.active();
        let map = &scene.map;
        for y in 0..MAP_H as i32 {
            for x in 0..MAP_W as i32 {
                if !scene.is_renderable_cell(x, y) {
                    continue;
                }
                let screen = self.world_to_screen(vec2(x as f32 * TILE_SIZE, y as f32 * TILE_SIZE));
                if !tile_on_screen(screen.x, screen.y) {
                    continue;
                }
                let Some(debug) = terrain_debug_cell(map, x, y) else {
                    continue;
                };
                draw_rectangle(
                    screen.x + 1.0,
                    screen.y + 1.0,
                    TILE_SIZE - 2.0,
                    TILE_SIZE - 2.0,
                    family_debug_color(debug.family),
                );

                if debug.has_transition() {
                    draw_rectangle_lines(
                        screen.x + 3.0,
                        screen.y + 3.0,
                        TILE_SIZE - 6.0,
                        TILE_SIZE - 6.0,
                        1.5,
                        Color::from_rgba(255, 245, 170, 210),
                    );
                }

                draw_transition_debug_marks(map, x, y, screen.x, screen.y);

                draw_text(
                    family_short_code(debug.family),
                    screen.x + 4.0,
                    screen.y + 13.0,
                    11.0,
                    WHITE,
                );
                if debug.water_mask != 0 {
                    draw_text(
                        "W",
                        screen.x + TILE_SIZE - 10.0,
                        screen.y + 13.0,
                        11.0,
                        Color::from_rgba(146, 224, 255, 255),
                    );
                }
                if debug.different_mask != 0 {
                    draw_text(
                        &format!("{}", debug.edge_count + debug.corner_count),
                        screen.x + 4.0,
                        screen.y + TILE_SIZE - 4.0,
                        10.0,
                        Color::from_rgba(255, 236, 142, 255),
                    );
                }
            }
        }

        self.draw_selected_terrain_debug_panel();
    }

    fn draw_selected_terrain_debug_panel(&self) {
        let map = &self.world.active().map;
        let (tx, ty) = self.selected_cell;
        let Some(debug) = terrain_debug_cell(map, tx, ty) else {
            return;
        };
        let transitions = resolve_terrain_transitions(map, tx, ty);
        let x = screen_width() - 390.0;
        let y = 24.0;
        draw_rectangle(x, y, 372.0, 354.0, Color::from_rgba(18, 30, 32, 226));
        draw_rectangle_lines(
            x,
            y,
            372.0,
            354.0,
            2.0,
            Color::from_rgba(151, 216, 207, 220),
        );
        draw_text(
            "Terrain Debug",
            x + 14.0,
            y + 25.0,
            18.0,
            Color::from_rgba(162, 228, 255, 255),
        );
        draw_text(
            &format!(
                "cell {},{}  tile {}  family {}",
                tx,
                ty,
                debug.tile.code(),
                debug.family.code()
            ),
            x + 14.0,
            y + 50.0,
            14.0,
            Color::from_rgba(244, 238, 201, 255),
        );
        draw_text(
            &format!(
                "same {}  diff {}  water {}  land {}",
                mask_code(debug.same_mask),
                mask_code(debug.different_mask),
                mask_code(debug.water_mask),
                mask_code(debug.land_mask)
            ),
            x + 14.0,
            y + 72.0,
            13.0,
            Color::from_rgba(220, 231, 236, 255),
        );
        draw_text(
            &format!(
                "edges {}  inner corners {}",
                transitions.edges.len(),
                transitions.corners.len()
            ),
            x + 14.0,
            y + 94.0,
            13.0,
            Color::from_rgba(220, 231, 236, 255),
        );
        draw_text(
            &format!(
                "edge materials: {}",
                transition_material_list(
                    &transitions
                        .edges
                        .iter()
                        .map(|edge| edge.material)
                        .collect::<Vec<_>>()
                )
            ),
            x + 14.0,
            y + 116.0,
            12.0,
            Color::from_rgba(198, 218, 225, 255),
        );
        let atlas_requests = resolve_transition_atlas_requests(&transitions);
        draw_text(
            &format!(
                "atlas masks: {}",
                transition_atlas_request_list(&atlas_requests)
            ),
            x + 14.0,
            y + 138.0,
            12.0,
            Color::from_rgba(198, 218, 225, 255),
        );
        let manifest_line = transition_atlas_manifest()
            .map(|manifest| manifest.coverage_summary())
            .unwrap_or_else(|error| format!("transition manifest unavailable: {error}"));
        draw_text(
            &manifest_line,
            x + 14.0,
            y + 160.0,
            13.0,
            Color::from_rgba(190, 214, 220, 255),
        );
        let rule_manifest_line = terrain_transition_rule_manifest()
            .map(|manifest| format!("terrain transition rules: {}", manifest.coverage_summary()))
            .unwrap_or_else(|error| format!("transition rule manifest unavailable: {error}"));
        draw_text(
            &rule_manifest_line,
            x + 14.0,
            y + 180.0,
            13.0,
            Color::from_rgba(190, 214, 220, 255),
        );
        let collision = map.collision_at(tx, ty);
        let collision_reason = match collision.reason {
            haven_core::CollisionReason::Open => "walkable".to_string(),
            haven_core::CollisionReason::OutOfBounds => "out of bounds".to_string(),
            haven_core::CollisionReason::Terrain { tile, class } => {
                format!("terrain {} ({class:?})", tile.code())
            }
            haven_core::CollisionReason::Object { index } => format!("object #{index}"),
            haven_core::CollisionReason::Stamp { index } => format!("stamp #{index}"),
        };
        draw_text(
            &format!(
                "collision: {} ({})",
                if collision.blocked { "blocked" } else { "open" },
                collision_reason
            ),
            x + 14.0,
            y + 202.0,
            13.0,
            if !collision.blocked {
                Color::from_rgba(158, 230, 168, 255)
            } else {
                Color::from_rgba(255, 142, 128, 255)
            },
        );
        if let Some(tuple) = lpc_mapped_terrain_diagnostic_for_map(map, tx, ty) {
            let (status, status_color) = match tuple.status {
                LpcTupleResolutionStatus::Exact => ("exact", Color::from_rgba(158, 230, 168, 255)),
                LpcTupleResolutionStatus::Unsupported => {
                    ("missing/workbench", Color::from_rgba(255, 178, 112, 255))
                }
            };
            let rect = tuple
                .rect
                .map(|rect| format!("{:.0},{:.0} {:.0}x{:.0}", rect.x, rect.y, rect.w, rect.h))
                .unwrap_or_else(|| "none".to_string());
            draw_text(
                &format!(
                    "tuple {} {}  rect {}",
                    status,
                    if tuple.is_mixed { "mixed" } else { "fill" },
                    rect
                ),
                x + 14.0,
                y + 226.0,
                12.0,
                status_color,
            );
            draw_text(
                &format!("TL {} | TR {}", tuple.corners[0], tuple.corners[1]),
                x + 14.0,
                y + 248.0,
                12.0,
                Color::from_rgba(198, 218, 225, 255),
            );
            draw_text(
                &format!("BL {} | BR {}", tuple.corners[2], tuple.corners[3]),
                x + 14.0,
                y + 270.0,
                12.0,
                Color::from_rgba(198, 218, 225, 255),
            );
            draw_text(
                &format!("signature {}", tuple.signature),
                x + 14.0,
                y + 292.0,
                11.0,
                Color::from_rgba(172, 198, 208, 255),
            );
        }
        draw_text(
            "T masks | Y rules | selected cell reports exact tuple + collision",
            x + 14.0,
            y + 326.0,
            12.0,
            Color::from_rgba(168, 214, 255, 255),
        );
    }
}

fn draw_transition_debug_marks(map: &TavernMap, x: i32, y: i32, px: f32, py: f32) {
    let transitions = resolve_terrain_transitions(map, x, y);
    for edge in transitions.edges {
        let color = material_debug_color(edge.material);
        match edge.direction {
            CardinalDirection::North => draw_line(
                px + 4.0,
                py + 2.0,
                px + TILE_SIZE - 4.0,
                py + 2.0,
                2.5,
                color,
            ),
            CardinalDirection::East => draw_line(
                px + TILE_SIZE - 2.0,
                py + 4.0,
                px + TILE_SIZE - 2.0,
                py + TILE_SIZE - 4.0,
                2.5,
                color,
            ),
            CardinalDirection::South => draw_line(
                px + 4.0,
                py + TILE_SIZE - 2.0,
                px + TILE_SIZE - 4.0,
                py + TILE_SIZE - 2.0,
                2.5,
                color,
            ),
            CardinalDirection::West => draw_line(
                px + 2.0,
                py + 4.0,
                px + 2.0,
                py + TILE_SIZE - 4.0,
                2.5,
                color,
            ),
        }
    }
    for corner in transitions.corners {
        let color = material_debug_color(corner.material);
        match corner.direction {
            DiagonalDirection::NorthEast => draw_circle(px + TILE_SIZE - 5.0, py + 5.0, 3.0, color),
            DiagonalDirection::SouthEast => {
                draw_circle(px + TILE_SIZE - 5.0, py + TILE_SIZE - 5.0, 3.0, color)
            }
            DiagonalDirection::SouthWest => draw_circle(px + 5.0, py + TILE_SIZE - 5.0, 3.0, color),
            DiagonalDirection::NorthWest => draw_circle(px + 5.0, py + 5.0, 3.0, color),
        }
    }
}

fn tile_on_screen(px: f32, py: f32) -> bool {
    px > -TILE_SIZE
        && py > -TILE_SIZE
        && px < screen_width() + TILE_SIZE
        && py < screen_height() + TILE_SIZE
}

fn family_short_code(family: TerrainFamily) -> &'static str {
    match family {
        TerrainFamily::Grass => "G",
        TerrainFamily::Dirt => "D",
        TerrainFamily::Sand => "S",
        TerrainFamily::WetSand => "Ws",
        TerrainFamily::PebblePath => "Pp",
        TerrainFamily::Road => "R",
        TerrainFamily::WoodFloor => "Wd",
        TerrainFamily::StoneFloor => "St",
        TerrainFamily::Farm => "F",
        TerrainFamily::ShallowWater => "Sw",
        TerrainFamily::Water => "Wa",
        TerrainFamily::DeepWater => "Dw",
        TerrainFamily::RockWall => "Rw",
        TerrainFamily::Cave => "Cv",
        TerrainFamily::Greenhouse => "Gh",
        TerrainFamily::Void => "-",
    }
}

fn family_debug_color(family: TerrainFamily) -> Color {
    match family {
        TerrainFamily::Grass => Color::new(0.08, 0.55, 0.12, 0.18),
        TerrainFamily::Dirt => Color::new(0.48, 0.25, 0.08, 0.20),
        TerrainFamily::Sand => Color::new(0.88, 0.74, 0.28, 0.22),
        TerrainFamily::WetSand => Color::new(0.64, 0.48, 0.24, 0.22),
        TerrainFamily::PebblePath => Color::new(0.50, 0.50, 0.46, 0.20),
        TerrainFamily::Road => Color::new(0.46, 0.38, 0.25, 0.20),
        TerrainFamily::WoodFloor => Color::new(0.58, 0.30, 0.10, 0.18),
        TerrainFamily::StoneFloor => Color::new(0.55, 0.56, 0.58, 0.18),
        TerrainFamily::Farm => Color::new(0.55, 0.28, 0.10, 0.20),
        TerrainFamily::ShallowWater => Color::new(0.18, 0.62, 0.82, 0.22),
        TerrainFamily::Water => Color::new(0.10, 0.48, 0.88, 0.22),
        TerrainFamily::DeepWater => Color::new(0.04, 0.20, 0.46, 0.24),
        TerrainFamily::RockWall => Color::new(0.20, 0.20, 0.23, 0.24),
        TerrainFamily::Cave => Color::new(0.12, 0.12, 0.14, 0.24),
        TerrainFamily::Greenhouse => Color::new(0.20, 0.85, 0.42, 0.18),
        TerrainFamily::Void => Color::new(0.0, 0.0, 0.0, 0.0),
    }
}

fn material_debug_color(material: TransitionMaterial) -> Color {
    match material {
        TransitionMaterial::WetSand => Color::from_rgba(196, 166, 104, 245),
        TransitionMaterial::Foam => Color::from_rgba(226, 250, 255, 245),
        TransitionMaterial::ShallowWaterEdge => Color::from_rgba(108, 202, 250, 245),
        TransitionMaterial::SandBlend => Color::from_rgba(232, 203, 115, 245),
        TransitionMaterial::GrassFringe => Color::from_rgba(92, 210, 85, 245),
        TransitionMaterial::DirtBlend => Color::from_rgba(143, 89, 42, 245),
        TransitionMaterial::RoadShoulder => Color::from_rgba(166, 134, 82, 245),
        TransitionMaterial::StoneShoulder => Color::from_rgba(184, 186, 178, 245),
        TransitionMaterial::RockShadow => Color::from_rgba(32, 33, 38, 245),
    }
}

fn transition_material_list(materials: &[TransitionMaterial]) -> String {
    if materials.is_empty() {
        return "-".to_string();
    }
    let mut parts = Vec::new();
    for material in materials.iter().take(4) {
        parts.push(material.code());
    }
    if materials.len() > 4 {
        parts.push("...");
    }
    parts.join(",")
}

fn transition_atlas_request_list(
    requests: &[haven_world::TerrainTransitionAtlasRequest],
) -> String {
    if requests.is_empty() {
        return "-".to_string();
    }
    let mut parts = Vec::new();
    for request in requests.iter().take(4) {
        parts.push(format!(
            "{}:{}",
            request.atlas_group,
            mask_code(request.mask4)
        ));
    }
    if requests.len() > 4 {
        parts.push("...".to_string());
    }
    parts.join(",")
}
