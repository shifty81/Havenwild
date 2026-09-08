use super::pixel_studio::{PixelInspectorTab, WorldAssetEditContext};
use super::scene_asset_context::{action_at, SceneAssetContextAction, SceneAssetContextMenu};
use super::*;
use haven_assets::asset_intake::repo_root_dir;
use haven_pixel::{PixelAssetKind, PixelDocument, PixelPreviewMode, PixelSelection};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use image::imageops::FilterType;

#[derive(Clone, Debug)]
struct ResolvedWorldAsset {
    semantic_id: String,
    source_path: String,
    source_rect: PixelSelection,
    generated_output: bool,
}

impl EditorApp {
    pub(crate) fn open_scene_asset_context_menu(&mut self) -> bool {
        if self.viewport_mode != EditorViewportMode::SceneMap {
            return false;
        }
        let Some((x, y)) = self.scene_cell_at_mouse() else {
            return false;
        };
        self.scene_cursor_x = x;
        self.scene_cursor_y = y;
        let object_hit = self
            .model
            .world
            .scenes
            .get(self.selected_scene)
            .and_then(|scene| hit_test_scene_cell(
                scene,
                GridPos { x, y },
                SceneAuthoringLayer::Objects,
            ));
        let object_id = object_hit.as_ref().and_then(|hit| match hit.selection_item() {
            SelectionItem::Object(id) => Some(id),
            _ => None,
        });
        if let Some(hit) = object_hit {
            self.select_scene_hit(hit);
        }
        let (mx, my) = mouse_position();
        let has_building = self.building_at_scene_cursor().is_some();
        self.scene_asset_context_menu = Some(SceneAssetContextMenu {
            screen_position: vec2(mx, my),
            cell: [x, y],
            object_id,
            has_building,
        });
        self.status_message = if let Some(id) = object_id {
            format!("Opened exact-source asset actions for object {:?} at {x}, {y}", id)
        } else {
            format!("Opened asset actions for terrain tile {x}, {y}")
        };
        true
    }

    pub(crate) fn handle_scene_asset_context_click(&mut self, mx: f32, my: f32) -> bool {
        let Some(menu) = self.scene_asset_context_menu else {
            return false;
        };
        let selected = action_at(menu, vec2(mx, my));
        self.scene_asset_context_menu = None;
        let Some(action) = selected else {
            return false;
        };
        self.scene_cursor_x = menu.cell[0];
        self.scene_cursor_y = menu.cell[1];
        match action {
            SceneAssetContextAction::EditAssetSource => {
                if let Some(object_id) = menu.object_id {
                    self.open_scene_object_source_in_pixel_studio(object_id);
                } else {
                    self.open_scene_tile_source_in_pixel_studio();
                }
            }
            SceneAssetContextAction::EditCellVariant => {
                self.open_scene_cell_variant_in_pixel_studio();
            }
            SceneAssetContextAction::EditSelection => {
                self.open_scene_selection_in_pixel_studio();
            }
            SceneAssetContextAction::EditBuildingComposite => {
                self.open_scene_building_composite_in_pixel_studio();
            }
            SceneAssetContextAction::EditSceneChunk => {
                self.open_active_scene_chunk_in_pixel_studio();
            }
            SceneAssetContextAction::InspectBinding => {
                if let Some(object_id) = menu.object_id {
                    self.inspect_scene_object_asset_binding(object_id);
                } else {
                    self.inspect_scene_tile_asset_binding();
                }
            }
            SceneAssetContextAction::RebuildNeighborhood => {
                self.autotile_caches.remove(
                    &self
                        .active_scene_id()
                        .unwrap_or_else(|| ProjectSceneId::new("none")),
                );
                self.status_message = format!(
                    "Invalidated terrain neighborhood around {}, {}",
                    menu.cell[0], menu.cell[1]
                );
            }
            SceneAssetContextAction::RevealSource => {
                if let Some(object_id) = menu.object_id {
                    self.reveal_scene_object_source(object_id);
                } else {
                    self.reveal_scene_tile_source();
                }
            }
        }
        true
    }

    fn resolve_scene_object_asset(&self, object_id: haven_editor::ObjectId) -> Option<ResolvedWorldAsset> {
        let scene = self.model.world.scenes.get(self.selected_scene)?;
        let object = scene.map.object(object_id)?;
        let definition = scene
            .map
            .object_asset_ref(object_id)
            .and_then(|asset_ref| self.placeable_registry.resolve_persistent_ref(asset_ref))
            .or_else(|| self.placeable_registry.for_legacy_object(object.kind))?;
        let source_path = definition.provenance.source_path.as_ref()?.clone();
        let source_rect = definition.provenance.source_rect?;
        let [x, y, width, height] = source_rect;
        if x < 0 || y < 0 || width <= 0 || height <= 0 {
            return None;
        }
        Some(ResolvedWorldAsset {
            semantic_id: definition.semantic_id.clone(),
            source_path,
            source_rect: PixelSelection {
                x: x as u32,
                y: y as u32,
                width: width as u32,
                height: height as u32,
            },
            generated_output: false,
        })
    }

    fn inspect_scene_object_asset_binding(&mut self, object_id: haven_editor::ObjectId) {
        self.status_message = self.resolve_scene_object_asset(object_id).map_or_else(
            || format!("Object {:?} has no reviewed exact-source binding yet", object_id),
            |binding| format!(
                "Object {:?} -> {} [{} x={}, y={}, {}x{}]",
                object_id,
                binding.semantic_id,
                binding.source_path,
                binding.source_rect.x,
                binding.source_rect.y,
                binding.source_rect.width,
                binding.source_rect.height,
            ),
        );
    }

    fn reveal_scene_object_source(&mut self, object_id: haven_editor::ObjectId) {
        self.status_message = self.resolve_scene_object_asset(object_id).map_or_else(
            || format!("Object {:?} has no reviewed exact-source binding", object_id),
            |binding| format!("Source: {} [{} ,{} {}x{}]", binding.source_path, binding.source_rect.x, binding.source_rect.y, binding.source_rect.width, binding.source_rect.height),
        );
    }

    pub(crate) fn open_scene_object_source_in_pixel_studio(&mut self, object_id: haven_editor::ObjectId) {
        let Some(scene_id) = self.active_scene_id() else { return; };
        let Some(binding) = self.resolve_scene_object_asset(object_id) else {
            self.status_message = format!("Object {:?} has no reviewed exact source; W43/W45 disposition remains authoritative", object_id);
            return;
        };
        self.open_resolved_world_asset_source(scene_id, binding, Some(object_id));
    }

