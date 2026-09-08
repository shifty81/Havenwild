use super::*;
use super::render_helpers::{draw_editor_widget, draw_wrapped};
use haven_assets::{
    asset_intake::repo_root_dir,
    building_instance::{
        BuildingInstanceDefinition, BuildingInstanceOrigin, BuildingInstanceViewState,
        BuildingPlacementSpace, BUILDING_INSTANCE_SCHEMA,
    },
    building_recipe::{BuildingRecipeDefinition, BuildingRecipePieceKind},
};

pub(crate) fn building_preview_state_for_recipe(
    instance: &BuildingInstanceDefinition,
    recipe: &BuildingRecipeDefinition,
) -> BuildingInstanceViewState {
    let mut state = BuildingInstanceViewState::for_definition(instance);
    state.inside = recipe.persistence.interior_policy != "linked_enclosed_scene";
    state
}

impl EditorApp {
    pub(crate) fn resolved_building_instances_for_scene(&self, scene: &SceneMap) -> Vec<BuildingInstanceDefinition> {
        if scene.kind == haven_core::SceneKind::Exterior {
            let manifest = haven_world::continuous_surface::ContinuousSurfaceManifest::for_world(&self.model.world);
            let origin = manifest
                .chunk_for_scene(&scene.id)
                .map(|chunk| [chunk.x * MAP_W as i32, chunk.y * MAP_H as i32]);
            self.building_instance_registry.resolved_for_scene(
                scene.id.code(),
                manifest.pcg_region.as_deref(),
                origin,
                [MAP_W as i32, MAP_H as i32],
                &self.building_recipe_registry,
            )
        } else {
            self.building_instance_registry.resolved_for_scene(
                scene.id.code(),
                None,
                None,
                [MAP_W as i32, MAP_H as i32],
                &self.building_recipe_registry,
            )
        }
    }

    pub(crate) fn draw_building_instance_previews(&self, scene: &SceneMap) {
        #[derive(Clone)]
        enum PreviewVisual {
            Piece {
                building_anchor_tile: [i32; 2],
                piece: haven_assets::building_instance::BuildingInstanceVisiblePiece,
            },
            Composite {
                entry: haven_core::SceneVisualOverride,
            },
        }

        let mut visuals = Vec::new();
        for instance in self.resolved_building_instances_for_scene(scene) {
            let Some(recipe) = self.building_recipe_registry.entry(&instance.recipe_id) else {
                continue;
            };
            let state = self
                .building_preview_views
                .get(&instance.id)
                .copied()
                .unwrap_or_else(|| building_preview_state_for_recipe(&instance, recipe));
            let building_bottom =
                (instance.anchor_tile[1] + recipe.footprint[1] as i32) as f32;

            if !state.inside {
                if let Some(entry) = scene.visual_overrides.iter().find(|entry| {
                    entry.is_building_composite()
                        && entry.x == instance.anchor_tile[0]
                        && entry.y == instance.anchor_tile[1]
                        && entry.w == recipe.footprint[0] as i32
                        && entry.h == recipe.footprint[1] as i32
                }) {
                    visuals.push((
                        building_bottom,
                        PreviewVisual::Composite { entry: entry.clone() },
                    ));
                    continue;
                }
            }

            for piece in self
                .building_instance_registry
                .visible_pieces_for_instance(&instance, recipe, state)
            {
                let sort_y = if piece.piece.kind == BuildingRecipePieceKind::Roof {
                    building_bottom
                } else {
                    piece.world_tile[1] as f32 + 1.0
                };
                visuals.push((
                    sort_y,
                    PreviewVisual::Piece {
                        building_anchor_tile: instance.anchor_tile,
                        piece,
                    },
                ));
            }
        }
        visuals.sort_by(|left, right| left.0.total_cmp(&right.0));
        for (_, visual) in visuals {
            match visual {
                PreviewVisual::Composite { entry } => {
                    let _ = self.editor_textures.draw_building_composite_override(&entry, 1.0);
                }
                PreviewVisual::Piece { building_anchor_tile, piece } => {
                    let opacity = if piece.piece.kind == BuildingRecipePieceKind::Roof {
                        0.92
                    } else {
                        1.0
                    };
                    let _ = if let Some(origin) = piece.piece.render_origin_px {
                        self.editor_textures.draw_published_asset_at_building_origin(
                            &piece.piece.asset_id,
                            piece.piece.state.as_deref(),
                            building_anchor_tile,
                            origin,
                            opacity,
                        )
                    } else {
                        self.editor_textures.draw_published_asset_at_tile(
                            &piece.piece.asset_id,
                            piece.piece.state.as_deref(),
                            piece.world_tile,
                            opacity,
                        )
                    };
                }
            }
        }
    }

