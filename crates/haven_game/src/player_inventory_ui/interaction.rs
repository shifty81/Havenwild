use super::*;
use crate::gameplay_hotbar::GameplayTool;

impl PlayerInventoryUi {
    pub(crate) fn handle_input(&mut self, controls: &ControlRuntime) {
        if controls.action_pressed(ControlAction::Inventory)
            || controls.action_pressed(ControlAction::Cancel)
        {
            self.open = false;
            self.active_station_context = None;
            self.active_station_instance = None;
            self.status = match self.save() {
                Ok(()) => "Inventory closed and saved".to_string(),
                Err(error) => format!("Inventory closed; save failed: {error}"),
            };
            return;
        }
        let columns = 6usize;
        if controls.action_pressed(ControlAction::MoveLeft) {
            self.selected_slot = self.selected_slot.saturating_sub(1);
        }
        if controls.action_pressed(ControlAction::MoveRight) {
            self.selected_slot = (self.selected_slot + 1).min(self.slots.len() - 1);
        }
        if controls.action_pressed(ControlAction::MoveUp) {
            self.selected_slot = self.selected_slot.saturating_sub(columns);
        }
        if controls.action_pressed(ControlAction::MoveDown) {
            self.selected_slot = (self.selected_slot + columns).min(self.slots.len() - 1);
        }
        if is_key_pressed(KeyCode::Q) || controls.action_pressed(ControlAction::PreviousTool) {
            self.selected_recipe = self.selected_recipe.saturating_sub(1);
        }
        if is_key_pressed(KeyCode::E) || controls.action_pressed(ControlAction::NextTool) {
            self.selected_recipe =
                (self.selected_recipe + 1).min(self.active_recipes().len().saturating_sub(1));
        }
        if is_key_pressed(KeyCode::Z) {
            self.selected_station = self.selected_station.saturating_sub(1);
            self.selected_recipe = 0;
        }
        if is_key_pressed(KeyCode::C) {
            self.selected_station = (self.selected_station + 1).min(crafting_stations().len() - 1);
            self.selected_recipe = 0;
        }
        if is_key_pressed(KeyCode::R) {
            self.deploy_selected_station_kit();
        }
        if is_key_pressed(KeyCode::F) {
            let _ = self.add_fuel_to_active_station();
        }
        if is_key_pressed(KeyCode::G) {
            let _ = self.collect_active_station_output();
        }
        if is_key_pressed(KeyCode::T) {
            let _ = self.deposit_selected_stack_to_active_station();
        }
        if is_key_pressed(KeyCode::Y) {
            let _ = self.withdraw_active_station_input();
        }
        if is_key_pressed(KeyCode::PageUp) {
            self.selected_queue_job = self.selected_queue_job.saturating_sub(1);
        }
        if is_key_pressed(KeyCode::PageDown) {
            let queue_len = self
                .active_station_record_index()
                .map(|index| self.placed_stations[index].processing_queue.len())
                .unwrap_or(0);
            self.selected_queue_job =
                (self.selected_queue_job + 1).min(queue_len.saturating_sub(1));
        }
        if is_key_pressed(KeyCode::X) {
            if is_key_down(KeyCode::LeftControl) || is_key_down(KeyCode::RightControl) {
                let _ = self.clear_active_station_queue();
            } else {
                let _ = self.cancel_selected_station_job();
            }
        }
        if is_key_pressed(KeyCode::P) {
            let _ = self.toggle_selected_station_job_pause();
        }
        if is_key_pressed(KeyCode::U) {
            let _ = self.move_selected_station_job_up();
        }
        if is_key_pressed(KeyCode::J) {
            let _ = self.move_selected_station_job_down();
        }
        if is_key_pressed(KeyCode::B) {
            self.selected_equipment_slot =
                (self.selected_equipment_slot + 1) % equipment_slot_order().len();
            self.status = format!(
                "Selected equipment slot: {}",
                equipment_slot_order()[self.selected_equipment_slot]
            );
        }
        if is_key_pressed(KeyCode::V) {
            self.equip_selected_item();
        }
        if is_key_pressed(KeyCode::N) {
            self.unequip_selected_slot();
        }
        if controls.action_pressed(ControlAction::Confirm) {
            if is_key_down(KeyCode::LeftShift) || is_key_down(KeyCode::RightShift) {
                self.try_enqueue_selected_batch();
            } else {
                self.try_craft_selected();
            }
        }

        let point = vec2(mouse_position().0, mouse_position().1);
        if is_mouse_button_pressed(MouseButton::Left) {
            self.drag_source = None;
            self.drag_equipment_source = None;

            for (index, slot, rect) in equipment_slot_rects() {
                if rect.contains(point) {
                    self.selected_equipment_slot = index;
                    self.drag_equipment_source =
                        self.equipment.get(slot).map(|_| slot.to_string());
                    return;
                }
            }
            for (index, rect) in inventory_slot_rects() {
                if rect.contains(point) {
                    self.selected_slot = index;
                    self.drag_source = self.slots[index].as_ref().map(|_| index);
                    return;
                }
            }
            for (index, rect) in recipe_rects(self.active_recipes().len()) {
                if rect.contains(point) {
                    self.selected_recipe = index;
                    self.try_craft_selected();
                    return;
                }
            }
        }
        if is_mouse_button_released(MouseButton::Left) {
            if let Some(source) = self.drag_source.take() {
                if let Some((target_index, target_slot, _)) = equipment_slot_rects()
                    .into_iter()
                    .find(|(_, _, rect)| rect.contains(point))
                {
                    self.selected_equipment_slot = target_index;
                    self.equip_inventory_index_to_slot(source, target_slot);
                    return;
                }
                if let Some((target, _)) = inventory_slot_rects()
                    .into_iter()
                    .find(|(_, rect)| rect.contains(point))
                {
                    self.move_or_merge_stack(source, target);
                    self.selected_slot = target;
                    return;
                }
            }

            if let Some(source_slot) = self.drag_equipment_source.take() {
                if let Some((target, _)) = inventory_slot_rects()
                    .into_iter()
                    .find(|(_, rect)| rect.contains(point))
                {
                    self.unequip_slot_to_inventory_target(&source_slot, target);
                    self.selected_slot = target;
                    return;
                }
            }
        }
        if is_mouse_button_pressed(MouseButton::Right) {
            if let Some((index, _)) = inventory_slot_rects()
                .into_iter()
                .find(|(_, rect)| rect.contains(point))
            {
                self.split_stack(index);
                self.selected_slot = index;
            }
        }
    }

