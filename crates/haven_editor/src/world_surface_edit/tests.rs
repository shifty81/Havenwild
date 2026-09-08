use super::*;
use haven_authoring::GridRect;
use haven_authoring::{EditorCommandBus, EditorCommandSource};
use haven_core::{
    GameWorld, ObjectFootprint, ObjectKind, ProjectSceneId, SceneBiome, SceneKind, SceneMap, TileKind, MAP_H,
    MAP_W, MAX_STRUCTURAL_LEVEL,
};
use haven_world::scene_rectangles::{
    SceneRectangleAssignment, SceneRectangleAssignmentsFile, SceneRectangleManifest,
    SceneRectangleSpec,
};

fn test_manifest() -> SceneRectangleManifest {
    SceneRectangleManifest {
        schema: "test".to_string(),
        name: "test".to_string(),
        world_layout: "test".to_string(),
        scene_count: 2,
        special_scene_count: 0,
        scene_scale_targets: haven_world::scene_rectangles::SceneScaleTargets {
            small_test_chunk_tiles: [MAP_W as i32, MAP_H as i32],
            standard_outdoor_scene_tiles: [MAP_W as i32, MAP_H as i32],
            large_special_scene_tiles: [MAP_W as i32, MAP_H as i32],
            city_district_scene_tiles: [MAP_W as i32, MAP_H as i32],
            gameplay_camera_tiles_approx: vec![],
        },
        edge_contract: haven_world::scene_rectangles::SceneEdgeContract {
            seam_validation_band_tiles: 1,
            decoration_safe_band_tiles: 1,
            camera_void_rule: "none".to_string(),
        },
        archipelago_generation: Default::default(),
        scene_rectangles: vec![
            SceneRectangleSpec {
                scene_id: "r0".to_string(),
                landmass_id: 1,
                landmass_name: "Test".to_string(),
                kind: "surface".to_string(),
                grid_x: Some(0),
                grid_y: Some(0),
                world_rect_preview_px: [0, 0, 1, 1],
                tile_size: [MAP_W as i32, MAP_H as i32],
                edge_contract: "seamless".to_string(),
                streaming: "chunk".to_string(),
            },
            SceneRectangleSpec {
                scene_id: "r1".to_string(),
                landmass_id: 1,
                landmass_name: "Test".to_string(),
                kind: "surface".to_string(),
                grid_x: Some(1),
                grid_y: Some(0),
                world_rect_preview_px: [0, 0, 1, 1],
                tile_size: [MAP_W as i32, MAP_H as i32],
                edge_contract: "seamless".to_string(),
                streaming: "chunk".to_string(),
            },
        ],
    }
}

fn test_assignments() -> SceneRectangleAssignmentsFile {
    SceneRectangleAssignmentsFile {
        schema: "test".to_string(),
        assignments: vec![
            SceneRectangleAssignment {
                scene_code: "scene_a".to_string(),
                rectangle_id: "r0".to_string(),
                role: "wilderness".to_string(),
                ownership: "wilderness".to_string(),
                notes: None,
            },
            SceneRectangleAssignment {
                scene_code: "scene_b".to_string(),
                rectangle_id: "r1".to_string(),
                role: "wilderness".to_string(),
                ownership: "wilderness".to_string(),
                notes: None,
            },
        ],
    }
}

fn test_world() -> GameWorld {
    let mut world = GameWorld::starter();
    world
        .scenes
        .insert(SceneMap::blank(
            "scene_a",
            "Scene A",
            SceneKind::Exterior,
            SceneBiome::Temperate,
        ))
        .expect("scene a");
    world
        .scenes
        .insert(SceneMap::blank(
            "scene_b",
            "Scene B",
            SceneKind::Exterior,
            SceneBiome::Temperate,
        ))
        .expect("scene b");
    world
}

#[test]
fn global_address_crosses_partition_boundary() {
    let world = test_world();
    let address = resolve_world_surface_cell(
        &test_manifest(),
        &test_assignments(),
        &world,
        1,
        GridPos {
            x: MAP_W as i32,
            y: 5,
        },
    )
    .expect("address");
    assert_eq!(address.scene_id.code(), "scene_b");
    assert_eq!(address.local, GridPos { x: 0, y: 5 });
}

