use super::*;
use std::collections::HashMap;
use crate::runtime_item_icons::draw_item_icon;
use crate::runtime_ui_theme::{
    draw_runtime_key_hint, draw_runtime_panel, draw_runtime_progress, draw_runtime_section,
    draw_runtime_slot, fit_runtime_label, ui_backdrop, ui_bad, ui_brass, ui_brass_bright,
    ui_good, ui_muted, ui_parchment, ui_teal,
};

impl PlayerInventoryUi {
    pub(crate) fn draw_processing_notifications(&self) {
        let now = get_time();
        let active = self
            .processing_notifications
            .iter()
            .rev()
            .filter(|notification| now - notification.created_at <= STATION_NOTIFICATION_SECONDS)
            .take(3)
            .collect::<Vec<_>>();
        for (index, notification) in active.into_iter().rev().enumerate() {
            let width = 460.0_f32.min(screen_width() - 32.0);
            let x = (screen_width() - width) * 0.5;
            let y = 18.0 + index as f32 * 48.0;
            draw_rectangle(x, y, width, 40.0, Color::from_rgba(31, 31, 27, 244));
            draw_rectangle(x, y, 4.0, 40.0, ui_brass());
            draw_rectangle_lines(x, y, width, 40.0, 1.0, ui_teal());
            draw_text(
                &fit_runtime_label(&notification.message, width - 28.0, 15),
                x + 14.0,
                y + 25.0,
                15.0,
                ui_parchment(),
            );
        }
    }

