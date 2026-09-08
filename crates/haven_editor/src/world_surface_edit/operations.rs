use std::collections::{HashSet, VecDeque};

use haven_authoring::{
    EditOperation, EditTransaction, EditTransactionBatch, EditorCommand, EditorCommandBus,
    EditorCommandKind, EditorCommandSource, GridPos, GridRect,
};
use haven_core::{GameWorld, ProjectSceneId, MAP_H, MAP_W};
use haven_world::scene_rectangles::{SceneRectangleAssignmentsFile, SceneRectangleManifest};

use super::{
    is_surface_rectangle, rectangle_origin, resolve_world_surface_cell, world_surface_bounds,
    WorldSurfaceEditOutcome, WorldSurfaceLayer, WorldSurfaceValue,
};

#[allow(clippy::too_many_arguments)]
pub fn paint_world_surface_cells(
    world: &mut GameWorld,
    command_bus: &mut EditorCommandBus,
    project_id: &str,
    source: EditorCommandSource,
    manifest: &SceneRectangleManifest,
    assignments: &SceneRectangleAssignmentsFile,
    landmass_id: i32,
    global_cells: impl IntoIterator<Item = GridPos>,
    value: WorldSurfaceValue,
    label: impl Into<String>,
) -> Result<WorldSurfaceEditOutcome, String> {
    let label = label.into();
    let backup = world.clone();
    let mut batch = EditTransactionBatch::new(label.clone());
    let mut changed_global: Vec<GridPos> = global_cells.into_iter().collect();
    changed_global.sort();
    changed_global.dedup();

    let result = (|| -> Result<(), String> {
        let mut actual_changes = Vec::new();
        for global in changed_global.iter().copied() {
            let address =
                resolve_world_surface_cell(manifest, assignments, world, landmass_id, global)?;
            let scene = world
                .scene_mut_by_id(&address.scene_id)
                .ok_or_else(|| format!("scene {} is not loaded", address.scene_id.label()))?;
            let mut transaction = EditTransaction::new(label.clone(), address.scene_id.clone());
            match value {
                WorldSurfaceValue::Terrain(after) => {
                    let before = scene.map.get(address.local.x, address.local.y);
                    if before == after {
                        continue;
                    }
                    scene.map.set(address.local.x, address.local.y, after);
                    transaction.push(EditOperation::SetTile {
                        cell: address.local,
                        before,
                        after,
                    });
                }
                WorldSurfaceValue::Zone(after) => {
                    let before = scene.zone_at(address.local.x, address.local.y);
                    if before == after {
                        continue;
                    }
                    scene.set_zone(address.local.x, address.local.y, after);
                    transaction.push(EditOperation::SetZone {
                        cell: address.local,
                        before,
                        after,
                    });
                }
                WorldSurfaceValue::StructuralLevel(after) => {
                    let after = haven_world::normalize_structural_authoring_level_v1(after);
                    let before = scene
                        .map
                        .structural_level_storage(address.local.x, address.local.y);
                    if before == after {
                        continue;
                    }
                    scene
                        .map
                        .set_structural_level(address.local.x, address.local.y, Some(after));
                    transaction.push(EditOperation::SetStructuralLevel {
                        cell: address.local,
                        before,
                        after,
                    });
                }
            }
            batch.push(transaction);
            actual_changes.push(global);
        }
        changed_global = actual_changes;
        Ok(())
    })();

    if let Err(error) = result {
        *world = backup;
        return Err(error);
    }
    if batch.is_empty() {
        return Err("Global edit would not change the world".to_string());
    }

    let scene_count = batch.scene_count();
    let operation_count = batch.operation_count();
    let message = format!(
        "{} across {} global cell{} in {} partition{}",
        label,
        operation_count,
        if operation_count == 1 { "" } else { "s" },
        scene_count,
        if scene_count == 1 { "" } else { "s" }
    );
    let command = EditorCommand::new(
        match value.layer() {
            WorldSurfaceLayer::Terrain => EditorCommandKind::PaintTerrain,
            WorldSurfaceLayer::Zones => EditorCommandKind::AssignRoom,
            WorldSurfaceLayer::StructuralLevels => EditorCommandKind::SetStructuralLevel,
        },
        source,
        project_id.to_string(),
        None,
        Some(value.label()),
        changed_global.clone(),
        message.clone(),
    );
    command_bus.record_transaction_batch(command, batch);
    Ok(WorldSurfaceEditOutcome {
        message,
        operation_count,
        scene_count,
        global_cells: changed_global,
    })
}