    fn selected_scene_tile(&self) -> Option<TileKind> {
        self.model
            .world
            .scenes
            .get(self.selected_scene)
            .map(|scene| scene.map.get(self.scene_cursor_x, self.scene_cursor_y))
    }

    fn resolve_selected_world_asset(&self) -> Option<ResolvedWorldAsset> {
        self.resolve_selected_structural_cliff_asset()
            .or_else(|| resolve_tile_asset(self.selected_scene_tile()?))
    }

    /// Mirrors the deliberately narrow runtime cliff lane certified in Z105/Z106.
    /// A structural cliff is not a 32x32 ground tile: the only runtime-visible
    /// recipe currently certified is the complete ElizaWy 1x3 straight south
    /// face. Keep editor inspection on that same authority instead of inventing
    /// corner/diagonal bindings that runtime cannot yet draw.
    fn resolve_selected_structural_cliff_asset(&self) -> Option<ResolvedWorldAsset> {
        let scene = self.model.world.scenes.get(self.selected_scene)?;
        let x = self.scene_cursor_x;
        let y = self.scene_cursor_y;
        if x == 0 || x + 1 >= MAP_W as i32 || y + 1 >= MAP_H as i32 {
            return None;
        }
        let level = |cx: i32, cy: i32| scene.map.get_structural_level(cx, cy).unwrap_or(0);
        let south_exposed = |cx: i32| level(cx, y) > level(cx, y + 1);
        if !south_exposed(x) || !south_exposed(x - 1) || !south_exposed(x + 1) {
            return None;
        }
        Some(ResolvedWorldAsset {
            semantic_id: "terrain.cliff.elizawy.south_repeat_a_1x3".to_string(),
            source_path: "assets/source/licensed/lpc_revised/Terrain/cliff_summer.png".to_string(),
            source_rect: PixelSelection { x: 320, y: 288, width: 32, height: 96 },
            generated_output: false,
        })
    }

    fn inspect_scene_tile_asset_binding(&mut self) {
        let Some(tile) = self.selected_scene_tile() else {
            return;
        };
        let structural = self.selected_structural_cliff_diagnostic();
        self.status_message = match self.resolve_selected_world_asset() {
            Some(binding) => format!(
                "{:?} -> {} [{} x={}, y={}, {}x{}]{}",
                tile,
                binding.semantic_id,
                binding.source_path,
                binding.source_rect.x,
                binding.source_rect.y,
                binding.source_rect.width,
                binding.source_rect.height,
                structural.as_deref().map(|value| format!(" | {value}")).unwrap_or_default()
            ),
            None => format!("{:?} has no reviewed editable source binding yet", tile),
        };
    }

    fn selected_structural_cliff_diagnostic(&self) -> Option<String> {
        let scene = self.model.world.scenes.get(self.selected_scene)?;
        let x = self.scene_cursor_x;
        let y = self.scene_cursor_y;
        if y + 1 >= MAP_H as i32 { return None; }
        let current = scene.map.get_structural_level(x, y).unwrap_or(0);
        let south = scene.map.get_structural_level(x, y + 1).unwrap_or(0);
        if current <= south { return None; }
        let exposed = current - south;
        let certified = self.resolve_selected_structural_cliff_asset().is_some();
        Some(format!(
            "structural south drop {current}->{south} (height {exposed}); visual recipe {}",
            if certified { "Z105-certified ElizaWy 1x3 south face" } else { "not runtime-certified for this topology" }
        ))
    }

    fn reveal_scene_tile_source(&mut self) {
        self.status_message = self.resolve_selected_world_asset().map_or_else(
            || "The selected tile has no reviewed source binding".to_string(),
            |binding| format!("Source: {}", binding.source_path),
        );
    }

    pub(crate) fn open_world_surface_tile_source_in_pixel_studio(&mut self) {
        let Some(manifest) = self.scene_rectangles.as_ref() else {
            self.status_message = "No world-surface manifest loaded".to_string();
            return;
        };
        let global = GridPos { x: self.world_cursor_x, y: self.world_cursor_y };
        let address = match resolve_world_surface_cell(
            manifest,
            &self.scene_assignments,
            &self.model.world,
            self.selected_landmass_id,
            global,
        ) {
            Ok(address) => address,
            Err(error) => {
                self.status_message = format!("Cannot edit world pixel source here: {error}");
                return;
            }
        };
        let Some(index) = self.model.world.scenes.position(&address.scene_id) else {
            self.status_message = format!("World partition {} is not loaded", address.scene_id.label());
            return;
        };
        self.selected_scene = index;
        self.scene_cursor_x = address.local.x;
        self.scene_cursor_y = address.local.y;
        self.open_scene_tile_source_in_pixel_studio();
        if self.viewport_mode == EditorViewportMode::PixelStudio {
            self.status_message = format!(
                "Editing exact visual source for global tile {}, {} | Ctrl+Enter saves and returns to World Editor",
                global.x, global.y
            );
        }
    }

    pub(crate) fn open_scene_tile_source_in_pixel_studio(&mut self) {
        let Some(scene_id) = self.active_scene_id() else { return; };
        let Some(tile) = self.selected_scene_tile() else { return; };
        let Some(binding) = self.resolve_selected_world_asset() else {
            self.status_message = format!("{:?} is not yet mapped to an editable production source", tile);
            return;
        };
        self.open_resolved_world_asset_source(scene_id, binding, None);
    }

    fn open_resolved_world_asset_source(
        &mut self,
        scene_id: ProjectSceneId,
        binding: ResolvedWorldAsset,
        object_id: Option<haven_editor::ObjectId>,
    ) {
        let source_path = resolve_project_path(&binding.source_path);
        let mut document = match PixelDocument::load_source_region(
            &source_path,
            binding.source_rect,
            binding.semantic_id.clone(),
            haven_pixel::PixelLicense::default(),
        ) {
            Ok(document) => document,
            Err(error) => {
                self.status_message = format!("Unable to open exact source region: {error}");
                return;
            }
        };
        document.metadata.grid.cell_width = document.metadata.width.min(32).max(1);
        document.metadata.grid.cell_height = document.metadata.height.min(32).max(1);
        document.metadata.selection = PixelSelection {
            x: 0,
            y: 0,
            width: document.metadata.width,
            height: document.metadata.height,
        };
        let context = WorldAssetEditContext {
            origin_scene_id: scene_id,
            origin_cell: [self.scene_cursor_x, self.scene_cursor_y],
            origin_camera: self.scene_canvas,
            origin_viewport_mode: self.viewport_mode,
            origin_world_cursor: [self.world_cursor_x, self.world_cursor_y],
            origin_world_camera: self.world_canvas,
            origin_landmass_id: self.selected_landmass_id,
            semantic_id: binding.semantic_id.clone(),
            generated_output: binding.generated_output,
        };
        self.pixel_studio.open_document_session(document);
        self.pixel_studio.reset_authoring_defaults();
        self.pixel_studio.world_asset_context = Some(context);
        self.pixel_studio.animation_context = None;
        self.pixel_studio.inspector_tab = PixelInspectorTab::Asset;
        self.pixel_studio.show_atlas_grid = false;
        self.pixel_studio.refresh_texture();
        self.pixel_studio.frame_document(self.pixel_canvas_rect());
        self.viewport_mode = EditorViewportMode::PixelStudio;
        self.status_message = match object_id {
            Some(id) => format!("Editing exact source region for object {:?}: {}", id, binding.semantic_id),
            None => format!("Editing exact source region for {} at {}, {}", binding.semantic_id, self.scene_cursor_x, self.scene_cursor_y),
        };
    }

