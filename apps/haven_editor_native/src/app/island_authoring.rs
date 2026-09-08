use std::collections::BTreeSet;

use haven_assets::asset_registry::audited_object_footprint_for_cell;
use haven_core::ProjectSceneId;
use haven_editor::{create_project_scene, EditorCommandKind, EditorCommandSource};
use haven_world::{
    archipelago_layout::{generate_archipelago_layout, rerolled_archipelago_seed},
    island_pcg::{generate_landmass, GeneratedIsland, IslandGenerationSettings},
    region_graph::{connect_generated_island_harbor, RegionPoint},
    ProductionWorldGenerationPlan,
};
use macroquad::prelude::*;

use super::workspace_shell::RightDockTab;
use super::world_canvas_context::{
    context_menu_action_at, WorldCanvasContextAction, WorldCanvasContextMenu,
};
use super::*;

impl EditorApp {
    pub(crate) fn restore_generated_harbor_routes(&mut self) {
        let Some(manifest) = &self.scene_rectangles else {
            return;
        };
        let routes: Vec<(i32, String, ProjectSceneId, String)> = self
            .scene_assignments
            .assignments
            .iter()
            .filter(|assignment| assignment.role == "harbor")
            .filter_map(|assignment| {
                let rectangle = manifest
                    .scene_rectangles
                    .iter()
                    .find(|rectangle| rectangle.scene_id == assignment.rectangle_id)?;
                let scene_id = ProjectSceneId::new(assignment.scene_code.clone());
                self.model.world.scene_by_id(&scene_id).map(|_| {
                    (
                        rectangle.landmass_id,
                        rectangle.landmass_name.clone(),
                        scene_id,
                        rectangle.scene_id.clone(),
                    )
                })
            })
            .collect();
        for (landmass_id, landmass_name, scene_id, rectangle_id) in routes {
            let position = self.rectangle_preview_center(&rectangle_id);
            connect_generated_island_harbor(
                &mut self.model.region_graph,
                landmass_id,
                &landmass_name,
                scene_id,
                position,
            );
        }
        self.apply_custom_harbor_routes();
    }

    pub(crate) fn open_world_canvas_context_menu(&mut self) -> bool {
        if self.viewport_mode != EditorViewportMode::SceneRectangles {
            return false;
        }
        let Some(manifest) = &self.scene_rectangles else {
            return false;
        };
        let Some(bounds) =
            world_scene_grid_bounds_for_landmass(manifest, self.selected_landmass_id)
        else {
            return false;
        };
        let viewport = self.world_canvas_viewport_rect();
        let (mx, my) = mouse_position();
        let mouse = vec2(mx, my);
        if !viewport.contains(mouse) {
            self.world_canvas_context_menu = None;
            return false;
        }
        let world_point = self.world_canvas.screen_to_world(viewport, bounds, mouse);
        let Some(index) = manifest
            .scene_rectangles
            .iter()
            .enumerate()
            .rev()
            .find(|(_, rectangle)| {
                rectangle_is_overworld_surface(rectangle)
                    && rectangle.landmass_id == self.selected_landmass_id
                    && world_scene_grid_rect(manifest, rectangle).contains(world_point)
            })
            .map(|(index, _)| index)
        else {
            self.world_canvas_context_menu = None;
            return true;
        };
        self.selected_rectangle = index;
        self.world_cursor_x = world_point.x.floor() as i32;
        self.world_cursor_y = world_point.y.floor() as i32;
        self.sync_assignment_cycles_to_selected_rectangle();
        self.world_canvas_context_menu = Some(WorldCanvasContextMenu {
            screen_position: mouse,
            rectangle_index: index,
            advanced: false,
        });
        self.status_message = "Opened global world-cell context actions".to_string();
        true
    }

