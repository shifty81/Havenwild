use super::{BuildingLevelDefinition, BuildingRecipeDefinition, BuildingRecipePiece, BuildingRecipePieceKind, BuildingWallEdge};
use crate::placeable_asset_registry::{
    PublishedWorldAssetCertification, PublishedWorldAssetRegistry, PublishedWorldAssetRole,
};
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq, Default)]
#[serde(rename_all = "snake_case")]
pub enum BuildingFurnishingKind {
    #[default]
    Furniture,
    Fixture,
    WallMounted,
    Workstation,
    Container,
    Decoration,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct BuildingInteractionSocket {
    pub id: String,
    pub purpose: String,
    #[serde(default)]
    pub offset: [i32; 2],
    #[serde(default)]
    pub reservation: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct BuildingFurnishingPlacement {
    pub id: String,
    #[serde(default)]
    pub asset_id: Option<String>,
    pub room_id: String,
    pub tile: [i32; 2],
    #[serde(default)]
    pub kind: BuildingFurnishingKind,
    #[serde(default)]
    pub state: Option<String>,
    #[serde(default)]
    pub wall_attachment: Option<BuildingWallEdge>,
    #[serde(default)]
    pub visual_status: String,
    #[serde(default)]
    pub blocks_navigation: bool,
    #[serde(default)]
    pub interaction_sockets: Vec<BuildingInteractionSocket>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq, Default)]
#[serde(rename_all = "camelCase")]
pub struct BuildingLevelNavigation {
    #[serde(default)]
    pub walkable_rects: Vec<[i32; 4]>,
    #[serde(default)]
    pub blocked_tiles: Vec<[i32; 2]>,
    /// Tiles reserved for mandatory circulation such as entry -> room access.
    /// Blocking furnishings may not occupy these cells.
    #[serde(default)]
    pub protected_tiles: Vec<[i32; 2]>,
}

impl BuildingRecipeDefinition {
    pub fn furnishing(&self, furnishing_id: &str) -> Option<(i32, &BuildingFurnishingPlacement)> {
        self.levels.iter().find_map(|level| {
            level
                .furnishings
                .iter()
                .find(|furnishing| furnishing.id == furnishing_id)
                .map(|furnishing| (level.level, furnishing))
        })
    }

    pub fn furnishing_at(
        &self,
        level_number: i32,
        local_tile: [i32; 2],
    ) -> Option<&BuildingFurnishingPlacement> {
        self.level(level_number)?
            .furnishings
            .iter()
            .find(|furnishing| furnishing.tile == local_tile)
    }