#[allow(clippy::too_many_arguments)]
pub fn paint_world_surface_rectangle(
    world: &mut GameWorld,
    command_bus: &mut EditorCommandBus,
    project_id: &str,
    source: EditorCommandSource,
    manifest: &SceneRectangleManifest,
    assignments: &SceneRectangleAssignmentsFile,
    landmass_id: i32,
    rect: GridRect,
    value: WorldSurfaceValue,
) -> Result<WorldSurfaceEditOutcome, String> {
    paint_world_surface_cells(
        world,
        command_bus,
        project_id,
        source,
        manifest,
        assignments,
        landmass_id,
        rect.cells(),
        value,
        format!("Rectangle paint {}", value.label()),
    )
}

#[allow(clippy::too_many_arguments)]
pub fn flood_fill_world_surface(
    world: &mut GameWorld,
    command_bus: &mut EditorCommandBus,
    project_id: &str,
    source: EditorCommandSource,
    manifest: &SceneRectangleManifest,
    assignments: &SceneRectangleAssignmentsFile,
    landmass_id: i32,
    start: GridPos,
    value: WorldSurfaceValue,
) -> Result<WorldSurfaceEditOutcome, String> {
    let source_address =
        resolve_world_surface_cell(manifest, assignments, world, landmass_id, start)?;
    let source_scene = world
        .scene_by_id(&source_address.scene_id)
        .ok_or_else(|| format!("scene {} is not loaded", source_address.scene_id.label()))?;
    let source_value = match value {
        WorldSurfaceValue::Terrain(_) => WorldSurfaceValue::Terrain(
            source_scene
                .map
                .get(source_address.local.x, source_address.local.y),
        ),
        WorldSurfaceValue::Zone(_) => WorldSurfaceValue::Zone(
            source_scene.zone_at(source_address.local.x, source_address.local.y),
        ),
        WorldSurfaceValue::StructuralLevel(_) => WorldSurfaceValue::StructuralLevel(
            source_scene
                .map
                .get_structural_level(source_address.local.x, source_address.local.y)
                .unwrap_or(0),
        ),
    };
    if source_value == value {
        return Err(format!(
            "Flood-fill source already contains {}",
            value.label()
        ));
    }
    let bounds = world_surface_bounds(manifest, landmass_id)
        .ok_or_else(|| format!("landmass {} has no surface bounds", landmass_id))?;
    let mut queue = VecDeque::from([start]);
    let mut visited = HashSet::new();
    let mut cells = Vec::new();
    while let Some(global) = queue.pop_front() {
        if global.x < bounds.min.x
            || global.y < bounds.min.y
            || global.x > bounds.max.x
            || global.y > bounds.max.y
            || !visited.insert(global)
        {
            continue;
        }
        let Ok(address) =
            resolve_world_surface_cell(manifest, assignments, world, landmass_id, global)
        else {
            continue;
        };
        let Some(scene) = world.scene_by_id(&address.scene_id) else {
            continue;
        };
        let matches = match source_value {
            WorldSurfaceValue::Terrain(tile) => {
                scene.map.get(address.local.x, address.local.y) == tile
            }
            WorldSurfaceValue::Zone(zone) => {
                scene.zone_at(address.local.x, address.local.y) == zone
            }
            WorldSurfaceValue::StructuralLevel(level) => {
                scene
                    .map
                    .get_structural_level(address.local.x, address.local.y)
                    .unwrap_or(0)
                    == level
            }
        };
        if !matches {
            continue;
        }
        cells.push(global);
        queue.push_back(GridPos {
            x: global.x - 1,
            y: global.y,
        });
        queue.push_back(GridPos {
            x: global.x + 1,
            y: global.y,
        });
        queue.push_back(GridPos {
            x: global.x,
            y: global.y - 1,
        });
        queue.push_back(GridPos {
            x: global.x,
            y: global.y + 1,
        });
    }
    paint_world_surface_cells(
        world,
        command_bus,
        project_id,
        source,
        manifest,
        assignments,
        landmass_id,
        cells,
        value,
        format!("Global flood fill {}", value.label()),
    )
}

