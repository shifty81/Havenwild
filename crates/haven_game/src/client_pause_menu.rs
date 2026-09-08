use macroquad::prelude::*;

use haven_core::TILE_SIZE;
use haven_sim::advance_day_clock;

use crate::client_controls::{ControlAction, ControlRuntime, ControllerBinding, RebindDevice};
use crate::runtime_ui_theme::{draw_runtime_panel, ui_backdrop, ui_muted, ui_teal};
use super::Game;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum ClientRuntimeFlow {
    Continue,
    ReturnToMainMenu,
    QuitDesktop,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum PauseMenuPage {
    Main,
    Settings,
    Controls,
    Controller,
}

impl Game {
    pub(super) fn update(&mut self, dt: f32) -> ClientRuntimeFlow {
        // Input is polled even while the simulation is paused so keyboard,
        // mouse, and controller navigation remain live inside the ESC menu.
        self.controls.poll();

        // Once open, the pause menu owns input before map/station/inventory
        // handlers can react to the same controller or keyboard event.
        if self.pause_menu_open {
            return self.update_pause_menu();
        }

        // Chat owns text input before gameplay handlers while focused. Escape
        // closes chat without also opening the pause menu on the same frame.
        if self.runtime_chat.focused() && self.handle_runtime_chat_input() {
            return ClientRuntimeFlow::Continue;
        }

        if self.handle_world_map_input() {
            return ClientRuntimeFlow::Continue;
        }
        if self.update_station_placement_mode() {
            return ClientRuntimeFlow::Continue;
        }
        if self.update_station_interaction() {
            return ClientRuntimeFlow::Continue;
        }
        if self.player_inventory_ui.open {
            // The hotbar remains visible and interactive while Inventory is open.
            // Inventory updates selection/drag state first; the hotbar then captures
            // only a real press-drag-release shortcut gesture without moving the item.
            self.player_inventory_ui.handle_input(&self.controls);
            self.handle_inventory_hotbar_drag_drop();
            self.synchronize_inventory_equipment_with_profile();
            return ClientRuntimeFlow::Continue;
        }
        if self.controls.action_pressed(ControlAction::Inventory) {
            self.player_inventory_ui.toggle();
            return ClientRuntimeFlow::Continue;
        }
        // Enter opens the bottom-left runtime chat only from ordinary gameplay;
        // inventory/map/station surfaces above retain their own Confirm semantics.
        if self.handle_runtime_chat_input() {
            return ClientRuntimeFlow::Continue;
        }
        if !self.pause_menu_open && self.controls.action_pressed(ControlAction::Pause) {
            self.pause_menu_open = true;
            self.pause_menu_page = PauseMenuPage::Main;
            self.pause_menu_selection = 0;
            return ClientRuntimeFlow::Continue;
        }
        // Single-player pause is real simulation pause because no game-time,
        // world, NPC, stamina, or processing advancement occurs above this line.
        self.player_inventory_ui.update_station_processing(dt);
        advance_day_clock(&mut self.day_clock, dt);
        self.update_building_door_animations(dt);
        self.update_scene_door_animations(dt);
        self.handle_global_input();
        self.update_runtime_projectiles(dt);
        self.update_player(dt);
        let player_tile_x = (self.player.x / TILE_SIZE).floor() as i32;
        let player_tile_y = (self.player.y / TILE_SIZE).floor() as i32;
        let player_tile = self.world.active().map.get(player_tile_x, player_tile_y);
        self.water_ripples
            .update_player(self.player, self.player_is_moving(), player_tile, get_time());
        if !self.dev_mode {
            self.update_transitions();
        }
        self.update_customers(dt);
        self.update_camera(dt);
        if self.dev_mode && self.build_mode {
            if self.layout_edit_mode {
                self.update_layout_editor();
            } else {
                self.update_editor();
            }
        }
        let now = get_time();
        self.update_character_world_autosave(now);
        self.update_surface_chunk_jobs();
        // H21A14AB4/H21A14AC2R3N: semantic edit paths synchronize immediately; this is only
        // the original low-frequency A14AB4 safety poll. Keep it at 0.35 s so idle
        // traversal never restores the old 10 Hz terrain-cache rescan path.
        if self.terrain_cache.scene_id() != &self.world.active().id
            || now >= self.terrain_cache_next_sync_at
        {
            self.terrain_cache.synchronize(self.world.active());
            self.terrain_cache_next_sync_at = now + 0.35;
        }
        ClientRuntimeFlow::Continue
    }

    pub(super) fn update_pause_menu(&mut self) -> ClientRuntimeFlow {
        if self.controls.rebind_capture().is_some() || self.controls.rebind_input_consumed() {
            return ClientRuntimeFlow::Continue;
        }

        if self.controls.action_pressed(ControlAction::Pause)
            || self.controls.action_pressed(ControlAction::Cancel)
        {
            if self.pause_menu_page == PauseMenuPage::Main {
                self.pause_menu_open = false;
            } else {
                self.pause_menu_page = match self.pause_menu_page {
                    PauseMenuPage::Controls | PauseMenuPage::Controller => PauseMenuPage::Settings,
                    PauseMenuPage::Settings => PauseMenuPage::Main,
                    PauseMenuPage::Main => PauseMenuPage::Main,
                };
                self.pause_menu_selection = 0;
            }
            return ClientRuntimeFlow::Continue;
        }

        let count = self.pause_menu_item_count();
        let delta = self.controls.menu_vertical_delta();
        if delta != 0 && count > 0 {
            self.pause_menu_selection =
                (self.pause_menu_selection as i32 + delta).rem_euclid(count as i32) as usize;
        }
        if self.pause_menu_page == PauseMenuPage::Controller {
            let action_count = ControlAction::SETTINGS_ROWS.len();
            let horizontal = self.controls.menu_horizontal_delta();
            if horizontal != 0 && self.pause_menu_selection == action_count {
                self.controls.cycle_prompt_style(horizontal);
            }
            if horizontal != 0 && self.pause_menu_selection == action_count + 1 {
                self.controls.adjust_deadzone(horizontal as f32 * 0.02);
            }
        }

        let mouse = vec2(mouse_position().0, mouse_position().1);
        let clicked = is_mouse_button_pressed(MouseButton::Left);
        if clicked {
            if let Some(index) = self.pause_menu_hit_test(mouse) {
                self.pause_menu_selection = index;
                return self.activate_pause_menu_selection();
            }
        }

        if self.controls.action_pressed(ControlAction::Confirm) {
            return self.activate_pause_menu_selection();
        }
        ClientRuntimeFlow::Continue
    }

    fn pause_menu_item_count(&self) -> usize {
        match self.pause_menu_page {
            PauseMenuPage::Main => 5,
            PauseMenuPage::Settings => 8,
            PauseMenuPage::Controls => ControlAction::SETTINGS_ROWS.len() + 2,
            PauseMenuPage::Controller => ControlAction::SETTINGS_ROWS.len() + 4,
        }
    }

    fn pause_menu_hit_test(&self, point: Vec2) -> Option<usize> {
        match self.pause_menu_page {
            PauseMenuPage::Main => (0..5).find(|index| pause_main_button_rect(*index).contains(point)),
            PauseMenuPage::Settings => {
                (0..8).find(|index| pause_settings_button_rect(*index).contains(point))
            }
            PauseMenuPage::Controls | PauseMenuPage::Controller => {
                let start = bindings_window_start(self.pause_menu_selection);
                let visible = visible_binding_count();
                for visible_index in 0..visible {
                    let action_index = start + visible_index;
                    if action_index < ControlAction::SETTINGS_ROWS.len()
                        && pause_binding_row_rect(visible_index, self.pause_menu_page == PauseMenuPage::Controller).contains(point)
                    {
                        return Some(action_index);
                    }
                }
                let footer_index = ControlAction::SETTINGS_ROWS.len();
                let controller = self.pause_menu_page == PauseMenuPage::Controller;
                let footer_count = if controller { 4 } else { 2 };
                for index in 0..footer_count {
                    if pause_binding_footer_rect(index, controller).contains(point) {
                        return Some(footer_index + index);
                    }
                }
                None
            }
        }
    }

    fn activate_pause_menu_selection(&mut self) -> ClientRuntimeFlow {
        match self.pause_menu_page {
            PauseMenuPage::Main => match self.pause_menu_selection {
                0 => self.pause_menu_open = false,
                1 => {
                    self.save_map();
                    self.status_message = format!("Saved {}", self.world_id.0);
                }
                2 => {
                    self.pause_menu_page = PauseMenuPage::Settings;
                    self.pause_menu_selection = 0;
                }
                3 => {
                    self.save_map();
                    return ClientRuntimeFlow::ReturnToMainMenu;
                }
                4 => {
                    self.save_map();
                    return ClientRuntimeFlow::QuitDesktop;
                }
                _ => {}
            },
            PauseMenuPage::Settings => match self.pause_menu_selection {
                0 => self.status_message = "Gameplay settings panel is staged for the next settings pass".to_string(),
                1 => {
                    self.pause_menu_page = PauseMenuPage::Controls;
                    self.pause_menu_selection = 0;
                }
                2 => {
                    self.pause_menu_page = PauseMenuPage::Controller;
                    self.pause_menu_selection = 0;
                }
                3 => self.status_message = "Audio settings panel is staged".to_string(),
                4 => self.status_message = "Video/display settings panel is staged".to_string(),
                5 => self.status_message = "Interface settings panel is staged".to_string(),
                6 => self.status_message = "Accessibility settings panel is staged".to_string(),
                7 => {
                    self.pause_menu_page = PauseMenuPage::Main;
                    self.pause_menu_selection = 0;
                }
                _ => {}
            },
            PauseMenuPage::Controls => {
                let action_count = ControlAction::SETTINGS_ROWS.len();
                if self.pause_menu_selection < action_count {
                    let action = ControlAction::SETTINGS_ROWS[self.pause_menu_selection];
                    self.controls.begin_rebind(action, RebindDevice::KeyboardMouse);
                } else if self.pause_menu_selection == action_count {
                    self.controls.reset_defaults();
                    self.status_message = "Keyboard/mouse and controller bindings reset to defaults".to_string();
                } else {
                    self.pause_menu_page = PauseMenuPage::Settings;
                    self.pause_menu_selection = 0;
                }
            }
            PauseMenuPage::Controller => {
                let action_count = ControlAction::SETTINGS_ROWS.len();
                if self.pause_menu_selection < action_count {
                    let action = ControlAction::SETTINGS_ROWS[self.pause_menu_selection];
                    self.controls.begin_rebind(action, RebindDevice::Controller);
                } else if self.pause_menu_selection == action_count {
                    self.controls.cycle_prompt_style(1);
                } else if self.pause_menu_selection == action_count + 1 {
                    self.controls.adjust_deadzone(0.02);
                } else if self.pause_menu_selection == action_count + 2 {
                    self.controls.reset_defaults();
                    self.status_message = "Keyboard/mouse and controller bindings reset to defaults".to_string();
                } else {
                    self.pause_menu_page = PauseMenuPage::Settings;
                    self.pause_menu_selection = 0;
                }
            }
        }
        ClientRuntimeFlow::Continue
    }

    pub(super) fn draw_pause_menu(&self) {
        draw_rectangle(
            0.0,
            0.0,
            screen_width(),
            screen_height(),
            Color::new(0.0, 0.0, 0.0, 0.72),
        );
        match self.pause_menu_page {
            PauseMenuPage::Main => self.draw_pause_main(),
            PauseMenuPage::Settings => self.draw_pause_settings(),
            PauseMenuPage::Controls => self.draw_pause_controls(false),
            PauseMenuPage::Controller => self.draw_pause_controls(true),
        }
        if self.controls.rebind_capture().is_some() {
            draw_rebind_overlay(self.controls.capture_message());
        }
    }

    fn draw_pause_main(&self) {
        let panel = pause_panel_rect(460.0, 500.0);
        draw_pause_panel(panel, "HAVENWILD", &format!("{}  |  Seed {}", self.world_id.0, self.world_seed));
        let labels = ["Resume", "Save Game", "Settings", "Save & Main Menu", "Save & Quit Desktop"];
        for (index, label) in labels.iter().enumerate() {
            draw_pause_button(
                pause_main_button_rect(index),
                label,
                self.pause_menu_selection == index,
                index == 0,
            );
        }
        draw_centered(
            &format!("{} resumes  |  controller and keyboard/mouse remain active together", self.controls.prompt_label(ControlAction::Pause)),
            panel.x + panel.w * 0.5,
            panel.y + panel.h - 22.0,
            13.0,
            Color::from_rgba(125, 149, 153, 255),
        );
    }

    fn draw_pause_settings(&self) {
        let panel = pause_panel_rect(520.0, 590.0);
        draw_pause_panel(panel, "SETTINGS", "Changes are stored locally in the Havenwild project workspace");
        let labels = [
            "Gameplay",
            "Controls",
            "Controller",
            "Audio",
            "Video / Display",
            "Interface",
            "Accessibility",
            "Back",
        ];
        for (index, label) in labels.iter().enumerate() {
            draw_pause_button(
                pause_settings_button_rect(index),
                label,
                self.pause_menu_selection == index,
                index == 1 || index == 2,
            );
        }
    }

    fn draw_pause_controls(&self, controller: bool) {
        let panel = pause_panel_rect(if controller { 940.0 } else { 760.0 }, 650.0);
        let subtitle = if controller {
            if self.controls.controller_connected() {
                "Controller connected - keyboard and mouse remain active"
            } else {
                "No XInput controller detected - keyboard and mouse remain active"
            }
        } else {
            "Select an action to rebind its primary keyboard/mouse control"
        };
        draw_pause_panel(panel, if controller { "CONTROLLER" } else { "CONTROLS" }, subtitle);

        let start = bindings_window_start(self.pause_menu_selection);
        let visible = visible_binding_count();
        for visible_index in 0..visible {
            let action_index = start + visible_index;
            if action_index >= ControlAction::SETTINGS_ROWS.len() {
                continue;
            }
            let action = ControlAction::SETTINGS_ROWS[action_index];
            let rect = pause_binding_row_rect(visible_index, controller);
            let selected = self.pause_menu_selection == action_index;
            let binding_label = if controller {
                self.controls.controller_binding_label(action)
            } else {
                self.controls.keyboard_binding_label(action)
            };
            draw_binding_row(rect, action.label(), &binding_label, selected);
        }

        let action_count = ControlAction::SETTINGS_ROWS.len();
        let footer_label = if controller {
            format!("Prompt: {}", self.controls.settings.prompt_style.label())
        } else {
            "Reset All Bindings".to_string()
        };
        draw_pause_button(
            pause_binding_footer_rect(0, controller),
            &footer_label,
            self.pause_menu_selection == action_count,
            false,
        );
        if controller {
            draw_pause_button(
                pause_binding_footer_rect(1, true),
                &format!("Deadzone: {:.0}%", self.controls.settings.controller_deadzone * 100.0),
                self.pause_menu_selection == action_count + 1,
                false,
            );
            draw_pause_button(
                pause_binding_footer_rect(2, true),
                "Reset All",
                self.pause_menu_selection == action_count + 2,
                false,
            );
            draw_pause_button(
                pause_binding_footer_rect(3, true),
                "Back",
                self.pause_menu_selection == action_count + 3,
                false,
            );
        } else {
            draw_pause_button(
                pause_binding_footer_rect(1, false),
                "Back",
                self.pause_menu_selection == action_count + 1,
                false,
            );
        }

        if controller {
            draw_controller_diagram(panel, &self.controls, self.pause_menu_selection);
        }
    }
}

fn bindings_window_start(selection: usize) -> usize {
    let count = ControlAction::SETTINGS_ROWS.len();
    let visible = visible_binding_count();
    if selection >= count || selection < visible {
        0
    } else {
        (selection + 1 - visible).min(count.saturating_sub(visible))
    }
}

fn visible_binding_count() -> usize {
    10
}

fn pause_panel_rect(width: f32, height: f32) -> Rect {
    Rect::new(
        (screen_width() - width).max(20.0) * 0.5,
        (screen_height() - height).max(20.0) * 0.5,
        width.min(screen_width() - 40.0),
        height.min(screen_height() - 40.0),
    )
}

fn pause_main_button_rect(index: usize) -> Rect {
    let panel = pause_panel_rect(460.0, 500.0);
    Rect::new(panel.x + 58.0, panel.y + 126.0 + index as f32 * 60.0, panel.w - 116.0, 46.0)
}

fn pause_settings_button_rect(index: usize) -> Rect {
    let panel = pause_panel_rect(520.0, 590.0);
    Rect::new(panel.x + 62.0, panel.y + 116.0 + index as f32 * 54.0, panel.w - 124.0, 42.0)
}

fn pause_binding_row_rect(index: usize, controller: bool) -> Rect {
    let panel = if controller { pause_panel_rect(940.0, 650.0) } else { pause_panel_rect(760.0, 650.0) };
    let width = if controller && panel.w >= 900.0 { panel.w - 390.0 } else { panel.w - 80.0 };
    Rect::new(panel.x + 36.0, panel.y + 112.0 + index as f32 * 42.0, width, 34.0)
}

fn pause_binding_footer_rect(index: usize, controller: bool) -> Rect {
    let panel = if controller { pause_panel_rect(940.0, 650.0) } else { pause_panel_rect(760.0, 650.0) };
    let (step, width) = if controller { (142.0, 132.0) } else { (210.0, 194.0) };
    Rect::new(panel.x + 36.0 + index as f32 * step, panel.y + panel.h - 66.0, width, 38.0)
}

fn draw_pause_panel(panel: Rect, title: &str, subtitle: &str) {
    // Pause, controls, world map, inventory/crafting and other player-facing
    // windows share the canonical runtime theme instead of private panel chrome.
    draw_rectangle(0.0, 0.0, screen_width(), screen_height(), ui_backdrop());
    draw_runtime_panel(panel, title, Some(subtitle));
}

fn draw_pause_button(rect: Rect, label: &str, selected: bool, primary: bool) {
    let mouse = vec2(mouse_position().0, mouse_position().1);
    let hovered = rect.contains(mouse);
    let color = if selected || hovered {
        if primary { Color::from_rgba(83, 137, 105, 255) } else { Color::from_rgba(65, 91, 91, 255) }
    } else if primary {
        Color::from_rgba(61, 109, 82, 255)
    } else {
        Color::from_rgba(43, 58, 64, 255)
    };
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, color);
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, if selected { 2.0 } else { 1.0 }, if selected { ui_teal() } else { ui_muted() });
    draw_centered(label, rect.x + rect.w * 0.5, rect.y + rect.h * 0.66, 17.0, Color::from_rgba(234, 238, 229, 255));
}