#[test]
fn rectangle_edit_records_one_cross_scene_undo_step() {
    let manifest = test_manifest();
    let assignments = test_assignments();
    let mut world = test_world();
    let mut bus = EditorCommandBus::with_limit(8);
    let outcome = paint_world_surface_rectangle(
        &mut world,
        &mut bus,
        "test",
        EditorCommandSource::MainEditor,
        &manifest,
        &assignments,
        1,
        GridRect::from_points(
            GridPos {
                x: MAP_W as i32 - 1,
                y: 4,
            },
            GridPos {
                x: MAP_W as i32,
                y: 4,
            },
        ),
        WorldSurfaceValue::Terrain(TileKind::Road),
    )
    .expect("edit");
    assert_eq!(outcome.scene_count, 2);
    assert_eq!(bus.undo_len(), 1);
    bus.undo_world(&mut world).expect("undo");
    assert_eq!(
        world
            .scene_by_id(&ProjectSceneId::new("scene_a"))
            .expect("scene a")
            .map
            .get(MAP_W as i32 - 1, 4),
        TileKind::Grass
    );
    assert_eq!(
        world
            .scene_by_id(&ProjectSceneId::new("scene_b"))
            .expect("scene b")
            .map
            .get(0, 4),
        TileKind::Grass
    );
}

#[test]
fn invalid_global_batch_rolls_back_every_partition() {
    let manifest = test_manifest();
    let assignments = test_assignments();
    let mut world = test_world();
    let mut bus = EditorCommandBus::with_limit(8);
    let valid = GridPos { x: 3, y: 4 };
    let outside = GridPos {
        x: MAP_W as i32 * 2,
        y: 4,
    };
    let result = paint_world_surface_cells(
        &mut world,
        &mut bus,
        "test",
        EditorCommandSource::MainEditor,
        &manifest,
        &assignments,
        1,
        [valid, outside],
        WorldSurfaceValue::Terrain(TileKind::Road),
        "Atomic global paint",
    );
    assert!(result.is_err());
    assert_eq!(
        world
            .scene_by_id(&ProjectSceneId::new("scene_a"))
            .expect("scene a")
            .map
            .get(valid.x, valid.y),
        TileKind::Grass
    );
    assert_eq!(bus.undo_len(), 0);
}

#[test]
fn clipboard_paste_crosses_partition_as_one_undo_step() {
    let manifest = test_manifest();
    let assignments = test_assignments();
    let mut world = test_world();
    world
        .scene_mut_by_id(&ProjectSceneId::new("scene_a"))
        .expect("scene a")
        .map
        .set(MAP_W as i32 - 1, 5, TileKind::Dirt);
    world
        .scene_mut_by_id(&ProjectSceneId::new("scene_b"))
        .expect("scene b")
        .map
        .set(0, 5, TileKind::Dirt);
    let clipboard = copy_world_surface_rectangle(
        &manifest,
        &assignments,
        &world,
        1,
        GridRect::from_points(
            GridPos {
                x: MAP_W as i32 - 1,
                y: 5,
            },
            GridPos {
                x: MAP_W as i32,
                y: 5,
            },
        ),
    )
    .expect("copy");
    let mut bus = EditorCommandBus::with_limit(8);
    let outcome = paste_world_surface_clipboard(
        &mut world,
        &mut bus,
        "test",
        EditorCommandSource::MainEditor,
        &manifest,
        &assignments,
        1,
        GridPos {
            x: MAP_W as i32 - 1,
            y: 9,
        },
        &clipboard,
    )
    .expect("paste");
    assert_eq!(outcome.scene_count, 2);
    assert_eq!(bus.undo_len(), 1);
    bus.undo_world(&mut world).expect("undo paste");
    assert_eq!(
        world
            .scene_by_id(&ProjectSceneId::new("scene_a"))
            .expect("scene a")
            .map
            .get(MAP_W as i32 - 1, 9),
        TileKind::Grass
    );
    assert_eq!(
        world
            .scene_by_id(&ProjectSceneId::new("scene_b"))
            .expect("scene b")
            .map
            .get(0, 9),
        TileKind::Grass
    );
}

#[test]
fn complete_object_footprint_cannot_be_cropped_by_partition_boundary() {
    let world = test_world();
    let two_wide = ObjectFootprint {
        visual_w: 2,
        collision_w: 2,
        interaction_w: 2,
        ..ObjectFootprint::single_tile()
    };
    let error = validate_world_surface_footprint(
        &test_manifest(),
        &test_assignments(),
        &world,
        1,
        GridPos {
            x: MAP_W as i32 - 1,
            y: 5,
        },
        two_wide,
    )
    .expect_err("cross-partition footprint must be rejected");
    assert!(error.contains("crosses storage partitions"));
}

