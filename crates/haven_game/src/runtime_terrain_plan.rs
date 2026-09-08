use super::*;

#[derive(Clone, Copy, Debug)]
pub(crate) struct VisibleTerrainCell {
    pub(crate) x: i32,
    pub(crate) y: i32,
    pub(crate) tile: TileKind,
    pub(crate) paint_owned: bool,
    pub(crate) resolved_group: Option<TileAutoGroup>,
    pub(crate) resolved_mask: u8,
    pub(crate) has_transitions: bool,
    pub(crate) mapped_entry: Option<LpcMappedTerrainEntry>,
    pub(crate) mapped_transition_entry: Option<LpcMappedTerrainEntry>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct TerrainWaterSpan {
    pub(crate) first_cell: usize,
    pub(crate) tile_count: usize,
    pub(crate) render_kind: TileKind,
}

/// Retains the complete visible terrain submission plan until either the
/// camera crosses a tile boundary, terrain changes, the active scene changes,
/// or world-paint ownership changes. Sub-tile camera movement only changes the
/// screen origin and therefore does not rebuild cell classification or spans.
#[derive(Debug, Default)]
pub(crate) struct VisibleTerrainPlanCache {
    pub(crate) bounds: Option<(i32, i32, i32, i32)>,
    pub(crate) scene_code: String,
    pub(crate) terrain_revision: u64,
    pub(crate) paint_sequence: u64,
    pub(crate) paint_active: bool,
    pub(crate) cells: Vec<VisibleTerrainCell>,
    pub(crate) base_indices: Vec<usize>,
    pub(crate) paint_indices: Vec<usize>,
    pub(crate) transition_indices: Vec<usize>,
    pub(crate) mapped_tuple_indices: Vec<usize>,
    pub(crate) greenhouse_indices: Vec<usize>,
    pub(crate) water_spans: Vec<TerrainWaterSpan>,
    pub(crate) visible_chunk_count: usize,
    pub(crate) hits: u64,
    pub(crate) rebuilds: u64,
    pub(crate) last_reason: &'static str,
}

impl VisibleTerrainPlanCache {
    pub(crate) fn needs_rebuild(
        &self,
        bounds: (i32, i32, i32, i32),
        scene_code: &str,
        terrain_revision: u64,
        paint_sequence: u64,
        paint_active: bool,
    ) -> bool {
        self.bounds != Some(bounds)
            || self.scene_code != scene_code
            || self.terrain_revision != terrain_revision
            || self.paint_sequence != paint_sequence
            || self.paint_active != paint_active
    }

    pub(crate) fn rebuild_reason(
        &self,
        bounds: (i32, i32, i32, i32),
        scene_code: &str,
        terrain_revision: u64,
        paint_sequence: u64,
        paint_active: bool,
    ) -> &'static str {
        if self.bounds.is_none() {
            "cold"
        } else if self.scene_code != scene_code {
            "scene"
        } else if self.terrain_revision != terrain_revision {
            "terrain-revision"
        } else if self.paint_sequence != paint_sequence || self.paint_active != paint_active {
            "paint-revision"
        } else if self.bounds != Some(bounds) {
            "camera-bounds"
        } else {
            "hit"
        }
    }

    pub(crate) fn begin_rebuild(
        &mut self,
        bounds: (i32, i32, i32, i32),
        scene_code: &str,
        terrain_revision: u64,
        paint_sequence: u64,
        paint_active: bool,
        desired_capacity: usize,
    ) {
        self.last_reason = self.rebuild_reason(
            bounds,
            scene_code,
            terrain_revision,
            paint_sequence,
            paint_active,
        );
        self.bounds = Some(bounds);
        self.scene_code.clear();
        self.scene_code.push_str(scene_code);
        self.terrain_revision = terrain_revision;
        self.paint_sequence = paint_sequence;
        self.paint_active = paint_active;
        self.cells.clear();
        self.base_indices.clear();
        self.paint_indices.clear();
        self.transition_indices.clear();
        self.mapped_tuple_indices.clear();
        self.greenhouse_indices.clear();
        self.water_spans.clear();
        if self.cells.capacity() < desired_capacity {
            self.cells.reserve(desired_capacity - self.cells.capacity());
        }
    }