    pub(crate) fn handle_world_canvas_context_click(&mut self, mx: f32, my: f32) -> bool {
        let Some(menu) = self.world_canvas_context_menu else {
            return false;
        };
        let point = vec2(mx, my);
        let action = context_menu_action_at(menu, point);
        self.world_canvas_context_menu = None;
        let Some(action) = action else {
            return false;
        };
        self.selected_rectangle = menu.rectangle_index;
        match action {
            WorldCanvasContextAction::PlayHere => self.play_development_world(true),
            WorldCanvasContextAction::EditTilePixels => {
                self.open_world_surface_tile_source_in_pixel_studio()
            }
            WorldCanvasContextAction::EditRegionPixels => {
                if self.world_selection.is_none() {
                    self.world_selection = Some(GridRect::single(GridPos {
                        x: self.world_cursor_x,
                        y: self.world_cursor_y,
                    }));
                }
                self.open_world_selection_in_pixel_studio();
            }
            WorldCanvasContextAction::CopyRegion => self.copy_world_selection(),
            WorldCanvasContextAction::DuplicateRegion => {
                if self.world_selection.is_none() {
                    self.world_selection = Some(GridRect::single(GridPos {
                        x: self.world_cursor_x,
                        y: self.world_cursor_y,
                    }));
                }
                self.duplicate_world_selection();
            }
            WorldCanvasContextAction::PromotePcg => {
                if self.world_selection.is_none() {
                    self.world_selection = Some(GridRect::single(GridPos {
                        x: self.world_cursor_x,
                        y: self.world_cursor_y,
                    }));
                }
                self.promote_world_selection_to_pcg_exemplar();
            }
            WorldCanvasContextAction::OpenAssets => {
                self.focus_right_dock(RightDockTab::Assets);
                self.status_message = "Opened World Assets".to_string();
            }
            WorldCanvasContextAction::OpenSelection => {
                self.focus_right_dock(RightDockTab::Properties);
                self.status_message = "Opened World Selection properties".to_string();
            }
            WorldCanvasContextAction::ClearSelection => {
                self.world_selection = None;
                self.status_message = "World region selection cleared".to_string();
            }
            WorldCanvasContextAction::AdvancedGeneration => {
                self.world_canvas_context_menu = Some(WorldCanvasContextMenu {
                    advanced: true,
                    ..menu
                });
                self.status_message = "Opened advanced PCG / partition actions".to_string();
            }
            WorldCanvasContextAction::BackToAuthoring => {
                self.world_canvas_context_menu = Some(WorldCanvasContextMenu {
                    advanced: false,
                    ..menu
                });
                self.status_message = "Returned to world authoring actions".to_string();
            }
            WorldCanvasContextAction::OpenScene => self.open_assigned_rectangle_scene(),
            WorldCanvasContextAction::AssignSelected => self.assign_selected_scene_to_rectangle(),
            WorldCanvasContextAction::ClearAssignment => self.clear_selected_rectangle_assignment(),
            WorldCanvasContextAction::GenerateScene => self.generate_selected_rectangle_scene(),
            WorldCanvasContextAction::GenerateIsland => self.generate_selected_landmass(),
            WorldCanvasContextAction::GenerateAllIslands => self.generate_all_landmasses(),
            WorldCanvasContextAction::FrameIsland => self.frame_selected_landmass(),
            WorldCanvasContextAction::RefreshHarborRoute => self.refresh_selected_harbor_route(),
            WorldCanvasContextAction::MoveLeft => self.move_selected_scene_cell(-1, 0),
            WorldCanvasContextAction::MoveUp => self.move_selected_scene_cell(0, -1),
            WorldCanvasContextAction::MoveDown => self.move_selected_scene_cell(0, 1),
            WorldCanvasContextAction::MoveRight => self.move_selected_scene_cell(1, 0),
        }
        true
    }

    pub(crate) fn selected_rectangle_spec(
        &self,
    ) -> Option<&haven_world::scene_rectangles::SceneRectangleSpec> {
        self.scene_rectangles
            .as_ref()?
            .scene_rectangles
            .get(self.selected_rectangle)
    }

    pub(crate) fn open_assigned_rectangle_scene(&mut self) {
        let Some(rectangle_id) = self
            .selected_rectangle_spec()
            .map(|rectangle| rectangle.scene_id.clone())
        else {
            return;
        };
        let Some(scene_code) = self
            .scene_assignments
            .assignment_for_rectangle(&rectangle_id)
            .map(|assignment| assignment.scene_code.clone())
        else {
            self.status_message = format!("{rectangle_id} has no assigned scene");
            return;
        };
        let scene_id = ProjectSceneId::new(scene_code);
        let Some(index) = self.model.world.scenes.position(&scene_id) else {
            self.status_message = format!("Assigned scene {scene_id} is not loaded");
            return;
        };
        self.select_scene_index(index);
        self.viewport_mode = EditorViewportMode::SceneMap;
        self.status_message = format!("Opened {} for editing", scene_id.label());
    }