#[test]
fn structural_platform_edit_crosses_partitions_without_changing_geology() {
    let manifest = test_manifest();
    let assignments = test_assignments();
    let mut world = test_world();
    let left = GridPos {
        x: MAP_W as i32 - 1,
        y: 12,
    };
    let right = GridPos {
        x: MAP_W as i32,
        y: 12,
    };
    world
        .scene_mut_by_id(&ProjectSceneId::new("scene_a"))
        .expect("scene a")
        .map
        .set_height(MAP_W as i32 - 1, 12, 211);
    world
        .scene_mut_by_id(&ProjectSceneId::new("scene_b"))
        .expect("scene b")
        .map
        .set_height(0, 12, 37);

    let mut bus = EditorCommandBus::with_limit(8);
    let outcome = paint_world_surface_cells(
        &mut world,
        &mut bus,
        "test",
        EditorCommandSource::MainEditor,
        &manifest,
        &assignments,
        1,
        [left, right],
        WorldSurfaceValue::StructuralLevel(1),
        "Normalize requested Level 1 to true Level 2 platform",
    )
    .expect("structural edit");

    assert_eq!(outcome.scene_count, 2);
    assert_eq!(bus.undo_len(), 1);
    assert_eq!(
        world
            .scene_by_id(&ProjectSceneId::new("scene_a"))
            .expect("scene a")
            .map
            .get_structural_level(MAP_W as i32 - 1, 12),
        Some(2)
    );
    assert_eq!(
        world
            .scene_by_id(&ProjectSceneId::new("scene_b"))
            .expect("scene b")
            .map
            .get_structural_level(0, 12),
        Some(2)
    );
    assert_eq!(
        world
            .scene_by_id(&ProjectSceneId::new("scene_a"))
            .expect("scene a")
            .map
            .get_height(MAP_W as i32 - 1, 12),
        211
    );
    assert_eq!(
        world
            .scene_by_id(&ProjectSceneId::new("scene_b"))
            .expect("scene b")
            .map
            .get_height(0, 12),
        37
    );

    bus.undo_world(&mut world).expect("undo structural edit");
    assert_eq!(
        world
            .scene_by_id(&ProjectSceneId::new("scene_a"))
            .expect("scene a")
            .map
            .get_structural_level(MAP_W as i32 - 1, 12),
        None
    );
    assert_eq!(
        world
            .scene_by_id(&ProjectSceneId::new("scene_b"))
            .expect("scene b")
            .map
            .get_structural_level(0, 12),
        None
    );
}

#[test]
fn raise_and_lower_platform_levels_are_clamped_and_transactional() {
    let manifest = test_manifest();
    let assignments = test_assignments();
    let mut world = test_world();
    let cell = GridPos { x: 8, y: 8 };
    let mut bus = EditorCommandBus::with_limit(8);

    // H20S: Level 1 is reserved for certified 2->1->0 ramp corridors, so
    // generic structural authoring deliberately steps 0 -> 2 -> 3 -> 4.
    for expected in [2, 3, MAX_STRUCTURAL_LEVEL] {
        adjust_world_structural_levels(
            &mut world,
            &mut bus,
            "test",
            EditorCommandSource::MainEditor,
            &manifest,
            &assignments,
            1,
            [cell],
            1,
            format!("Raise platform to Level {expected}"),
        )
        .expect("raise structural level");
        assert_eq!(
            world
                .scene_by_id(&ProjectSceneId::new("scene_a"))
                .expect("scene a")
                .map
                .get_structural_level(8, 8),
            Some(expected)
        );
    }

    assert!(adjust_world_structural_levels(
        &mut world,
        &mut bus,
        "test",
        EditorCommandSource::MainEditor,
        &manifest,
        &assignments,
        1,
        [cell],
        1,
        "Raise beyond maximum",
    )
    .is_err());

    // Lowering follows the inverse generic-authoring sequence and also skips
    // Level 1. The final step returns to ordinary Level-0 ground/relief.
    for expected in [3, 2, 0] {
        adjust_world_structural_levels(
            &mut world,
            &mut bus,
            "test",
            EditorCommandSource::MainEditor,
            &manifest,
            &assignments,
            1,
            [cell],
            -1,
            format!("Lower platform to Level {expected}"),
        )
        .expect("lower structural level");
        assert_eq!(
            world
                .scene_by_id(&ProjectSceneId::new("scene_a"))
                .expect("scene a")
                .map
                .get_structural_level(8, 8),
            Some(expected)
        );
    }

    assert!(adjust_world_structural_levels(
        &mut world,
        &mut bus,
        "test",
        EditorCommandSource::MainEditor,
        &manifest,
        &assignments,
        1,
        [cell],
        -1,
        "Lower below ground",
    )
    .is_err());
}