    fn first_building_in_current_scene(&self) -> Option<BuildingInstanceDefinition> {
        let scene = self.model.world.scenes.get(self.selected_scene)?;
        self.resolved_building_instances_for_scene(scene).into_iter().next()
    }

    pub(crate) fn building_at_scene_cursor(&self) -> Option<BuildingInstanceDefinition> {
        let scene = self.model.world.scenes.get(self.selected_scene)?;
        let tile = [self.scene_cursor_x, self.scene_cursor_y];
        self.resolved_building_instances_for_scene(scene)
            .into_iter()
            .find(|instance| {
                self.building_recipe_registry
                    .entry(&instance.recipe_id)
                    .is_some_and(|recipe| instance.footprint_contains_world_tile(recipe, tile))
            })
    }

    pub(crate) fn draw_building_authoring_inspector(
        &self,
        rect: Rect,
        instance: &BuildingInstanceDefinition,
    ) {
        let recipe = self.building_recipe_registry.entry(&instance.recipe_id);
        draw_editor_text("Building Authoring", rect.x, rect.y + 22.0, 24.0, TEXT);
        draw_scissored_text(
            recipe.map_or(instance.recipe_id.as_str(), |recipe| recipe.label.as_str()),
            rect.x,
            rect.y + 50.0,
            rect.w,
            16.0,
            GOOD,
        );
        draw_scissored_text(
            &format!("Anchor {},{} | {}", instance.anchor_tile[0], instance.anchor_tile[1], instance.id),
            rect.x,
            rect.y + 74.0,
            rect.w,
            14.0,
            MUTED,
        );
        for (index, label) in [
            "Create/Open Interior",
            "Collision",
            "Play Here",
            "Move Left",
            "Move Right",
            "Delete Building",
        ]
        .into_iter()
        .enumerate()
        {
            draw_editor_widget(building_authoring_action_rect(rect, index), label, false);
        }
        draw_wrapped(
            "Exterior composition is recipe/socket driven. Create/Open Interior generates a linked void-backed EnclosedScene from the exterior footprint and keeps the front doorway as the authoritative transition threshold.",
            rect.x,
            rect.y + 264.0,
            rect.w,
            14.0,
            TEXT,
        );
    }

    pub(crate) fn handle_building_authoring_inspector_click(
        &mut self,
        mx: f32,
        my: f32,
        rect: Rect,
    ) -> bool {
        let mouse = vec2(mx, my);
        if !rect.contains(mouse) {
            return false;
        }
        let Some(instance) = self.building_at_scene_cursor() else {
            return true;
        };
        for index in 0..6 {
            if !building_authoring_action_rect(rect, index).contains(mouse) {
                continue;
            }
            match index {
                0 => self.create_or_open_building_interior(&instance),
                1 => {
                    let visible = !self.canvas_layer_kind_visible(super::canvas_layers::CanvasLayerKind::Collision);
                    self.set_game_canvas_layer_visibility(super::canvas_layers::CanvasLayerKind::Collision, visible);
                    self.status_message = format!(
                        "Building collision overlay {}",
                        if visible { "enabled" } else { "disabled" }
                    );
                }
                2 => self.play_development_world(true),
                3 => { self.move_building_instance_at_scene_cursor(-1, 0); },
                4 => { self.move_building_instance_at_scene_cursor(1, 0); },
                5 => { self.delete_building_instance_at_scene_cursor(); },
                _ => {}
            }
            return true;
        }
        true
    }