#[allow(clippy::too_many_arguments)]
pub fn adjust_world_structural_levels(
    world: &mut GameWorld,
    command_bus: &mut EditorCommandBus,
    project_id: &str,
    source: EditorCommandSource,
    manifest: &SceneRectangleManifest,
    assignments: &SceneRectangleAssignmentsFile,
    landmass_id: i32,
    global_cells: impl IntoIterator<Item = GridPos>,
    delta: i8,
    label: impl Into<String>,
) -> Result<WorldSurfaceEditOutcome, String> {
    if delta == 0 {
        return Err("Structural level adjustment must be non-zero".to_string());
    }
    let label = label.into();
    let backup = world.clone();
    let mut batch = EditTransactionBatch::new(label.clone());
    let mut changed_global: Vec<GridPos> = global_cells.into_iter().collect();
    changed_global.sort();
    changed_global.dedup();
    let mut actual_changes = Vec::new();

    let result = (|| -> Result<(), String> {
        for global in changed_global.iter().copied() {
            let address =
                resolve_world_surface_cell(manifest, assignments, world, landmass_id, global)?;
            let scene = world
                .scene_mut_by_id(&address.scene_id)
                .ok_or_else(|| format!("scene {} is not loaded", address.scene_id.label()))?;
            let before = scene
                .map
                .structural_level_storage(address.local.x, address.local.y);
            let current = scene
                .map
                .get_structural_level(address.local.x, address.local.y)
                .unwrap_or(0);
            let after = haven_world::step_structural_authoring_level_v1(current, delta);
            if current == after {
                continue;
            }
            scene
                .map
                .set_structural_level(address.local.x, address.local.y, Some(after));
            let mut transaction = EditTransaction::new(label.clone(), address.scene_id.clone());
            transaction.push(EditOperation::SetStructuralLevel {
                cell: address.local,
                before,
                after,
            });
            batch.push(transaction);
            actual_changes.push(global);
        }
        Ok(())
    })();

    if let Err(error) = result {
        *world = backup;
        return Err(error);
    }
    if batch.is_empty() {
        return Err("Structural level adjustment would not change the world".to_string());
    }
    let scene_count = batch.scene_count();
    let operation_count = batch.operation_count();
    let message = format!(
        "{} across {} global cell{} in {} partition{}",
        label,
        operation_count,
        if operation_count == 1 { "" } else { "s" },
        scene_count,
        if scene_count == 1 { "" } else { "s" }
    );
    let command = EditorCommand::new(
        EditorCommandKind::SetStructuralLevel,
        source,
        project_id.to_string(),
        None,
        Some("structural_levels".to_string()),
        actual_changes.clone(),
        message.clone(),
    );
    command_bus.record_transaction_batch(command, batch);
    Ok(WorldSurfaceEditOutcome {
        message,
        operation_count,
        scene_count,
        global_cells: actual_changes,
    })
}

