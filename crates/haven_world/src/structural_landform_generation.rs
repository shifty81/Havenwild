//! Deterministic discrete structural landforms for fresh PCG surfaces.
//!
//! Havenwild keeps smooth geological height for hydrology/material decisions,
//! but visible traversal elevation is deliberately a small authored-style set
//! of platform levels. This pass converts continuous geology into explicit
//! Level 0/2/4 plateaus (with odd levels reserved only for authored LPC ramp
//! corridors) across the complete landmass assembly so cliffs
//! are real generated structure rather than an accidental by-product of noise.

use std::collections::BTreeMap;

use haven_core::{ObjectKind, SceneMap, TileKind, ZoneKind, MAP_H, MAP_W};

use crate::structural_landform_coastal::{
    choose_shoreline_ladder_hosts, marine_shore_tile, shoreline_distance_cells,
    COASTAL_CORE_CLEARANCE_CELLS,
};
use crate::structural_landform_ramps::{
    choose_inland_ladder_hosts, choose_or_carve_south_ramp_edges, directional_ramp_corridor_indices,
};
#[cfg(test)]
use crate::structural_landform_ramps::{
    choose_south_ramp_edges, directional_ramp_orientation_for_candidate,
};
use crate::{
    geographic_landforms::geographic_structural_level,
    open_world::ChunkCoord,
    structural_landform_masks::{
        fill_small_structural_holes, normalize_structural_contours, retain_broad_candidates,
    },
};

pub const STRUCTURAL_LANDFORM_GENERATION_SCHEMA: &str =
    "havenwild.structural_landform_generation.v0_2";

const PROTECTED_BUFFER_RADIUS: i32 = 6;
const GUARANTEE_RADIUS_X: i32 = 9;
const GUARANTEE_RADIUS_Y: i32 = 6;

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct StructuralLandformReport {
    pub level_zero_cells: usize,
    pub level_one_cells: usize,
    pub level_two_cells: usize,
    pub level_three_cells: usize,
    pub level_four_cells: usize,
    pub cliff_boundaries: usize,
    pub generated_ramps: usize,
    pub generated_ladders: usize,
    pub guaranteed_plateau: bool,
}

/// Connector-only structural reconciliation for an independently streamed
/// surface partition. Initial world assemblies run `materialize_structural_landforms`
/// across many chunks, but on-demand partitions historically stopped after
/// structural-level normalization. That produced valid cliffs with no generated
/// MountainPath ramp footprints or ladder objects outside the initial assembly.
///
/// This pass deliberately does *not* regenerate the plateau footprint or
/// hydrology. It consumes the already-authoritative structural levels in the
/// generated partition and adds only certified south-facing LPC ramps plus dry
/// inland ladders. The operation is deterministic, idempotent for generated
/// baselines, and never touches player delta snapshots.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct StreamedStructuralAccessReport {
    pub generated_ramps: usize,
    pub generated_ramp_cells: usize,
    pub generated_ladders: usize,
}

