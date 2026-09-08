use super::*;

impl PlayerInventoryUi {
    pub(crate) fn deposit_selected_stack_to_active_station(&mut self) -> bool {
        let Some(station_index) = self.active_station_record_index() else {
            self.status = "Open a physical crafting station first".to_string();
            return false;
        };
        let Some(stack) = self
            .slots
            .get_mut(self.selected_slot)
            .and_then(Option::take)
        else {
            self.status = "Select an inventory stack to transfer".to_string();
            return false;
        };
        let display_name = stack.display_name.clone();
        if let Some(existing) = self.placed_stations[station_index]
            .input_storage
            .iter_mut()
            .find(|stored| stored.item_id == stack.item_id)
        {
            existing.quantity = existing.quantity.saturating_add(stack.quantity);
        } else {
            self.placed_stations[station_index]
                .input_storage
                .push(stack);
        }
        self.status = format!("Transferred {display_name} to station input storage");
        self.mark_dirty();
        true
    }

    pub(crate) fn withdraw_active_station_input(&mut self) -> bool {
        let Some(station_index) = self.active_station_record_index() else {
            self.status = "Open a physical crafting station first".to_string();
            return false;
        };
        if self.placed_stations[station_index].input_storage.is_empty() {
            self.status = "Station input storage is empty".to_string();
            return false;
        }
        let stack = self.placed_stations[station_index].input_storage.remove(0);
        let display_name = stack.display_name.clone();
        if self.add_item(&stack.item_id, &stack.display_name, stack.quantity) {
            self.status = format!("Withdrew {display_name} from station input storage");
            self.mark_dirty();
            true
        } else {
            self.placed_stations[station_index]
                .input_storage
                .insert(0, stack);
            self.status = "Inventory is full".to_string();
            false
        }
    }

    pub(crate) fn add_fuel_to_active_station(&mut self) -> bool {
        let Some(instance_id) = self.active_station_instance.clone() else {
            self.status = "Open a fuel-using station first".to_string();
            return false;
        };
        if self.item_quantity("wood") == 0 && self.item_quantity("charcoal") == 0 {
            self.status = "No wood or charcoal available for fuel".to_string();
            return false;
        }
        let fuel_item = if self.item_quantity("charcoal") > 0 {
            "charcoal"
        } else {
            "wood"
        };
        self.consume(fuel_item, 1);
        let Some(station) = self
            .placed_stations
            .iter_mut()
            .find(|record| record.instance_id == instance_id)
        else {
            return false;
        };
        station.fuel = station
            .fuel
            .saturating_add(if fuel_item == "charcoal" { 3 } else { 1 });
        self.status = format!(
            "Added fuel to {}",
            station_display_name(&station.station_id)
        );
        self.mark_dirty();
        true
    }

    pub(crate) fn collect_active_station_output(&mut self) -> bool {
        let Some(instance_id) = self.active_station_instance.clone() else {
            return false;
        };
        let Some(index) = self
            .placed_stations
            .iter()
            .position(|record| record.instance_id == instance_id)
        else {
            return false;
        };
        let outputs = std::mem::take(&mut self.placed_stations[index].output_storage);
        let mut remaining = Vec::new();
        let mut collected = 0_u16;
        for stack in outputs {
            if self.add_item(&stack.item_id, &stack.display_name, stack.quantity) {
                collected = collected.saturating_add(stack.quantity);
            } else {
                remaining.push(stack);
            }
        }
        self.placed_stations[index].output_storage = remaining;
        self.status = if collected > 0 {
            format!("Collected {collected} processed item(s)")
        } else {
            "No station output available".to_string()
        };
        if collected > 0 {
            self.mark_dirty();
        }
        collected > 0
    }