    fn generate_selected_rectangle_scene(&mut self) {
        let Some(rectangle) = self.selected_rectangle_spec().cloned() else {
            return;
        };
        let Some(manifest) = &self.scene_rectangles else {
            return;
        };
        match generate_landmass(
            manifest,
            rectangle.landmass_id,
            self.island_generation_settings(rectangle.landmass_id),
        ) {
            Ok(mut generated) => {
                let Some(mut generated_scene) = generated
                    .scenes
                    .drain(..)
                    .find(|entry| entry.rectangle_id == rectangle.scene_id)
                else {
                    self.status_message =
                        "Generator did not return the selected rectangle".to_string();
                    return;
                };
                generated_scene.scene.transitions.retain(|transition| {
                    self.model
                        .world
                        .scene_by_reference(&transition.target)
                        .is_some()
                });
                self.install_generated_scene(
                    generated_scene.rectangle_id,
                    generated_scene.scene,
                    generated.harbor_rectangle_id,
                );
                self.status_message = format!(
                    "Generated editable scene cell {} on {}",
                    rectangle.scene_id, generated.landmass_name
                );
            }
            Err(error) => self.status_message = format!("Scene generation failed: {error}"),
        }
    }

    fn generate_selected_landmass(&mut self) {
        let Some(landmass_id) = self
            .selected_rectangle_spec()
            .map(|entry| entry.landmass_id)
        else {
            return;
        };
        self.generate_landmass_by_id(landmass_id);
    }

    fn production_world_plan_for_current_manifest(
        &self,
        seed: u64,
    ) -> Result<ProductionWorldGenerationPlan, String> {
        let manifest = self
            .scene_rectangles
            .as_ref()
            .ok_or_else(|| "scene rectangle manifest is unavailable".to_string())?;
        let major_landmass_count = manifest
            .scene_rectangles
            .iter()
            .filter(|entry| rectangle_is_overworld_surface(entry))
            .map(|entry| entry.landmass_id)
            .collect::<BTreeSet<_>>()
            .len();
        if !(3..=15).contains(&major_landmass_count) {
            return Err(format!(
                "Development World topology must expose 3-15 major landmasses; current compatibility manifest exposes {major_landmass_count}"
            ));
        }
        let mut settings = self.development_world_settings.clone();
        settings.seed = seed.max(1);
        settings.land.major_landmass_count = major_landmass_count as u8;
        ProductionWorldGenerationPlan::from_settings(&settings)
    }

    pub(crate) fn production_world_generation_summary(&self) -> String {
        let seed = self
            .scene_rectangles
            .as_ref()
            .map(|manifest| manifest.archipelago_generation.seed)
            .unwrap_or(self.development_world_settings.seed);
        match self.production_world_plan_for_current_manifest(seed) {
            Ok(plan) => format!(
                "Production World · seed {} · {} major landmasses · {} deterministic stages · ocean-bounded · authored overrides preserved",
                plan.seed,
                plan.major_landmass_count,
                plan.stages.len(),
            ),
            Err(error) => format!("Production World plan invalid: {error}"),
        }
    }

    pub(crate) fn regenerate_current_archipelago_seed(&mut self) {
        let seed = self
            .scene_rectangles
            .as_ref()
            .map(|manifest| manifest.archipelago_generation.seed)
            .unwrap_or(self.development_world_settings.seed);
        let plan = match self.production_world_plan_for_current_manifest(seed) {
            Ok(plan) => plan,
            Err(error) => {
                self.status_message = format!("Production World generation blocked: {error}");
                return;
            }
        };
        match self.apply_archipelago_layout(seed) {
            Ok(report) => {
                self.generate_all_landmasses();
                self.status_message = format!(
                    "Regenerated Development World · {} major landmasses · seed {} · {} production stages validated · {}px compatibility-layout gap · authored overrides remain a separate authority",
                    report.island_count, report.seed, plan.stages.len(), report.minimum_gap_px
                );
            }
            Err(error) => {
                self.status_message = format!("Archipelago layout failed: {error}");
            }
        }
    }