#[allow(clippy::too_many_arguments)]
pub fn replace_world_surface_value(
    world: &mut GameWorld,
    command_bus: &mut EditorCommandBus,
    project_id: &str,
    source: EditorCommandSource,
    manifest: &SceneRectangleManifest,
    assignments: &SceneRectangleAssignmentsFile,
    landmass_id: i32,
    sample: GridPos,
    value: WorldSurfaceValue,
) -> Result<WorldSurfaceEditOutcome, String> {
    let address = resolve_world_surface_cell(manifest, assignments, world, landmass_id, sample)?;
    let scene = world
        .scene_by_id(&address.scene_id)
        .ok_or_else(|| format!("scene {} is not loaded", address.scene_id.label()))?;
    let source_value = match value {
        WorldSurfaceValue::Terrain(_) => {
            WorldSurfaceValue::Terrain(scene.map.get(address.local.x, address.local.y))
        }
        WorldSurfaceValue::Zone(_) => {
            WorldSurfaceValue::Zone(scene.zone_at(address.local.x, address.local.y))
        }
        WorldSurfaceValue::StructuralLevel(_) => WorldSurfaceValue::StructuralLevel(
            scene
                .map
                .get_structural_level(address.local.x, address.local.y)
                .unwrap_or(0),
        ),
    };
    if source_value == value {
        return Err(format!(
            "Selected landmass already uses {} at the sample",
            value.label()
        ));
    }
    let mut cells = Vec::new();
    for rectangle in manifest
        .scene_rectangles
        .iter()
        .filter(|rectangle| rectangle.landmass_id == landmass_id && is_surface_rectangle(rectangle))
    {
        let origin = rectangle_origin(rectangle);
        let assignment = match assignments.assignment_for_rectangle(&rectangle.scene_id) {
            Some(assignment) => assignment,
            None => continue,
        };
        let scene_id = ProjectSceneId::new(assignment.scene_code.as_str());
        let Some(scene) = world.scene_by_id(&scene_id) else {
            continue;
        };
        let width = rectangle.tile_size[0].min(MAP_W as i32).max(1);
        let height = rectangle.tile_size[1].min(MAP_H as i32).max(1);
        for y in 0..height {
            for x in 0..width {
                let matches = match source_value {
                    WorldSurfaceValue::Terrain(tile) => scene.map.get(x, y) == tile,
                    WorldSurfaceValue::Zone(zone) => scene.zone_at(x, y) == zone,
                    WorldSurfaceValue::StructuralLevel(level) => {
                        scene.map.get_structural_level(x, y).unwrap_or(0) == level
                    }
                };
                if matches {
                    cells.push(GridPos {
                        x: origin.x + x,
                        y: origin.y + y,
                    });
                }
            }
        }
    }
    paint_world_surface_cells(
        world,
        command_bus,
        project_id,
        source,
        manifest,
        assignments,
        landmass_id,
        cells,
        value,
        format!("Replace {} with {}", source_value.label(), value.label()),
    )
}

#[allow(clippy::too_many_arguments)]
pub fn resolve_world_structural_connector_plan(
    world: &GameWorld,
    manifest: &SceneRectangleManifest,
    assignments: &SceneRectangleAssignmentsFile,
    landmass_id: i32,
    selection: GridRect,
    kind: super::WorldStructuralConnectorKind,
) -> Result<super::WorldStructuralConnectorPlan, String> {
    let center = GridPos {
        x: selection.min.x + selection.width().saturating_sub(1) / 2,
        y: selection.min.y + selection.height().saturating_sub(1) / 2,
    };
    let search = GridRect::from_points(
        GridPos { x: selection.min.x - 2, y: selection.min.y - 2 },
        GridPos { x: selection.max.x + 2, y: selection.max.y + 2 },
    );
    let mut candidates = Vec::new();
    for host in search.cells() {
        match kind {
            super::WorldStructuralConnectorKind::Ramp => {
                for orientation in [
                    haven_world::CertifiedRampOrientationV1::RiseRight,
                    haven_world::CertifiedRampOrientationV1::RiseLeft,
                ] {
                    if let Ok(plan) = validate_ramp_plan(
                        world,
                        manifest,
                        assignments,
                        landmass_id,
                        host,
                        orientation,
                    ) {
                        if plan.footprint.intersects(selection) {
                            candidates.push(plan);
                        }
                    }
                }
            }
            super::WorldStructuralConnectorKind::Ladder => {
                if let Ok(plan) = validate_ladder_plan(
                    world,
                    manifest,
                    assignments,
                    landmass_id,
                    host,
                ) {
                    if plan.footprint.intersects(selection) {
                        candidates.push(plan);
                    }
                }
            }
        }
    }
    candidates.sort_by_key(|plan| {
        (
            (plan.host.x - center.x).abs() + (plan.host.y - center.y).abs(),
            plan.host.y,
            plan.host.x,
            matches!(
                plan.ramp_orientation,
                Some(haven_world::CertifiedRampOrientationV1::RiseLeft)
            ),
        )
    });
    candidates.into_iter().next().ok_or_else(|| match kind {
        super::WorldStructuralConnectorKind::Ramp => {
            "No certified south-facing Level-2 → Level-0 ramp host intersects the selected cliff section"
                .to_string()
        }
        super::WorldStructuralConnectorKind::Ladder => {
            "No dry, straight, south-facing true-cliff ladder host intersects the selected cliff section"
                .to_string()
        }
    })
}