    pub(crate) fn equipped_items(&self) -> &BTreeMap<String, ItemStack> {
        &self.equipment
    }

    pub(crate) fn bootstrap_equipment(&mut self, equipment: BTreeMap<String, ItemStack>) {
        if !self.equipment.is_empty() || equipment.is_empty() {
            return;
        }
        self.equipment = equipment;
        self.status = "Starter clothing registered as equipped inventory items".to_string();
        self.mark_dirty();
    }

    pub(crate) fn take_equipment_changed(&mut self) -> bool {
        std::mem::take(&mut self.equipment_changed)
    }

    fn equip_inventory_index_to_slot(&mut self, source: usize, target_slot: &str) {
        let Some(stack) = self.slots.get(source).and_then(Option::as_ref) else {
            self.status = "That backpack slot is empty".to_string();
            return;
        };
        let Some(canonical_slot) = equipment_slot_for_item(&stack.item_id) else {
            self.status = format!("{} is not equippable", stack.display_name);
            return;
        };

        // GameplayTool is a taxonomy/action adapter, not a hotbar assignment.
        // Recognized tools must still enter the canonical Main Hand equipment
        // slot before gameplay can use them.
        if GameplayTool::from_item_id(&stack.item_id).is_some() && canonical_slot != "main_hand" {
            self.status = format!("{} must equip to Main Hand", stack.display_name);
            return;
        }
        if canonical_slot != target_slot {
            self.status = format!(
                "{} belongs in {}, not {}",
                stack.display_name, canonical_slot, target_slot
            );
            return;
        }

        self.selected_slot = source;
        if let Some(index) = equipment_slot_order()
            .iter()
            .position(|slot| *slot == target_slot)
        {
            self.selected_equipment_slot = index;
        }
        self.equip_selected_item();
    }

    fn unequip_slot_to_inventory_target(&mut self, source_slot: &str, target: usize) {
        if target >= self.slots.len() {
            return;
        }
        let Some(stack) = self.equipment.remove(source_slot) else {
            self.status = format!("Nothing is equipped in {source_slot}");
            return;
        };

        let accepted = match self.slots[target].as_mut() {
            None => {
                self.slots[target] = Some(stack.clone());
                true
            }
            Some(target_stack)
                if target_stack.item_id == stack.item_id
                    && target_stack.quantity < item_stack_limit(&stack.item_id) =>
            {
                target_stack.quantity = target_stack.quantity.saturating_add(stack.quantity);
                true
            }
            Some(_) => false,
        };

        if !accepted {
            self.equipment.insert(source_slot.to_string(), stack);
            self.status = "Target backpack slot is occupied".to_string();
            return;
        }

        self.equipment_changed = true;
        self.mark_dirty();
        self.status = format!("Unequipped {} to backpack", stack.display_name);
    }