pub fn materialize_streamed_structural_access_v1(
    scene: &mut SceneMap,
    seed: u64,
) -> StreamedStructuralAccessReport {
    let width = MAP_W;
    let height = MAP_H;
    let cell_count = width.saturating_mul(height);
    let mut levels = vec![0u8; cell_count];
    let mut ramp_land = vec![false; cell_count];
    let mut protected = vec![false; cell_count];

    for y in 0..MAP_H as i32 {
        for x in 0..MAP_W as i32 {
            let index = y as usize * width + x as usize;
            let tile = scene.map.get(x, y);
            levels[index] = scene.map.get_structural_level(x, y).unwrap_or_else(|| {
                if tile == TileKind::MountainRock { 2 } else { 0 }
            });
            ramp_land[index] = ramp_surface_tile(tile);
            protected[index] = protected_surface_cell(scene, x, y, tile);
        }
    }

    let ramp_edges = choose_or_carve_south_ramp_edges(
        &mut levels,
        &ramp_land,
        &protected,
        width,
        height,
        seed,
    );
    let mut ramp_claimed = vec![false; cell_count];
    let mut report = StreamedStructuralAccessReport::default();

    for (upper_index, lower_index, rises_right) in ramp_edges {
        // `choose_or_carve_south_ramp_edges` is the single corridor authority:
        // it has already carved the exact six source-native levels into
        // `levels`. Do not reinterpret the immediate lower cell here (it is
        // now the authored middle tier); copy the chosen corridor verbatim.
        let corridor = directional_ramp_corridor_indices(
            upper_index,
            lower_index,
            width,
            height,
            rises_right,
        );
        if corridor.len() != 6 {
            continue;
        }
        for index in corridor {
            ramp_claimed[index] = true;
            let x = (index % width) as i32;
            let y = (index / width) as i32;
            scene.map.set_structural_level(x, y, Some(levels[index]));
            if ramp_compatible_tile(scene.map.get(x, y)) {
                scene.map.set(x, y, TileKind::MountainPath);
            }
            report.generated_ramp_cells += 1;
        }
        report.generated_ramps += 1;
    }

    for host_index in choose_inland_ladder_hosts(
        &levels,
        &ramp_land,
        &protected,
        &ramp_claimed,
        width,
        height,
        seed ^ 0x4c41_4444_4552,
    ) {
        let x = (host_index % width) as i32;
        let y = (host_index / width) as i32;
        let already_ladder = scene.map.object_at(x, y).and_then(|index| {
            let object = scene.map.objects.get(index)?;
            (object.kind == ObjectKind::Stairs
                && scene.map.object_state(object.id).is_some_and(|state| state.eq_ignore_ascii_case("ladder")))
                .then_some(())
        }).is_some();
        if already_ladder {
            continue;
        }
        if let Some(id) = scene.map.place_object(ObjectKind::Stairs, x, y) {
            scene.map.set_object_state(id, "ladder");
            report.generated_ladders += 1;
        }
    }

    report
}

