use haven_world::WorldCreationSettings;
use macroquad::prelude::*;

use crate::client_character_frontend_draw::{
    draw_button, draw_panel, draw_text_centered, draw_title, mouse_vec,
};

const PAGE_COUNT: usize = 8;
const PAGE_TITLES: [&str; PAGE_COUNT] = [
    "Identity",
    "Challenge",
    "Land",
    "Water",
    "Biomes",
    "Settlements",
    "Relationships & Family",
    "Review",
];

#[derive(Clone, Debug)]
pub(crate) enum WorldCreationWizardAction {
    None,
    Cancel,
    Invalid(String),
    Create(WorldCreationSettings),
}

#[derive(Clone, Debug)]
pub(crate) struct WorldCreationWizard {
    pub settings: WorldCreationSettings,
    page: usize,
    selected_row: usize,
    name_focused: bool,
}

impl WorldCreationWizard {
    pub(crate) fn new(seed: u64, display_name: impl Into<String>) -> Self {
        let settings = WorldCreationSettings {
            seed: seed.max(1),
            display_name: display_name.into(),
            ..Default::default()
        };
        Self {
            settings,
            page: 0,
            selected_row: 0,
            name_focused: true,
        }
    }

    pub(crate) fn update(&mut self) -> WorldCreationWizardAction {
        if self.page == 0 && self.name_focused {
            while let Some(character) = get_char_pressed() {
                if !character.is_control() && self.settings.display_name.chars().count() < 40 {
                    self.settings.display_name.push(character);
                }
            }
            if is_key_pressed(KeyCode::Backspace) {
                self.settings.display_name.pop();
            }
        }

        if is_key_pressed(KeyCode::R) && self.page == 0 {
            self.reroll_seed();
        }
        if is_key_pressed(KeyCode::Up) {
            self.selected_row = self.selected_row.saturating_sub(1);
        }
        if is_key_pressed(KeyCode::Down) {
            self.selected_row = (self.selected_row + 1).min(self.field_count().saturating_sub(1));
        }
        if is_key_pressed(KeyCode::Left) {
            self.adjust_selected(-1);
        }
        if is_key_pressed(KeyCode::Right) {
            self.adjust_selected(1);
        }

        if is_key_pressed(KeyCode::PageUp) && self.page > 0 {
            self.page -= 1;
            self.selected_row = 0;
            self.name_focused = self.page == 0;
        }
        if is_key_pressed(KeyCode::PageDown) && self.page + 1 < PAGE_COUNT {
            self.page += 1;
            self.selected_row = 0;
            self.name_focused = false;
        }

        if is_mouse_button_pressed(MouseButton::Left) {
            let mouse = mouse_vec();
            if back_rect().contains(mouse) {
                return WorldCreationWizardAction::Cancel;
            }
            if previous_rect().contains(mouse) && self.page > 0 {
                self.page -= 1;
                self.selected_row = 0;
                self.name_focused = self.page == 0;
                return WorldCreationWizardAction::None;
            }
            if next_rect().contains(mouse) {
                if self.page + 1 < PAGE_COUNT {
                    self.page += 1;
                    self.selected_row = 0;
                    self.name_focused = false;
                    return WorldCreationWizardAction::None;
                }
                return self.create_action();
            }
            if self.page == 0 && name_rect().contains(mouse) {
                self.name_focused = true;
                self.selected_row = 0;
                return WorldCreationWizardAction::None;
            }
            self.name_focused = false;
            for row in 0..self.field_count() {
                let (left, body, right) = field_rects(row);
                if left.contains(mouse) {
                    self.selected_row = row;
                    self.adjust_selected(-1);
                    return WorldCreationWizardAction::None;
                }
                if right.contains(mouse) || body.contains(mouse) {
                    self.selected_row = row;
                    self.adjust_selected(1);
                    return WorldCreationWizardAction::None;
                }
            }
        }

        if is_key_pressed(KeyCode::Enter) && self.page + 1 == PAGE_COUNT {
            return self.create_action();
        }

        WorldCreationWizardAction::None
    }