    /// Opens the complete active exterior storage chunk as one Pixel Studio
    /// document. The semantic terrain remains authoritative and locked as the
    /// generated snapshot; hand-authored pixels live on a transparent visual
    /// override layer that can be saved back without changing collision, zones,
    /// transitions, structural levels, or object placement.
    pub(crate) fn open_active_scene_chunk_in_pixel_studio(&mut self) {
        let Some(scene_id) = self.active_scene_id() else {
            self.status_message = "No active scene is available for chunk pixel authoring".to_string();
            return;
        };
        let Some(scene) = self.model.world.scene_by_id(&scene_id) else { return; };
        if scene.kind != SceneKind::Exterior {
            self.status_message = "Whole-chunk Pixel Studio authoring is currently available for exterior surface chunks".to_string();
            return;
        }
        let width = scene.dimensions.width as i32;
        let height = scene.dimensions.height as i32;

        // W81: global surface coordinates are optional metadata, not permission
        // to edit the scene. Stale/missing rectangle assignments fall back to
        // the scene-local bounds instead of blocking Pixel Studio entirely.
        let global = self.scene_rectangles.as_ref().and_then(|manifest| {
            let assignment = self.scene_assignments.assignments.iter()
                .find(|assignment| assignment.scene_code == scene_id.code())?;
            let rectangle = manifest.scene_rectangles.iter()
                .find(|rectangle| rectangle.scene_id == assignment.rectangle_id)?;
            Some((rectangle.landmass_id, rectangle.grid_x?, rectangle.grid_y?))
        });
        if let Some((landmass_id, grid_x, grid_y)) = global {
            let origin = GridPos { x: grid_x * MAP_W as i32, y: grid_y * MAP_H as i32 };
            let far = GridPos { x: origin.x + width - 1, y: origin.y + height - 1 };
            self.selected_landmass_id = landmass_id;
            self.world_cursor_x = origin.x;
            self.world_cursor_y = origin.y;
            self.world_selection = Some(GridRect::from_points(origin, far));
            self.open_world_selection_in_pixel_studio();
        } else {
            let local = GridRect::from_points(GridPos { x: 0, y: 0 }, GridPos { x: width - 1, y: height - 1 });
            self.open_scene_local_rect_in_pixel_studio(scene_id.clone(), local, "scene_chunk_local", None);
        }
        if self.viewport_mode == EditorViewportMode::PixelStudio {
            self.status_message = format!(
                "Editing complete scene chunk {} ({}x{} tiles / {}x{} px) | generated terrain is locked; paint Authored Visual Override | Ctrl+S apply, Ctrl+Enter apply + return",
                scene_id.code(), width, height, width * 32, height * 32
            );
        }
    }

    pub(crate) fn open_scene_cell_variant_in_pixel_studio(&mut self) {
        let Some(scene_id) = self.active_scene_id() else { return; };
        let rect = GridRect::single(GridPos { x: self.scene_cursor_x, y: self.scene_cursor_y });
        self.open_scene_local_rect_in_pixel_studio(scene_id, rect, "cell_variant", None);
    }

    pub(crate) fn open_scene_selection_in_pixel_studio(&mut self) {
        let Some(scene_id) = self.active_scene_id() else { return; };
        let rect = self.selection.bounds.unwrap_or_else(|| GridRect::single(GridPos {
            x: self.scene_cursor_x,
            y: self.scene_cursor_y,
        }));
        self.open_scene_local_rect_in_pixel_studio(scene_id, rect, "selection", None);
    }

    pub(crate) fn open_scene_building_composite_in_pixel_studio(&mut self) {
        let Some(scene_id) = self.active_scene_id() else { return; };
        let Some(instance) = self.building_at_scene_cursor() else {
            self.status_message = "No BuildingInstance is under the cursor; select the house before opening a building composite".to_string();
            return;
        };
        let Some(recipe) = self.building_recipe_registry.entry(&instance.recipe_id) else {
            self.status_message = format!("Building recipe {} is unavailable", instance.recipe_id);
            return;
        };
        let min = GridPos { x: instance.anchor_tile[0], y: instance.anchor_tile[1] };
        let max = GridPos {
            x: instance.anchor_tile[0] + recipe.footprint[0] as i32 - 1,
            y: instance.anchor_tile[1] + recipe.footprint[1] as i32 - 1,
        };
        self.open_scene_local_rect_in_pixel_studio(scene_id, GridRect::from_points(min, max), "building_composite", Some(instance));
    }