pub fn materialize_structural_landforms(
    scenes: &mut [SceneMap],
    chunks: &[ChunkCoord],
    seed: u64,
    mountain_strength: f32,
) -> Result<StructuralLandformReport, String> {
    if scenes.len() != chunks.len() || scenes.is_empty() {
        return Err(format!(
            "structural landform generation requires matching non-empty scene/chunk arrays ({} scenes, {} chunks)",
            scenes.len(),
            chunks.len()
        ));
    }

    let mut scene_by_chunk = BTreeMap::new();
    for (index, chunk) in chunks.iter().copied().enumerate() {
        if scene_by_chunk.insert(chunk, index).is_some() {
            return Err(format!(
                "structural landform generation received duplicate chunk {},{}",
                chunk.x, chunk.y
            ));
        }
    }

    let min_chunk_x = chunks.iter().map(|chunk| chunk.x).min().unwrap_or(0);
    let max_chunk_x = chunks.iter().map(|chunk| chunk.x).max().unwrap_or(0);
    let min_chunk_y = chunks.iter().map(|chunk| chunk.y).min().unwrap_or(0);
    let max_chunk_y = chunks.iter().map(|chunk| chunk.y).max().unwrap_or(0);
    let origin_x = min_chunk_x * MAP_W as i32;
    let origin_y = min_chunk_y * MAP_H as i32;
    let width = usize::try_from((max_chunk_x - min_chunk_x + 1) * MAP_W as i32)
        .map_err(|_| "structural landform width is invalid".to_string())?;
    let height = usize::try_from((max_chunk_y - min_chunk_y + 1) * MAP_H as i32)
        .map_err(|_| "structural landform height is invalid".to_string())?;
    let cell_count = width
        .checked_mul(height)
        .ok_or_else(|| "structural landform grid overflow".to_string())?;

    let local_cell = |global_x: i32, global_y: i32| -> Option<(usize, i32, i32)> {
        let chunk = ChunkCoord::new(
            global_x.div_euclid(MAP_W as i32),
            global_y.div_euclid(MAP_H as i32),
        );
        let scene_index = *scene_by_chunk.get(&chunk)?;
        Some((
            scene_index,
            global_x.rem_euclid(MAP_W as i32),
            global_y.rem_euclid(MAP_H as i32),
        ))
    };

    let mut present = vec![false; cell_count];
    let mut land = vec![false; cell_count];
    let mut ramp_land = vec![false; cell_count];
    let mut marine_shore = vec![false; cell_count];
    let mut protected = vec![false; cell_count];
    let mut raw_heights = vec![0u8; cell_count];
    let mut geographic_levels = vec![0u8; cell_count];

    for grid_y in 0..height {
        for grid_x in 0..width {
            let index = grid_y * width + grid_x;
            let global_x = origin_x + grid_x as i32;
            let global_y = origin_y + grid_y as i32;
            let Some((scene_index, x, y)) = local_cell(global_x, global_y) else {
                continue;
            };
            present[index] = true;
            let scene = &scenes[scene_index];
            let tile = scene.map.get(x, y);
            let is_land = structural_land_tile(tile);
            land[index] = is_land;
            // Freshwater remains structural land for elevation/waterfalls, but
            // it is never a legal generated ramp corridor. Otherwise connector
            // selection can stamp a dry mountain ramp through a river simply
            // because both cells share valid structural levels.
            ramp_land[index] = is_land && ramp_surface_tile(tile);
            marine_shore[index] = marine_shore_tile(tile);
            raw_heights[index] = scene.map.get_height(x, y);
            protected[index] = is_land && protected_surface_cell(scene, x, y, tile);
        }
    }

    let protected_sources = protected
        .iter()
        .enumerate()
        .filter_map(|(index, value)| value.then_some(index))
        .collect::<Vec<_>>();
    for index in protected_sources {
        let center_x = (index % width) as i32;
        let center_y = (index / width) as i32;
        for offset_y in -PROTECTED_BUFFER_RADIUS..=PROTECTED_BUFFER_RADIUS {
            for offset_x in -PROTECTED_BUFFER_RADIUS..=PROTECTED_BUFFER_RADIUS {
                let x = center_x + offset_x;
                let y = center_y + offset_y;
                if x < 0 || y < 0 || x >= width as i32 || y >= height as i32 {
                    continue;
                }
                protected[y as usize * width + x as usize] = true;
            }
        }
    }

    let strength = mountain_strength.clamp(0.0, 1.0) as f64;

    // Z108/H20/H21A14AC1: visible structural topology comes from finite
    // macro-geographic features, never from thresholded raw noise. First resolve
    // one broad raised mask and clean its contour as a binary shape. The final
    // height grammar is applied after contour cleanup: outer inland terrain is
    // Level 2 and sufficiently broad nested highland cores rise to Level 4.
    let mut raised_candidates = vec![false; cell_count];
    for grid_y in 0..height {
        for grid_x in 0..width {
            let index = grid_y * width + grid_x;
            if !present[index] || !land[index] || protected[index] {
                continue;
            }
            let global_x = origin_x + grid_x as i32;
            let global_y = origin_y + grid_y as i32;
            let geographic_level =
                geographic_structural_level(seed, global_x, global_y, mountain_strength);
            geographic_levels[index] = geographic_level;
            raised_candidates[index] = geographic_level >= 1;
        }
    }

    let raised_mask = retain_broad_candidates(
        &raised_candidates,
        &present,
        &land,
        &protected,
        width,
        height,
        2,
        56,
    );
    let mut levels = raised_mask
        .iter()
        .map(|raised| u8::from(*raised))
        .collect::<Vec<_>>();

    // Clean only the binary footprint. Running the old nested Level-1/Level-2
    // normalization created one-high inland shoulders around every plateau,
    // which is visually incompatible with the complete two-tier LPC ramp.
    fill_small_structural_holes(&mut levels, &land, &protected, width, height);
    normalize_structural_contours(&mut levels, &land, &protected, width, height);

    let mut guaranteed_plateau = false;
    if count_boundaries(&levels, &present, width, height) == 0 {
        if let Some(best_index) = best_plateau_anchor(&raw_heights, &land, &protected) {
            for (index, level) in levels.iter_mut().enumerate() {
                if present[index] {
                    *level = 0;
                }
            }
            stamp_guaranteed_plateau(
                &mut levels,
                &land,
                &protected,
                width,
                height,
                best_index,
                strength,
            );
            guaranteed_plateau = true;
        }
    }

    let shore_distance = shoreline_distance_cells(
        &marine_shore,
        &present,
        width,
        height,
        COASTAL_CORE_CLEARANCE_CELLS.saturating_add(6),
    );

    // H21A14AC1: retain the cleaned outer raised footprint, then materialize a
    // genuinely nested highland core. Normal inland cliffs use a 0->2 step; a
    // broad geographic core rises again from 2->4. Skipping generic Level 3
    // keeps one-high walls out of the world while still allowing Level 3 as the
    // reserved middle of a certified 4->3->2 ramp corridor.
    let raised_footprint = levels.iter().map(|level| *level > 0).collect::<Vec<_>>();
    // Keep a real Level-2 shoulder around every Level-4 core. Without this
    // interior-distance guard, contour cleanup could let a geographic core kiss
    // outer lowland and create an unintended 4->0 wall that has no certified
    // single-ramp traversal grammar.
    let raised_lowland_sources = present
        .iter()
        .enumerate()
        .map(|(index, is_present)| *is_present && !raised_footprint[index])
        .collect::<Vec<_>>();
    let raised_interior_distance = shoreline_distance_cells(
        &raised_lowland_sources,
        &present,
        width,
        height,
        8,
    );
    let core_candidates = geographic_levels
        .iter()
        .enumerate()
        .map(|(index, level)| {
            *level >= 2
                && raised_footprint[index]
                && raised_interior_distance[index] > 4
                && shore_distance[index] > COASTAL_CORE_CLEARANCE_CELLS.saturating_add(4)
        })
        .collect::<Vec<_>>();
    let core_land = raised_footprint.clone();
    let core_mask = retain_broad_candidates(
        &core_candidates,
        &present,
        &core_land,
        &protected,
        width,
        height,
        2,
        60,
    );
    let mut core_levels = core_mask
        .iter()
        .map(|core| u8::from(*core))
        .collect::<Vec<_>>();
    fill_small_structural_holes(&mut core_levels, &core_land, &protected, width, height);
    normalize_structural_contours(&mut core_levels, &core_land, &protected, width, height);
    for (index, core_level) in core_levels.iter_mut().enumerate() {
        if raised_interior_distance[index] <= 3 {
            *core_level = 0;
        }
    }

    for (index, level) in levels.iter_mut().enumerate() {
        if *level == 0 {
            continue;
        }
        // Source-native cliff grammar: generated terrain owns only even
        // platform levels. Level 1 and Level 3 are introduced later only by
        // the exact six-cell LPC ramp corridor (2->1->0 or 4->3->2). This
        // removes the old generic one-high coastal shelf that had no matching
        // certified cliff/ramp presentation and could become an invisible or
        // visually inconsistent barrier.
        *level = if core_levels[index] > 0 { 4 } else { 2 };
    }

    // Certified directional ramps bridge exact two-level drops. This applies
    // both to the outer 2->0 wall and to a nested 4->2 highland wall. The only
    // odd structural level introduced is the ramp's own middle lane.
    let ramp_edges = choose_or_carve_south_ramp_edges(
        &mut levels,
        &ramp_land,
        &protected,
        width,
        height,
        seed,
    );
    let mut ramp_claimed = vec![false; cell_count];
    for (upper_index, lower_index, rises_right) in &ramp_edges {
        // The chooser has already carved the exact corridor. This pass only
        // claims its six cells so ladder placement cannot compete with it.
        let corridor = directional_ramp_corridor_indices(
            *upper_index,
            *lower_index,
            width,
            height,
            *rises_right,
        );
        for index in corridor {
            ramp_claimed[index] = true;
        }
    }

    let mut report = StructuralLandformReport {
        guaranteed_plateau,
        ..StructuralLandformReport::default()
    };

    for grid_y in 0..height {
        for grid_x in 0..width {
            let index = grid_y * width + grid_x;
            if !present[index] {
                continue;
            }
            let global_x = origin_x + grid_x as i32;
            let global_y = origin_y + grid_y as i32;
            let Some((scene_index, x, y)) = local_cell(global_x, global_y) else {
                continue;
            };
            let level = levels[index];
            scenes[scene_index]
                .map
                .set_structural_level(x, y, Some(level));

            // Material and topology share the same geographic authority. A
            // protected road/civic cut can clip a raised feature after the
            // pre-road material pass, so normalize stale Rock Ground back to
            // ordinary grass outside true raised cells. Conversely, ensure
            // surviving Level-2/Level-4 terrain is visibly Rock Ground.
            let tile = scenes[scene_index].map.get(x, y);
            if level >= 2
                && matches!(tile, TileKind::Grass | TileKind::TallGrass | TileKind::Dirt)
            {
                scenes[scene_index].map.set(x, y, TileKind::MountainRock);
            } else if level < 2
                && tile == TileKind::MountainRock
                && scene_zone_allows_geographic_material_normalization(
                    scenes[scene_index].zone_at(x, y),
                )
            {
                scenes[scene_index].map.set(x, y, TileKind::Grass);
            }

            match level {
                0 => report.level_zero_cells += 1,
                1 => report.level_one_cells += 1,
                2 => report.level_two_cells += 1,
                3 => report.level_three_cells += 1,
                4 => report.level_four_cells += 1,
                _ => {}
            }
        }
    }

    for (upper_index, lower_index, rises_right) in ramp_edges {
        let corridor = directional_ramp_corridor_indices(
            upper_index,
            lower_index,
            width,
            height,
            rises_right,
        );
        for index in corridor {
            let grid_x = index % width;
            let grid_y = index / width;
            let global_x = origin_x + grid_x as i32;
            let global_y = origin_y + grid_y as i32;
            let Some((scene_index, x, y)) = local_cell(global_x, global_y) else {
                continue;
            };
            if ramp_compatible_tile(scenes[scene_index].map.get(x, y)) {
                scenes[scene_index].map.set(x, y, TileKind::MountainPath);
            }
        }
        report.generated_ramps += 1;
    }

    // Dry inland true cliffs receive ladder access in addition to ramps. The
    // selector requires an exact straight south face and stays clear of authored
    // ramp footprints, so the runtime's certified ladder overlay remains valid.
    for host_index in choose_inland_ladder_hosts(
        &levels,
        &ramp_land,
        &protected,
        &ramp_claimed,
        width,
        height,
        seed ^ 0x4c41_4444_4552,
    ) {
        let grid_x = host_index % width;
        let grid_y = host_index / width;
        let global_x = origin_x + grid_x as i32;
        let global_y = origin_y + grid_y as i32;
        let Some((scene_index, x, y)) = local_cell(global_x, global_y) else {
            continue;
        };
        if let Some(id) = scenes[scene_index].map.place_object(ObjectKind::Stairs, x, y) {
            scenes[scene_index].map.set_object_state(id, "ladder");
            report.generated_ladders += 1;
        }
    }

    // Water-facing cliff access remains reserved for the natural vine/climb
    // lane; this selector intentionally returns no constructed ladders.
    for host_index in choose_shoreline_ladder_hosts(
        &levels,
        &marine_shore,
        &present,
        &protected,
        width,
        height,
        seed,
    ) {
        let grid_x = host_index % width;
        let grid_y = host_index / width;
        let global_x = origin_x + grid_x as i32;
        let global_y = origin_y + grid_y as i32;
        let Some((scene_index, x, y)) = local_cell(global_x, global_y) else {
            continue;
        };
        if let Some(id) = scenes[scene_index].map.place_object(ObjectKind::Stairs, x, y) {
            scenes[scene_index].map.set_object_state(id, "ladder");
            report.generated_ladders += 1;
        }
    }

    report.cliff_boundaries = count_boundaries(&levels, &present, width, height);
    Ok(report)
}