    pub(crate) fn reroll_structural_archipelago(&mut self) {
        let (current_seed, next_reroll_index) = self
            .scene_rectangles
            .as_ref()
            .map(|manifest| {
                (
                    manifest.archipelago_generation.seed,
                    manifest
                        .archipelago_generation
                        .reroll_index
                        .saturating_add(1),
                )
            })
            .unwrap_or((self.development_world_settings.seed, 1));
        let next_seed = rerolled_archipelago_seed(current_seed, next_reroll_index);
        if let Err(error) = self.production_world_plan_for_current_manifest(next_seed) {
            self.status_message = format!("Production World reroll blocked: {error}");
            return;
        }
        match self.apply_archipelago_layout(next_seed) {
            Ok(report) => {
                if let Some(manifest) = self.scene_rectangles.as_mut() {
                    manifest.archipelago_generation.reroll_index = next_reroll_index;
                }
                self.generate_all_landmasses();
                self.status_message = format!(
                    "Rerolled archipelago seed {}: {} islands placed with a {}px minimum gap. New saves can reuse or replace this shareable seed.",
                    report.seed, report.island_count, report.minimum_gap_px
                );
            }
            Err(error) => {
                self.status_message = format!("Archipelago reroll failed: {error}");
            }
        }
    }

    fn apply_archipelago_layout(
        &mut self,
        seed: u64,
    ) -> Result<haven_world::archipelago_layout::ArchipelagoLayoutReport, String> {
        let manifest = self
            .scene_rectangles
            .as_mut()
            .ok_or_else(|| "scene rectangle manifest is unavailable".to_string())?;
        let report = generate_archipelago_layout(manifest, seed)?;
        let major_landmass_count = manifest
            .scene_rectangles
            .iter()
            .filter(|entry| rectangle_is_overworld_surface(entry))
            .map(|entry| entry.landmass_id)
            .collect::<BTreeSet<_>>()
            .len()
            .clamp(3, 15) as u8;
        self.development_world_settings.seed = seed.max(1);
        self.development_world_settings.land.major_landmass_count = major_landmass_count;
        self.development_world_semantic_bake = development_session::development_semantic_world_bake(
            &self.development_world_settings,
        );
        self.model.region_graph = haven_world::region_graph::starter_island_region_graph();
        self.route_source_landmass_id = None;
        Ok(report)
    }

    pub(crate) fn generate_all_landmasses(&mut self) {
        let Some(manifest) = &self.scene_rectangles else {
            return;
        };
        let landmasses: BTreeSet<i32> = manifest
            .scene_rectangles
            .iter()
            .filter(|entry| rectangle_is_overworld_surface(entry))
            .map(|entry| entry.landmass_id)
            .collect();
        let total = landmasses.len();
        let exterior_cells = manifest
            .scene_rectangles
            .iter()
            .filter(|entry| rectangle_is_overworld_surface(entry))
            .count();
        let mut generated = 0usize;
        for landmass_id in landmasses {
            if self.generate_landmass_by_id_internal(landmass_id).is_ok() {
                generated += 1;
            }
        }
        let world_scene_total = self.model.world.scenes.len();
        self.status_message = format!(
            "Generated {generated}/{total} structural islands across {exterior_cells} exterior cells; world now contains {world_scene_total} scenes. Use Save All to persist."
        );
    }

    fn generate_landmass_by_id(&mut self, landmass_id: i32) {
        match self.generate_landmass_by_id_internal(landmass_id) {
            Ok(summary) => self.status_message = summary,
            Err(error) => self.status_message = format!("Island generation failed: {error}"),
        }
    }

    fn generate_landmass_by_id_internal(&mut self, landmass_id: i32) -> Result<String, String> {
        let manifest = self
            .scene_rectangles
            .as_ref()
            .ok_or_else(|| "scene rectangle manifest is unavailable".to_string())?;
        let generated = generate_landmass(
            manifest,
            landmass_id,
            self.island_generation_settings(landmass_id),
        )?;
        let summary = self.install_generated_island(generated)?;
        Ok(summary)
    }