#[allow(clippy::too_many_arguments)]
pub fn place_world_structural_connector(
    world: &mut GameWorld,
    command_bus: &mut EditorCommandBus,
    project_id: &str,
    source: EditorCommandSource,
    manifest: &SceneRectangleManifest,
    assignments: &SceneRectangleAssignmentsFile,
    landmass_id: i32,
    plan: &super::WorldStructuralConnectorPlan,
) -> Result<WorldSurfaceEditOutcome, String> {
    // Re-resolve the plan immediately before mutation so a stale preview can
    // never commit against terrain/object state that changed after selection.
    let validated = match plan.kind {
        super::WorldStructuralConnectorKind::Ramp => validate_ramp_plan(
            world,
            manifest,
            assignments,
            landmass_id,
            plan.host,
            plan.ramp_orientation.ok_or_else(|| "Ramp plan is missing its certified orientation".to_string())?,
        )?,
        super::WorldStructuralConnectorKind::Ladder => validate_ladder_plan(
            world,
            manifest,
            assignments,
            landmass_id,
            plan.host,
        )?,
    };
    if validated != *plan {
        return Err("Structural connector preview is stale; reselect the cliff section and preview again".to_string());
    }

    let label = format!("Place {}", plan.kind.label());
    let backup = world.clone();
    let mut batch = EditTransactionBatch::new(label.clone());
    let result = (|| -> Result<(), String> {
        match plan.kind {
            super::WorldStructuralConnectorKind::Ramp => {
                let orientation = plan.ramp_orientation.ok_or_else(|| "Ramp plan is missing its certified orientation".to_string())?;
                for ((dx, dy), target_level) in haven_world::certified_ramp_offsets_v1(orientation)
                    .iter()
                    .copied()
                    .zip(haven_world::certified_ramp_levels_v1().iter().copied())
                {
                    let global = GridPos { x: plan.host.x + dx, y: plan.host.y + dy };
                    let address = resolve_world_surface_cell(manifest, assignments, world, landmass_id, global)?;
                    let scene = world.scene_mut_by_id(&address.scene_id)
                        .ok_or_else(|| format!("scene {} is not loaded", address.scene_id.label()))?;
                    let mut tx = EditTransaction::new(label.clone(), address.scene_id.clone());
                    let before_tile = scene.map.get(address.local.x, address.local.y);
                    if before_tile != haven_core::TileKind::MountainPath {
                        scene.map.set(address.local.x, address.local.y, haven_core::TileKind::MountainPath);
                        tx.push(EditOperation::SetTile { cell: address.local, before: before_tile, after: haven_core::TileKind::MountainPath });
                    }
                    let before_level = scene.map.structural_level_storage(address.local.x, address.local.y);
                    if before_level != target_level {
                        scene.map.set_structural_level(address.local.x, address.local.y, Some(target_level));
                        tx.push(EditOperation::SetStructuralLevel { cell: address.local, before: before_level, after: target_level });
                    }
                    if !tx.is_empty() { batch.push(tx); }
                }
            }
            super::WorldStructuralConnectorKind::Ladder => {
                let address = resolve_world_surface_cell(manifest, assignments, world, landmass_id, plan.host)?;
                let scene = world.scene_mut_by_id(&address.scene_id)
                    .ok_or_else(|| format!("scene {} is not loaded", address.scene_id.label()))?;
                let id = scene.map.place_object(haven_core::ObjectKind::Stairs, address.local.x, address.local.y)
                    .ok_or_else(|| "Ladder host became occupied before placement".to_string())?;
                let object = *scene.map.object(id).ok_or_else(|| "Placed ladder object could not be recovered".to_string())?;
                scene.map.set_object_state(id, "ladder");
                let mut tx = EditTransaction::new(label.clone(), address.scene_id.clone());
                tx.push(EditOperation::InsertObject { object });
                tx.push(EditOperation::SetObjectState { id, before: None, after: Some("ladder".to_string()) });
                batch.push(tx);
            }
        }
        Ok(())
    })();
    if let Err(error) = result {
        *world = backup;
        return Err(error);
    }
    if batch.is_empty() {
        *world = backup;
        return Err("Structural connector placement would not change the world".to_string());
    }
    let scene_count = batch.scene_count();
    let operation_count = batch.operation_count();
    let message = format!("Placed {} as one undoable authoring transaction across {} partition{}", plan.kind.label(), scene_count, if scene_count == 1 { "" } else { "s" });
    let command = EditorCommand::new(
        if plan.kind == super::WorldStructuralConnectorKind::Ladder { EditorCommandKind::PlaceObject } else { EditorCommandKind::SetStructuralLevel },
        source,
        project_id.to_string(),
        None,
        Some(match plan.kind { super::WorldStructuralConnectorKind::Ramp => "connector.ramp", super::WorldStructuralConnectorKind::Ladder => "connector.ladder" }.to_string()),
        plan.global_cells.clone(),
        message.clone(),
    );
    command_bus.record_transaction_batch(command, batch);
    Ok(WorldSurfaceEditOutcome { message, operation_count, scene_count, global_cells: plan.global_cells.clone() })
}