fn scene_zone_allows_geographic_material_normalization(zone: ZoneKind) -> bool {
    matches!(zone, ZoneKind::None)
}

fn structural_land_tile(tile: TileKind) -> bool {
    // Inland freshwater remains attached to the structural surface beneath it.
    // That is what lets a river/pool on Level 2 continue across Level 2->1->0
    // boundaries and produce required waterfall connectors. Marine water and
    // shoreline presentation remain Level 0.
    !matches!(
        tile,
        TileKind::OceanDeep
            | TileKind::OceanShallow
            | TileKind::RiverMouthBlend
            | TileKind::Sand
            | TileKind::WetSand
            | TileKind::PebbleShore
            | TileKind::MudBank
            | TileKind::ShoreFoam
            | TileKind::Cliff
            | TileKind::Wall
            | TileKind::CaveWall
    )
}

fn protected_surface_cell(scene: &SceneMap, x: i32, y: i32, tile: TileKind) -> bool {
    !matches!(scene.zone_at(x, y), ZoneKind::None | ZoneKind::Cave)
        || matches!(
            tile,
            TileKind::Road
                | TileKind::StonePath
                | TileKind::Bridge
                | TileKind::WoodFloor
                | TileKind::PlankFloor
                | TileKind::StoneFloor
                | TileKind::BrickFloor
        )
}