    pub(crate) fn cancel_selected_station_job(&mut self) -> bool {
        let Some(station_index) = self.active_station_record_index() else {
            self.status = "Open a physical crafting station first".to_string();
            return false;
        };
        let queue_len = self.placed_stations[station_index].processing_queue.len();
        if queue_len == 0 {
            self.status = "The processing queue is empty".to_string();
            return false;
        }
        self.selected_queue_job = self.selected_queue_job.min(queue_len - 1);
        let job = self.placed_stations[station_index]
            .processing_queue
            .remove(self.selected_queue_job);
        let cancelled_name = job.display_name.clone();
        self.placed_stations[station_index].fuel = self.placed_stations[station_index]
            .fuel
            .saturating_add(job.fuel_cost);
        for ingredient in job.consumed_ingredients {
            merge_stack(
                &mut self.placed_stations[station_index].input_storage,
                ingredient,
            );
        }
        self.selected_queue_job = self.selected_queue_job.min(
            self.placed_stations[station_index]
                .processing_queue
                .len()
                .saturating_sub(1),
        );
        self.status = format!("Cancelled {cancelled_name}; materials and fuel returned to station");
        self.push_station_notification(format!("Cancelled {cancelled_name}"));
        self.mark_dirty();
        true
    }

    pub(super) fn toggle_selected_station_job_pause(&mut self) -> bool {
        let Some(station_index) = self.active_station_record_index() else {
            self.status = "Open a physical crafting station first".to_string();
            return false;
        };
        let queue_len = self.placed_stations[station_index].processing_queue.len();
        if queue_len == 0 {
            self.status = "The processing queue is empty".to_string();
            return false;
        }
        self.selected_queue_job = self.selected_queue_job.min(queue_len - 1);
        let (paused, display_name) = {
            let job =
                &mut self.placed_stations[station_index].processing_queue[self.selected_queue_job];
            job.paused = !job.paused;
            (job.paused, job.display_name.clone())
        };
        let state = if paused { "Paused" } else { "Resumed" };
        self.status = format!("{state} {display_name}");
        self.push_station_notification(format!("{state} {display_name}"));
        self.mark_dirty();
        true
    }

    pub(super) fn clear_active_station_queue(&mut self) -> bool {
        let Some(station_index) = self.active_station_record_index() else {
            self.status = "Open a physical crafting station first".to_string();
            return false;
        };
        if self.placed_stations[station_index]
            .processing_queue
            .is_empty()
        {
            self.status = "The processing queue is empty".to_string();
            return false;
        }
        let jobs = std::mem::take(&mut self.placed_stations[station_index].processing_queue);
        let cancelled_count = jobs.len();
        for job in jobs {
            self.placed_stations[station_index].fuel = self.placed_stations[station_index]
                .fuel
                .saturating_add(job.fuel_cost);
            for ingredient in job.consumed_ingredients {
                merge_stack(
                    &mut self.placed_stations[station_index].input_storage,
                    ingredient,
                );
            }
        }
        self.selected_queue_job = 0;
        self.status = format!(
            "Cleared {cancelled_count} queued job{}; materials and fuel returned",
            if cancelled_count == 1 { "" } else { "s" }
        );
        self.push_station_notification(format!("Cleared {cancelled_count} queued job(s)"));
        self.mark_dirty();
        true
    }

    pub(super) fn move_selected_station_job_up(&mut self) -> bool {
        let Some(station_index) = self.active_station_record_index() else {
            self.status = "Open a physical crafting station first".to_string();
            return false;
        };
        let queue_len = self.placed_stations[station_index].processing_queue.len();
        if queue_len < 2 || self.selected_queue_job == 0 {
            self.status = "Selected job is already first in the queue".to_string();
            return false;
        }
        self.selected_queue_job = self.selected_queue_job.min(queue_len - 1);
        self.placed_stations[station_index]
            .processing_queue
            .swap(self.selected_queue_job, self.selected_queue_job - 1);
        self.selected_queue_job -= 1;
        self.status = "Moved selected job earlier in the queue".to_string();
        self.mark_dirty();
        true
    }

