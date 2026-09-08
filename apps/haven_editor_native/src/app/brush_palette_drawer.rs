use super::asset_browser_ui::*;
use super::brush_authoring::BrushMode;
use super::render_helpers::{draw_editor_widget_tone, draw_wrapped, WidgetTone};
use super::*;
use haven_assets::asset_palette::{AssetPaletteCategory, AssetPaletteEntry, AssetPaletteKind};

const HEADER_H: f32 = 28.0;
const CONTEXT_H: f32 = 24.0;
const SEMANTIC_ROW_H: f32 = 34.0;
const FOOTER_H: f32 = 24.0;

#[derive(Clone, Copy)]
struct SemanticChoice {
    id: &'static str,
    label: &'static str,
}

const COLLISION_CHOICES: &[SemanticChoice] = &[
    SemanticChoice { id: "collision.auto", label: "Auto" },
    SemanticChoice { id: "collision.walkable", label: "Walkable" },
    SemanticChoice { id: "collision.blocked", label: "Blocked" },
    SemanticChoice { id: "collision.swim", label: "Swim" },
    SemanticChoice { id: "collision.wade", label: "Wade" },
    SemanticChoice { id: "collision.climb", label: "Climb" },
    SemanticChoice { id: "collision.ramp", label: "Ramp" },
    SemanticChoice { id: "collision.doorway", label: "Doorway" },
    SemanticChoice { id: "collision.bridge", label: "Bridge" },
    SemanticChoice { id: "collision.trigger", label: "Trigger" },
    SemanticChoice { id: "collision.clear_override", label: "Clear Override" },
];

const NAVIGATION_CHOICES: &[SemanticChoice] = &[
    SemanticChoice { id: "navigation.auto", label: "Auto" },
    SemanticChoice { id: "navigation.walkable", label: "Walkable" },
    SemanticChoice { id: "navigation.blocked", label: "Blocked" },
    SemanticChoice { id: "navigation.slow", label: "Slow" },
    SemanticChoice { id: "navigation.climb", label: "Climb" },
    SemanticChoice { id: "navigation.one_way", label: "One Way" },
    SemanticChoice { id: "navigation.clear_override", label: "Clear Override" },
];

const GAMEPLAY_CHOICES: &[SemanticChoice] = &[
    SemanticChoice { id: "gameplay.trigger", label: "Trigger Area" },
    SemanticChoice { id: "gameplay.spawn", label: "Spawn Area" },
    SemanticChoice { id: "gameplay.encounter", label: "Encounter Area" },
    SemanticChoice { id: "gameplay.shop", label: "Shop Area" },
    SemanticChoice { id: "gameplay.quest", label: "Quest Area" },
    SemanticChoice { id: "gameplay.audio", label: "Audio Area" },
    SemanticChoice { id: "gameplay.ownership", label: "Ownership Area" },
    SemanticChoice { id: "gameplay.safe", label: "Safe Area" },
    SemanticChoice { id: "gameplay.no_build", label: "No-Build Area" },
];

const ATMOSPHERE_CHOICES: &[SemanticChoice] = &[
    SemanticChoice { id: "atmosphere.clear", label: "Clear" },
    SemanticChoice { id: "atmosphere.morning_mist", label: "Morning Mist" },
    SemanticChoice { id: "atmosphere.coastal_haze", label: "Coastal Haze" },
    SemanticChoice { id: "atmosphere.mountain_fog", label: "Mountain Fog" },
    SemanticChoice { id: "atmosphere.swamp_mist", label: "Swamp Mist" },
    SemanticChoice { id: "atmosphere.cave_dust", label: "Cave Dust" },
    SemanticChoice { id: "atmosphere.storm_haze", label: "Storm Haze" },
    SemanticChoice { id: "atmosphere.snow_haze", label: "Snow Haze" },
];

const WEATHER_CHOICES: &[SemanticChoice] = &[
    SemanticChoice { id: "weather.clear", label: "Clear" },
    SemanticChoice { id: "weather.partly_cloudy", label: "Partly Cloudy" },
    SemanticChoice { id: "weather.cloudy", label: "Cloudy" },
    SemanticChoice { id: "weather.light_rain", label: "Light Rain" },
    SemanticChoice { id: "weather.rain", label: "Rain" },
    SemanticChoice { id: "weather.heavy_rain", label: "Heavy Rain" },
    SemanticChoice { id: "weather.thunderstorm", label: "Thunderstorm" },
    SemanticChoice { id: "weather.fog", label: "Fog" },
    SemanticChoice { id: "weather.light_snow", label: "Light Snow" },
    SemanticChoice { id: "weather.snow", label: "Snow" },
    SemanticChoice { id: "weather.blizzard", label: "Blizzard" },
];