fn ramp_surface_tile(tile: TileKind) -> bool {
    matches!(
        tile,
        TileKind::Grass | TileKind::TallGrass | TileKind::Dirt | TileKind::MountainRock | TileKind::MountainPath
    )
}

fn ramp_compatible_tile(tile: TileKind) -> bool {
    matches!(
        tile,
        TileKind::Grass
            | TileKind::TallGrass
            | TileKind::Dirt
            | TileKind::MountainRock
            | TileKind::MountainPath
    )
}

fn best_plateau_anchor(raw_heights: &[u8], land: &[bool], protected: &[bool]) -> Option<usize> {
    raw_heights
        .iter()
        .copied()
        .enumerate()
        .filter(|(index, _)| land[*index] && !protected[*index])
        .max_by_key(|(_, height)| *height)
        .map(|(index, _)| index)
}

fn stamp_guaranteed_plateau(
    levels: &mut [u8],
    land: &[bool],
    protected: &[bool],
    width: usize,
    height: usize,
    center_index: usize,
    _strength: f64,
) {
    let center_x = (center_index % width) as i32;
    let center_y = (center_index / width) as i32;

    // The fallback stamps only the binary raised footprint. The final
    // inland/coastal height policy promotes this to Level 2 or Level 1 after
    // contour cleanup, so the fallback cannot reintroduce an inland one-high
    // cliff shoulder.
    for offset_x in -GUARANTEE_RADIUS_X..=GUARANTEE_RADIUS_X {
        let bend_y = if offset_x < 0 { offset_x / 4 } else { offset_x / 6 };
        for shoulder in -GUARANTEE_RADIUS_Y..=GUARANTEE_RADIUS_Y {
            let x = center_x + offset_x;
            let y = center_y + bend_y + shoulder;
            if x < 0 || y < 0 || x >= width as i32 || y >= height as i32 {
                continue;
            }
            let end_taper = (offset_x.abs() - (GUARANTEE_RADIUS_X - 3)).max(0);
            if shoulder.abs() + end_taper > GUARANTEE_RADIUS_Y {
                continue;
            }
            let index = y as usize * width + x as usize;
            if land[index] && !protected[index] {
                levels[index] = 1;
            }
        }
    }
}