fn draw_binding_row(rect: Rect, action: &str, binding: &str, selected: bool) {
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, if selected { Color::from_rgba(57, 79, 79, 255) } else { Color::from_rgba(34, 46, 51, 255) });
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, if selected { 2.0 } else { 1.0 }, if selected { ui_teal() } else { ui_muted() });
    draw_text(action, rect.x + 10.0, rect.y + 23.0, 15.0, Color::from_rgba(232, 235, 226, 255));
    let width = measure_text(binding, None, 15, 1.0).width;
    draw_text(binding, rect.x + rect.w - width - 10.0, rect.y + 23.0, 15.0, Color::from_rgba(190, 211, 200, 255));
}

fn draw_controller_diagram(panel: Rect, controls: &ControlRuntime, selected_index: usize) {
    if panel.w < 900.0 {
        return;
    }
    let area = Rect::new(panel.x + panel.w - 340.0, panel.y + 122.0, 300.0, 398.0);
    draw_rectangle(area.x, area.y, area.w, area.h, Color::from_rgba(27, 38, 43, 255));
    draw_rectangle_lines(area.x, area.y, area.w, area.h, 1.0, ui_muted());
    draw_centered("CURRENT CONTROLLER MAP", area.x + area.w * 0.5, area.y + 27.0, 15.0, Color::from_rgba(239, 226, 182, 255));

    let selected_action = ControlAction::SETTINGS_ROWS.get(selected_index).copied();
    let nodes = [
        (ControllerBinding::LeftTrigger, 48.0, 68.0),
        (ControllerBinding::RightTrigger, 214.0, 68.0),
        (ControllerBinding::LeftShoulder, 48.0, 118.0),
        (ControllerBinding::RightShoulder, 214.0, 118.0),
        (ControllerBinding::DpadUp, 64.0, 184.0),
        (ControllerBinding::DpadLeft, 34.0, 216.0),
        (ControllerBinding::DpadRight, 94.0, 216.0),
        (ControllerBinding::DpadDown, 64.0, 248.0),
        (ControllerBinding::North, 226.0, 174.0),
        (ControllerBinding::West, 196.0, 208.0),
        (ControllerBinding::East, 256.0, 208.0),
        (ControllerBinding::South, 226.0, 242.0),
        (ControllerBinding::Back, 100.0, 328.0),
        (ControllerBinding::Start, 198.0, 328.0),
        (ControllerBinding::RightThumb, 154.0, 296.0),
    ];
    for (binding, x, y) in nodes {
        let selected = selected_action
            .is_some_and(|action| controls.action_uses_controller_binding(action, binding));
        draw_controller_node(
            area.x + x,
            area.y + y,
            binding.short_label(),
            &controls.controller_actions_label(binding),
            selected,
        );
    }

    let left_stick_selected = selected_action.is_some_and(|action| {
        matches!(
            action,
            ControlAction::MoveUp
                | ControlAction::MoveDown
                | ControlAction::MoveLeft
                | ControlAction::MoveRight
        ) || controls.action_uses_controller_binding(action, ControllerBinding::LeftThumb)
    });
    let left_stick_click = controls.controller_actions_label(ControllerBinding::LeftThumb);
    let left_stick_label = if left_stick_click == "Unbound" {
        "Move (analog)".to_string()
    } else {
        format!("Move / {} click", left_stick_click)
    };
    draw_controller_node(
        area.x + 126.0,
        area.y + 260.0,
        "LS",
        &left_stick_label,
        left_stick_selected,
    );

    draw_centered(
        "All mappings shown live; keyboard/mouse stay enabled",
        area.x + area.w * 0.5,
        area.y + area.h - 14.0,
        10.5,
        Color::from_rgba(142, 165, 164, 255),
    );
}