    fn open_scene_local_rect_in_pixel_studio(
        &mut self,
        scene_id: ProjectSceneId,
        local_rect: GridRect,
        scope_kind: &str,
        building_instance: Option<haven_assets::building_instance::BuildingInstanceDefinition>,
    ) {
        let Some(scene) = self.model.world.scene_by_id(&scene_id) else { return; };
        let width_px = (local_rect.width().max(1) as u32).saturating_mul(32);
        let height_px = (local_rect.height().max(1) as u32).saturating_mul(32);
        if width_px > 8192 || height_px > 8192 {
            self.status_message = "Pixel authoring scope is too large; keep one edit document at or below 256x256 tiles".to_string();
            return;
        }
        let target_key = format!("{}:{}:{}:{}:{}x{}", scene_id.code(), scope_kind, local_rect.min.x, local_rect.min.y, local_rect.width(), local_rect.height());
        let revision = super::authoring_changeset::next_revision(&target_key);
        let slug = scene_id.code().replace('/', "_").replace('\\', "_");
        let output_path = if scope_kind == "building_composite" {
            let building_slug = building_instance
                .as_ref()
                .map(|instance| instance.id.replace('/', "_").replace('\\', "_").replace(':', "_"))
                .unwrap_or_else(|| "unknown_building".to_string());
            format!(
                "assets/source/original/building_composites/drafts/{}_{}_{}.png",
                building_slug, slug, revision
            )
        } else {
            format!(
                "assets/source/original/world_overrides/{}_{}_{}_{}x{}_{}.png",
                slug, local_rect.min.x, local_rect.min.y, local_rect.width(), local_rect.height(), revision
            )
        };
        let mut document = PixelDocument::from_rgba(
            width_px,
            height_px,
            format!("{} {} {}", scene.name, scope_kind.replace('_', " "), revision),
        );
        document.metadata.asset_kind = PixelAssetKind::Tilesheet;
        document.metadata.preview_mode = PixelPreviewMode::None;
        document.metadata.grid.cell_width = 32;
        document.metadata.grid.cell_height = 32;
        document.metadata.grid.subgrid = 8;
        document.metadata.selection = PixelSelection { x: 0, y: 0, width: width_px, height: height_px };
        document.metadata.output_path = output_path.clone();
        document.metadata.asset_id = format!("world_override/{}/{}_{}_{}", scene_id.code(), local_rect.min.x, local_rect.min.y, revision);
        document.metadata.tags = vec![
            "canvas_document".to_string(),
            scope_kind.to_string(),
            "semantic_world_preserved".to_string(),
            revision.clone(),
        ];
        if let Some(instance) = building_instance.as_ref() {
            document.metadata.tags.push(format!("building_instance:{}", instance.id));
            document.metadata.tags.push(format!("building_recipe:{}", instance.recipe_id));
            document.metadata.tags.push("clean_authoring_composite".to_string());
        }
        document.metadata.license.status = "project_owned".to_string();
        document.metadata.license.source_name = "Havenwild Unified Canvas".to_string();
        let composition = if scope_kind == "building_composite" {
            let Some(instance) = building_instance.as_ref() else {
                self.status_message = "Building Composite authoring requires an authoritative BuildingInstance".to_string();
                return;
            };
            self.prepare_building_canvas_composition(&scene_id, local_rect, instance)
        } else {
            self.prepare_scene_canvas_composition(&scene_id, local_rect)
        };
        let composition = match composition {
            Ok(value) => value,
            Err(error) => {
                self.status_message = format!("Unable to prepare clean authoring composition: {error}");
                return;
            }
        };
        let composition_summary = format!(
            "{} building(s), {} object(s), {} stamp(s)",
            composition.building_count, composition.object_count, composition.stamp_count
        );
        for (index, prepared) in composition.layers.into_iter().enumerate() {
            if index == 0 {
                document.rename_active_layer(&prepared.name);
                document.active_layer_mut().image = prepared.image;
            } else {
                document.add_layer(&prepared.name);
                document.active_layer_mut().image = prepared.image;
            }
            if prepared.locked && !document.active_layer().metadata.locked {
                document.toggle_active_layer_lock();
            }
        }
        // Materialize the source-only reference first and fingerprint it before
        // any editable authoring layer is introduced. This catches accidental
        // preview/overlay contamination at the bridge boundary.
        document.refresh_composite();
        let reference_fingerprint = rgba_fingerprint_v1(document.rgba_bytes());

        if scope_kind == "building_composite" {
            document.add_layer("Authored Building Composite Draft");
            let draft_index = document.layer_count().saturating_sub(1);
            document.select_layer(draft_index);
            document.refresh_composite();
            let opened_fingerprint = rgba_fingerprint_v1(document.rgba_bytes());
            if opened_fingerprint != reference_fingerprint {
                self.status_message = format!(
                    "Authoring handoff mismatch for building composite: expected {:016x}, opened {:016x}; saving disabled",
                    reference_fingerprint, opened_fingerprint
                );
                return;
            }
            document.metadata.tags.push(format!(
                "authoring_handoff_rgba_fingerprint_v1:{:016x}",
                reference_fingerprint
            ));
        } else {
            if local_rect.width() > 1 || local_rect.height() > 1 {
                document.add_layer("Semantic Transition Guide");
                document.toggle_active_layer_lock();
            }
            document.add_layer("Authored Visual Override");
            document.add_layer("Physical Collision Reference");
            match self.prepare_scene_collision_reference(&scene_id, local_rect) {
                Ok(image) => document.active_layer_mut().image = image,
                Err(error) => self.status_message = format!("Collision reference unavailable: {error}"),
            }
            document.toggle_active_layer_lock();
            document.add_layer("Collision Add");
            document.add_layer("Collision Subtract");
            let visual_index = document.layer_count().saturating_sub(4);
            document.select_layer(visual_index);
            document.refresh_composite();
        }
        document.mark_clean();

        let global_rect = self.scene_global_rect(&scene_id, local_rect).unwrap_or(local_rect);
        self.pixel_studio.open_document_session(document);
        self.pixel_studio.reset_authoring_defaults();
        self.pixel_studio.world_region_context = Some(super::pixel_studio::WorldRegionPixelEditContext {
            scene_id,
            local_rect,
            global_rect,
            scope_kind: scope_kind.to_string(),
            revision: revision.clone(),
            origin_viewport_mode: self.viewport_mode,
            origin_scene_id: self.active_scene_id(),
            origin_scene_cursor: [self.scene_cursor_x, self.scene_cursor_y],
            origin_scene_camera: self.scene_canvas,
            origin_world_camera: self.world_canvas,
            origin_landmass_id: self.selected_landmass_id,
            output_path,
        });
        self.pixel_studio.world_asset_context = None;
        self.pixel_studio.animation_context = None;
        self.pixel_studio.inspector_tab = PixelInspectorTab::Asset;
        self.pixel_studio.tool = haven_pixel::PixelTool::Selection;
        self.pixel_studio.show_atlas_grid = true;
        self.pixel_studio.refresh_texture();
        self.pixel_studio.frame_document(self.pixel_canvas_rect());
        self.viewport_mode = EditorViewportMode::PixelStudio;
        self.status_message = if scope_kind == "building_composite" {
            format!(
                "Editing clean building composite {} | {} | source components only; terrain/editor overlays excluded | draft saves do not change runtime until Building Component Authoring commit",
                revision, composition_summary
            )
        } else {
            format!(
                "Editing {} {} | {} | {} | Select is active; choose a tool explicitly",
                scope_kind.replace('_', " "), revision, target_key, composition_summary
            )
        };
    }