fn count_boundaries(levels: &[u8], present: &[bool], width: usize, height: usize) -> usize {
    let mut boundaries = 0usize;
    for y in 0..height {
        for x in 0..width {
            let index = y * width + x;
            if !present[index] {
                continue;
            }
            if x + 1 < width {
                let east = index + 1;
                boundaries += usize::from(present[east] && levels[index] != levels[east]);
            }
            if y + 1 < height {
                let south = index + width;
                boundaries += usize::from(present[south] && levels[index] != levels[south]);
            }
        }
    }
    boundaries
}

#[cfg(test)]
mod tests {
    use super::*;
    use haven_core::{ProjectSceneId, SceneBiome, SceneKind};

    fn scene(id: &str, height: u8) -> SceneMap {
        let mut scene = SceneMap::blank(
            ProjectSceneId::new(id),
            id,
            SceneKind::Exterior,
            SceneBiome::Temperate,
        );
        scene.map.tiles.fill(TileKind::Grass);
        scene.map.heights.fill(height);
        scene
    }

    #[test]
    fn streamed_access_materializer_uses_only_source_native_ramp_tiers() {
        let mut scene = scene("pcg_streamed_access_0_0", 64);
        for y in 10..=28 {
            for x in 10..=40 {
                scene.map.set(x, y, TileKind::MountainRock);
                scene.map.set_structural_level(x, y, Some(2));
            }
        }
        for y in 29..MAP_H as i32 {
            for x in 0..MAP_W as i32 {
                scene.map.set_structural_level(x, y, Some(0));
            }
        }

        let report = materialize_streamed_structural_access_v1(&mut scene, 0xACCE_5501);
        assert!(
            report.generated_ramps > 0,
            "a broad dry 2->0 south face should receive a certified LPC ramp"
        );
        assert!(report.generated_ramp_cells >= 6);
        for y in 0..MAP_H as i32 {
            for x in 0..MAP_W as i32 {
                if matches!(scene.map.get_structural_level(x, y), Some(1) | Some(3)) {
                    assert_eq!(
                        scene.map.get(x, y),
                        TileKind::MountainPath,
                        "odd structural levels are connector-local and must use MountainPath"
                    );
                }
            }
        }
    }