    pub(crate) fn finish_rebuild(&mut self, visible_chunk_count: usize) {
        // The base cache is chunk-major. Sorting once per camera tile-boundary
        // produces stable row-major submissions and lets water spans cross
        // chunk boundaries instead of splitting every sixteen tiles.
        self.cells.sort_unstable_by_key(|cell| (cell.y, cell.x));
        self.visible_chunk_count = visible_chunk_count;

        for (index, cell) in self.cells.iter().enumerate() {
            if cell.paint_owned {
                self.paint_indices.push(index);
            } else {
                if !cell.tile.is_water() {
                    self.base_indices.push(index);
                }
                if cell.mapped_transition_entry.is_some() {
                    self.mapped_tuple_indices.push(index);
                }
                if cell.has_transitions {
                    self.transition_indices.push(index);
                }
            }
            if cell.tile == TileKind::GreenhouseZone {
                self.greenhouse_indices.push(index);
            }
        }

        let mut index = 0usize;
        while index < self.cells.len() {
            let cell = self.cells[index];
            if cell.paint_owned || !cell.tile.is_water() {
                index += 1;
                continue;
            }
            let render_kind = canonical_water_render_kind(cell.tile);
            let mut span_end = index + 1;
            while span_end < self.cells.len() {
                let next = self.cells[span_end];
                if next.y != cell.y
                    || next.x != cell.x + (span_end - index) as i32
                    || next.paint_owned
                    || !next.tile.is_water()
                    || canonical_water_render_kind(next.tile) != render_kind
                {
                    break;
                }
                span_end += 1;
            }
            self.water_spans.push(TerrainWaterSpan {
                first_cell: index,
                tile_count: span_end - index,
                render_kind,
            });
            index = span_end;
        }
        self.rebuilds = self.rebuilds.saturating_add(1);
    }

    pub(crate) fn record_hit(&mut self) {
        self.hits = self.hits.saturating_add(1);
        self.last_reason = "hit";
    }
}

#[derive(Debug, Default)]
pub(crate) struct SceneBackdropHeightCache {
    pub(crate) scene_code: String,
    pub(crate) next_refresh_at: f64,
    pub(crate) max_heights: Vec<u8>,
}

pub(crate) fn canonical_water_render_kind(tile: TileKind) -> TileKind {
    match tile {
        TileKind::OceanDeep => TileKind::OceanDeep,
        TileKind::OceanShallow => TileKind::OceanShallow,
        TileKind::DeepWater => TileKind::DeepWater,
        _ => TileKind::ShallowWater,
    }
}

pub(crate) fn world_paint_layers_active(
    dev_mode: bool,
    editor_tab: EditorTab,
    has_bindings: bool,
) -> bool {
    // World Paint is a separate machine-local authoring surface. Keeping its
    // cached atlas layers active while the semantic Tiles/Map tools are in use
    // lets stale water material cells visually own freshly painted grass or
    // dirt. Only the dedicated Paint tab may display those bindings.
    dev_mode && editor_tab == EditorTab::Paint && has_bindings
}

pub(crate) fn color_span_lod_enabled(
    camera_zoom: f32,
    terrain_atlas_loaded: bool,
    mapped_terrain_atlas_loaded: bool,
) -> bool {
    camera_zoom <= 0.95 && !terrain_atlas_loaded && !mapped_terrain_atlas_loaded
}

pub(crate) fn pixel_snapped_screen_origin(
    camera_target: Vec2,
    viewport: Vec2,
    camera_zoom: f32,
) -> Vec2 {
    let half = viewport * 0.5;
    let zoom = camera_zoom.max(0.01);
    // Runtime terrain positions are submitted in screen-style coordinates and
    // then transformed by the game camera. Snap the *final* projected world
    // origin, not the pre-scaled coordinate, so every cell boundary lands on a
    // device pixel at the quantized zoom.
    let projected_origin = vec2(
        (half.x - camera_target.x * zoom).round(),
        (half.y - camera_target.y * zoom).round(),
    );
    half + (projected_origin - half) / zoom
}