    pub(crate) fn draw(&self) {
        draw_title("CREATE WORLD");
        draw_text_centered(
            &format!(
                "Step {} of {} • {}",
                self.page + 1,
                PAGE_COUNT,
                PAGE_TITLES[self.page]
            ),
            screen_width() * 0.5,
            112.0,
            20.0,
            WHITE,
        );
        draw_page_tabs(self.page);
        let panel = content_rect();
        draw_panel(panel, true);

        if self.page + 1 == PAGE_COUNT {
            self.draw_review(panel);
        } else {
            for row in 0..self.field_count() {
                let (label, value) = self.field_label_value(row);
                let (left, body, right) = field_rects(row);
                let active = row == self.selected_row;
                draw_text(
                    label,
                    body.x + 8.0,
                    body.y + 24.0,
                    18.0,
                    if active { WHITE } else { LIGHTGRAY },
                );
                draw_text_centered(&value, body.x + body.w * 0.69, body.y + 25.0, 18.0, WHITE);
                draw_button(left, "<", false);
                draw_button(right, ">", false);
            }
            if self.page == 0 {
                draw_text(
                    "Type a world name. Press R to reroll the seed.",
                    panel.x + 28.0,
                    panel.y + panel.h - 34.0,
                    16.0,
                    LIGHTGRAY,
                );
            } else {
                draw_text(
                    "Arrow keys adjust the selected option. Page Up/Down changes pages.",
                    panel.x + 28.0,
                    panel.y + panel.h - 34.0,
                    16.0,
                    LIGHTGRAY,
                );
            }
        }

        draw_button(back_rect(), "CANCEL", false);
        draw_button(previous_rect(), "PREVIOUS", false);
        draw_button(
            next_rect(),
            if self.page + 1 == PAGE_COUNT {
                "GENERATE WORLD"
            } else {
                "NEXT"
            },
            true,
        );
    }

    fn draw_review(&self, panel: Rect) {
        let [width, height] = self.settings.world_dimensions_tiles();
        let world_line = if self.settings.is_endless() {
            format!(
                "World: Endless • {}-tile geographic regions • {} finite preview",
                haven_world::GEOGRAPHIC_REGION_SIZE_TILES,
                self.settings.size.label()
            )
        } else {
            format!(
                "World: {} • {} × {} tiles",
                self.settings.size.label(),
                width,
                height
            )
        };
        let lines = [
            format!("Name: {}", self.settings.display_name),
            format!("Seed: {}", self.settings.seed),
            format!("Difficulty: {}", self.settings.difficulty.label()),
            world_line,
            format!(
                "Landform: {} • {}% land",
                self.settings.landform.label(),
                self.settings.land.land_coverage_percent
            ),
            format!(
                "Water: rivers {}, lakes {}, wetlands {} • waterfall drops required",
                self.settings.hydrology.river_density.label(),
                self.settings.hydrology.lake_density.label(),
                self.settings.hydrology.wetland_density.label(),
            ),
            format!(
                "Biomes: {} • forests {}",
                self.settings.biomes.variety.label(),
                self.settings.biomes.forest_density.label(),
            ),
            format!(
                "Settlements: Willowmere + {} cities • {}–{} villages per city",
                self.settings.settlements.secondary_city_count,
                self.settings.settlements.villages_per_city_min,
                self.settings.settlements.villages_per_city_max,
            ),
            format!(
                "Housing: {} city listings • {} village listing normally",
                self.settings.settlements.housing.city_available_homes_target,
                self.settings.settlements.housing.village_available_homes_target,
            ),
            format!(
                "Families: player marriage {} • NPC marriage {} • children {}",
                enabled(self.settings.social.player_player_marriage_enabled),
                enabled(self.settings.social.player_npc_marriage_enabled),
                enabled(self.settings.social.children_enabled),
            ),
            "Willowmere is permanent. No mandatory static farmstead is generated.".to_string(),
        ];
        let mut y = panel.y + 34.0;
        for line in lines {
            draw_text(&line, panel.x + 30.0, y, 17.0, WHITE);
            y += 29.0;
        }
        draw_text(
            "Generation settings are saved with the world and remain available to Host World Builder.",
            panel.x + 30.0,
            panel.y + panel.h - 30.0,
            14.0,
            LIGHTGRAY,
        );
    }

    fn create_action(&self) -> WorldCreationWizardAction {
        match self.settings.validate() {
            Ok(()) => WorldCreationWizardAction::Create(self.settings.clone()),
            Err(error) => WorldCreationWizardAction::Invalid(error),
        }
    }

    fn reroll_seed(&mut self) {
        let entropy = get_time().to_bits() ^ self.settings.seed.rotate_left(17);
        self.settings.seed = splitmix64(entropy).max(1);
    }