    fn scene_global_rect(&self, scene_id: &ProjectSceneId, local_rect: GridRect) -> Option<GridRect> {
        let assignment = self.scene_assignments.assignments.iter().find(|entry| entry.scene_code == scene_id.code())?;
        let manifest = self.scene_rectangles.as_ref()?;
        let rectangle = manifest.scene_rectangles.iter().find(|entry| entry.scene_id == assignment.rectangle_id)?;
        let origin = GridPos { x: rectangle.grid_x? * MAP_W as i32, y: rectangle.grid_y? * MAP_H as i32 };
        Some(GridRect::from_points(
            GridPos { x: origin.x + local_rect.min.x, y: origin.y + local_rect.min.y },
            GridPos { x: origin.x + local_rect.max.x, y: origin.y + local_rect.max.y },
        ))
    }

    pub(crate) fn open_world_selection_in_pixel_studio(&mut self) {
        let origin_viewport_mode = self.viewport_mode;
        let origin_scene_id = self.active_scene_id();
        let origin_scene_cursor = [self.scene_cursor_x, self.scene_cursor_y];
        let origin_scene_camera = self.scene_canvas;
        let Some(manifest) = self.scene_rectangles.as_ref() else {
            self.status_message = "No world-surface manifest loaded".to_string();
            return;
        };
        let global_rect = self.world_selection.unwrap_or_else(|| GridRect::single(GridPos {
            x: self.world_cursor_x,
            y: self.world_cursor_y,
        }));
        let first = match resolve_world_surface_cell(
            manifest,
            &self.scene_assignments,
            &self.model.world,
            self.selected_landmass_id,
            global_rect.min,
        ) {
            Ok(address) => address,
            Err(error) => { self.status_message = error; return; }
        };
        let last = match resolve_world_surface_cell(
            manifest,
            &self.scene_assignments,
            &self.model.world,
            self.selected_landmass_id,
            global_rect.max,
        ) {
            Ok(address) => address,
            Err(error) => { self.status_message = error; return; }
        };
        if first.scene_id != last.scene_id {
            self.status_message = "Pixel-region editing currently requires the selection to stay inside one storage partition; cross-partition visual overrides are scheduled for the cross-chunk authoring pass".to_string();
            return;
        }
        let local_rect = GridRect::from_points(first.local, last.local);
        let Some(scene) = self.model.world.scene_by_id(&first.scene_id) else { return; };
        let width_px = (local_rect.width().max(1) as u32).saturating_mul(32);
        let height_px = (local_rect.height().max(1) as u32).saturating_mul(32);
        if width_px > 8192 || height_px > 8192 {
            self.status_message = "World pixel selection is too large; select a region no larger than 256x256 tiles".to_string();
            return;
        }
        let mut document = PixelDocument::from_rgba(
            width_px,
            height_px,
            format!("World {} {}_{}", first.scene_id.code(), local_rect.min.x, local_rect.min.y),
        );
        document.metadata.asset_kind = PixelAssetKind::Tilesheet;
        document.metadata.preview_mode = PixelPreviewMode::None;
        document.metadata.grid.cell_width = 32;
        document.metadata.grid.cell_height = 32;
        document.metadata.selection = PixelSelection { x: 0, y: 0, width: width_px, height: height_px };
        let target_key = format!(
            "{}:world_selection:{}:{}:{}x{}",
            first.scene_id.code(), local_rect.min.x, local_rect.min.y, local_rect.width(), local_rect.height()
        );
        let revision = super::authoring_changeset::next_revision(&target_key);
        let output_path = format!(
            "assets/source/original/world_overrides/{}_{}_{}_{}x{}_{}.png",
            first.scene_id.code().replace('/', "_"),
            local_rect.min.x,
            local_rect.min.y,
            local_rect.width(),
            local_rect.height(),
            revision,
        );
        document.metadata.output_path = output_path.clone();
        document.metadata.asset_id = format!(
            "world_override/{}/{}_{}_{}x{}",
            first.scene_id.code(), local_rect.min.x, local_rect.min.y, local_rect.width(), local_rect.height()
        );
        document.metadata.tags = vec![
            "world_region".to_string(),
            "authored_visual_override".to_string(),
            "semantic_world_preserved".to_string(),
        ];
        document.metadata.license.status = "project_owned".to_string();
        document.metadata.license.source_name = "Havenwild World Editor".to_string();
        document.rename_active_layer("Generated World Snapshot");

        let mut sources: HashMap<PathBuf, image::DynamicImage> = HashMap::new();
        for local in local_rect.cells() {
            let tile = scene.map.get(local.x, local.y);
            let Some(binding) = resolve_tile_asset(tile) else { continue; };
            let path = resolve_project_path(&binding.source_path);
            if !sources.contains_key(&path) {
                if let Ok(image) = image::open(&path) { sources.insert(path.clone(), image); }
            }
            let Some(source) = sources.get(&path) else { continue; };
            let source_rect = binding.source_rect;
            if source_rect.x + source_rect.width > source.width() || source_rect.y + source_rect.height > source.height() {
                continue;
            }
            let cropped = source.crop_imm(source_rect.x, source_rect.y, source_rect.width, source_rect.height)
                .resize_exact(32, 32, FilterType::Nearest)
                .to_rgba8();
            let target_x = ((local.x - local_rect.min.x) as u32) * 32;
            let target_y = ((local.y - local_rect.min.y) as u32) * 32;
            for py in 0..32u32 {
                for px in 0..32u32 {
                    document.set_pixel(target_x + px, target_y + py, cropped.get_pixel(px, py).0);
                }
            }
        }
        document.toggle_active_layer_lock();
        document.add_layer("Semantic Transition Guide");
        document.toggle_active_layer_lock();
        document.add_layer("Authored Visual Override");
        document.add_layer("Collision Mask [8px default / 1px precision]");
        let visual_index = document.layer_count().saturating_sub(2);
        document.select_layer(visual_index);
        document.mark_clean();
        document.metadata.grid.subgrid = 8;
        document.metadata.selection = PixelSelection { x: 0, y: 0, width: width_px, height: height_px };
        self.pixel_studio.open_document_session(document);
        self.pixel_studio.reset_authoring_defaults();
        self.pixel_studio.world_region_context = Some(super::pixel_studio::WorldRegionPixelEditContext {
            scene_id: first.scene_id,
            local_rect,
            global_rect,
            scope_kind: "world_selection".to_string(),
            revision,
            origin_viewport_mode,
            origin_scene_id,
            origin_scene_cursor,
            origin_scene_camera,
            origin_world_camera: self.world_canvas,
            origin_landmass_id: self.selected_landmass_id,
            output_path,
        });
        self.pixel_studio.world_asset_context = None;
        self.pixel_studio.animation_context = None;
        self.pixel_studio.inspector_tab = PixelInspectorTab::Asset;
        self.pixel_studio.tool = haven_pixel::PixelTool::Selection;
        self.pixel_studio.show_atlas_grid = true;
        self.pixel_studio.refresh_texture();
        self.pixel_studio.frame_document(self.pixel_canvas_rect());
        self.viewport_mode = EditorViewportMode::PixelStudio;
        self.status_message = format!(
            "Editing world region {}x{} at global {},{} | paint the Authored Visual Override layer; Ctrl+S applies, Ctrl+Enter applies and returns",
            global_rect.width(), global_rect.height(), global_rect.min.x, global_rect.min.y
        );
    }