const ELEVATION_CHOICES: &[SemanticChoice] = &[
    SemanticChoice { id: "elevation.preserve", label: "Preserve" },
    SemanticChoice { id: "elevation.level_0", label: "Level 0" },
    SemanticChoice { id: "elevation.level_2", label: "Level 2" },
    SemanticChoice { id: "elevation.level_3", label: "Level 3" },
    SemanticChoice { id: "elevation.level_4", label: "Level 4" },
    SemanticChoice { id: "connector.ramp", label: "Ramp 2→1→0" },
    SemanticChoice { id: "connector.ladder", label: "Ladder" },
];

impl EditorApp {
    pub(crate) fn draw_canvas_brush_palette(&mut self, rect: Rect) {
        draw_rectangle(rect.x, rect.y, rect.w, rect.h, Color::new(0.055, 0.06, 0.065, 0.97));
        draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.0, editor_theme::colors::BORDER_STRONG);
        draw_editor_text("PALETTE", rect.x + 10.0, rect.y + 18.0, 10.5, editor_theme::colors::TEXT_DISABLED);
        let terrain_actions = super::terrain_tile_variant_authoring::terrain_palette_actions_available(
            self.canvas_authoring_context.brush_mode,
        );
        draw_scissored_text(
            &self.canvas_palette_context_title(),
            rect.x + 78.0,
            rect.y + 18.0,
            (rect.w - if terrain_actions { 330.0 } else { 156.0 }).max(40.0),
            11.0,
            editor_theme::colors::TEXT_PRIMARY,
        );
        if terrain_actions {
            draw_editor_widget_tone(
                super::terrain_tile_variant_authoring::terrain_new_tile_rect(rect),
                "+ Tile",
                false,
                WidgetTone::Standard,
            );
            draw_editor_widget_tone(
                super::terrain_tile_variant_authoring::terrain_variant_rect(rect),
                "Variant",
                self.selected_canvas_asset_entry().is_some(),
                WidgetTone::Standard,
            );
            draw_editor_widget_tone(
                super::terrain_tile_variant_authoring::terrain_coverage_rect(rect),
                "Coverage",
                false,
                WidgetTone::Standard,
            );
        }
        let context = Rect::new(rect.x + 8.0, rect.y + HEADER_H, rect.w - 16.0, CONTEXT_H);
        let source = self.canvas_authoring_context.compact_source_label();
        draw_scissored_text(
            &format!("{} • {}", self.canvas_authoring_context.brush_mode.label(), source),
            context.x,
            context.y + 16.0,
            context.w,
            10.5,
            editor_theme::colors::TEXT_SECONDARY,
        );