    pub(super) fn move_selected_station_job_down(&mut self) -> bool {
        let Some(station_index) = self.active_station_record_index() else {
            self.status = "Open a physical crafting station first".to_string();
            return false;
        };
        let queue_len = self.placed_stations[station_index].processing_queue.len();
        if queue_len < 2 {
            self.status = "The processing queue has fewer than two jobs".to_string();
            return false;
        }
        self.selected_queue_job = self.selected_queue_job.min(queue_len - 1);
        if self.selected_queue_job + 1 >= queue_len {
            self.status = "Selected job is already last in the queue".to_string();
            return false;
        }
        self.placed_stations[station_index]
            .processing_queue
            .swap(self.selected_queue_job, self.selected_queue_job + 1);
        self.selected_queue_job += 1;
        self.status = "Moved selected job later in the queue".to_string();
        self.mark_dirty();
        true
    }

    pub(super) fn try_enqueue_selected_batch(&mut self) {
        let is_timed_recipe = self
            .active_recipes()
            .get(self.selected_recipe)
            .is_some_and(|recipe| recipe.process_seconds > 0.0);
        if !is_timed_recipe {
            self.try_craft_selected();
            return;
        }
        let mut queued = 0usize;
        for _ in 0..4 {
            let before = self
                .active_station_record_index()
                .map(|index| self.placed_stations[index].processing_queue.len())
                .unwrap_or(0);
            self.try_craft_selected();
            let after = self
                .active_station_record_index()
                .map(|index| self.placed_stations[index].processing_queue.len())
                .unwrap_or(before);
            if after <= before {
                break;
            }
            queued += after - before;
        }
        if queued > 0 {
            self.status = format!(
                "Queued {queued} processing job{}",
                if queued == 1 { "" } else { "s" }
            );
        }
    }

    pub(crate) fn update_station_processing(&mut self, dt: f32) {
        let mut changed = false;
        let mut notifications = Vec::new();
        for station in &mut self.placed_stations {
            if station.processing_queue.is_empty() {
                continue;
            }
            {
                let job = &mut station.processing_queue[0];
                if job.paused {
                    continue;
                }
                if job.remaining_seconds > 0.0 {
                    job.remaining_seconds = (job.remaining_seconds - dt).max(0.0);
                }
            }
            if station.processing_queue[0].remaining_seconds > 0.0 {
                continue;
            }
            let output_item_id = station.processing_queue[0].output_item_id.clone();
            let output_quantity = station.processing_queue[0].output_quantity;
            if !can_accept_station_output(&station.output_storage, &output_item_id, output_quantity)
            {
                let job = &mut station.processing_queue[0];
                if !job.blocked_on_output {
                    job.blocked_on_output = true;
                    notifications.push(format!(
                        "{} is waiting: {} output storage is full",
                        job.display_name,
                        station_display_name(&station.station_id)
                    ));
                    changed = true;
                }
                continue;
            }
            let completed = station.processing_queue.remove(0);
            merge_stack(
                &mut station.output_storage,
                ItemStack {
                    item_id: completed.output_item_id,
                    display_name: completed.output_display_name,
                    quantity: completed.output_quantity,
                },
            );
            notifications.push(format!(
                "{} completed at {}",
                completed.display_name,
                station_display_name(&station.station_id)
            ));
            changed = true;
        }
        for notification in notifications {
            self.push_station_notification(notification);
        }
        if changed {
            self.status = "Crafting station state updated".to_string();
            self.mark_dirty();
        }
    }

    pub(super) fn push_station_notification(&mut self, message: String) {
        self.processing_notifications.push(StationNotification {
            message,
            #[allow(dead_code)]
            created_at: get_time(),
        });
        if self.processing_notifications.len() > 6 {
            let excess = self.processing_notifications.len() - 6;
            self.processing_notifications.drain(0..excess);
        }
    }
}