    pub(crate) fn persist_active_world_region_pixels(&mut self) -> Result<String, String> {
        let context = self
            .pixel_studio
            .world_region_context
            .clone()
            .ok_or_else(|| "No world-region Pixel Studio session is active".to_string())?;

        if context.scope_kind == "building_composite" {
            let (rgba, width, height, instance_id) = {
                let document = self
                    .pixel_studio
                    .document
                    .as_mut()
                    .ok_or_else(|| "Building Composite Pixel Studio document is unavailable".to_string())?;
                document.refresh_composite();
                let instance_id = document
                    .metadata
                    .tags
                    .iter()
                    .find_map(|tag| tag.strip_prefix("building_instance:"))
                    .map(str::to_string)
                    .ok_or_else(|| "Building Composite document is missing its building instance identity".to_string())?;
                (
                    document.rgba_bytes().to_vec(),
                    document.width(),
                    document.height(),
                    instance_id,
                )
            };
            let building_slug = instance_id
                .replace('/', "_")
                .replace('\\', "_")
                .replace(':', "_");
            let scene_slug = context.scene_id.code().replace('/', "_").replace('\\', "_");
            let output_path = format!(
                "assets/source/original/world_overrides/building_composites/{}_{}.png",
                building_slug, scene_slug
            );
            let output = repo_root_dir().join(&output_path);
            if let Some(parent) = output.parent() {
                std::fs::create_dir_all(parent)
                    .map_err(|error| format!("Building Composite publish directory failed: {error}"))?;
            }
            let image = image::RgbaImage::from_raw(width, height, rgba.clone())
                .ok_or_else(|| "Building Composite composite RGBA size is invalid".to_string())?;
            image
                .save(&output)
                .map_err(|error| format!("Building Composite publish PNG save failed: {error}"))?;

            let override_value = haven_core::SceneVisualOverride::new(
                context.local_rect.min.x,
                context.local_rect.min.y,
                context.local_rect.width(),
                context.local_rect.height(),
                output_path.clone(),
            )?;
            let scene = self
                .model
                .world
                .scene_mut_by_id(&context.scene_id)
                .ok_or_else(|| "Origin scene is no longer loaded".to_string())?;
            scene.set_visual_override(override_value);
            self.editor_textures.install_world_visual_override_texture(
                output_path.clone(),
                width,
                height,
                &rgba,
            );
            let editor_world_path = development_session::editor_world_path();
            save_world_to_path(&editor_world_path.to_string_lossy(), &self.model.world)
                .map_err(|error| format!("Building Composite published but Dev World persistence failed: {error}"))?;

            if let Some(document) = self.pixel_studio.document.as_mut() {
                document.metadata.output_path = output_path.clone();
                document.mark_clean();
            }
            let _ = super::authoring_changeset::record_authoring_change(
                "building_composite_publish",
                "building_composite".to_string(),
                instance_id,
                context.revision.clone(),
                vec![output_path.clone()],
                "Published exact Pixel Studio building composite as the exterior visual authority; BuildingRecipe gameplay/collision/interior semantics remain unchanged".to_string(),
            );
            return Ok(output_path);
        }

        let (rgba, width, height, asset_path, collision_output) = {
            let document = self
                .pixel_studio
                .document
                .as_mut()
                .ok_or_else(|| "World-region Pixel Studio document is unavailable".to_string())?;
            document
                .save(repo_root_dir())
                .map_err(|error| format!("World-region pixel document save failed: {error}"))?;

            // Reference/composite layers never become runtime output. Only the
            // explicitly authored visual layer is installed into SceneVisualOverride.
            let authored_layer = document
                .layers()
                .iter()
                .find(|layer| layer.metadata.name == "Authored Visual Override")
                .ok_or_else(|| {
                    "World-region document is missing its Authored Visual Override layer".to_string()
                })?;
            let rgba = authored_layer.image.as_raw().to_vec();
            let width = authored_layer.image.width();
            let height = authored_layer.image.height();
            let asset_path = document.metadata.output_path.replace('\\', "/");
            let output = repo_root_dir().join(&asset_path);
            if let Some(parent) = output.parent() {
                std::fs::create_dir_all(parent)
                    .map_err(|error| format!("World-region override directory failed: {error}"))?;
            }
            authored_layer
                .image
                .save(&output)
                .map_err(|error| format!("World-region override PNG save failed: {error}"))?;

            // W60E2: collision is authored as additive and subtractive masks over a
            // locked reference generated from the same map/building collision authority.
            let collision_output = {
                let add = document.layers().iter().find(|layer| layer.metadata.name == "Collision Add");
                let subtract = document.layers().iter().find(|layer| layer.metadata.name == "Collision Subtract");
                let has_add = add.is_some_and(|layer| layer.image.pixels().any(|pixel| pixel.0[3] != 0));
                let has_subtract = subtract.is_some_and(|layer| layer.image.pixels().any(|pixel| pixel.0[3] != 0));
                if !has_add && !has_subtract {
                    None
                } else {
                    let base = asset_path.trim_end_matches(".png").to_string();
                    let add_path = base.clone() + ".collision.add.png";
                    let subtract_path = base.clone() + ".collision.subtract.png";
                    let metadata_relative = base + ".collision.json";
                    let blank = image::RgbaImage::new(width, height);
                    let add_image = add.map(|layer| &layer.image).unwrap_or(&blank);
                    let subtract_image = subtract.map(|layer| &layer.image).unwrap_or(&blank);
                    let add_output = repo_root_dir().join(&add_path);
                    let subtract_output = repo_root_dir().join(&subtract_path);
                    if let Some(parent) = add_output.parent() {
                        std::fs::create_dir_all(parent)
                            .map_err(|error| format!("collision output directory failed: {error}"))?;
                    }
                    add_image.save(&add_output)
                        .map_err(|error| format!("collision add mask save failed: {error}"))?;
                    subtract_image.save(&subtract_output)
                        .map_err(|error| format!("collision subtract mask save failed: {error}"))?;
                    let metadata_path = repo_root_dir().join(&metadata_relative);
                    let metadata = serde_json::json!({
                        "schema": "havenwild.pixel_collision_override.v2",
                        "addMask": add_path.clone(),
                        "subtractMask": subtract_path.clone(),
                        "authoringResolutionPx": 1,
                        "defaultSnapPx": 8,
                        "allowedSnapPx": [32,16,8,4,2,1],
                        "sceneId": context.scene_id.code(),
                        "localRect": [context.local_rect.min.x, context.local_rect.min.y, context.local_rect.width(), context.local_rect.height()],
                        "revision": context.revision.clone(),
                        "runtimeRule": "subtract_then_add_over_base_collision"
                    });
                    std::fs::write(&metadata_path, serde_json::to_string_pretty(&metadata).unwrap_or_default())
                        .map_err(|error| format!("collision metadata save failed: {error}"))?;
                    Some((add_path, subtract_path, metadata_relative))
                }
            };
            (rgba, width, height, asset_path, collision_output)
        };

        let override_value = haven_core::SceneVisualOverride::new(
            context.local_rect.min.x,
            context.local_rect.min.y,
            context.local_rect.width(),
            context.local_rect.height(),
            asset_path.clone(),
        )?;
        let scene = self
            .model
            .world
            .scene_mut_by_id(&context.scene_id)
            .ok_or_else(|| "Origin scene is no longer loaded".to_string())?;
        scene.set_visual_override(override_value);
        self.editor_textures.install_world_visual_override_texture(
            asset_path.clone(),
            width,
            height,
            &rgba,
        );
        let editor_world_path = development_session::editor_world_path();
        save_world_to_path(&editor_world_path.to_string_lossy(), &self.model.world)
            .map_err(|error| format!("Visual override saved but Dev World persistence failed: {error}"))?;

        let mut outputs = vec![asset_path.clone()];
        if let Some((add_path, subtract_path, metadata_path)) = collision_output.as_ref() {
            outputs.push(add_path.clone());
            outputs.push(subtract_path.clone());
            outputs.push(metadata_path.clone());
            let registry_path = super::collision_authoring::update_collision_override_registry(
                &repo_root_dir(),
                &context.scene_id,
                context.local_rect,
                &context.revision,
                add_path,
                subtract_path,
            )?;
            outputs.push(registry_path);
        }

        // W58B: a multi-cell visual correction becomes a versioned junction
        // candidate rather than an anonymous flattened image. It is local by
        // default; explicit promotion is required before PCG may reuse it.
        if matches!(context.scope_kind.as_str(), "selection" | "world_selection")
            && (context.local_rect.width() > 1 || context.local_rect.height() > 1)
        {
            if let Some(scene) = self.model.world.scene_by_id(&context.scene_id) {
                let semantic_grid = context.local_rect.cells().into_iter().map(|cell| {
                    serde_json::json!({"x": cell.x - context.local_rect.min.x, "y": cell.y - context.local_rect.min.y, "terrain": scene.map.get(cell.x, cell.y).code()})
                }).collect::<Vec<_>>();
                let registry_path = repo_root_dir().join("content/terrain/authored_junction_variants_v1.json");
                let mut registry = if registry_path.is_file() {
                    std::fs::read_to_string(&registry_path).ok()
                        .and_then(|text| serde_json::from_str::<serde_json::Value>(&text).ok())
                        .unwrap_or_else(|| serde_json::json!({"schema":"havenwild.authored_junction_variants.v1","entries":[]}))
                } else {
                    serde_json::json!({"schema":"havenwild.authored_junction_variants.v1","entries":[]})
                };
                let entry = serde_json::json!({
                    "id": format!("junction.{}.{}.{}.{}", context.scene_id.code().replace('/', "_"), context.local_rect.min.x, context.local_rect.min.y, context.revision),
                    "revision": context.revision.clone(),
                    "sceneId": context.scene_id.code(),
                    "scope": context.scope_kind.clone(),
                    "localRect": [context.local_rect.min.x, context.local_rect.min.y, context.local_rect.width(), context.local_rect.height()],
                    "semanticGrid": semantic_grid,
                    "visualAsset": asset_path.clone(),
                    "collisionAdd": collision_output.as_ref().map(|(add_path, _, _)| add_path.clone()),
                    "collisionSubtract": collision_output.as_ref().map(|(_, subtract_path, _)| subtract_path.clone()),
                    "promotion": "local",
                    "pcgEligible": false,
                    "notes": "Use Promote Variant/Exemplar before PCG reuse. Exact semantic signature remains authoritative."
                });
                if let Some(entries) = registry.get_mut("entries").and_then(|value| value.as_array_mut()) {
                    entries.push(entry);
                }
                if let Some(parent) = registry_path.parent() { let _ = std::fs::create_dir_all(parent); }
                std::fs::write(&registry_path, serde_json::to_string_pretty(&registry).unwrap_or_default())
                    .map_err(|error| format!("junction registry write failed: {error}"))?;
                outputs.push("content/terrain/authored_junction_variants_v1.json".to_string());
            }
        }

        let target = format!("{}:{}:{}:{}:{}x{}", context.scene_id.code(), context.scope_kind, context.local_rect.min.x, context.local_rect.min.y, context.local_rect.width(), context.local_rect.height());
        let _ = super::authoring_changeset::record_authoring_change(
            if context.scope_kind == "building_composite" { "building_composite" } else { "pixel_region" },
            context.scope_kind.clone(),
            target,
            context.revision.clone(),
            outputs,
            format!("Authored {} {}x{} tiles in {}", context.scope_kind, context.local_rect.width(), context.local_rect.height(), context.scene_id.label()),
        );

        self.world_selection = Some(context.global_rect);
        self.world_cursor_x = context.global_rect.min.x;
        self.world_cursor_y = context.global_rect.min.y;
        self.world_canvas = context.origin_world_camera;
        self.selected_landmass_id = context.origin_landmass_id;
        Ok(context.output_path)
    }