    fn create_or_open_building_interior(&mut self, instance: &BuildingInstanceDefinition) {
        let Some(recipe) = self.building_recipe_registry.entry(&instance.recipe_id).cloned() else {
            self.status_message = "Building recipe is unavailable".to_string();
            return;
        };
        let Some(level) = recipe.level(recipe.default_level) else {
            self.status_message = "Building default level is unavailable".to_string();
            return;
        };
        let Some(opening) = level
            .openings
            .iter()
            .find(|opening| opening.id == "front_door")
            .or_else(|| level.openings.iter().find(|opening| opening.kind == haven_assets::building_recipe::BuildingOpeningKind::Door))
        else {
            self.status_message = "Building has no doorway available for an interior link".to_string();
            return;
        };
        let world_tile = [
            instance.anchor_tile[0] + opening.tile[0],
            instance.anchor_tile[1] + opening.tile[1],
        ];
        let Some(source_scene) = self.model.world.scenes.get(self.selected_scene) else { return; };
        if let Some(transition) = source_scene.transition_at(world_tile[0], world_tile[1]).cloned() {
            let target = transition.target.project_id().clone();
            if let Some(index) = self.model.world.scenes.position(&target) {
                self.select_scene_index(index);
                let _ = self.model.world.set_active_scene(target.clone());
                self.scene_cursor_x = transition.spawn_x;
                self.scene_cursor_y = transition.spawn_y;
                self.viewport_mode = EditorViewportMode::SceneMap;
                self.status_message = format!("Opened linked interior {}", target.label());
                return;
            }
        }
        let source_id = source_scene.id.clone();
        let source_name = source_scene.name.clone();
        let source_dimensions = source_scene.dimensions;
        self.create_linked_building_interior(
            &recipe,
            level,
            source_id,
            source_name,
            source_dimensions,
            world_tile,
            opening.tile[0],
            &instance.id,
        );
    }

    #[allow(clippy::too_many_arguments)]
    fn create_linked_building_interior(
        &mut self,
        recipe: &haven_assets::building_recipe::BuildingRecipeDefinition,
        level: &haven_assets::building_recipe::BuildingLevelDefinition,
        source_id: ProjectSceneId,
        source_name: String,
        source_dimensions: haven_core::SceneDimensions,
        world_tile: [i32; 2],
        entry_x: i32,
        instance_id: &str,
    ) {
        let materialized = match haven_assets::building_recipe::materialize_linked_building_interior(
            recipe,
            level,
            &self.placeable_registry,
            &source_id,
            &source_name,
            instance_id,
            entry_x,
        ) {
            Ok(materialized) => materialized,
            Err(error) => {
                self.status_message = format!("Unable to create mapped building interior: {error}");
                return;
            }
        };
        let candidate = materialized.scene.id.clone();
        if let Some(index) = self.model.world.scenes.position(&candidate) {
            self.select_scene_index(index);
            let _ = self.model.world.set_active_scene(candidate.clone());
            self.viewport_mode = EditorViewportMode::SceneMap;
            self.status_message = format!("Opened linked interior {}", candidate.label());
            return;
        }
        let destination = materialized.scene;
        let doorway = materialized.entry_threshold;

        let destination_spawn = (destination.spawn_x, destination.spawn_y);
        if let Err(error) = create_project_scene(
            &mut self.model.world,
            &mut self.command_bus,
            &self.model.project.project_id,
            EditorCommandSource::MainEditor,
            destination,
        ) {
            self.status_message = format!("Unable to create linked building interior: {error}");
            return;
        }

        if let Err(error) = create_scene_transition(
            &mut self.model.world,
            &mut self.command_bus,
            &self.model.project.project_id,
            EditorCommandSource::MainEditor,
            source_id.clone(),
            world_tile[0],
            world_tile[1],
            1,
            1,
            candidate.clone(),
            destination_spawn.0,
            destination_spawn.1,
            format!("Enter {}", recipe.label),
        ) {
            self.status_message = format!("Created interior, but exterior link failed: {error}");
            return;
        }

        let return_x = world_tile[0].clamp(0, source_dimensions.width as i32 - 1);
        let return_y = (world_tile[1] + 1).clamp(0, source_dimensions.height as i32 - 1);
        if let Err(error) = create_scene_transition(
            &mut self.model.world,
            &mut self.command_bus,
            &self.model.project.project_id,
            EditorCommandSource::MainEditor,
            candidate.clone(),
            doorway[0],
            doorway[1],
            1,
            1,
            source_id,
            return_x,
            return_y,
            format!("Exit {}", recipe.label),
        ) {
            self.status_message = format!("Created interior, but return link failed: {error}");
            return;
        }

        if let Some(index) = self.model.world.scenes.position(&candidate) {
            self.select_scene_index(index);
            let _ = self.model.world.set_active_scene(candidate.clone());
            self.scene_cursor_x = destination_spawn.0;
            self.scene_cursor_y = destination_spawn.1;
            self.viewport_mode = EditorViewportMode::SceneMap;
            self.focus_right_dock(super::workspace_shell::RightDockTab::Assets);
            self.selection.clear();
            self.scene_canvas = CanvasCameraState::default();
        }
        self.status_message = format!(
            "Created mapped {} interior from recipe walls, doors, furnishings, collision, and void shell",
            recipe.label
        );
    }