    #[test]
    fn fresh_surface_materializes_explicit_structural_levels() {
        let mut scenes = vec![scene("pcg_test_0_0", 190)];
        let report =
            materialize_structural_landforms(&mut scenes, &[ChunkCoord::new(0, 0)], 19, 0.60)
                .expect("landforms");

        assert!(report.level_two_cells > 0);
        assert!(
            report.level_four_cells > 0,
            "seed 19 should retain a broad nested highland core"
        );
        assert!(scenes[0]
            .map
            .structural_levels
            .iter()
            .all(|level| *level <= haven_core::MAX_STRUCTURAL_LEVEL));
        for y in 0..MAP_H as i32 {
            for x in 0..MAP_W as i32 {
                if scenes[0].map.get_structural_level(x, y) != Some(4) {
                    continue;
                }
                for (dx, dy) in [(0, -1), (1, 0), (0, 1), (-1, 0)] {
                    let nx = x + dx;
                    let ny = y + dy;
                    if !(0..MAP_W as i32).contains(&nx) || !(0..MAP_H as i32).contains(&ny) {
                        continue;
                    }
                    assert_ne!(
                        scenes[0].map.get_structural_level(nx, ny),
                        Some(0),
                        "Level-4 highland core touched Level-0 lowland at {x},{y} -> {nx},{ny}"
                    );
                }
            }
        }
    }

    #[test]
    fn flat_world_still_receives_a_deterministic_cliff_plateau() {
        let mut scenes = vec![scene("pcg_test_0_0", 96)];
        let report =
            materialize_structural_landforms(&mut scenes, &[ChunkCoord::new(0, 0)], 23, 0.25)
                .expect("landforms");

        assert!(report.guaranteed_plateau);
        assert!(report.cliff_boundaries > 0);
        assert!(report.level_two_cells > 0);
    }

    #[test]
    fn directional_ramp_corridors_follow_the_authored_six_cell_diagonals() {
        let width = 7;
        let height = 7;
        let upper = 2 * width + 3;
        let lower = upper + width;

        let rise_right = directional_ramp_corridor_indices(upper, lower, width, height, true);
        let rise_left = directional_ramp_corridor_indices(upper, lower, width, height, false);

        let coords = |indices: Vec<usize>| {
            indices
                .into_iter()
                .map(|index| (index % width, index / width))
                .collect::<Vec<_>>()
        };
        assert_eq!(
            coords(rise_right),
            vec![(4, 1), (4, 2), (3, 2), (3, 3), (2, 3), (2, 4)]
        );
        assert_eq!(
            coords(rise_left),
            vec![(2, 1), (2, 2), (3, 2), (3, 3), (4, 3), (4, 4)]
        );
    }

