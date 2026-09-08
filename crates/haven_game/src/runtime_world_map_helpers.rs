fn loaded_surface_scene_map<'a>(
    world: &'a GameWorld,
    manifest: &haven_world::ContinuousSurfaceManifest,
) -> BTreeMap<ChunkCoord, &'a SceneMap> {
    manifest
        .exterior_bindings
        .iter()
        .filter_map(|binding| {
            world
                .scene_by_id(&binding.scene_id)
                .map(|scene| (binding.chunk, scene))
        })
        .collect()
}

fn surface_tile_at(
    scenes: &BTreeMap<ChunkCoord, &SceneMap>,
    global_x: i32,
    global_y: i32,
) -> Option<TileKind> {
    let address = haven_world::surface_tile_address(WorldTileCoord::new(global_x, global_y));
    scenes
        .get(&address.chunk)
        .map(|scene| scene.map.get(address.local_x, address.local_y))
}

fn draw_minimap_natural_objects(
    scenes: &BTreeMap<ChunkCoord, &SceneMap>,
    center: WorldTileCoord,
    half_cols: i32,
    half_rows: i32,
    grid_origin: Vec2,
    cell_px: f32,
    clip_center: Vec2,
    clip_radius: f32,
) {
    let min_x = center.x - half_cols;
    let min_y = center.y - half_rows;
    let max_x = center.x + half_cols;
    let max_y = center.y + half_rows;
    for (chunk, scene) in scenes {
        let offset_x = chunk.x * MAP_W as i32;
        let offset_y = chunk.y * MAP_H as i32;
        for object in &scene.map.objects {
            let global_x = offset_x + object.x;
            let global_y = offset_y + object.y;
            if global_x < min_x || global_x > max_x || global_y < min_y || global_y > max_y {
                continue;
            }
            let Some(color) = natural_object_map_color(object.kind) else {
                continue;
            };
            let col = global_x - min_x;
            let row = global_y - min_y;
            let marker_center = vec2(
                grid_origin.x + (col as f32 + 0.5) * cell_px,
                grid_origin.y + (row as f32 + 0.5) * cell_px,
            );
            let dx = marker_center.x - clip_center.x;
            let dy = marker_center.y - clip_center.y;
            if dx * dx + dy * dy > clip_radius * clip_radius {
                continue;
            }
            draw_rectangle(
                grid_origin.x + col as f32 * cell_px + 1.0,
                grid_origin.y + row as f32 * cell_px + 1.0,
                (cell_px - 1.0).max(1.0),
                (cell_px - 1.0).max(1.0),
                color,
            );
        }
    }
}

fn natural_object_map_color(kind: ObjectKind) -> Option<Color> {
    match kind {
        ObjectKind::Tree => Some(Color::from_rgba(18, 67, 31, 255)),
        ObjectKind::Bush => Some(Color::from_rgba(39, 99, 47, 255)),
        ObjectKind::Mushroom => Some(Color::from_rgba(207, 178, 126, 255)),
        ObjectKind::Herb => Some(Color::from_rgba(232, 196, 88, 255)),
        _ => None,
    }
}

fn find_rectangle_spec<'a>(
    manifest: &'a SceneRectangleManifest,
    region: &str,
    chunk: ChunkCoord,
) -> Option<&'a SceneRectangleSpec> {
    manifest.scene_rectangles.iter().find(|spec| {
        spec.grid_x == Some(chunk.x)
            && spec.grid_y == Some(chunk.y)
            && region_matches_landmass(region, &spec.landmass_name)
    })
}

fn region_matches_landmass(region: &str, landmass_name: &str) -> bool {
    let landmass = slug(landmass_name);
    let alderreach_legacy_match =
        landmass == "alderreach" && matches!(region, "mainland" | "havenwild_mainland");
    alderreach_legacy_match
        || region == landmass
        || region.ends_with(&format!("_{landmass}"))
        || landmass.ends_with(&format!("_{region}"))
}

fn slug(value: &str) -> String {
    let mut result = String::new();
    let mut separator = false;
    for character in value.chars() {
        if character.is_ascii_alphanumeric() {
            if separator && !result.is_empty() {
                result.push('_');
            }
            result.push(character.to_ascii_lowercase());
            separator = false;
        } else {
            separator = true;
        }
    }
    result
}