fn validate_ramp_plan(
    world: &GameWorld,
    manifest: &SceneRectangleManifest,
    assignments: &SceneRectangleAssignmentsFile,
    landmass_id: i32,
    host: GridPos,
    orientation: haven_world::CertifiedRampOrientationV1,
) -> Result<super::WorldStructuralConnectorPlan, String> {
    let mut cells = Vec::with_capacity(6);
    for (step, (dx, dy)) in haven_world::certified_ramp_offsets_v1(orientation).iter().copied().enumerate() {
        let global = GridPos { x: host.x + dx, y: host.y + dy };
        let address = resolve_world_surface_cell(manifest, assignments, world, landmass_id, global)?;
        let scene = world.scene_by_id(&address.scene_id)
            .ok_or_else(|| format!("scene {} is not loaded", address.scene_id.label()))?;
        let tile = scene.map.get(address.local.x, address.local.y);
        if !matches!(tile, haven_core::TileKind::Grass | haven_core::TileKind::Dirt | haven_core::TileKind::MountainRock | haven_core::TileKind::MountainPath) {
            return Err(format!("Ramp footprint contains incompatible {} at {},{}", tile.label(), global.x, global.y));
        }
        if haven_core::terrain_gameplay_profile(tile).water_depth != haven_core::WaterDepthClass::None {
            return Err(format!("Ramp footprint reaches water at {},{}", global.x, global.y));
        }
        if scene.map.object_at(address.local.x, address.local.y).is_some() || scene.map.stamp_at(address.local.x, address.local.y).is_some() {
            return Err(format!("Ramp footprint is occupied at {},{}", global.x, global.y));
        }
        let current = scene.map.get_structural_level(address.local.x, address.local.y).unwrap_or_else(|| if tile == haven_core::TileKind::MountainRock { 2 } else { 0 });
        let expected = if step <= 2 { 2 } else { 0 };
        if current != expected {
            return Err(format!("Ramp requires a clean Level-2 → Level-0 south face; {},{} is Level {}", global.x, global.y, current));
        }
        cells.push(global);
    }
    let footprint = bounds_for_cells(&cells).expect("certified ramp always has cells");
    Ok(super::WorldStructuralConnectorPlan { kind: super::WorldStructuralConnectorKind::Ramp, host, ramp_orientation: Some(orientation), footprint, global_cells: cells })
}