    fn field_count(&self) -> usize {
        match self.page {
            0 => 3,
            1 => 7,
            2 => 6,
            3 => 7,
            4 => 3,
            5 => 8,
            6 => 7,
            _ => 0,
        }
    }

    fn field_label_value(&self, row: usize) -> (&'static str, String) {
        match (self.page, row) {
            (0, 0) => ("World name", self.settings.display_name.clone()),
            (0, 1) => ("Seed", self.settings.seed.to_string()),
            (0, 2) => ("World extent", self.settings.extent_mode.label().to_string()),

            (1, 0) => ("Difficulty preset", self.settings.difficulty.label().to_string()),
            (1, 1) => ("Resource abundance", format!("{}%", self.settings.difficulty_tuning.resource_abundance_percent)),
            (1, 2) => ("Survival pressure", format!("{}%", self.settings.difficulty_tuning.survival_pressure_percent)),
            (1, 3) => ("Hostile pressure", format!("{}%", self.settings.difficulty_tuning.hostile_pressure_percent)),
            (1, 4) => ("Weather severity", format!("{}%", self.settings.difficulty_tuning.weather_severity_percent)),
            (1, 5) => ("Economy pressure", format!("{}%", self.settings.difficulty_tuning.economy_pressure_percent)),
            (1, 6) => ("Recovery penalty", format!("{}%", self.settings.difficulty_tuning.recovery_penalty_percent)),

            (2, 0) => ("Finite size / preview", self.settings.size.label().to_string()),
            (2, 1) => ("Landform", self.settings.landform.label().to_string()),
            (2, 2) => ("Land coverage", format!("{}%", self.settings.land.land_coverage_percent)),
            (2, 3) => ("Coastline complexity", self.settings.land.coastline_complexity.label().to_string()),
            (2, 4) => ("Mountain coverage", self.settings.land.mountain_coverage.label().to_string()),
            (2, 5) => ("Island frequency", self.settings.land.island_frequency.label().to_string()),

            (3, 0) => ("Marine water", self.settings.hydrology.marine_water_abundance.label().to_string()),
            (3, 1) => ("Rivers", self.settings.hydrology.river_density.label().to_string()),
            (3, 2) => ("Lakes", self.settings.hydrology.lake_density.label().to_string()),
            (3, 3) => ("Ponds", self.settings.hydrology.pond_density.label().to_string()),
            (3, 4) => ("Wetlands", self.settings.hydrology.wetland_density.label().to_string()),
            (3, 5) => ("Waterfall sources", self.settings.hydrology.waterfall_density.label().to_string()),
            (3, 6) => ("Estuaries", enabled(self.settings.hydrology.estuaries_enabled).to_string()),

            (4, 0) => ("Biome variety", self.settings.biomes.variety.label().to_string()),
            (4, 1) => ("Forest density", self.settings.biomes.forest_density.label().to_string()),
            (4, 2) => ("Special biomes", self.settings.biomes.special_biome_frequency.label().to_string()),

            (5, 0) => ("Secondary cities", self.settings.settlements.secondary_city_count.to_string()),
            (5, 1) => ("Max villages per city", self.settings.settlements.villages_per_city_max.to_string()),
            (5, 2) => ("Independent villages", self.settings.settlements.independent_village_count.to_string()),
            (5, 3) => ("Road density", self.settings.settlements.road_density.label().to_string()),
            (5, 4) => ("Willowmere setting", self.settings.settlements.willowmere_location.label().to_string()),
            (5, 5) => ("City housing choices", self.settings.settlements.housing.city_available_homes_target.to_string()),
            (5, 6) => ("Village housing choices", self.settings.settlements.housing.village_available_homes_target.to_string()),
            (5, 7) => ("Lease to own", enabled(self.settings.settlements.housing.lease_to_own_enabled).to_string()),

            (6, 0) => ("NPC reputation", enabled(self.settings.social.npc_reputation_enabled).to_string()),
            (6, 1) => ("NPC relationships", enabled(self.settings.social.npc_relationships_enabled).to_string()),
            (6, 2) => ("Player partnerships", enabled(self.settings.social.player_player_partnership_enabled).to_string()),
            (6, 3) => ("Player marriage", enabled(self.settings.social.player_player_marriage_enabled).to_string()),
            (6, 4) => ("NPC marriage", enabled(self.settings.social.player_npc_marriage_enabled).to_string()),
            (6, 5) => ("Children and adoption", enabled(self.settings.social.children_enabled).to_string()),
            (6, 6) => ("Pregnancy body visuals", enabled(self.settings.social.pregnancy_visual_layers_enabled).to_string()),
            _ => ("", String::new()),
        }
    }

