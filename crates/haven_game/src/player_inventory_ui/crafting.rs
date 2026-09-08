use super::*;

impl PlayerInventoryUi {
    pub(super) fn item_quantity(&self, item_id: &str) -> u16 {
        self.slots
            .iter()
            .flatten()
            .filter(|stack| stack.item_id == item_id)
            .map(|stack| stack.quantity)
            .sum()
    }

    pub(super) fn active_station_record_index(&self) -> Option<usize> {
        let instance_id = self.active_station_instance.as_deref()?;
        self.placed_stations
            .iter()
            .position(|record| record.instance_id == instance_id && record.placement_confirmed)
    }

    pub(super) fn crafting_item_quantity(&self, item_id: &str) -> u16 {
        let inventory_quantity = self.item_quantity(item_id);
        let station_quantity = self
            .active_station_record_index()
            .map(|index| {
                self.placed_stations[index]
                    .input_storage
                    .iter()
                    .filter(|stack| stack.item_id == item_id)
                    .map(|stack| stack.quantity)
                    .sum::<u16>()
            })
            .unwrap_or(0);
        inventory_quantity.saturating_add(station_quantity)
    }

    pub(super) fn can_craft(&self, recipe: &RecipeDefinition) -> bool {
        recipe
            .ingredients
            .iter()
            .all(|(item_id, quantity)| self.crafting_item_quantity(item_id) >= *quantity)
    }

    pub(super) fn consume(&mut self, item_id: &str, mut quantity: u16) {
        if let Some(index) = self.active_station_record_index() {
            for stack in &mut self.placed_stations[index].input_storage {
                if stack.item_id != item_id {
                    continue;
                }
                let taken = stack.quantity.min(quantity);
                stack.quantity -= taken;
                quantity -= taken;
                if quantity == 0 {
                    break;
                }
            }
            self.placed_stations[index]
                .input_storage
                .retain(|stack| stack.quantity > 0);
        }
        if quantity == 0 {
            return;
        }
        for slot in &mut self.slots {
            let Some(stack) = slot else { continue };
            if stack.item_id != item_id {
                continue;
            }
            let taken = stack.quantity.min(quantity);
            stack.quantity -= taken;
            quantity -= taken;
            if stack.quantity == 0 {
                *slot = None;
            }
            if quantity == 0 {
                break;
            }
        }
    }

    pub(crate) fn add_item(
        &mut self,
        item_id: &str,
        display_name: &str,
        mut quantity: u16,
    ) -> bool {
        if quantity == 0 {
            return true;
        }
        let original_slots = self.slots.clone();
        let stack_limit = item_stack_limit(item_id);
        for stack in self
            .slots
            .iter_mut()
            .flatten()
            .filter(|stack| stack.item_id == item_id)
        {
            let room = stack_limit.saturating_sub(stack.quantity);
            let moved = room.min(quantity);
            stack.quantity = stack.quantity.saturating_add(moved);
            quantity -= moved;
            if quantity == 0 {
                return true;
            }
        }
        while quantity > 0 {
            let Some(slot) = self.slots.iter_mut().find(|slot| slot.is_none()) else {
                self.slots = original_slots;
                return false;
            };
            let moved = stack_limit.min(quantity);
            *slot = Some(ItemStack {
                item_id: item_id.to_string(),
                display_name: display_name.to_string(),
                quantity: moved,
            });
            quantity -= moved;
        }
        true
    }

    pub(crate) fn try_add_items(&mut self, items: &[ItemStack]) -> bool {
        let original_slots = self.slots.clone();
        for item in items {
            if !self.add_item(&item.item_id, &item.display_name, item.quantity) {
                self.slots = original_slots;
                return false;
            }
        }
        self.mark_dirty();
        true
    }

    pub(super) fn station_is_available(&self, station_id: &str) -> bool {
        station_id == "hand"
            || self
                .placed_stations
                .iter()
                .any(|station| station.placement_confirmed && station.station_id == station_id)
    }

