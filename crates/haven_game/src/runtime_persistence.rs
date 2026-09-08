use super::*;

impl Game {
    fn reload_building_instance_authority(
        &mut self,
        worldgen_pack_path: Option<&str>,
        reason: &str,
    ) -> Result<usize, String> {
        let mut registry = haven_assets::building_instance::BuildingInstanceRegistry::load_from_project_root(
            runtime_root(),
            &self.building_recipe_registry,
        )?;
        let generated = if let Some(path) = worldgen_pack_path {
            registry.merge_worldgen_pack_placements(path, &self.building_recipe_registry)?
        } else {
            0
        };
        let restored = registry.apply_world_state_from_path(
            &building_instance_save_path(&self.save_paths.root),
            &self.world_id.0,
            &self.building_recipe_registry,
        )?;
        self.building_instance_registry = registry;
        self.building_instance_views = self.building_instance_registry.initial_view_states();
        self.refresh_building_instance_views();
        self.log.event(&format!(
            "{reason}: BuildingInstance authority reloaded (generated={generated}, save_deltas={restored})"
        ));
        Ok(generated)
    }

    pub(super) fn save_map(&mut self) {
        self.prepare_world_paint_deltas_before_save();
        match save_world_to_path(&self.save_paths.world, &self.world) {
            Ok(_) => {
                let building_result = self.building_instance_registry.save_world_state_to_path(
                    &building_instance_save_path(&self.save_paths.root),
                    &self.world_id.0,
                );
                self.save_layout();
                if let Err(error) = self.persist_character_world_state("manual save") {
                    self.log
                        .event(&format!("Character-world save failed: {error}"));
                }
                if let Err(error) = self.player_inventory_ui.save() {
                    self.log.event(&format!("Inventory save failed: {error}"));
                }
                match building_result {
                    Ok(()) => {
                        self.status_message = format!(
                            "Saved {} + BuildingInstance deltas {}",
                            self.save_paths.world, building_instance_save_path(&self.save_paths.root).display()
                        );
                    }
                    Err(error) => {
                        self.status_message = format!(
                            "World saved, but BuildingInstance state save failed: {error}"
                        );
                    }
                }
                self.log.event(&self.status_message);
            }
            Err(err) => {
                self.status_message = format!("Save failed: {err}");
                self.log.event(&self.status_message);
            }
        }
    }

    pub(super) fn load_map(&mut self) {
        match load_world_from_path(&self.save_paths.world) {
            Ok(world) => {
                self.world = world;
                self.ui_layout = Self::load_saved_layout(&mut self.log);
                self.reload_character_world_state();
                let inventory_path = player_inventory_ui::PlayerInventoryUi::inventory_save_path(
                    &self.save_paths.character_links,
                    &self.character_id.0,
                );
                self.player_inventory_ui =
                    player_inventory_ui::PlayerInventoryUi::load_or_starter(inventory_path);
                self.replay_paint_deltas_after_world_load("Manual load paint delta replay");
                let pack = runtime_worldgen_pack_path();
                let building_status = self
                    .reload_building_instance_authority(Some(&pack), "Manual load")
                    .map(|count| format!("building placements={count}"))
                    .unwrap_or_else(|error| format!("building authority error={error}"));
                self.status_message = format!(
                    "Loaded {}; {}; {}",
                    self.save_paths.world, self.world_paint_delta_status, building_status
                );
                self.log.event(&self.status_message);
            }
            Err(err) => {
                self.status_message = format!("Load failed: {err}");
                self.log.event(&self.status_message);
            }
        }
    }

    pub(super) fn load_worldgen_pack(&mut self) {
        let worldgen_pack_path = runtime_worldgen_pack_path();
        match load_worldgen_pack_from_path(&worldgen_pack_path) {
            Ok((mut world, report)) => {
                let canonicalized_world_assets =
                    self.placeable_registry.canonicalize_world_aliases(&mut world);
                self.world = world;
                self.selected_object_index = None;
                self.object_list_offset = 0;
                self.reload_character_world_state();
                self.replay_paint_deltas_after_world_load("Worldgen load paint delta replay");
                let building_status = self
                    .reload_building_instance_authority(
                        Some(&worldgen_pack_path),
                        "Worldgen pack load",
                    )
                    .map(|count| format!("BuildingInstances={count}"))
                    .unwrap_or_else(|error| format!("BuildingInstance error={error}"));
                self.validation_messages = validate_world(&self.world);
                self.status_message = format!(
                    "{}; published aliases canonicalized={}; {}; {}",
                    report.status_line(),
                    canonicalized_world_assets,
                    building_status,
                    self.world_paint_delta_status
                );
                self.log.event(&self.status_message);
                for warning in &report.warnings {
                    self.log.event(&format!("Worldgen warning: {warning}"));
                }
            }
            Err(err) => {
                self.status_message = format!("Worldgen load failed: {err}");
                self.log.event(&self.status_message);
            }
        }
    }

    pub(super) fn export_worldgen_json(&mut self) {
        let export_path = runtime_worldgen_export_path();
        match export_worldgen_pack_to_path(&self.world, &export_path) {
            Ok(report) => {
                self.status_message = report.status_line();
                self.log.event(&self.status_message);
                for warning in &report.warnings {
                    self.log
                        .event(&format!("Worldgen export warning: {warning}"));
                }
            }
            Err(err) => {
                self.status_message = format!("Worldgen export failed: {err}");
                self.log.event(&self.status_message);
            }
        }
    }

    pub(super) fn save_layout(&mut self) {
        let layout_path = runtime_layout_path();
        if let Err(err) = save_ui_layout_to_path(&layout_path, &self.ui_layout) {
            self.log.event(&format!("Layout save failed: {err}"));
        }
    }
}