    fn install_generated_island(&mut self, generated: GeneratedIsland) -> Result<String, String> {
        let harbor_rectangle = generated.harbor_rectangle_id.clone();
        let scene_count = generated.scenes.len();
        let natural_objects = generated.natural_objects;
        let mainland_features = generated.mainland_features;
        for entry in generated.scenes {
            let mut scene = entry.scene;
            for object in &mut scene.map.objects {
                object.footprint =
                    audited_object_footprint_for_cell(object.kind, object.x, object.y);
            }
            self.install_generated_scene(entry.rectangle_id, scene, harbor_rectangle.clone());
        }
        let position = self.rectangle_preview_center(&harbor_rectangle);
        connect_generated_island_harbor(
            &mut self.model.region_graph,
            generated.landmass_id,
            &generated.landmass_name,
            generated.harbor_scene_id,
            position,
        );
        self.apply_custom_harbor_routes();
        self.command_bus.record_event(self.app_command(
            EditorCommandKind::SceneMutation,
            format!("Generated procedural island {}", generated.landmass_name),
        ));
        Ok(format!(
            "Generated structural {} across {} editable scene cells | grass land {} cells | shoreline {} cells | {} authored natural/resource objects | {} road tiles across {} partitions | {} Willowmere plot reservations | {} cave entrance(s) | harbor connected to World Routes",
            generated.landmass_name,
            scene_count,
            generated.land_cells,
            generated.shoreline_cells,
            natural_objects,
            mainland_features.road_tiles,
            mainland_features.road_partitions,
            mainland_features.city_plot_reservations,
            mainland_features.cave_entrances,
        ))
    }

    fn install_generated_scene(
        &mut self,
        rectangle_id: String,
        scene: haven_core::SceneMap,
        harbor_rectangle_id: String,
    ) {
        let scene_id = scene.id.clone();
        if let Some(existing) = self.model.world.scene_mut_by_id(&scene_id) {
            *existing = scene;
        } else {
            let project_id = self.model.project.project_id.clone();
            let _ = create_project_scene(
                &mut self.model.world,
                &mut self.command_bus,
                &project_id,
                EditorCommandSource::MainEditor,
                scene,
            );
        }
        if !self
            .model
            .project
            .scenes
            .iter()
            .any(|existing| existing == scene_id.code())
        {
            self.model.project.scenes.push(scene_id.code().to_string());
        }
        let is_harbor = rectangle_id == harbor_rectangle_id;
        self.scene_assignments.assign_scene_to_rectangle(
            scene_id.code(),
            &rectangle_id,
            if is_harbor { "harbor" } else { "forest_border" },
            if is_harbor { "civic" } else { "wilderness" },
        );
    }

    pub(crate) fn frame_entire_world(&mut self) {
        let Some(bake) = self.development_world_semantic_bake.as_ref() else {
            self.status_message = "Development World has no canonical semantic world bake".to_string();
            return;
        };
        let Some(bounds) = world_archipelago_overview_bounds(bake) else {
            self.status_message = "Development World semantic bake has invalid bounds".to_string();
            return;
        };
        self.world_show_entire_world = true;
        self.viewport_mode = EditorViewportMode::SceneRectangles;
        let viewport = self.world_canvas_viewport_rect();
        self.world_canvas.frame_rect(viewport, bounds, bounds);
        self.status_message =
            "Opened the complete persistent Havenwild Development World".to_string();
    }

    pub(crate) fn frame_selected_landmass(&mut self) {
        let Some((landmass_id, landmass_name)) = self
            .selected_rectangle_spec()
            .map(|rectangle| (rectangle.landmass_id, rectangle.landmass_name.clone()))
        else {
            return;
        };
        let Some(manifest) = &self.scene_rectangles else {
            return;
        };
        let Some(bounds) = world_scene_grid_bounds_for_landmass(manifest, landmass_id) else {
            return;
        };
        self.world_show_entire_world = false;
        let mut target: Option<Rect> = None;
        for entry in manifest.scene_rectangles.iter().filter(|entry| {
            entry.landmass_id == landmass_id && rectangle_is_overworld_surface(entry)
        }) {
            let rect = world_scene_grid_rect(manifest, entry);
            target = Some(match target {
                Some(current) => union_rect(current, rect),
                None => rect,
            });
        }
        if let Some(target) = target {
            let viewport = self.world_canvas_viewport_rect();
            self.world_canvas.frame_rect(viewport, bounds, target);
            self.status_message = format!("Framed landmass {landmass_name}");
        }
    }