        if let Some(choices) = semantic_choices(self.canvas_authoring_context.brush_mode) {
            self.draw_semantic_brush_choices(rect, choices);
        } else {
            self.draw_asset_brush_choices(rect);
        }
    }

    pub(crate) fn handle_canvas_brush_palette_click(&mut self, mx: f32, my: f32, rect: Rect) -> bool {
        let point = vec2(mx, my);
        if !rect.contains(point) { return false; }
        if super::terrain_tile_variant_authoring::terrain_palette_actions_available(
            self.canvas_authoring_context.brush_mode,
        ) {
            if super::terrain_tile_variant_authoring::terrain_new_tile_rect(rect).contains(point) {
                self.create_blank_terrain_tile_draft();
                return true;
            }
            if super::terrain_tile_variant_authoring::terrain_variant_rect(rect).contains(point) {
                self.create_selected_terrain_variant_draft();
                return true;
            }
            if super::terrain_tile_variant_authoring::terrain_coverage_rect(rect).contains(point) {
                self.open_terrain_pattern_coverage();
                return true;
            }
        }
        if let Some(choices) = semantic_choices(self.canvas_authoring_context.brush_mode) {
            let area = semantic_choice_area(rect);
            let columns = semantic_columns(area.w);
            for (index, choice) in choices.iter().enumerate() {
                if semantic_choice_rect(area, columns, index).contains(point) {
                    self.apply_semantic_brush_choice(*choice);
                    return true;
                }
            }
            return true;
        }

        let entries = self.canvas_brush_asset_entries();
        let grid = brush_asset_grid_rect(rect);
        let capacity = brush_palette_visible_capacity(grid).max(1);
        let start = self.brush_palette_offset.min(entries.len().saturating_sub(capacity));
        for (slot, entry) in entries.iter().skip(start).take(capacity).enumerate() {
            if brush_palette_card_rect(grid, slot).contains(point) {
                self.select_palette_asset(entry.stable_id.clone(), entry.kind);
                self.workspace_shell.shared_palette_visible = false;
                let _ = self.workspace_shell.save_default();
                return true;
            }
        }
        true
    }

    pub(crate) fn update_canvas_brush_palette_scroll(&mut self, rect: Rect) -> bool {
        if semantic_choices(self.canvas_authoring_context.brush_mode).is_some() { return false; }
        let point = vec2(mouse_position().0, mouse_position().1);
        let grid = brush_asset_grid_rect(rect);
        if !grid.contains(point) { return false; }
        let wheel = mouse_wheel().1;
        if wheel.abs() <= 0.01 { return false; }
        let entries = self.canvas_brush_asset_entries();
        let capacity = brush_palette_visible_capacity(grid).max(1);
        let columns = brush_palette_columns(grid.w).max(1);
        let delta = columns.saturating_mul(wheel.abs().ceil().max(1.0) as usize);
        if wheel < 0.0 {
            self.brush_palette_offset = self.brush_palette_offset.saturating_add(delta).min(entries.len().saturating_sub(capacity));
        } else {
            self.brush_palette_offset = self.brush_palette_offset.saturating_sub(delta);
        }
        true
    }

    fn draw_semantic_brush_choices(&self, rect: Rect, choices: &[SemanticChoice]) {
        let area = semantic_choice_area(rect);
        let columns = semantic_columns(area.w);
        for (index, choice) in choices.iter().enumerate() {
            let button = semantic_choice_rect(area, columns, index);
            let selected = self.canvas_authoring_context.source_id.as_deref() == Some(choice.id);
            draw_editor_widget_tone(button, choice.label, selected, if selected { WidgetTone::Primary } else { WidgetTone::Standard });
        }
        let footer = Rect::new(rect.x + 8.0, rect.y + rect.h - FOOTER_H, rect.w - 16.0, FOOTER_H - 4.0);
        draw_scissored_text(
            "Semantic choices modify authoring intent; they are not raw asset-browser entries.",
            footer.x, footer.y + 14.0, footer.w, 9.5, editor_theme::colors::TEXT_SECONDARY,
        );
    }

    fn draw_asset_brush_choices(&mut self, rect: Rect) {
        let entries = self.canvas_brush_asset_entries();
        let grid = brush_asset_grid_rect(rect);
        let capacity = brush_palette_visible_capacity(grid).max(1);
        let max_start = entries.len().saturating_sub(capacity);
        self.brush_palette_offset = self.brush_palette_offset.min(max_start);
        let start = self.brush_palette_offset;
        for (slot, entry) in entries.iter().skip(start).take(capacity).enumerate() {
            let card = brush_palette_card_rect(grid, slot);
            let active = self.asset_entry_is_selected(entry);
            draw_browser_card_surface(card, active);
            let thumbnail = browser_thumbnail_rect(card);
            draw_rectangle(thumbnail.x, thumbnail.y, thumbnail.w, thumbnail.h, Color::new(0.08, 0.09, 0.09, 1.0));
            let drew = self.editor_textures.draw_palette_thumbnail(entry, thumbnail);
            if !drew { draw_thumbnail_placeholder(thumbnail, &entry.label); }
            let subtitle = format!("{} · {}", self.canvas_authoring_context.brush_mode.label(), entry.category.label());
            draw_browser_card_labels(card, &entry.label, Some(&subtitle));
        }
        if entries.is_empty() {
            draw_editor_text("No compatible brush resources", grid.x + 8.0, grid.y + 28.0, 14.0, editor_theme::colors::TEXT_SECONDARY);
            draw_wrapped(
                "The Project Asset Browser may still contain source/reference assets, but this Palette only exposes resources compatible with the active layer and brush.",
                grid.x + 8.0, grid.y + 48.0, grid.w - 16.0, 12.0, editor_theme::colors::TEXT_SECONDARY,
            );
        }
        let footer = Rect::new(rect.x + 8.0, rect.y + rect.h - FOOTER_H, rect.w - 16.0, FOOTER_H - 4.0);
        draw_scissored_text(
            &format!("{} compatible resources", entries.len()),
            footer.x, footer.y + 14.0, footer.w, 9.5, editor_theme::colors::TEXT_SECONDARY,
        );
    }

    pub(crate) fn canvas_brush_asset_entries(&self) -> Vec<AssetPaletteEntry> {
        let mut entries = self.asset_catalog.entries().iter()
            .filter(|entry| entry.runtime_ready())
            .filter(|entry| brush_accepts_asset(self.canvas_authoring_context.brush_mode, entry))
            .cloned()
            .collect::<Vec<_>>();
        entries.sort_by_key(|entry| {
            let favorite = !self.asset_palette_state.is_favorite(&entry.stable_id);
            let recent = self.asset_palette_state.recent().iter().position(|id| id == &entry.stable_id).unwrap_or(usize::MAX);
            (favorite, recent, entry.label.to_ascii_lowercase())
        });
        entries
    }

    fn apply_semantic_brush_choice(&mut self, choice: SemanticChoice) {
        self.canvas_authoring_context.source_id = Some(choice.id.to_string());
        match choice.id {
            "elevation.preserve" => self.canvas_authoring_context.elevation_policy = super::brush_authoring::ElevationBrushPolicy::Preserve,
            "elevation.level_0" => { self.canvas_authoring_context.elevation_policy = super::brush_authoring::ElevationBrushPolicy::SetLevel; self.world_structural_level = 0; }
            "elevation.level_2" => { self.canvas_authoring_context.elevation_policy = super::brush_authoring::ElevationBrushPolicy::SetLevel; self.world_structural_level = 2; }
            "elevation.level_3" => { self.canvas_authoring_context.elevation_policy = super::brush_authoring::ElevationBrushPolicy::SetLevel; self.world_structural_level = 3; }
            "elevation.level_4" => { self.canvas_authoring_context.elevation_policy = super::brush_authoring::ElevationBrushPolicy::SetLevel; self.world_structural_level = 4; }
            "connector.ramp" | "connector.ladder" => {
                self.canvas_authoring_context.elevation_policy = super::brush_authoring::ElevationBrushPolicy::Preserve;
                self.world_layer_mode = WorldLayerMode::StructuralLevels;
                self.set_world_edit_tool(WorldEditTool::Select);
                self.canvas_active_tool = super::tool_registry::UniversalTool::Select;
            }
            _ => {}
        }
        self.sync_canvas_authoring_context();
        self.status_message = format!("Palette source: {}", choice.label);
    }
}