    #[test]
    fn directional_ramp_orientation_requires_the_complete_authored_level_footprint() {
        let width = 7;
        let height = 7;
        let upper = 2 * width + 3;
        let lower = upper + width;
        let mut levels = vec![0u8; width * height];
        let land = vec![true; levels.len()];
        let protected = vec![false; levels.len()];

        for (step, index) in directional_ramp_corridor_indices(upper, lower, width, height, true)
            .into_iter()
            .enumerate()
        {
            levels[index] = if step <= 2 { 2 } else { 0 };
        }
        assert_eq!(
            directional_ramp_orientation_for_candidate(
                upper, lower, &levels, &land, &protected, width, height, 7
            ),
            Some(true)
        );

        let blocked = 1 * width + 4;
        let mut protected_blocked = protected.clone();
        protected_blocked[blocked] = true;
        assert_eq!(
            directional_ramp_orientation_for_candidate(
                upper, lower, &levels, &land, &protected_blocked, width, height, 7
            ),
            None
        );
    }

    #[test]
    fn each_disconnected_raised_component_receives_a_south_gateway() {
        let width = 12;
        let height = 6;
        let mut levels = vec![0u8; width * height];

        // Two disconnected Level-2 plateaus drop directly to Level 0.
        // Selected gateways carve their own Level-1 middle cells later.
        for y in 1..=2 {
            for x in 2..=4 {
                levels[y * width + x] = 2;
            }
            for x in 7..=9 {
                levels[y * width + x] = 2;
            }
        }

        let land = vec![true; levels.len()];
        let protected = vec![false; levels.len()];
        let ramps = choose_south_ramp_edges(&levels, &land, &protected, width, height, 0x51f7);

        let left_component_has_gateway = ramps.iter().any(|(upper, _, _)| {
            let x = *upper % width;
            let y = *upper / width;
            (2..=4).contains(&x) && (1..=2).contains(&y)
        });
        let right_component_has_gateway = ramps.iter().any(|(upper, _, _)| {
            let x = *upper % width;
            let y = *upper / width;
            (7..=9).contains(&x) && (1..=2).contains(&y)
        });

        assert!(
            left_component_has_gateway,
            "left disconnected raised component did not receive a south gateway: {ramps:?}"
        );
        assert!(
            right_component_has_gateway,
            "right disconnected raised component did not receive a south gateway: {ramps:?}"
        );
    }

    #[test]
    fn shoreline_ladder_generation_fails_closed_for_water_facing_relief() {
        let width = 7;
        let height = 5;
        let mut levels = vec![0_u8; width * height];
        let mut marine = vec![false; width * height];
        let present = vec![true; width * height];
        let protected = vec![false; width * height];

        for x in 1..=5 {
            levels[1 * width + x] = 1;
            marine[2 * width + x] = true;
        }
        assert!(choose_shoreline_ladder_hosts(
            &levels,
            &marine,
            &present,
            &protected,
            width,
            height,
            0x51,
        )
        .is_empty());

        // A true water-facing cliff also does not receive a constructed ladder;
        // NaturalVine is the reserved connector policy for that host class.
        levels[1 * width + 3] = 2;
        assert!(choose_shoreline_ladder_hosts(
            &levels,
            &marine,
            &present,
            &protected,
            width,
            height,
            0x51,
        )
        .is_empty());
    }

    #[test]
    fn public_paths_are_kept_out_of_structural_cliff_boundaries() {
        let mut scene = scene("pcg_test_0_0", 190);
        for y in 0..MAP_H as i32 {
            scene.map.set(MAP_W as i32 / 2, y, TileKind::Road);
            scene.set_zone(MAP_W as i32 / 2, y, ZoneKind::PublicPath);
        }
        let mut scenes = vec![scene];
        materialize_structural_landforms(&mut scenes, &[ChunkCoord::new(0, 0)], 29, 0.60)
            .expect("landforms");

        let road_x = MAP_W as i32 / 2;
        for y in 0..MAP_H as i32 {
            for offset_x in -PROTECTED_BUFFER_RADIUS..=PROTECTED_BUFFER_RADIUS {
                let x = road_x + offset_x;
                if (0..MAP_W as i32).contains(&x) {
                    assert_eq!(scenes[0].map.get_structural_level(x, y), Some(0));
                }
            }
        }
    }

}