fn draw_controller_node(x: f32, y: f32, button: &str, label: &str, selected: bool) {
    let rect = Rect::new(x - 27.0, y - 14.0, 54.0, 28.0);
    let fill = if selected {
        Color::from_rgba(72, 89, 75, 255)
    } else {
        Color::from_rgba(48, 66, 70, 255)
    };
    let outline = if selected { ui_teal() } else { ui_muted() };
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, fill);
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, if selected { 2.0 } else { 1.0 }, outline);
    draw_centered(button, x, y + 5.0, 12.5, Color::from_rgba(239, 226, 182, 255));
    let short = label.chars().take(22).collect::<String>();
    draw_centered(&short, x, y + 25.0, 9.5, Color::from_rgba(162, 184, 180, 255));
}

fn draw_rebind_overlay(message: &str) {
    let rect = Rect::new(screen_width() * 0.5 - 260.0, screen_height() * 0.5 - 64.0, 520.0, 128.0);
    draw_runtime_panel(rect, "REBIND CONTROL", Some(message));
    draw_centered(
        "Esc cancels keyboard capture",
        rect.x + rect.w * 0.5,
        rect.y + 101.0,
        12.0,
        ui_muted(),
    );
}

fn draw_centered(text: &str, center_x: f32, baseline_y: f32, size: f32, color: Color) {
    let dimensions = measure_text(text, None, size as u16, 1.0);
    draw_text(text, center_x - dimensions.width * 0.5, baseline_y, size, color);
}
