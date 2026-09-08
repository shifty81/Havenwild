impl Game {
    /// Compatibility entry point retained for the existing input flow. The
    /// player map is discovery-backed now: it snapshots the actual streamed
    /// scene the player has entered instead of pre-revealing a synthetic
    /// geography raster. This preserves roads, structural cliffs, hydrology,
    /// and player/editor terrain changes exactly as they exist in the world.
    pub(super) fn rebuild_world_map_geographic_overview(&mut self) {
        self.capture_active_world_map_chunk();
        self.world_map.overview = if self.world_map.development_reveal_all {
            self.build_development_world_map_overview()
        } else {
            None
        };
    }

    /// Development Reveal-All is a semantic LOD of the production world, not a
    /// separate preview image. Each cell samples the same deterministic
    /// geography/hydrology/structural authority used by streamed chunks. Exact
    /// explored/live recipes are drawn over this coarse world-scale cache.
    fn build_development_world_map_overview(&self) -> Option<WorldMapOverview> {
        let profile = haven_world::GeographicGenerationProfile::from_world_creation(
            &self.world_creation_settings,
        );
        if !profile.finite_world {
            return None;
        }

        // H20V2B1: New Game persists this complete semantic world authority.
        // Prefer it here so opening Reveal All never has to redesign/recompute
        // the finite world's drainage/map raster. Older saves retain the exact
        // deterministic sampler below as a compatibility fallback.
        let semantic_bake_path = std::path::Path::new(&self.save_paths.root)
            .join(haven_world::SEMANTIC_WORLD_BAKE_RELATIVE_PATH);
        if let Ok(bake) = haven_world::load_semantic_world_bake_v1_from_path(&semantic_bake_path) {
            if bake.matches(self.world_seed, profile) {
                let mut landmarks = bake
                    .landmarks
                    .iter()
                    .map(|landmark| WorldMapLandmark {
                        world_x: landmark.world_x,
                        world_y: landmark.world_y,
                        label: landmark.label.clone(),
                        capital: landmark.capital,
                    })
                    .collect::<Vec<_>>();
                if let Some(capital) = self
                    .building_instance_registry
                    .entries()
                    .iter()
                    .find(|definition| definition.id.starts_with("pcg.willowmere."))
                    .and_then(|definition| definition.global_anchor_tile)
                {
                    if !landmarks
                        .iter()
                        .any(|landmark| landmark.label.eq_ignore_ascii_case("Willowmere"))
                    {
                        landmarks.push(WorldMapLandmark {
                            world_x: capital[0],
                            world_y: capital[1],
                            label: "Willowmere".to_string(),
                            capital: true,
                        });
                    }
                }
                return Some(WorldMapOverview {
                    origin_x: bake.origin_x,
                    origin_y: bake.origin_y,
                    span_w: bake.span_w,
                    span_h: bake.span_h,
                    cols: bake.cols,
                    rows: bake.rows,
                    cells: bake.cells,
                    landmarks,
                });
            }
        }

        let skeleton = haven_world::ArchipelagoSkeleton::for_geographic_profile(
            self.world_seed,
            profile,
        );
        let (origin_x, origin_y) = skeleton.geographic_origin_tiles();
        let span_w = skeleton.world_width_tiles.max(1);
        let span_h = skeleton.world_height_tiles.max(1);
        const MAX_AXIS_CELLS: usize = 192;
        let longest = span_w.max(span_h) as f32;
        let cols = ((span_w as f32 / longest) * MAX_AXIS_CELLS as f32)
            .round()
            .clamp(1.0, MAX_AXIS_CELLS as f32) as usize;
        let rows = ((span_h as f32 / longest) * MAX_AXIS_CELLS as f32)
            .round()
            .clamp(1.0, MAX_AXIS_CELLS as f32) as usize;
        let drainage = haven_world::drainage_features_for_bounds(
            self.world_seed,
            origin_x,
            origin_y,
            origin_x + span_w - 1,
            origin_y + span_h - 1,
            profile,
        );
        let mut cells = Vec::with_capacity(cols.saturating_mul(rows));
        for row in 0..rows {
            let sample_y = origin_y
                + (((row as f64 + 0.5) * span_h as f64 / rows as f64).floor() as i32)
                    .clamp(0, span_h - 1);
            for col in 0..cols {
                let sample_x = origin_x
                    + (((col as f64 + 0.5) * span_w as f64 / cols as f64).floor() as i32)
                        .clamp(0, span_w - 1);
                cells.push(haven_world::sample_generated_surface_map_code_with_drainage(
                    self.world_seed,
                    sample_x,
                    sample_y,
                    profile,
                    &drainage,
                ));
            }
        }
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

}
