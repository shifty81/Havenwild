// H20 world-completion development-map helpers.
// Kept separate from runtime_world_map_game.rs so the already-large input/draw
// coordinator does not continue accumulating world-generation diagnostics.

impl Game {
    /// H20 acceptance aid: reveal the complete finite generated macro surface
    /// without materializing every storage partition. This intentionally samples
    /// the same geographic surface authority used by chunk generation and is
    /// capped at a 256-cell longest axis so opening the map remains bounded.
    /// Exploration fog stays available behind the development reveal toggle and
    /// can be restored as the normal release behavior after worldgen acceptance.
    fn development_world_map_overview(&self) -> Option<WorldMapOverview> {
        if !self.world_map.development_reveal_all
            || self.world_topology.extent != haven_world::WorldTopologyExtent::Finite
        {
            return None;
        }

        let origin_x = self.world_topology.origin_x_tiles;
        let origin_y = self.world_topology.origin_y_tiles;
        let span_w = self.world_topology.width_tiles.max(1);
        let span_h = self.world_topology.height_tiles.max(1);
        let target_longest = 256.0_f32;
        let sample_step = ((span_w.max(span_h) as f32 / target_longest).ceil() as i32).max(1);
        let cols = ((span_w + sample_step - 1) / sample_step).max(1) as usize;
        let rows = ((span_h + sample_step - 1) / sample_step).max(1) as usize;
        let profile = haven_world::GeographicGenerationProfile::from_world_creation(
            &self.world_creation_settings,
        );
        let seed = self.world_creation_settings.seed;
        let mut cells = Vec::with_capacity(cols.saturating_mul(rows));

        for row in 0..rows {
            let local_y = ((row as i32) * sample_step + sample_step / 2).min(span_h - 1);
            let global_y = origin_y + local_y;
            for col in 0..cols {
                let local_x = ((col as i32) * sample_step + sample_step / 2).min(span_w - 1);
                let global_x = origin_x + local_x;
                let surface = haven_world::sample_geographic_surface(seed, global_x, global_y, profile);
                let code = if !surface.land {
                    if surface.shallow_ocean { 1 } else { 0 }
                } else if surface.shoreline {
                    2
                } else if surface.structural_level >= 2 {
                    5
                } else if surface.structural_level == 1 {
                    4
                } else {
                    3
                };
                cells.push(code);
            }
        }

        let skeleton = haven_world::ArchipelagoSkeleton::for_geographic_profile(seed, profile);
        let mut landmarks = skeleton
            .landmasses
            .iter()
            .filter(|landmass| matches!(
                landmass.class,
                haven_world::LandmassClass::Mainland | haven_world::LandmassClass::MajorIsland
            ))
            .map(|landmass| WorldMapLandmark {
                world_x: landmass.center.x,
                world_y: landmass.center.y,
                label: landmass.name.clone(),
                capital: landmass.class == haven_world::LandmassClass::Mainland,
            })
            .collect::<Vec<_>>();
        if let Some(capital) = self
            .building_instance_registry
            .entries()
            .iter()
            .find(|definition| definition.id.starts_with("pcg.willowmere."))
            .and_then(|definition| definition.global_anchor_tile)
        {
            landmarks.push(WorldMapLandmark {
                world_x: capital[0],
                world_y: capital[1],
                label: "Willowmere".to_string(),
                capital: true,
            });
        }

        Some(WorldMapOverview {
            origin_x,
            origin_y,
            span_w,
            span_h,
            cols,
            rows,
            cells,
            landmarks,
        })
    }


    fn draw_world_map_landmarks(&self, overview: &WorldMapOverview, viewport: Rect) {
        for landmark in &overview.landmarks {
            let screen = self.world_map_canvas_to_screen(
                vec2(landmark.world_x as f32, landmark.world_y as f32),
                viewport,
            );
            if !viewport.contains(screen) {
                continue;
            }
            let radius = if landmark.capital { 5.0 } else { 3.5 };
            draw_circle(
                screen.x,
                screen.y,
                radius,
                if landmark.capital {
                    Color::from_rgba(255, 220, 116, 255)
                } else {
                    Color::from_rgba(223, 226, 188, 235)
                },
            );
            if self.world_map.zoom >= 0.16 {
                draw_text(
                    &landmark.label,
                    screen.x + radius + 3.0,
                    screen.y - 2.0,
                    12.0,
                    Color::from_rgba(226, 230, 207, 238),
                );
            }
        }
    }
}