    pub(crate) fn place_building_instance_at_scene_cursor(&mut self) -> bool {
        let Some(scene) = self.model.world.scenes.get(self.selected_scene).cloned() else {
            return false;
        };
        let Some(recipe) = self
            .building_recipe_registry
            .entries()
            .iter()
            .find(|recipe| !recipe.classification.diagnostic_only)
            .or_else(|| self.building_recipe_registry.entries().first())
            .cloned()
        else {
            self.status_message = "No BuildingRecipe is available for placement".to_string();
            return true;
        };
        let mut definition = BuildingInstanceDefinition {
            schema: BUILDING_INSTANCE_SCHEMA.to_string(),
            id: String::new(),
            recipe_id: recipe.id.clone(),
            scene_id: scene.id.code().to_string(),
            anchor_tile: [self.scene_cursor_x, self.scene_cursor_y],
            initial_level: recipe.default_level,
            diagnostic_only: false,
            origin: BuildingInstanceOrigin::Authored,
            placement_space: BuildingPlacementSpace::SceneLocal,
            surface_region_id: None,
            global_anchor_tile: None,
        };
        if scene.kind == haven_core::SceneKind::Exterior {
            let manifest = haven_world::continuous_surface::ContinuousSurfaceManifest::for_world(&self.model.world);
            if let Some(chunk) = manifest.chunk_for_scene(&scene.id) {
                definition.placement_space = BuildingPlacementSpace::ContinuousSurface;
                definition.surface_region_id = manifest.pcg_region.clone();
                definition.global_anchor_tile = Some([
                    chunk.x * MAP_W as i32 + self.scene_cursor_x,
                    chunk.y * MAP_H as i32 + self.scene_cursor_y,
                ]);
            }
        }
        match self
            .building_instance_registry
            .place_authored_instance(definition, &self.building_recipe_registry)
        {
            Ok(id) => {
                let view = self
                    .building_instance_registry
                    .entry(&id)
                    .map(|instance| building_preview_state_for_recipe(instance, &recipe))
                    .unwrap_or(BuildingInstanceViewState {
                        active_level: recipe.default_level,
                        inside: recipe.persistence.interior_policy != "linked_enclosed_scene",
                    });
                self.building_preview_views.insert(id.clone(), view);
                self.status_message = match self
                    .building_instance_registry
                    .save_authored_to_project_root(repo_root_dir())
                {
                    Ok(()) => format!(
                        "Placed and saved BuildingInstance {id} using {} at {}, {}.",
                        recipe.id, self.scene_cursor_x, self.scene_cursor_y
                    ),
                    Err(error) => format!(
                        "Placed BuildingInstance {id}, but source persistence failed: {error}"
                    ),
                };
                self.command_bus.record_event(self.app_command(
                    EditorCommandKind::SceneMutation,
                    self.status_message.clone(),
                ));
            }
            Err(error) => self.status_message = format!("Building placement failed: {error}"),
        }
        true
    }