    pub(crate) fn equip_selected_item(&mut self) {
        let Some(stack) = self
            .slots
            .get(self.selected_slot)
            .and_then(Option::as_ref)
            .cloned()
        else {
            self.status = "Select clothing or equipment before equipping".to_string();
            return;
        };
        let Some(equipment_slot) = equipment_slot_for_item(&stack.item_id) else {
            self.status = format!("{} is not equippable", stack.display_name);
            return;
        };
        if self
            .equipment
            .get(&equipment_slot)
            .is_some_and(|equipped| equipped.item_id == stack.item_id)
        {
            self.status = format!("{} is already equipped", stack.display_name);
            return;
        }

        let previous = self.equipment.remove(&equipment_slot);
        if let Some(selected) = self.slots[self.selected_slot].as_mut() {
            selected.quantity = selected.quantity.saturating_sub(1);
            if selected.quantity == 0 {
                self.slots[self.selected_slot] = None;
            }
        }
        if let Some(previous_stack) = previous.as_ref() {
            if !self.add_item(
                &previous_stack.item_id,
                &previous_stack.display_name,
                previous_stack.quantity,
            ) {
                if let Some(selected) = self.slots[self.selected_slot].as_mut() {
                    selected.quantity = selected.quantity.saturating_add(1);
                } else {
                    self.slots[self.selected_slot] = Some(stack);
                }
                self.equipment
                    .insert(equipment_slot, previous_stack.clone());
                self.status = "No inventory space to swap equipment".to_string();
                return;
            }
        }
        self.equipment.insert(
            equipment_slot.clone(),
            ItemStack {
                item_id: stack.item_id.clone(),
                display_name: stack.display_name.clone(),
                quantity: 1,
            },
        );
        self.selected_equipment_slot = equipment_slot_order()
            .iter()
            .position(|slot| *slot == equipment_slot.as_str())
            .unwrap_or(0);
        self.equipment_changed = true;
        self.mark_dirty();
        self.status = format!("Equipped {} in {}", stack.display_name, equipment_slot);
    }

    pub(super) fn unequip_selected_slot(&mut self) {
        let slot = equipment_slot_order()[self.selected_equipment_slot].to_string();
        let Some(stack) = self.equipment.remove(&slot) else {
            self.status = format!("Nothing is equipped in {slot}");
            return;
        };
        if !self.add_item(&stack.item_id, &stack.display_name, stack.quantity) {
            self.equipment.insert(slot.clone(), stack);
            self.status = "Inventory is full; equipment was not removed".to_string();
            return;
        }
        self.equipment_changed = true;
        self.mark_dirty();
        self.status = format!("Unequipped {}", stack.display_name);
    }

    pub(super) fn move_or_merge_stack(&mut self, source: usize, target: usize) {
        if source == target || source >= self.slots.len() || target >= self.slots.len() {
            return;
        }
        let Some(source_stack) = self.slots[source].take() else {
            return;
        };
        match self.slots[target].as_mut() {
            Some(target_stack)
                if target_stack.item_id == source_stack.item_id
                    && item_stack_limit(&source_stack.item_id) > 1 =>
            {
                target_stack.quantity = target_stack.quantity.saturating_add(source_stack.quantity);
                self.status = format!("Merged {}", target_stack.display_name);
            }
            Some(_) => {
                let target_stack = self.slots[target].take();
                self.slots[target] = Some(source_stack);
                self.slots[source] = target_stack;
                self.status = "Swapped inventory slots".to_string();
            }
            None => {
                self.slots[target] = Some(source_stack);
                self.status = "Moved inventory stack".to_string();
            }
        }
        self.mark_dirty();
    }

    pub(super) fn split_stack(&mut self, source: usize) {
        let Some(stack) = self.slots.get_mut(source).and_then(Option::as_mut) else {
            return;
        };
        if stack.quantity < 2 {
            return;
        }
        let split_quantity = stack.quantity / 2;
        stack.quantity -= split_quantity;
        let split_stack = ItemStack {
            item_id: stack.item_id.clone(),
            display_name: stack.display_name.clone(),
            quantity: split_quantity,
        };
        if let Some(target) = self.slots.iter_mut().find(|slot| slot.is_none()) {
            *target = Some(split_stack);
            self.status = "Split inventory stack".to_string();
            self.mark_dirty();
        } else if let Some(stack) = self.slots[source].as_mut() {
            stack.quantity = stack.quantity.saturating_add(split_quantity);
            self.status = "No empty slot available for split".to_string();
        }
    }
}