    pub(super) fn active_recipes(&self) -> &'static [RecipeDefinition] {
        recipes_for_station(crafting_stations()[self.selected_station].id.as_str())
    }

    pub(super) fn deploy_selected_station_kit(&mut self) {
        let Some(stack) = self.slots.get(self.selected_slot).and_then(Option::as_ref) else {
            self.status = "Select a station kit before deploying".to_string();
            return;
        };
        let station_id = match stack.item_id.as_str() {
            "workbench_kit" => "workbench",
            "campfire_kit" => "campfire",
            "primitive_forge_kit" => "primitive_forge",
            "tailor_bench_kit" => "tailor_bench",
            _ => {
                self.status = format!(
                    "{} is not a deployable crafting station",
                    stack.display_name
                );
                return;
            }
        };
        if self.station_is_available(station_id) {
            self.status = format!(
                "{} is already available",
                crafting_stations()
                    .iter()
                    .find(|station| station.id == station_id)
                    .map_or(station_id, |station| station.display_name.as_str())
            );
            return;
        }
        self.consume(&format!("{station_id}_kit"), 1);
        self.deployed_stations.push(station_id.to_string());
        let instance_id = format!("{}-{}", station_id, self.placed_stations.len() + 1);
        self.placed_stations.push(PlacedStationRecord {
            instance_id,
            station_id: station_id.to_string(),
            world_x: 0.0,
            world_y: 0.0,
            scene_id: String::new(),
            placement_confirmed: false,
            fuel: 0,
            input_storage: Vec::new(),
            output_storage: Vec::new(),
            processing_queue: Vec::new(),
        });
        self.pending_station_placement = Some(station_id.to_string());
        self.open = false;
        self.selected_station = crafting_stations()
            .iter()
            .position(|station| station.id == station_id)
            .unwrap_or(0);
        self.selected_recipe = 0;
        self.status = format!(
            "{} kit registered; world placement is awaiting confirmation",
            crafting_stations()[self.selected_station].display_name
        );
        self.mark_dirty();
    }

    pub(crate) fn pending_station_placement(&self) -> Option<&str> {
        self.pending_station_placement.as_deref()
    }

    pub(crate) fn confirm_station_placement(
        &mut self,
        station_id: &str,
        world_x: f32,
        world_y: f32,
        scene_id: &str,
    ) -> bool {
        let Some(record) = self
            .placed_stations
            .iter_mut()
            .rev()
            .find(|record| record.station_id == station_id && !record.placement_confirmed)
        else {
            return false;
        };
        record.world_x = world_x;
        record.world_y = world_y;
        record.scene_id = scene_id.to_string();
        record.placement_confirmed = true;
        if self.pending_station_placement.as_deref() == Some(station_id) {
            self.pending_station_placement = None;
        }
        self.status = format!("Placed {} in the world", station_display_name(station_id));
        self.mark_dirty();
        true
    }

    pub(crate) fn cancel_pending_station_placement(&mut self) -> bool {
        let Some(station_id) = self.pending_station_placement.take() else {
            return false;
        };
        if let Some(index) = self
            .placed_stations
            .iter()
            .rposition(|record| record.station_id == station_id && !record.placement_confirmed)
        {
            self.placed_stations.remove(index);
        }
        self.deployed_stations
            .retain(|deployed| deployed != &station_id);
        let item_id = format!("{station_id}_kit");
        let display_name = format!("{} Kit", station_display_name(&station_id));
        let _ = self.add_item(&item_id, &display_name, 1);
        self.status = format!(
            "Cancelled {} placement; kit returned",
            station_display_name(&station_id)
        );
        self.mark_dirty();
        true
    }

    pub(crate) fn placed_stations(&self) -> &[PlacedStationRecord] {
        &self.placed_stations
    }

    pub(super) fn try_craft_selected(&mut self) {
        let station = &crafting_stations()[self.selected_station];
        if !self.station_is_available(station.id.as_str()) {
            self.status = format!("{} requires a placed station", station.display_name);
            return;
        }
        if station.id != "hand"
            && self.active_station_context.as_deref() != Some(station.id.as_str())
        {
            self.status = format!(
                "Stand near the {} and press F to use it",
                station.display_name
            );
            return;
        }
        let recipes = self.active_recipes();
        if recipes.is_empty() {
            self.status = format!("{} has no registered recipes", station.display_name);
            return;
        }
        self.selected_recipe = self.selected_recipe.min(recipes.len() - 1);
        let recipe = &recipes[self.selected_recipe];
        if !self.can_craft(recipe) {
            self.status = format!("Missing materials for {}", recipe.display_name);
            return;
        }
        if recipe.process_seconds <= 0.0
            && !self.slots.iter().any(Option::is_none)
            && !self
                .slots
                .iter()
                .flatten()
                .any(|stack| stack.item_id == recipe.output.0.as_str())
        {
            self.status = "Inventory is full".to_string();
            return;
        }
        if recipe.process_seconds > 0.0 {
            let Some(instance_id) = self.active_station_instance.clone() else {
                self.status = format!(
                    "{} requires a physical station instance",
                    recipe.display_name
                );
                return;
            };
            let Some(station_index) = self
                .placed_stations
                .iter()
                .position(|record| record.instance_id == instance_id && record.placement_confirmed)
            else {
                self.status = "The active crafting station is no longer available".to_string();
                return;
            };
            if self.placed_stations[station_index].processing_queue.len() >= 4 {
                self.status = format!("{} processing queue is full", station.display_name);
                return;
            }
            if self.placed_stations[station_index].fuel < recipe.fuel_cost {
                self.status = format!("{} needs {} fuel", station.display_name, recipe.fuel_cost);
                return;
            }
            for (item_id, quantity) in &recipe.ingredients {
                self.consume(item_id, *quantity);
            }
            let station_record = &mut self.placed_stations[station_index];
            station_record.fuel -= recipe.fuel_cost;
            station_record.processing_queue.push(StationProcessingJob {
                recipe_id: recipe.id.to_string(),
                display_name: recipe.display_name.to_string(),
                output_item_id: recipe.output.0.to_string(),
                output_display_name: recipe.output.1.to_string(),
                output_quantity: recipe.output.2,
                remaining_seconds: recipe.process_seconds,
                total_seconds: recipe.process_seconds,
                consumed_ingredients: recipe
                    .ingredients
                    .iter()
                    .map(|(item_id, quantity)| ItemStack {
                        item_id: item_id.clone(),
                        display_name: item_display_name(item_id),
                        quantity: *quantity,
                    })
                    .collect(),
                fuel_cost: recipe.fuel_cost,
                blocked_on_output: false,
                paused: false,
            });
            self.status = format!("Queued {} at {}", recipe.display_name, station.display_name);
        } else {
            for (item_id, quantity) in &recipe.ingredients {
                self.consume(item_id, *quantity);
            }
            let _ = self.add_item(&recipe.output.0, &recipe.output.1, recipe.output.2);
            self.status = format!(
                "Crafted {} at {} [{}]",
                recipe.display_name, station.display_name, recipe.id
            );
        }
        self.mark_dirty();
    }
}