    pub(crate) fn move_building_instance_at_scene_cursor(&mut self, dx: i32, dy: i32) -> bool {
        let Some(resolved) = self.building_at_scene_cursor() else {
            self.status_message = "No BuildingInstance footprint under the scene cursor".to_string();
            return true;
        };
        let Some(authoritative) = self.building_instance_registry.entry(&resolved.id).cloned() else {
            return false;
        };
        let local_anchor = [
            authoritative.anchor_tile[0] + dx,
            authoritative.anchor_tile[1] + dy,
        ];
        let global_anchor = authoritative
            .global_anchor_tile
            .map(|anchor| [anchor[0] + dx, anchor[1] + dy]);
        match self.building_instance_registry.move_authored_instance(
            &resolved.id,
            local_anchor,
            global_anchor,
            &self.building_recipe_registry,
        ) {
            Ok(()) => {
                self.scene_cursor_x = (self.scene_cursor_x + dx).clamp(0, MAP_W as i32 - 1);
                self.scene_cursor_y = (self.scene_cursor_y + dy).clamp(0, MAP_H as i32 - 1);
                self.status_message = match self
                    .building_instance_registry
                    .save_authored_to_project_root(repo_root_dir())
                {
                    Ok(()) => format!(
                        "Moved and saved BuildingInstance {} by {}, {}. Stable id preserved.",
                        resolved.id, dx, dy
                    ),
                    Err(error) => format!(
                        "Moved BuildingInstance {}, but source persistence failed: {error}",
                        resolved.id
                    ),
                };
                self.command_bus.record_event(self.app_command(
                    EditorCommandKind::SceneMutation,
                    self.status_message.clone(),
                ));
            }
            Err(error) => self.status_message = format!("Building move failed: {error}"),
        }
        true
    }

    pub(crate) fn delete_building_instance_at_scene_cursor(&mut self) -> bool {
        let Some(instance) = self.building_at_scene_cursor() else {
            self.status_message = "No BuildingInstance footprint under the scene cursor".to_string();
            return true;
        };
        match self
            .building_instance_registry
            .delete_authored_instance(&instance.id, &self.building_recipe_registry)
        {
            Ok(()) => {
                self.building_preview_views.remove(&instance.id);
                self.status_message = match self
                    .building_instance_registry
                    .save_authored_to_project_root(repo_root_dir())
                {
                    Ok(()) => format!(
                        "Deleted and saved authored BuildingInstance {}.",
                        instance.id
                    ),
                    Err(error) => format!(
                        "Deleted BuildingInstance {}, but source persistence failed: {error}",
                        instance.id
                    ),
                };
                self.command_bus.record_event(self.app_command(
                    EditorCommandKind::SceneMutation,
                    self.status_message.clone(),
                ));
            }
            Err(error) => self.status_message = format!("Building delete failed: {error}"),
        }
        true
    }