    pub(crate) fn save_world_region_pixels(&mut self, return_to_world: bool) {
        let scope_kind = self
            .pixel_studio
            .world_region_context
            .as_ref()
            .map(|context| context.scope_kind.clone());
        match self.persist_active_world_region_pixels() {
            Ok(output_path) => {
                if return_to_world {
                    let context = self.pixel_studio.world_region_context.take();
                    if let Some(context) = context {
                        if let Some(scene_id) = context.origin_scene_id.as_ref() {
                            if let Some(index) = self.model.world.scenes.position(scene_id) {
                                self.selected_scene = index;
                            }
                        }
                        self.scene_cursor_x = context.origin_scene_cursor[0];
                        self.scene_cursor_y = context.origin_scene_cursor[1];
                        self.scene_canvas = context.origin_scene_camera;
                        self.viewport_mode = context.origin_viewport_mode;
                    } else {
                        self.viewport_mode = EditorViewportMode::SceneRectangles;
                    }
                }
                self.status_message = if scope_kind.as_deref() == Some("building_composite") {
                    format!(
                        "Published Building Composite {}{} | Scene Editor and runtime now resolve this exterior visual; gameplay/collision/interior authority remains on the BuildingRecipe",
                        output_path,
                        if return_to_world { format!(" | returned to {}", self.viewport_mode.label()) } else { String::new() }
                    )
                } else {
                    format!(
                        "Saved project-owned visual override {} and persisted Dev World semantic state{}",
                        output_path,
                        if return_to_world {
                            format!(" | returned to {}", self.viewport_mode.label())
                        } else {
                            String::new()
                        }
                    )
                };
            }
            Err(error) => self.status_message = error,
        }
    }