    fn adjust_selected(&mut self, delta: i32) {
        match (self.page, self.selected_row) {
            (0, 0) => self.name_focused = true,
            (0, 1) => {
                self.settings.seed = if delta < 0 {
                    self.settings.seed.saturating_sub(1).max(1)
                } else {
                    self.settings.seed.saturating_add(1).max(1)
                };
            }
            (0, 2) => self.settings.extent_mode = self.settings.extent_mode.cycle(delta),

            (1, 0) => {
                let preset = self.settings.difficulty.cycle(delta);
                self.settings.set_difficulty_preset(preset);
            }
            (1, 1) => adjust_difficulty_percent(
                &mut self.settings.difficulty,
                &mut self.settings.difficulty_tuning.resource_abundance_percent,
                delta,
            ),
            (1, 2) => adjust_difficulty_percent(
                &mut self.settings.difficulty,
                &mut self.settings.difficulty_tuning.survival_pressure_percent,
                delta,
            ),
            (1, 3) => adjust_difficulty_percent(
                &mut self.settings.difficulty,
                &mut self.settings.difficulty_tuning.hostile_pressure_percent,
                delta,
            ),
            (1, 4) => adjust_difficulty_percent(
                &mut self.settings.difficulty,
                &mut self.settings.difficulty_tuning.weather_severity_percent,
                delta,
            ),
            (1, 5) => adjust_difficulty_percent(
                &mut self.settings.difficulty,
                &mut self.settings.difficulty_tuning.economy_pressure_percent,
                delta,
            ),
            (1, 6) => adjust_difficulty_percent(
                &mut self.settings.difficulty,
                &mut self.settings.difficulty_tuning.recovery_penalty_percent,
                delta,
            ),

            (2, 0) => self.settings.size = self.settings.size.cycle(delta),
            (2, 1) => self.settings.landform = self.settings.landform.cycle(delta),
            (2, 2) => {
                let next = i32::from(self.settings.land.land_coverage_percent) + delta * 5;
                self.settings.land.land_coverage_percent = next.clamp(45, 80) as u8;
            }
            (2, 3) => self.settings.land.coastline_complexity = self.settings.land.coastline_complexity.cycle(delta),
            (2, 4) => self.settings.land.mountain_coverage = self.settings.land.mountain_coverage.cycle(delta),
            (2, 5) => self.settings.land.island_frequency = self.settings.land.island_frequency.cycle(delta),

            (3, 0) => self.settings.hydrology.marine_water_abundance = self.settings.hydrology.marine_water_abundance.cycle(delta),
            (3, 1) => self.settings.hydrology.river_density = self.settings.hydrology.river_density.cycle(delta),
            (3, 2) => self.settings.hydrology.lake_density = self.settings.hydrology.lake_density.cycle(delta),
            (3, 3) => self.settings.hydrology.pond_density = self.settings.hydrology.pond_density.cycle(delta),
            (3, 4) => self.settings.hydrology.wetland_density = self.settings.hydrology.wetland_density.cycle(delta),
            (3, 5) => self.settings.hydrology.waterfall_density = self.settings.hydrology.waterfall_density.cycle(delta),
            (3, 6) => self.settings.hydrology.estuaries_enabled = !self.settings.hydrology.estuaries_enabled,

            (4, 0) => self.settings.biomes.variety = self.settings.biomes.variety.cycle(delta),
            (4, 1) => self.settings.biomes.forest_density = self.settings.biomes.forest_density.cycle(delta),
            (4, 2) => self.settings.biomes.special_biome_frequency = self.settings.biomes.special_biome_frequency.cycle(delta),

            (5, 0) => self.settings.settlements.secondary_city_count = cycle_u8(self.settings.settlements.secondary_city_count, delta, 0, 4),
            (5, 1) => self.settings.settlements.villages_per_city_max = cycle_u8(self.settings.settlements.villages_per_city_max, delta, 1, 5),
            (5, 2) => self.settings.settlements.independent_village_count = cycle_u8(self.settings.settlements.independent_village_count, delta, 0, 4),
            (5, 3) => self.settings.settlements.road_density = self.settings.settlements.road_density.cycle(delta),
            (5, 4) => self.settings.settlements.willowmere_location = self.settings.settlements.willowmere_location.cycle(delta),
            (5, 5) => self.settings.settlements.housing.city_available_homes_target = cycle_u8(self.settings.settlements.housing.city_available_homes_target, delta, 2, 8),
            (5, 6) => self.settings.settlements.housing.village_available_homes_target = cycle_u8(self.settings.settlements.housing.village_available_homes_target, delta, 1, 2),
            (5, 7) => self.settings.settlements.housing.lease_to_own_enabled = !self.settings.settlements.housing.lease_to_own_enabled,

            (6, 0) => self.settings.social.npc_reputation_enabled = !self.settings.social.npc_reputation_enabled,
            (6, 1) => self.settings.social.npc_relationships_enabled = !self.settings.social.npc_relationships_enabled,
            (6, 2) => self.settings.social.player_player_partnership_enabled = !self.settings.social.player_player_partnership_enabled,
            (6, 3) => self.settings.social.player_player_marriage_enabled = !self.settings.social.player_player_marriage_enabled,
            (6, 4) => self.settings.social.player_npc_marriage_enabled = !self.settings.social.player_npc_marriage_enabled,
            (6, 5) => {
                self.settings.social.children_enabled = !self.settings.social.children_enabled;
                self.settings.social.adoption_enabled = self.settings.social.children_enabled;
            }
            (6, 6) => {
                self.settings.social.pregnancy_visual_layers_enabled = !self.settings.social.pregnancy_visual_layers_enabled;
                self.settings.social.pregnancy_enabled = self.settings.social.pregnancy_visual_layers_enabled;
            }
            _ => {}
        }
    }
}