fn validate_ladder_plan(
    world: &GameWorld,
    manifest: &SceneRectangleManifest,
    assignments: &SceneRectangleAssignmentsFile,
    landmass_id: i32,
    host: GridPos,
) -> Result<super::WorldStructuralConnectorPlan, String> {
    let lower = GridPos { x: host.x, y: host.y + 1 };
    let host_address = resolve_world_surface_cell(manifest, assignments, world, landmass_id, host)?;
    let lower_address = resolve_world_surface_cell(manifest, assignments, world, landmass_id, lower)?;
    let host_scene = world.scene_by_id(&host_address.scene_id).ok_or_else(|| format!("scene {} is not loaded", host_address.scene_id.label()))?;
    let lower_scene = world.scene_by_id(&lower_address.scene_id).ok_or_else(|| format!("scene {} is not loaded", lower_address.scene_id.label()))?;
    let host_tile = host_scene.map.get(host_address.local.x, host_address.local.y);
    let lower_tile = lower_scene.map.get(lower_address.local.x, lower_address.local.y);
    let upper_level = host_scene.map.get_structural_level(host_address.local.x, host_address.local.y).unwrap_or_else(|| if host_tile == haven_core::TileKind::MountainRock { 2 } else { 0 });
    let lower_level = lower_scene.map.get_structural_level(lower_address.local.x, lower_address.local.y).unwrap_or_else(|| if lower_tile == haven_core::TileKind::MountainRock { 2 } else { 0 });
    if !haven_world::constructed_ladder_allowed_v1(upper_level.saturating_sub(lower_level), haven_core::terrain_gameplay_profile(lower_tile).water_depth != haven_core::WaterDepthClass::None) || lower_level != 0 {
        return Err("Ladder requires a dry Level-2+ → Level-0 south-facing cliff".to_string());
    }
    if host_scene.map.object_at(host_address.local.x, host_address.local.y).is_some() || host_scene.map.stamp_at(host_address.local.x, host_address.local.y).is_some() {
        return Err(format!("Ladder host {},{} is occupied", host.x, host.y));
    }
    let north = GridPos { x: host.x, y: host.y - 1 };
    let north_address = resolve_world_surface_cell(manifest, assignments, world, landmass_id, north)
        .map_err(|_| "Ladder host is on an unsupported cliff corner".to_string())?;
    let north_scene = world.scene_by_id(&north_address.scene_id)
        .ok_or_else(|| "Ladder north partition is not loaded".to_string())?;
    let north_tile = north_scene.map.get(north_address.local.x, north_address.local.y);
    let north_level = north_scene.map.get_structural_level(north_address.local.x, north_address.local.y)
        .unwrap_or_else(|| if north_tile == haven_core::TileKind::MountainRock { 2 } else { 0 });
    if north_level != upper_level {
        return Err("Ladder host is not a straight south-facing cliff segment".to_string());
    }
    // Fail closed on corners: the current certified ladder art belongs only to
    // a straight south face, so both adjacent columns must continue the same
    // upper plateau and the same Level-0 receiver where addressable.
    for dx in [-1, 1] {
        let side_upper = GridPos { x: host.x + dx, y: host.y };
        let side_lower = GridPos { x: host.x + dx, y: host.y + 1 };
        let Ok(upper_address) = resolve_world_surface_cell(manifest, assignments, world, landmass_id, side_upper) else { return Err("Ladder host is on an unsupported cliff corner".to_string()); };
        let Ok(side_lower_address) = resolve_world_surface_cell(manifest, assignments, world, landmass_id, side_lower) else { return Err("Ladder host is on an unsupported cliff corner".to_string()); };
        let upper_scene = world.scene_by_id(&upper_address.scene_id).ok_or_else(|| "Ladder side partition is not loaded".to_string())?;
        let side_lower_scene = world.scene_by_id(&side_lower_address.scene_id).ok_or_else(|| "Ladder side partition is not loaded".to_string())?;
        let upper_tile = upper_scene.map.get(upper_address.local.x, upper_address.local.y);
        let side_lower_tile = side_lower_scene.map.get(side_lower_address.local.x, side_lower_address.local.y);
        let side_upper_level = upper_scene.map.get_structural_level(upper_address.local.x, upper_address.local.y).unwrap_or_else(|| if upper_tile == haven_core::TileKind::MountainRock { 2 } else { 0 });
        let side_lower_level = side_lower_scene.map.get_structural_level(side_lower_address.local.x, side_lower_address.local.y).unwrap_or_else(|| if side_lower_tile == haven_core::TileKind::MountainRock { 2 } else { 0 });
        if side_upper_level != upper_level || side_lower_level != 0 {
            return Err("Ladder host is not a straight south-facing cliff segment".to_string());
        }
    }
    let cells = vec![host, lower];
    Ok(super::WorldStructuralConnectorPlan { kind: super::WorldStructuralConnectorKind::Ladder, host, ramp_orientation: None, footprint: GridRect::from_points(host, lower), global_cells: cells })
}

fn bounds_for_cells(cells: &[GridPos]) -> Option<GridRect> {
    let first = *cells.first()?;
    let mut min = first;
    let mut max = first;
    for cell in &cells[1..] {
        min.x = min.x.min(cell.x);
        min.y = min.y.min(cell.y);
        max.x = max.x.max(cell.x);
        max.y = max.y.max(cell.y);
    }
    Some(GridRect::from_points(min, max))
}