fn semantic_choices(mode: BrushMode) -> Option<&'static [SemanticChoice]> {
    match mode {
        BrushMode::Collision => Some(COLLISION_CHOICES),
        BrushMode::Navigation => Some(NAVIGATION_CHOICES),
        BrushMode::GameplayRegion => Some(GAMEPLAY_CHOICES),
        BrushMode::Atmosphere => Some(ATMOSPHERE_CHOICES),
        BrushMode::Weather => Some(WEATHER_CHOICES),
        BrushMode::Elevation => Some(ELEVATION_CHOICES),
        _ => None,
    }
}

fn brush_accepts_asset(mode: BrushMode, entry: &AssetPaletteEntry) -> bool {
    use AssetPaletteCategory as C;
    use AssetPaletteKind as K;
    match mode {
        BrushMode::SemanticTerrain | BrushMode::Autotile | BrushMode::TerrainElevation => {
            matches!(entry.kind, K::Tile(_)) && matches!(entry.category, C::Terrain | C::Paths | C::Water | C::Elevation)
        }
        BrushMode::ExactTile | BrushMode::VisualOverride => matches!(entry.kind, K::Tile(_)),
        BrushMode::Stamp => matches!(entry.kind, K::Stamp),
        BrushMode::Hydrology => matches!(entry.kind, K::Tile(_)) && matches!(entry.category, C::Water | C::Terrain),
        BrushMode::Object | BrushMode::Scatter => matches!(entry.kind, K::Object(_) | K::Stamp)
            && matches!(entry.category, C::Nature | C::Resources | C::Farm | C::Objects | C::Furniture | C::Storage | C::Decor | C::Props | C::Access),
        BrushMode::Lighting => matches!(entry.kind, K::Object(_)) && entry.category == C::Lighting,
        BrushMode::Pixel => false,
        BrushMode::Collision | BrushMode::Navigation | BrushMode::GameplayRegion | BrushMode::Atmosphere | BrushMode::Weather | BrushMode::Elevation | BrushMode::None => false,
    }
}