fn content_rect() -> Rect {
    Rect::new(
        (screen_width() - 820.0) * 0.5,
        160.0,
        820.0,
        (screen_height() - 265.0).max(420.0),
    )
}

fn field_rects(row: usize) -> (Rect, Rect, Rect) {
    let panel = content_rect();
    let y = panel.y + 28.0 + row as f32 * 52.0;
    let left = Rect::new(panel.x + 22.0, y, 42.0, 36.0);
    let body = Rect::new(panel.x + 72.0, y, panel.w - 144.0, 36.0);
    let right = Rect::new(panel.x + panel.w - 64.0, y, 42.0, 36.0);
    (left, body, right)
}

fn name_rect() -> Rect {
    field_rects(0).1
}
fn back_rect() -> Rect {
    Rect::new(32.0, screen_height() - 72.0, 150.0, 42.0)
}
fn previous_rect() -> Rect {
    Rect::new(
        screen_width() * 0.5 - 165.0,
        screen_height() - 72.0,
        150.0,
        42.0,
    )
}
fn next_rect() -> Rect {
    Rect::new(
        screen_width() * 0.5 + 15.0,
        screen_height() - 72.0,
        220.0,
        42.0,
    )
}

fn draw_page_tabs(active: usize) {
    let total_width = 820.0;
    let tab_width = total_width / PAGE_COUNT as f32;
    let start_x = (screen_width() - total_width) * 0.5;
    for (index, label) in PAGE_TITLES.iter().enumerate() {
        let x = start_x + index as f32 * tab_width;
        draw_rectangle(
            x,
            126.0,
            tab_width - 3.0,
            25.0,
            if index == active {
                Color::from_rgba(65, 91, 99, 255)
            } else {
                Color::from_rgba(31, 40, 45, 255)
            },
        );
        draw_text_centered(label, x + (tab_width - 3.0) * 0.5, 144.0, 12.0, WHITE);
    }
}

fn enabled(value: bool) -> &'static str {
    if value {
        "Enabled"
    } else {
        "Disabled"
    }
}

fn adjust_difficulty_percent(
    preset: &mut haven_world::WorldDifficultyPreset,
    value: &mut u8,
    delta: i32,
) {
    *preset = haven_world::WorldDifficultyPreset::Custom;
    *value = (i32::from(*value) + delta * 5).clamp(0, 100) as u8;
}

fn cycle_u8(value: u8, delta: i32, min: u8, max: u8) -> u8 {
    let count = i32::from(max - min + 1);
    (i32::from(value - min) + delta).rem_euclid(count) as u8 + min
}

fn splitmix64(mut value: u64) -> u64 {
    value = value.wrapping_add(0x9e37_79b9_7f4a_7c15);
    value = (value ^ (value >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
    value = (value ^ (value >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
    value ^ (value >> 31)
}