fn world_map_exploration_path(save_manifest_path: &str) -> PathBuf {
    let manifest = Path::new(save_manifest_path);
    manifest
        .parent()
        .unwrap_or_else(|| Path::new("."))
        .join("world_map_exploration.json")
}

fn load_world_map_exploration(
    path: &Path,
) -> BTreeMap<(i32, i32), WorldMapChunkSnapshot> {
    let Ok(bytes) = fs::read(path) else {
        return BTreeMap::new();
    };
    let Ok(payload) = serde_json::from_slice::<PersistedWorldMapExploration>(&bytes) else {
        return BTreeMap::new();
    };
    if payload.schema != WORLD_MAP_EXPLORATION_SCHEMA {
        return BTreeMap::new();
    }
    payload
        .chunks
        .into_iter()
        .filter(|snapshot| {
            snapshot.cols == WORLD_MAP_CHUNK_COLS
                && snapshot.rows == WORLD_MAP_CHUNK_ROWS
                && snapshot.cells.len() == snapshot.cols.saturating_mul(snapshot.rows)
        })
        .map(|snapshot| ((snapshot.chunk_x, snapshot.chunk_y), snapshot))
        .collect()
}

fn world_map_exploration_bytes(
    chunks: &BTreeMap<(i32, i32), WorldMapChunkSnapshot>,
) -> Result<Vec<u8>, String> {
    let payload = PersistedWorldMapExploration {
        schema: WORLD_MAP_EXPLORATION_SCHEMA.to_string(),
        chunks: chunks.values().cloned().collect(),
    };
    serde_json::to_vec(&payload).map_err(|error| error.to_string())
}

fn empty_world_map_chunk_snapshot(chunk: ChunkCoord) -> WorldMapChunkSnapshot {
    WorldMapChunkSnapshot {
        chunk_x: chunk.x,
        chunk_y: chunk.y,
        cols: WORLD_MAP_CHUNK_COLS,
        rows: WORLD_MAP_CHUNK_ROWS,
        cells: vec![WORLD_MAP_UNEXPLORED; WORLD_MAP_CHUNK_COLS * WORLD_MAP_CHUNK_ROWS],
    }
}

const fn world_map_code_priority(code: u8) -> u8 {
    match code {
        7 => 100, // road
        9 => 99,  // bridge
        10 => 95, // path
        6 => 90,  // structural cliff edge
        8 => 85,  // river/freshwater
        5 => 70,  // level 2/highland
        11 => 65, // deterministic forest habitat
        4 => 60,  // level 1/upland
        2 => 50,  // shore
        1 => 40,  // shallow water
        3 => 30,  // ordinary land
        _ => 20,  // deep water
    }
}

fn explored_world_map_bounds(
    chunks: &BTreeMap<(i32, i32), WorldMapChunkSnapshot>,
) -> Option<(i32, i32, i32, i32)> {
    let mut bounds: Option<(i32, i32, i32, i32)> = None;
    for snapshot in chunks.values() {
        let chunk_origin_x = snapshot.chunk_x * MAP_W as i32;
        let chunk_origin_y = snapshot.chunk_y * MAP_H as i32;
        for row in 0..snapshot.rows {
            for col in 0..snapshot.cols {
                if snapshot.cells[row * snapshot.cols + col] == WORLD_MAP_UNEXPLORED {
                    continue;
                }
                let x0 = chunk_origin_x + col as i32 * WORLD_MAP_SAMPLE_STEP;
                let y0 = chunk_origin_y + row as i32 * WORLD_MAP_SAMPLE_STEP;
                let x1 = x0 + WORLD_MAP_SAMPLE_STEP;
                let y1 = y0 + WORLD_MAP_SAMPLE_STEP;
                bounds = Some(match bounds {
                    Some((min_x, min_y, max_x, max_y)) => (
                        min_x.min(x0),
                        min_y.min(y0),
                        max_x.max(x1),
                        max_y.max(y1),
                    ),
                    None => (x0, y0, x1, y1),
                });
            }
        }
    }
    bounds
}