    pub(crate) fn refresh_selected_harbor_route(&mut self) {
        let Some(landmass_id) = self
            .selected_rectangle_spec()
            .map(|entry| entry.landmass_id)
        else {
            return;
        };
        let Some(manifest) = &self.scene_rectangles else {
            return;
        };
        match generate_landmass(
            manifest,
            landmass_id,
            self.island_generation_settings(landmass_id),
        ) {
            Ok(generated) => {
                let position = self.rectangle_preview_center(&generated.harbor_rectangle_id);
                connect_generated_island_harbor(
                    &mut self.model.region_graph,
                    generated.landmass_id,
                    &generated.landmass_name,
                    generated.harbor_scene_id,
                    position,
                );
                self.apply_custom_harbor_routes();
                self.status_message = format!(
                    "World Routes harbor node refreshed for {}",
                    generated.landmass_name
                );
            }
            Err(error) => self.status_message = format!("Harbor route failed: {error}"),
        }
    }

    fn island_generation_settings(&self, landmass_id: i32) -> IslandGenerationSettings {
        let world_seed = self
            .scene_rectangles
            .as_ref()
            .map(|manifest| manifest.archipelago_generation.seed)
            .unwrap_or(self.development_world_settings.seed);
        IslandGenerationSettings {
            seed: world_seed ^ (landmass_id as i64 as u64).wrapping_mul(0x9e37_79b9_7f4a_7c15),
            mountain_radius: if landmass_id == 0 { 0.44 } else { 0.31 },
            shoreline_width: 0.12,
            tree_density: haven_world::island_pcg::natural_object_density_for_landmass(landmass_id),
            geography: haven_world::GeographicGenerationProfile::from_world_creation(
                &self.development_world_settings,
            ),
        }
    }

    fn rectangle_preview_center(&self, rectangle_id: &str) -> RegionPoint {
        let Some(manifest) = &self.scene_rectangles else {
            return RegionPoint::new(0.5, 0.5);
        };
        let Some(rectangle) = manifest
            .scene_rectangles
            .iter()
            .find(|entry| entry.scene_id == rectangle_id)
        else {
            return RegionPoint::new(0.5, 0.5);
        };
        let min_x = manifest
            .scene_rectangles
            .iter()
            .map(|entry| entry.world_rect_preview_px[0])
            .min()
            .unwrap_or(0) as f32;
        let min_y = manifest
            .scene_rectangles
            .iter()
            .map(|entry| entry.world_rect_preview_px[1])
            .min()
            .unwrap_or(0) as f32;
        let max_x = manifest
            .scene_rectangles
            .iter()
            .map(|entry| entry.world_rect_preview_px[0] + entry.world_rect_preview_px[2])
            .max()
            .unwrap_or(1) as f32;
        let max_y = manifest
            .scene_rectangles
            .iter()
            .map(|entry| entry.world_rect_preview_px[1] + entry.world_rect_preview_px[3])
            .max()
            .unwrap_or(1) as f32;
        let [x, y, width, height] = rectangle.world_rect_preview_px;
        let center_x = x as f32 + width as f32 * 0.5;
        let center_y = y as f32 + height as f32 * 0.78;
        RegionPoint::new(
            ((center_x - min_x) / (max_x - min_x).max(1.0)).clamp(0.04, 0.96),
            ((center_y - min_y) / (max_y - min_y).max(1.0)).clamp(0.04, 0.96),
        )
    }
}

fn union_rect(left: Rect, right: Rect) -> Rect {
    let min_x = left.x.min(right.x);
    let min_y = left.y.min(right.y);
    let max_x = (left.x + left.w).max(right.x + right.w);
    let max_y = (left.y + left.h).max(right.y + right.h);
    Rect::new(min_x, min_y, max_x - min_x, max_y - min_y)
}