pub(crate) fn screen_position(cell: VisibleTerrainCell, screen_origin: Vec2) -> Vec2 {
    vec2(
        cell.x as f32 * TILE_SIZE + screen_origin.x,
        cell.y as f32 * TILE_SIZE + screen_origin.y,
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn machine_local_world_paint_is_editor_only() {
        assert!(!world_paint_layers_active(false, EditorTab::Paint, true));
        assert!(!world_paint_layers_active(true, EditorTab::Tiles, true));
        assert!(!world_paint_layers_active(true, EditorTab::Map, true));
        assert!(!world_paint_layers_active(true, EditorTab::Paint, false));
        assert!(world_paint_layers_active(true, EditorTab::Paint, true));
    }

    #[test]
    fn production_atlases_disable_solid_color_grass_spans_at_every_zoom() {
        for zoom in [0.85, 0.95, 1.05, 1.35, 2.20] {
            assert!(!color_span_lod_enabled(zoom, true, false));
            assert!(!color_span_lod_enabled(zoom, false, true));
            assert!(!color_span_lod_enabled(zoom, true, true));
        }
    }

    #[test]
    fn emergency_no_atlas_mode_can_still_use_wide_grass_spans() {
        assert!(color_span_lod_enabled(0.85, false, false));
        assert!(!color_span_lod_enabled(1.35, false, false));
    }

    #[test]
    fn deep_and_shallow_water_keep_distinct_runtime_materials() {
        assert_eq!(
            canonical_water_render_kind(TileKind::OceanDeep),
            TileKind::OceanDeep
        );
        assert_eq!(
            canonical_water_render_kind(TileKind::DeepWater),
            TileKind::DeepWater
        );
        assert_eq!(
            canonical_water_render_kind(TileKind::OceanShallow),
            TileKind::OceanShallow
        );
        assert_eq!(
            canonical_water_render_kind(TileKind::RiverWater),
            TileKind::ShallowWater
        );
    }

    #[test]
    fn visible_plan_reuses_sub_tile_camera_motion_and_rebuilds_on_revision_change() {
        let mut plan = VisibleTerrainPlanCache::default();
        let bounds = (0, 0, 7, 7);
        assert!(plan.needs_rebuild(bounds, "farmstead", 1, 0, false));
        plan.begin_rebuild(bounds, "farmstead", 1, 0, false, 64);
        plan.finish_rebuild(1);
        assert!(!plan.needs_rebuild(bounds, "farmstead", 1, 0, false));
        assert!(plan.needs_rebuild(bounds, "farmstead", 2, 0, false));
        assert!(plan.needs_rebuild((1, 0, 8, 7), "farmstead", 1, 0, false));
    }

    #[test]
    fn visible_plan_merges_water_spans_after_row_major_sorting() {
        let mut plan = VisibleTerrainPlanCache::default();
        plan.begin_rebuild((0, 0, 3, 0), "water", 1, 0, false, 4);
        for x in [2, 0, 3, 1] {
            plan.cells.push(VisibleTerrainCell {
                x,
                y: 0,
                tile: TileKind::DeepWater,
                paint_owned: false,
                resolved_group: None,
                resolved_mask: 0,
                has_transitions: false,
                mapped_entry: None,
                mapped_transition_entry: None,
            });
        }
        plan.finish_rebuild(1);
        assert_eq!(plan.water_spans.len(), 1);
        assert_eq!(plan.water_spans[0].tile_count, 4);
        assert_eq!(plan.water_spans[0].render_kind, TileKind::DeepWater);
    }

    #[test]
    fn screen_origin_is_pixel_snapped() {
        let viewport = vec2(1920.0, 1080.0);
        let zoom = 43.0 / 32.0;
        let origin = pixel_snapped_screen_origin(vec2(100.4, 201.6), viewport, zoom);
        let projected = (origin - viewport * 0.5) * zoom + viewport * 0.5;
        let alignment_error = projected - projected.round();
        assert!(
            alignment_error.x.abs() <= 0.001 && alignment_error.y.abs() <= 0.001,
            "projected terrain origin must remain within one thousandth of a device pixel: {projected:?}"
        );
    }
}