    pub(crate) fn save_world_asset_pixels_and_return(&mut self) {
        let Some(context) = self.pixel_studio.world_asset_context.clone() else {
            self.status_message = "No world-asset Pixel Studio bridge is active".to_string();
            return;
        };
        if context.generated_output {
            self.status_message =
                "Generated atlas output is read-only; edit its reviewed source or override"
                    .to_string();
            return;
        }
        let Some(document) = self.pixel_studio.document.as_mut() else {
            return;
        };
        if let Err(error) = document.save(repo_root_dir()) {
            self.status_message = format!("World asset save failed: {error}");
            return;
        }
        if let Some(index) = self.model.world.scenes.position(&context.origin_scene_id) {
            self.selected_scene = index;
        }
        self.scene_cursor_x = context.origin_cell[0];
        self.scene_cursor_y = context.origin_cell[1];
        self.scene_canvas = context.origin_camera;
        self.world_cursor_x = context.origin_world_cursor[0];
        self.world_cursor_y = context.origin_world_cursor[1];
        self.world_canvas = context.origin_world_camera;
        self.selected_landmass_id = context.origin_landmass_id;
        self.pixel_studio.world_asset_context = None;
        self.viewport_mode = context.origin_viewport_mode;
        self.status_message = format!(
            "Saved derived working copy for {} and returned to {}. Runtime binding is unchanged until Publish Slice Draft -> approve -> Bake + Reload.",
            context.semantic_id,
            context.origin_viewport_mode.label()
        );
    }
}

fn rgba_fingerprint_v1(bytes: &[u8]) -> u64 {
    // Stable FNV-1a fingerprint used only as an authoring-handoff identity check.
    // It is intentionally dependency-free and is not a security primitive.
    let mut hash = 0xcbf29ce484222325u64;
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(0x100000001b3);
    }
    hash
}

fn resolve_tile_asset(tile: TileKind) -> Option<ResolvedWorldAsset> {
    // A cliff cell is structural elevation. The visible face can consist of
    // several source cells, so it must be inspected through the cliff
    // composition resolver rather than pretending it is one ground tile.
    if tile == TileKind::Cliff {
        return None;
    }

    // World -> Pixel Studio must follow the same semantic terrain authority as
    // runtime/worldgen. Do not grow another TileKind -> atlas match table here.
    let semantic_id = haven_assets::runtime_asset_adapters::terrain_semantic_id(tile);
    resolve_reviewed_edit_binding(tile, semantic_id)
        .or_else(|| resolve_semantic_terrain_source(tile, semantic_id))
}

fn resolve_reviewed_edit_binding(
    tile: TileKind,
    semantic_id: &'static str,
) -> Option<ResolvedWorldAsset> {
    let reviewed_semantic = haven_assets::terrain_material_bindings::reviewed_v7_pure_fill_semantic_id(tile)?;
    let bindings_path = repo_root_dir().join("content/editor/world_asset_edit_bindings_v0_2.json");
    let bytes = std::fs::read(bindings_path).ok()?;
    let catalog: serde_json::Value = serde_json::from_slice(&bytes).ok()?;
    let binding = catalog.get("bindings")?.as_array()?.iter().find(|binding| {
        binding.get("semantic_id").and_then(serde_json::Value::as_str) == Some(reviewed_semantic)
    })?;
    let source_path = binding.get("source_path")?.as_str()?;
    let rect = binding.get("source_rect")?.as_array()?;
    if rect.len() != 4 { return None; }
    let component = |index: usize| -> Option<u32> {
        u32::try_from(rect.get(index)?.as_u64()?).ok()
    };
    Some(ResolvedWorldAsset {
        semantic_id: semantic_id.to_string(),
        source_path: source_path.to_string(),
        source_rect: PixelSelection {
            x: component(0)?, y: component(1)?, width: component(2)?, height: component(3)?,
        },
        generated_output: false,
    })
}

fn resolve_semantic_terrain_source(
    tile: TileKind,
    semantic_id: &'static str,
) -> Option<ResolvedWorldAsset> {
    let registry_path = repo_root_dir()
        .join("content/worldgen/terrain_world_semantic_registry_v1.json");
    let bytes = std::fs::read(&registry_path).ok()?;
    let registry: serde_json::Value = serde_json::from_slice(&bytes).ok()?;
    let tile_kind = format!("{tile:?}");
    let material = registry
        .get("materials")?
        .as_array()?
        .iter()
        .find(|material| {
            material.get("id").and_then(serde_json::Value::as_str) == Some(semantic_id)
                || material.get("tileKind").and_then(serde_json::Value::as_str)
                    == Some(tile_kind.as_str())
        })?;
    let source = material.get("source")?;
    let source_path = source.get("image")?.as_str()?;
    let rect = source.get("rect")?.as_array()?;
    if rect.len() != 4 {
        return None;
    }
    let component = |index: usize| -> Option<u32> {
        u32::try_from(rect.get(index)?.as_u64()?).ok()
    };
    let lifecycle = material
        .get("ownership")
        .and_then(|ownership| ownership.get("lifecycle"))
        .and_then(serde_json::Value::as_str)
        .unwrap_or("authored");
    let generated_output = lifecycle.eq_ignore_ascii_case("generated")
        || source_path.contains("/generated/")
        || source_path.contains("\\generated\\");

    // Semantic ids originate from the static runtime adapter and therefore
    // remain valid for the lifetime of this binding.
    Some(ResolvedWorldAsset {
        semantic_id: semantic_id.to_string(),
        source_path: source_path.to_string(),
        source_rect: PixelSelection {
            x: component(0)?,
            y: component(1)?,
            width: component(2)?,
            height: component(3)?,
        },
        generated_output,
    })
}
fn resolve_project_path(path: &str) -> PathBuf {
    let candidate = Path::new(path);
    if candidate.is_absolute() {
        candidate.to_path_buf()
    } else {
        repo_root_dir().join(candidate)
    }
}