fn semantic_choice_area(rect: Rect) -> Rect {
    Rect::new(rect.x + 8.0, rect.y + HEADER_H + CONTEXT_H + 6.0, rect.w - 16.0, rect.h - HEADER_H - CONTEXT_H - FOOTER_H - 12.0)
}

fn semantic_columns(width: f32) -> usize {
    if width >= 390.0 { 3 } else if width >= 250.0 { 2 } else { 1 }
}

fn semantic_choice_rect(area: Rect, columns: usize, index: usize) -> Rect {
    let gap = 5.0;
    let width = ((area.w - gap * columns.saturating_sub(1) as f32) / columns.max(1) as f32).max(76.0);
    let column = index % columns.max(1);
    let row = index / columns.max(1);
    Rect::new(area.x + column as f32 * (width + gap), area.y + row as f32 * (SEMANTIC_ROW_H + gap), width, SEMANTIC_ROW_H)
}

const BRUSH_PALETTE_TARGET_CARD_W: f32 = 154.0;

fn brush_palette_columns(width: f32) -> usize {
    (((width + BROWSER_GAP) / (BRUSH_PALETTE_TARGET_CARD_W + BROWSER_GAP)).floor() as usize)
        .clamp(1, 12)
}

fn brush_palette_card_rect(area: Rect, slot: usize) -> Rect {
    let columns = brush_palette_columns(area.w);
    let gaps = BROWSER_GAP * columns.saturating_sub(1) as f32;
    let width = ((area.w - gaps) / columns.max(1) as f32).max(96.0);
    let column = slot % columns;
    let row = slot / columns;
    Rect::new(
        area.x + column as f32 * (width + BROWSER_GAP),
        area.y + row as f32 * (BROWSER_CARD_H + BROWSER_GAP),
        width,
        BROWSER_CARD_H,
    )
}

fn brush_palette_visible_capacity(area: Rect) -> usize {
    let columns = brush_palette_columns(area.w);
    let rows = ((area.h + BROWSER_GAP) / (BROWSER_CARD_H + BROWSER_GAP)).floor().max(1.0) as usize;
    columns.saturating_mul(rows).max(1)
}

fn brush_asset_grid_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + 8.0, rect.y + HEADER_H + CONTEXT_H + 6.0, rect.w - 16.0, rect.h - HEADER_H - CONTEXT_H - FOOTER_H - 12.0)
}

#[cfg(test)]
mod tests {
    use super::*;
    use haven_core::{ObjectKind, TileKind};

    fn entry(category: AssetPaletteCategory, kind: AssetPaletteKind) -> AssetPaletteEntry {
        AssetPaletteEntry {
            stable_id: "test".to_string(), label: "Test".to_string(), category, kind,
            sheet: Some("sheet.png".to_string()), rect: Some(haven_assets::asset_registry::AtlasRect { x: 0.0, y: 0.0, w: 32.0, h: 32.0 }),
            provenance: haven_assets::asset_palette::AssetProvenance::ProjectGenerated,
            warning: None, keywords: Vec::new(),
        }
    }

    #[test]
    fn terrain_palette_does_not_admit_unrelated_objects() {
        assert!(brush_accepts_asset(BrushMode::Autotile, &entry(AssetPaletteCategory::Terrain, AssetPaletteKind::Tile(TileKind::Grass))));
        assert!(!brush_accepts_asset(BrushMode::Autotile, &entry(AssetPaletteCategory::Objects, AssetPaletteKind::Object(ObjectKind::Chair))));
    }

    #[test]
    fn semantic_palettes_are_not_asset_browser_categories() {
        assert!(semantic_choices(BrushMode::Collision).is_some());
        assert!(semantic_choices(BrushMode::Weather).is_some());
        assert!(semantic_choices(BrushMode::Autotile).is_none());
    }

    #[test]
    fn wide_bottom_palette_uses_dense_horizontal_cards() {
        let area = Rect::new(0.0, 0.0, 1280.0, 112.0);
        assert!(brush_palette_columns(area.w) >= 7);
        assert!(brush_palette_visible_capacity(area) >= 7);
        let first = brush_palette_card_rect(area, 0);
        assert!(first.w < 190.0);
    }
}