    pub fn furnishing_asset_ids(&self) -> BTreeSet<&str> {
        self.levels
            .iter()
            .flat_map(|level| level.furnishings.iter())
            .filter_map(|furnishing| furnishing.asset_id.as_deref())
            .collect()
    }
}

pub(super) fn materialize_level_furnishings(
    recipe_id: &str,
    level: &BuildingLevelDefinition,
) -> Vec<BuildingRecipePiece> {
    level
        .furnishings
        .iter()
        .filter_map(|furnishing| {
            let asset_id = furnishing.asset_id.as_ref()?;
            Some(BuildingRecipePiece {
                id: format!("{}:furnishing:{}", recipe_id, furnishing.id),
                kind: BuildingRecipePieceKind::Furnishing,
                asset_id: asset_id.clone(),
                level: level.level,
                tile: furnishing.tile,
                state: furnishing.state.clone(),
                occlusion_group: Some(format!("building.interior.level.{}", level.level)),
                render_origin_px: None,
            })
        })
        .collect()
}

pub(super) fn validate_level_interior(
    recipe: &BuildingRecipeDefinition,
    level: &BuildingLevelDefinition,
    room_ids: &BTreeSet<&str>,
    furnishing_ids: &mut BTreeSet<String>,
    errors: &mut Vec<String>,
) {
    for rect in &level.navigation.walkable_rects {
        validate_local_rect(recipe, *rect, "navigation walkable rect", errors);
    }
    for tile in &level.navigation.blocked_tiles {
        validate_local_tile(recipe, *tile, "navigation blocked tile", errors);
    }
    for tile in &level.navigation.protected_tiles {
        validate_local_tile(recipe, *tile, "navigation protected tile", errors);
        if level.navigation.blocked_tiles.iter().any(|blocked| blocked == tile) {
            errors.push(format!(
                "{} level {} marks protected navigation tile {:?} as blocked",
                recipe.id, level.id, tile
            ));
        }
    }
    for furnishing in &level.furnishings {
        if furnishing.id.trim().is_empty() {
            errors.push(format!("{} level {} has an empty furnishing id", recipe.id, level.id));
            continue;
        }
        if !furnishing_ids.insert(furnishing.id.clone()) {
            errors.push(format!("{} duplicates furnishing id {}", recipe.id, furnishing.id));
        }
        if !room_ids.contains(furnishing.room_id.as_str()) {
            errors.push(format!(
                "{} furnishing {} references unknown room {} on level {}",
                recipe.id, furnishing.id, furnishing.room_id, level.id
            ));
        }
        validate_local_tile(recipe, furnishing.tile, &format!("furnishing {}", furnishing.id), errors);
        if let Some(room) = level.rooms.iter().find(|room| room.id == furnishing.room_id) {
            let anchor_is_in_room = rect_contains(room.rect, furnishing.tile);
            let anchor_is_on_declared_wall = furnishing.kind == BuildingFurnishingKind::WallMounted
                && furnishing
                    .wall_attachment
                    .is_some_and(|edge| wall_attachment_matches_room_boundary(room.rect, furnishing.tile, edge));
            if !anchor_is_in_room && !anchor_is_on_declared_wall {
                errors.push(format!(
                    "{} furnishing {} anchor {:?} lies outside declared room {}",
                    recipe.id, furnishing.id, furnishing.tile, furnishing.room_id
                ));
            }
        }
        if furnishing.blocks_navigation
            && level
                .navigation
                .protected_tiles
                .iter()
                .any(|tile| *tile == furnishing.tile)
        {
            errors.push(format!(
                "{} furnishing {} blocks protected circulation tile {:?}",
                recipe.id, furnishing.id, furnishing.tile
            ));
        }
        if furnishing.asset_id.is_none() && furnishing.visual_status != "deferred_exact_source" {
            errors.push(format!(
                "{} furnishing {} has no asset and is not deferred_exact_source",
                recipe.id, furnishing.id
            ));
        }
        if furnishing.asset_id.is_some() && furnishing.visual_status == "deferred_exact_source" {
            errors.push(format!(
                "{} furnishing {} declares an asset while marked deferred_exact_source",
                recipe.id, furnishing.id
            ));
        }
        if furnishing.kind == BuildingFurnishingKind::WallMounted && furnishing.wall_attachment.is_none() {
            errors.push(format!(
                "{} wall-mounted furnishing {} requires wallAttachment",
                recipe.id, furnishing.id
            ));
        }
        let mut socket_ids = BTreeSet::new();
        for socket in &furnishing.interaction_sockets {
            if socket.id.trim().is_empty() || socket.purpose.trim().is_empty() {
                errors.push(format!("{} furnishing {} has an incomplete interaction socket", recipe.id, furnishing.id));
            }
            if !socket_ids.insert(socket.id.as_str()) {
                errors.push(format!("{} furnishing {} duplicates socket {}", recipe.id, furnishing.id, socket.id));
            }
        }
    }
}

pub(super) fn validate_interior_assets(
    recipe: &BuildingRecipeDefinition,
    assets: &PublishedWorldAssetRegistry,
    errors: &mut Vec<String>,
) {
    for level in &recipe.levels {
        for furnishing in &level.furnishings {
            let Some(asset_id) = furnishing.asset_id.as_deref() else { continue; };
            let Some(asset) = assets.resolve_alias(asset_id) else {
                errors.push(format!("{} furnishing {} references unknown PublishedWorldAsset {}", recipe.id, furnishing.id, asset_id));
                continue;
            };
            if matches!(
                asset.certification,
                PublishedWorldAssetCertification::Rejected
                    | PublishedWorldAssetCertification::Missing
                    | PublishedWorldAssetCertification::Placeholder
            ) {
                errors.push(format!(
                    "{} furnishing {} references unusable PublishedWorldAsset {} ({:?})",
                    recipe.id, furnishing.id, asset_id, asset.certification
                ));
            }
            match furnishing.kind {
                BuildingFurnishingKind::WallMounted => {
                    if asset.structure.is_none() && !matches!(&asset.role, PublishedWorldAssetRole::Placeable) {
                        errors.push(format!("{} wall-mounted furnishing {} has incompatible asset role", recipe.id, furnishing.id));
                    }
                }
                _ => {
                    if !matches!(&asset.role, PublishedWorldAssetRole::Placeable | PublishedWorldAssetRole::StructureComponent) {
                        errors.push(format!("{} furnishing {} has incompatible asset role {:?}", recipe.id, furnishing.id, &asset.role));
                    }
                }
            }
            if let Some(state) = furnishing.state.as_deref() {
                if !asset.supports_state(state) {
                    errors.push(format!("{} furnishing {} uses unsupported state {} for {}", recipe.id, furnishing.id, state, asset_id));
                }
            }
            if furnishing.blocks_navigation {
                let state = furnishing.state.as_deref().or_else(|| asset.initial_state());
                let footprint = asset.footprint_for_state(state);
                if footprint.blocks_movement {
                    for yy in 0..footprint.collision_h.max(0) {
                        for xx in 0..footprint.collision_w.max(0) {
                            let tile = [
                                furnishing.tile[0] + footprint.collision_offset_x + xx,
                                furnishing.tile[1] + footprint.collision_offset_y + yy,
                            ];
                            if level.navigation.protected_tiles.iter().any(|protected| *protected == tile) {
                                errors.push(format!(
                                    "{} furnishing {} collision footprint reaches protected circulation tile {:?}",
                                    recipe.id, furnishing.id, tile
                                ));
                            }
                            if !navigation_allows(level, tile) {
                                errors.push(format!(
                                    "{} furnishing {} collision footprint occupies non-walkable tile {:?}",
                                    recipe.id, furnishing.id, tile
                                ));
                            }
                        }
                    }
                }
            }
        }
    }
}

pub(crate) fn navigation_allows(level: &BuildingLevelDefinition, local_tile: [i32; 2]) -> bool {
    if level.navigation.blocked_tiles.iter().any(|tile| *tile == local_tile) {
        return false;
    }
    if level.navigation.walkable_rects.is_empty() {
        return true;
    }
    level.navigation.walkable_rects.iter().any(|rect| rect_contains(*rect, local_tile))
}

fn validate_local_rect(
    recipe: &BuildingRecipeDefinition,
    rect: [i32; 4],
    label: &str,
    errors: &mut Vec<String>,
) {
    let [x, y, w, h] = rect;
    if x < 0 || y < 0 || w <= 0 || h <= 0 || x + w > recipe.footprint[0] as i32 || y + h > recipe.footprint[1] as i32 {
        errors.push(format!("{} {} exceeds recipe footprint or is invalid", recipe.id, label));
    }
}

fn validate_local_tile(
    recipe: &BuildingRecipeDefinition,
    tile: [i32; 2],
    label: &str,
    errors: &mut Vec<String>,
) {
    if tile[0] < 0 || tile[1] < 0 || tile[0] >= recipe.footprint[0] as i32 || tile[1] >= recipe.footprint[1] as i32 {
        errors.push(format!("{} {} lies outside recipe footprint", recipe.id, label));
    }
}

fn rect_contains(rect: [i32; 4], tile: [i32; 2]) -> bool {
    tile[0] >= rect[0]
        && tile[1] >= rect[1]
        && tile[0] < rect[0] + rect[2]
        && tile[1] < rect[1] + rect[3]
}

/// Wall-mounted furnishings are authored against the structural wall line rather
/// than forced into the room's walkable rectangle.  A south-wall sign, for
/// example, legitimately lives at `room.y + room.h` while still belonging to
/// that room.  Keep ordinary furnishings inside the room, but permit a
/// wall-mounted anchor on the one-cell boundary named by `wallAttachment`.
fn wall_attachment_matches_room_boundary(
    rect: [i32; 4],
    tile: [i32; 2],
    edge: BuildingWallEdge,
) -> bool {
    let [x, y, w, h] = rect;
    let in_horizontal_span = tile[0] >= x && tile[0] < x + w;
    let in_vertical_span = tile[1] >= y && tile[1] < y + h;
    match edge {
        BuildingWallEdge::North => in_horizontal_span && tile[1] == y - 1,
        BuildingWallEdge::East => in_vertical_span && tile[0] == x + w,
        BuildingWallEdge::South => in_horizontal_span && tile[1] == y + h,
        BuildingWallEdge::West => in_vertical_span && tile[0] == x - 1,
        BuildingWallEdge::Interior => false,
    }
}

/// Fully materialized linked interior shared by the native editor and runtime.
/// The exterior BuildingInstance remains intact; entering the exterior threshold
/// transitions into this compact void-backed EnclosedScene.
#[derive(Clone, Debug)]
pub struct LinkedBuildingInteriorScene {
    pub scene: haven_core::SceneMap,
    pub entry_threshold: [i32; 2],
}

/// Stable linked-interior identity for one BuildingInstance. Including the
/// instance id prevents multiple copies of one recipe from sharing mutable rooms.
pub fn linked_interior_scene_id(
    source_scene_id: &haven_core::ProjectSceneId,
    instance_id: &str,
) -> haven_core::ProjectSceneId {
    fn normalized(value: &str) -> String {
        let mut out = String::with_capacity(value.len());
        let mut separator = false;
        for ch in value.chars() {
            if ch.is_ascii_alphanumeric() {
                out.push(ch.to_ascii_lowercase());
                separator = false;
            } else if !separator {
                out.push('_');
                separator = true;
            }
        }
        out.trim_matches('_').to_string()
    }
    haven_core::ProjectSceneId::new(format!(
        "{}_{}_interior",
        normalized(source_scene_id.code()),
        normalized(instance_id)
    ))
}

/// Converts the canonical BuildingRecipe level into the same semantic interior
/// scene for editor and game runtime: floor fills, blocking interior walls,
/// doorway cuts, published animated doors and furnishings all come from the
/// recipe. Unused backing remains wall/void through EnclosedScene authority.
pub fn materialize_linked_building_interior(
    recipe: &BuildingRecipeDefinition,
    level: &BuildingLevelDefinition,
    placeables: &PublishedWorldAssetRegistry,
    source_scene_id: &haven_core::ProjectSceneId,
    source_scene_name: &str,
    instance_id: &str,
    entry_x: i32,
) -> Result<LinkedBuildingInteriorScene, String> {
    use haven_core::{EnclosedSceneSkin, EnclosedSceneSpec, PlacedObject, TileKind};

    let target_id = linked_interior_scene_id(source_scene_id, instance_id);
    let [interior_width_u32, interior_height_u32] = recipe
        .persistence
        .linked_interior_size
        .unwrap_or([
            recipe.footprint[0].saturating_sub(2).max(3),
            recipe.footprint[1].saturating_sub(2).max(3),
        ]);
    let interior_width = interior_width_u32.max(3) as usize;
    let interior_height = interior_height_u32.max(3) as usize;
    let entry_x = entry_x.clamp(1, interior_width as i32) as usize;
    let display_name = format!("{} — {} Interior", source_scene_name, recipe.label);
    let spec = EnclosedSceneSpec::rectangular(
        target_id,
        display_name,
        EnclosedSceneSkin::House,
        interior_width,
        interior_height,
        entry_x,
    )?;
    let mut scene = spec.build()?;

    for fill in &level.floor_fills {
        let [x, y, w, h] = fill.rect;
        for yy in y..y + h {
            for xx in x..x + w {
                if scene.contains_cell(xx, yy) {
                    scene.map.set(xx, yy, TileKind::WoodFloor);
                }
            }
        }
    }

    for wall in &level.wall_runs {
        if wall.edge != BuildingWallEdge::Interior || !wall.blocks_movement {
            continue;
        }
        for offset in 0..wall.length as i32 {
            let x = wall.start[0] + offset;
            let y = wall.start[1];
            if scene.contains_cell(x, y) {
                scene.map.set(x, y, TileKind::Wall);
            }
        }
    }

    let place_definition = |scene: &mut haven_core::SceneMap,
                            definition: &crate::placeable_asset_registry::PublishedWorldAssetDefinition,
                            tile: [i32; 2],
                            state: Option<&str>| {
        let object = PlacedObject::with_footprint(
            definition.compatibility_kind(),
            tile[0],
            tile[1],
            definition.footprint_for_state(state),
        );
        scene.map.place_pack_defined_object_with_state(
            object,
            definition.persistent_ref(),
            state,
        )
    };

    for opening in &level.openings {
        if opening.kind != super::BuildingOpeningKind::Door {
            continue;
        }
        // Exterior wall coordinates and linked-interior depth are separate
        // authorities. A south-edge exterior entry always maps to the generated
        // interior threshold instead of leaving the animated door stranded at
        // the old exterior-envelope Y coordinate when interior depth changes.
        let opening_tile = if opening.edge == BuildingWallEdge::South
            && opening.tile[1] == recipe.footprint[1] as i32 - 1
        {
            spec.entry_threshold
        } else {
            opening.tile
        };
        if scene.contains_cell(opening_tile[0], opening_tile[1]) {
            scene.map.set(opening_tile[0], opening_tile[1], TileKind::WoodFloor);
        }
        if let Some(definition) = placeables.resolve_alias(&opening.asset_id) {
            let _ = place_definition(
                &mut scene,
                definition,
                opening_tile,
                opening.state.as_deref().or_else(|| definition.initial_state()),
            );
        }
    }

    for furnishing in &level.furnishings {
        let Some(asset_id) = furnishing.asset_id.as_deref() else { continue; };
        let Some(definition) = placeables.resolve_alias(asset_id) else { continue; };
        let _ = place_definition(
            &mut scene,
            definition,
            furnishing.tile,
            furnishing.state.as_deref().or_else(|| definition.initial_state()),
        );
    }

    Ok(LinkedBuildingInteriorScene {
        scene,
        entry_threshold: spec.entry_threshold,
    })
}


#[cfg(test)]
mod wall_attachment_room_validation_tests {
    use super::*;

    #[test]
    fn wall_mounted_anchors_may_live_on_declared_room_boundary() {
        let room = [1, 5, 13, 5];
        assert!(wall_attachment_matches_room_boundary(
            room,
            [5, 10],
            BuildingWallEdge::South
        ));
        assert!(wall_attachment_matches_room_boundary(
            room,
            [5, 4],
            BuildingWallEdge::North
        ));
        assert!(wall_attachment_matches_room_boundary(
            room,
            [14, 7],
            BuildingWallEdge::East
        ));
        assert!(wall_attachment_matches_room_boundary(
            room,
            [0, 7],
            BuildingWallEdge::West
        ));
    }

    #[test]
    fn wall_attachment_does_not_legalize_wrong_edge_or_interior_outside_anchor() {
        let room = [1, 5, 13, 5];
        assert!(!wall_attachment_matches_room_boundary(
            room,
            [5, 10],
            BuildingWallEdge::North
        ));
        assert!(!wall_attachment_matches_room_boundary(
            room,
            [5, 10],
            BuildingWallEdge::Interior
        ));
        assert!(!wall_attachment_matches_room_boundary(
            room,
            [15, 10],
            BuildingWallEdge::South
        ));
    }
}