    pub(crate) fn cycle_building_preview_level(&mut self, delta: i32) -> bool {
        let Some(instance) = self.first_building_in_current_scene() else {
            return false;
        };
        let Some(recipe) = self.building_recipe_registry.entry(&instance.recipe_id) else {
            return false;
        };
        let mut levels = recipe.levels.iter().map(|level| level.level).collect::<Vec<_>>();
        levels.sort_unstable();
        levels.dedup();
        if levels.is_empty() {
            return false;
        }
        let linked_interior = recipe.persistence.interior_policy == "linked_enclosed_scene";
        let state = self
            .building_preview_views
            .entry(instance.id.clone())
            .or_insert_with(|| {
                let mut state = BuildingInstanceViewState::for_definition(&instance);
                state.inside = !linked_interior;
                state
            });
        let current = levels
            .iter()
            .position(|level| *level == state.active_level)
            .unwrap_or(0) as i32;
        let next = (current + delta).clamp(0, levels.len() as i32 - 1) as usize;
        state.active_level = levels[next];
        state.inside = !linked_interior;
        self.status_message = format!(
            "Building preview {}: structural level {} (PageUp/PageDown)",
            instance.id, state.active_level
        );
        true
    }

    pub(crate) fn toggle_building_preview_cutaway(&mut self) -> bool {
        let Some(instance) = self.first_building_in_current_scene() else {
            return false;
        };
        let Some(recipe) = self.building_recipe_registry.entry(&instance.recipe_id) else {
            return false;
        };
        if recipe.persistence.interior_policy == "linked_enclosed_scene" {
            self.status_message = format!(
                "Building preview {} uses a linked EnclosedScene interior; keep the exterior intact and use Open Interior to author the inside.",
                instance.id
            );
            return true;
        }
        let state = self
            .building_preview_views
            .entry(instance.id.clone())
            .or_insert_with(|| BuildingInstanceViewState::for_definition(&instance));
        state.inside = !state.inside;
        self.status_message = format!(
            "Building preview {}: {} (Home toggles cutaway)",
            instance.id,
            if state.inside {
                format!("cutaway level {}", state.active_level)
            } else {
                "exterior roof view".to_string()
            }
        );
        true
    }

    pub(crate) fn building_preview_label(&self, scene: &SceneMap) -> Option<String> {
        let instance = self.resolved_building_instances_for_scene(scene).into_iter().next()?;
        let state = self
            .building_preview_views
            .get(&instance.id)
            .copied()
            .unwrap_or_else(|| {
                self.building_recipe_registry
                    .entry(&instance.recipe_id)
                    .map(|recipe| building_preview_state_for_recipe(&instance, recipe))
                    .unwrap_or_else(|| BuildingInstanceViewState::for_definition(&instance))
            });
        Some(if state.inside {
            format!(
                "Building cutaway L{} | PgUp/PgDn floor | Home exterior | Ctrl+B place | Ctrl+Alt+Arrows move | Ctrl+Shift+B delete",
                state.active_level
            )
        } else {
            "Building exterior/roof | Home cutaway | PgUp/PgDn floor | Ctrl+B place".to_string()
        })
    }
}

fn building_authoring_action_rect(rect: Rect, index: usize) -> Rect {
    let gap = 6.0;
    let width = ((rect.w - gap) * 0.5).max(92.0);
    Rect::new(
        rect.x + (index % 2) as f32 * (width + gap),
        rect.y + 118.0 + (index / 2) as f32 * 38.0,
        width,
        31.0,
    )
}

#[cfg(test)]
mod w57l_preview_tests {
    use super::*;
    use haven_assets::{
        building_instance::BuildingInstanceRegistry,
        building_recipe::BuildingRecipeRegistry,
    };

    #[test]
    fn linked_interior_preview_starts_as_intact_exterior() {
        let project_root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
        let recipes = BuildingRecipeRegistry::load_from_project_root(&project_root)
            .expect("building recipes should load");
        let instances = BuildingInstanceRegistry::load_from_project_root(&project_root, &recipes)
            .expect("building instances should load");
        let instance = instances
            .entry("havenwild.estate.dev.starter_cottage")
            .expect("Estate cottage instance should exist");
        let recipe = recipes
            .entry(&instance.recipe_id)
            .expect("Estate cottage recipe should exist");
        let state = building_preview_state_for_recipe(instance, recipe);
        assert!(!state.inside);
        assert_eq!(state.active_level, recipe.default_level);
    }
}