fn explored_world_map_color(code: u8) -> Color {
    match code {
        0 => Color::from_rgba(13, 48, 82, 255),
        1 => Color::from_rgba(47, 113, 149, 255),
        2 => Color::from_rgba(206, 188, 121, 255),
        4 => Color::from_rgba(81, 116, 61, 255),
        5 => Color::from_rgba(92, 100, 74, 255),
        6 => Color::from_rgba(65, 54, 43, 255),
        7 => Color::from_rgba(156, 111, 67, 255),
        8 => Color::from_rgba(63, 133, 158, 255),
        9 => Color::from_rgba(171, 128, 70, 255),
        10 => Color::from_rgba(139, 105, 71, 255),
        11 => Color::from_rgba(38, 94, 48, 255),
        _ => Color::from_rgba(55, 129, 66, 255),
    }
}

fn geographic_overview_color(code: u8) -> Color {
    match code {
        0 => Color::from_rgba(13, 48, 82, 255),
        1 => Color::from_rgba(47, 113, 149, 255),
        2 => Color::from_rgba(206, 188, 121, 255),
        4 => Color::from_rgba(67, 112, 58, 255),
        5 => Color::from_rgba(83, 96, 66, 255),
        6 => Color::from_rgba(65, 54, 43, 255),
        8 => Color::from_rgba(63, 133, 158, 255),
        11 => Color::from_rgba(38, 94, 48, 255),
        _ => Color::from_rgba(55, 129, 66, 255),
    }
}

fn world_map_tile_color(tile: TileKind) -> Color {
    match tile {
        TileKind::OceanDeep | TileKind::DeepWater => Color::from_rgba(24, 66, 102, 255),
        TileKind::OceanShallow | TileKind::ShallowWater | TileKind::Water => {
            Color::from_rgba(52, 111, 139, 255)
        }
        TileKind::RiverWater | TileKind::RiverMouthBlend => Color::from_rgba(65, 127, 148, 255),
        TileKind::Sand | TileKind::WetSand => Color::from_rgba(194, 177, 116, 255),
        TileKind::Grass | TileKind::TallGrass => Color::from_rgba(61, 126, 67, 255),
        TileKind::Dirt | TileKind::Road | TileKind::MountainPath => {
            Color::from_rgba(133, 99, 64, 255)
        }
        TileKind::PebbleShore | TileKind::StonePath => Color::from_rgba(126, 127, 117, 255),
        TileKind::MountainRock | TileKind::Cliff | TileKind::CaveWall => {
            Color::from_rgba(82, 91, 92, 255)
        }
        TileKind::MudBank | TileKind::WateredSoil => Color::from_rgba(92, 67, 48, 255),
        TileKind::TilledSoil | TileKind::Crop => Color::from_rgba(111, 77, 49, 255),
        TileKind::CaveFloor | TileKind::StoneFloor => Color::from_rgba(94, 93, 88, 255),
        TileKind::WoodFloor | TileKind::PlankFloor => Color::from_rgba(127, 84, 49, 255),
        TileKind::BrickFloor | TileKind::Wall => Color::from_rgba(112, 89, 78, 255),
        TileKind::Bridge => Color::from_rgba(142, 102, 59, 255),
        TileKind::ShoreFoam => Color::from_rgba(182, 218, 211, 255),
        TileKind::GreenhouseZone => Color::from_rgba(89, 155, 112, 255),
    }
}

fn world_map_panel_rect() -> Rect {
    let margin = 28.0;
    Rect::new(
        margin,
        margin,
        (screen_width() - margin * 2.0).max(320.0),
        (screen_height() - margin * 2.0).max(260.0),
    )
}

fn world_map_viewport_rect() -> Rect {
    let panel = world_map_panel_rect();
    Rect::new(
        panel.x + 18.0,
        panel.y + 72.0,
        panel.w - 36.0,
        panel.h - 106.0,
    )
}

fn rects_intersect(left: Rect, right: Rect) -> bool {
    left.x < right.x + right.w
        && left.x + left.w > right.x
        && left.y < right.y + right.h
        && left.y + left.h > right.y
}

fn rect_intersection(left: Rect, right: Rect) -> Option<Rect> {
    if !rects_intersect(left, right) {
        return None;
    }
    let x = left.x.max(right.x);
    let y = left.y.max(right.y);
    let right_edge = (left.x + left.w).min(right.x + right.w);
    let bottom_edge = (left.y + left.h).min(right.y + right.h);
    Some(Rect::new(x, y, right_edge - x, bottom_edge - y))
}