#[test]
fn selected_cliff_resolves_and_commits_certified_ramp_as_one_undo_step() {
    let manifest = test_manifest();
    let assignments = test_assignments();
    let mut world = test_world();
    let host = GridPos { x: 20, y: 20 };
    let orientation = haven_world::CertifiedRampOrientationV1::RiseRight;
    {
        let scene = world
            .scene_mut_by_id(&ProjectSceneId::new("scene_a"))
            .expect("scene a");
        for (step, (dx, dy)) in haven_world::certified_ramp_offsets_v1(orientation)
            .iter()
            .copied()
            .enumerate()
        {
            let x = host.x + dx;
            let y = host.y + dy;
            let level = if step <= 2 { 2 } else { 0 };
            scene.map.set_structural_level(x, y, Some(level));
            scene.map.set(x, y, if level == 2 { TileKind::MountainRock } else { TileKind::Grass });
        }
    }
    let plan = resolve_world_structural_connector_plan(
        &world,
        &manifest,
        &assignments,
        1,
        GridRect::from_points(host, GridPos { x: host.x, y: host.y + 1 }),
        WorldStructuralConnectorKind::Ramp,
    )
    .expect("resolve ramp");
    assert_eq!(plan.host, host);
    assert_eq!(plan.ramp_orientation, Some(orientation));

    let mut bus = EditorCommandBus::with_limit(8);
    let outcome = place_world_structural_connector(
        &mut world,
        &mut bus,
        "test",
        EditorCommandSource::MainEditor,
        &manifest,
        &assignments,
        1,
        &plan,
    )
    .expect("place ramp");
    assert_eq!(outcome.global_cells.len(), 6);
    assert_eq!(bus.undo_len(), 1);
    let scene = world.scene_by_id(&ProjectSceneId::new("scene_a")).expect("scene a");
    for ((dx, dy), expected) in haven_world::certified_ramp_offsets_v1(orientation)
        .iter()
        .zip(haven_world::certified_ramp_levels_v1().iter())
    {
        assert_eq!(scene.map.get(host.x + dx, host.y + dy), TileKind::MountainPath);
        assert_eq!(scene.map.get_structural_level(host.x + dx, host.y + dy), Some(*expected));
    }
    bus.undo_world(&mut world).expect("undo ramp");
    let scene = world.scene_by_id(&ProjectSceneId::new("scene_a")).expect("scene a");
    for (step, (dx, dy)) in haven_world::certified_ramp_offsets_v1(orientation)
        .iter()
        .copied()
        .enumerate()
    {
        let level = if step <= 2 { 2 } else { 0 };
        assert_eq!(scene.map.get_structural_level(host.x + dx, host.y + dy), Some(level));
        assert_eq!(scene.map.get(host.x + dx, host.y + dy), if level == 2 { TileKind::MountainRock } else { TileKind::Grass });
    }
}

#[test]
fn selected_true_cliff_places_stateful_ladder_and_undo_restores_world() {
    let manifest = test_manifest();
    let assignments = test_assignments();
    let mut world = test_world();
    let host = GridPos { x: 24, y: 24 };
    {
        let scene = world
            .scene_mut_by_id(&ProjectSceneId::new("scene_a"))
            .expect("scene a");
        for y in [host.y - 1, host.y] {
            for x in host.x - 1..=host.x + 1 {
                scene.map.set_structural_level(x, y, Some(2));
                scene.map.set(x, y, TileKind::MountainRock);
            }
        }
        for x in host.x - 1..=host.x + 1 {
            scene.map.set_structural_level(x, host.y + 1, Some(0));
            scene.map.set(x, host.y + 1, TileKind::Grass);
        }
    }
    let plan = resolve_world_structural_connector_plan(
        &world,
        &manifest,
        &assignments,
        1,
        GridRect::single(host),
        WorldStructuralConnectorKind::Ladder,
    )
    .expect("resolve ladder");
    assert_eq!(plan.host, host);

    let mut bus = EditorCommandBus::with_limit(8);
    place_world_structural_connector(
        &mut world,
        &mut bus,
        "test",
        EditorCommandSource::MainEditor,
        &manifest,
        &assignments,
        1,
        &plan,
    )
    .expect("place ladder");
    assert_eq!(bus.undo_len(), 1);
    let scene = world.scene_by_id(&ProjectSceneId::new("scene_a")).expect("scene a");
    let ladder = scene
        .map
        .objects
        .iter()
        .find(|object| object.kind == ObjectKind::Stairs && object.x == host.x && object.y == host.y)
        .expect("ladder stairs object");
    assert_eq!(scene.map.object_state(ladder.id), Some("ladder"));
    bus.undo_world(&mut world).expect("undo ladder");
    let scene = world.scene_by_id(&ProjectSceneId::new("scene_a")).expect("scene a");
    assert!(scene.map.objects.iter().all(|object| !(object.kind == ObjectKind::Stairs && object.x == host.x && object.y == host.y)));
}