    pub(crate) fn draw(
        &self,
        item_icon_atlas: Option<&Texture2D>,
        item_icon_rects: &HashMap<String, [f32; 4]>,
    ) {
        draw_rectangle(0.0, 0.0, screen_width(), screen_height(), ui_backdrop());
        let panel = inventory_panel_rect();
        draw_runtime_panel(
            panel,
            "INVENTORY & CRAFTING",
            Some("Equip real items, organize supplies, and craft through available stations"),
        );

        let equipment_section = Rect::new(panel.x + 20.0, panel.y + 66.0, 282.0, 350.0);
        draw_runtime_section(equipment_section, "EQUIPMENT");
        let doll = equipment_paper_doll_rect();
        draw_rectangle(doll.x, doll.y, doll.w, doll.h, Color::from_rgba(7, 14, 17, 205));
        draw_rectangle_lines(doll.x, doll.y, doll.w, doll.h, 1.0, ui_teal());
        draw_text("CHARACTER", doll.x + 15.0, doll.y + 15.0, 10.0, ui_muted());
        for (index, slot, rect) in equipment_slot_rects() {
            let selected = index == self.selected_equipment_slot;
            draw_runtime_slot(rect, selected, true);
            let short_slot = match slot {
                "main_hand" => "MAIN",
                "off_hand" => "OFF",
                "torso" => "BODY",
                other => other,
            };
            draw_text(short_slot, rect.x + 4.0, rect.y + 11.0, 9.0, ui_muted());
            if let Some(stack) = self.equipment.get(slot) {
                let icon_rect = Rect::new(rect.x + 19.0, rect.y + 4.0, rect.w - 22.0, rect.h - 8.0);
                let drawn = draw_item_icon(item_icon_atlas, item_icon_rects, &stack.item_id, icon_rect, WHITE);
                if !drawn {
                    draw_text(
                        &fit_runtime_label(&stack.display_name, rect.w - 8.0, 9),
                        rect.x + 4.0,
                        rect.y + 30.0,
                        9.0,
                        if selected { ui_brass_bright() } else { ui_parchment() },
                    );
                }
            } else {
                draw_text("—", rect.x + rect.w - 13.0, rect.y + 29.0, 13.0, Color::from_rgba(116, 118, 106, 255));
            }
        }
        draw_text(
            "Drag backpack items onto matching slots · drag gear back to backpack",
            equipment_section.x + 8.0,
            equipment_section.y + equipment_section.h - 9.0,
            9.0,
            ui_muted(),
        );

        let inventory_section = Rect::new(panel.x + 312.0, panel.y + 66.0, 394.0, 350.0);
        draw_runtime_section(inventory_section, "BACKPACK");
        for (index, rect) in inventory_slot_rects() {
            let selected = index == self.selected_slot;
            draw_runtime_slot(rect, selected, self.slots[index].is_some());
            if let Some(stack) = &self.slots[index] {
                let icon_dest = Rect::new(rect.x + 5.0, rect.y + 4.0, rect.w - 10.0, rect.h - 16.0);
                let drawn = draw_item_icon(item_icon_atlas, item_icon_rects, &stack.item_id, icon_dest, WHITE);
                if !drawn {
                    let label = fit_runtime_label(&stack.display_name, rect.w - 9.0, 10);
                    draw_text(
                        &label,
                        rect.x + 5.0,
                        rect.y + 25.0,
                        10.0,
                        if selected { ui_brass_bright() } else { ui_parchment() },
                    );
                }
                let quantity = stack.quantity.to_string();
                let q_w = measure_text(&quantity, None, 12, 1.0).width;
                draw_text(
                    &quantity,
                    rect.x + rect.w - q_w - 5.0,
                    rect.y + rect.h - 6.0,
                    12.0,
                    ui_parchment(),
                );
            }
        }
        if let Some(stack) = self.slots.get(self.selected_slot).and_then(Option::as_ref) {
            draw_text(
                &fit_runtime_label(
                    &format!("Selected · {} ×{}", stack.display_name, stack.quantity),
                    inventory_section.w - 20.0,
                    13,
                ),
                inventory_section.x + 10.0,
                inventory_section.y + inventory_section.h - 10.0,
                13.0,
                ui_parchment(),
            );
        }

        let craft_section = Rect::new(
            panel.x + 20.0,
            panel.y + 426.0,
            panel.w - 40.0,
            (panel.h - 480.0).max(150.0),
        );
        draw_runtime_section(craft_section, "CRAFTING");
        let craft_x = panel.x + 28.0;
        let craft_y = panel.y + 444.0;
        let station = &crafting_stations()[self.selected_station];
        let station_available = self.station_is_available(station.id.as_str());
        draw_text(
            station.display_name.as_str(),
            craft_x,
            craft_y + 2.0,
            17.0,
            if station_available { ui_brass_bright() } else { ui_bad() },
        );
        draw_text(
            if station_available { "READY" } else { "KIT REQUIRED" },
            craft_x + 156.0,
            craft_y + 2.0,
            11.0,
            if station_available { ui_good() } else { ui_bad() },
        );

        for row in 0..2 {
            for column in 0..2 {
                let rect = Rect::new(
                    craft_x + column as f32 * 58.0,
                    craft_y + 18.0 + row as f32 * 58.0,
                    50.0,
                    50.0,
                );
                draw_runtime_slot(rect, false, true);
                let index = row * 2 + column;
                if let Some(stack) = &self.crafting_grid[index] {
                    draw_text(
                        &fit_runtime_label(&stack.display_name, rect.w - 8.0, 10),
                        rect.x + 4.0,
                        rect.y + 21.0,
                        10.0,
                        ui_parchment(),
                    );
                    draw_text(
                        &format!("×{}", stack.quantity),
                        rect.x + 4.0,
                        rect.y + 39.0,
                        10.0,
                        ui_muted(),
                    );
                }
            }
        }
        draw_line(craft_x + 126.0, craft_y + 82.0, craft_x + 148.0, craft_y + 82.0, 2.0, ui_brass());
        draw_triangle(
            vec2(craft_x + 151.0, craft_y + 82.0),
            vec2(craft_x + 143.0, craft_y + 77.0),
            vec2(craft_x + 143.0, craft_y + 87.0),
            ui_brass(),
        );
        let output_rect = Rect::new(craft_x + 164.0, craft_y + 48.0, 72.0, 72.0);
        draw_runtime_slot(output_rect, false, station_available);
        draw_text("OUTPUT", output_rect.x + 13.0, output_rect.y + 40.0, 10.0, ui_muted());

        let station_summary = format!(
            "{} inputs · {} outputs · {} fuel · {}",
            station.input_slots, station.output_slots, station.fuel_slots, station.recipe_category
        );
        draw_text(
            &fit_runtime_label(&station_summary, 460.0, 12),
            craft_x,
            craft_y + 145.0,
            12.0,
            ui_muted(),
        );

        if let Some(instance_id) = self.active_station_instance.as_deref() {
            if let Some(record) = self
                .placed_stations
                .iter()
                .find(|record| record.instance_id == instance_id)
            {
                let queue_x = craft_x + 250.0;
                draw_text(
                    &format!(
                        "Fuel {} · Input {} · Queue {}/4 · Output {}/{}",
                        record.fuel,
                        record.input_storage.iter().map(|stack| stack.quantity as u32).sum::<u32>(),
                        record.processing_queue.len(),
                        record.output_storage.len(),
                        STATION_OUTPUT_STACK_LIMIT,
                    ),
                    queue_x,
                    craft_y + 22.0,
                    12.0,
                    ui_muted(),
                );
                for (queue_index, job) in record.processing_queue.iter().take(4).enumerate() {
                    let progress = if job.total_seconds > 0.0 {
                        1.0 - job.remaining_seconds / job.total_seconds
                    } else {
                        1.0
                    };
                    let y = craft_y + 36.0 + queue_index as f32 * 27.0;
                    let label = format!(
                        "{}{}. {}{}",
                        if queue_index == self.selected_queue_job { ">" } else { " " },
                        queue_index + 1,
                        job.display_name,
                        if job.blocked_on_output { " · OUTPUT FULL" } else if job.paused { " · PAUSED" } else { "" },
                    );
                    draw_text(
                        &fit_runtime_label(&label, 330.0, 11),
                        queue_x,
                        y + 10.0,
                        11.0,
                        if queue_index == self.selected_queue_job { ui_brass_bright() } else { ui_parchment() },
                    );
                    draw_runtime_progress(
                        Rect::new(queue_x + 338.0, y + 2.0, 92.0, 9.0),
                        progress,
                        if job.blocked_on_output { ui_bad() } else { ui_good() },
                    );
                }
            }
        }

        let recipes = self.active_recipes();
        draw_text("RECIPES", panel.x + 520.0, panel.y + 448.0, 14.0, ui_brass_bright());
        for (index, rect) in recipe_rects(recipes.len()) {
            let recipe = &recipes[index];
            let available = self.can_craft(recipe);
            draw_runtime_slot(rect, index == self.selected_recipe, available);
            draw_text(
                &fit_runtime_label(recipe.display_name.as_str(), rect.w - 18.0, 14),
                rect.x + 9.0,
                rect.y + 20.0,
                14.0,
                if available { ui_parchment() } else { ui_bad() },
            );
            let requirements = recipe
                .ingredients
                .iter()
                .map(|(id, qty)| format!("{}×{}", qty, id))
                .collect::<Vec<_>>()
                .join("  ");
            draw_text(
                &fit_runtime_label(&requirements, rect.w - 18.0, 11),
                rect.x + 9.0,
                rect.y + 39.0,
                11.0,
                if available { ui_good() } else { ui_muted() },
            );
        }

        let footer_y = panel.y + panel.h - 32.0;
        let mut hint_x = panel.x + 22.0;
        for (key, label) in [
            ("B", "Gear Slot"),
            ("V", "Equip"),
            ("N", "Unequip"),
            ("Z/C", "Station"),
            ("Q/E", "Recipe"),
            ("Enter", "Craft"),
        ] {
            let width = draw_runtime_key_hint(hint_x, footer_y, key, label);
            hint_x += width;
            if hint_x > panel.x + panel.w - 190.0 {
                break;
            }
        }
        draw_text(
            &fit_runtime_label(
                &format!("{}{}", self.status, if self.dirty { " · unsaved" } else { "" }),
                (panel.w - 44.0).max(80.0),
                12,
            ),
            panel.x + 22.0,
            panel.y + panel.h - 43.0,
            12.0,
            ui_muted(),
        );
    }
}
