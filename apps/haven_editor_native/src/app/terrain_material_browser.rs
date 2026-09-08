use super::render_helpers::{draw_editor_widget_tone, draw_scissored_text, WidgetTone};
use super::*;
use serde::Deserialize;
use std::{fs, path::Path};

pub(crate) const TERRAIN_STANDARD_PATH: &str = "content/terrain/havenwild_terrain_standard_v1.json";
const ROW_H: f32 = 28.0;
const HEADER_H: f32 = 58.0;
const FOOTER_H: f32 = 52.0;

#[allow(dead_code)]
#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub(crate) struct TerrainMaterialEntry {
    pub id: String,
    pub code: String,
    pub stable_ordinal: usize,
    pub label: String,
    pub category: String,
    pub base_terrain: String,
    pub collision_class: String,
    pub walkable: bool,
    pub source_representative_tile: usize,
    pub runtime_status: String,
    pub art_status: String,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct TerrainMaterialFile {
    materials: Vec<TerrainMaterialEntry>,
}

#[derive(Clone, Debug, Default)]
pub(crate) struct TerrainMaterialCatalog {
    pub materials: Vec<TerrainMaterialEntry>,
}

impl TerrainMaterialCatalog {
    pub(crate) fn load_default() -> Result<Self, String> {
        Self::load_from_project_root(&repo_root_dir())
    }

    fn load_from_project_root(project_root: &Path) -> Result<Self, String> {
        let path = project_root.join(TERRAIN_STANDARD_PATH);
        let text = fs::read_to_string(&path)
            .map_err(|error| format!("could not read {}: {error}", path.display()))?;
        let mut file: TerrainMaterialFile = serde_json::from_str(&text)
            .map_err(|error| format!("could not parse {}: {error}", path.display()))?;
        file.materials.sort_by_key(|entry| entry.stable_ordinal);
        Ok(Self { materials: file.materials })
    }

    pub(crate) fn len(&self) -> usize { self.materials.len() }
    pub(crate) fn get(&self, index: usize) -> Option<&TerrainMaterialEntry> { self.materials.get(index) }

    pub(crate) fn legacy_tile_for_code(code: &str) -> Option<TileKind> {
        Some(match code {
            "Grass" | "Grass_Light" | "Grass_Dark" | "Grass_Dead" => TileKind::Grass,
            "Dirt_Tan" | "Dirt_Brown" | "Dirt_Dark" | "Dirt_Roots" | "Earth_Cracked" => TileKind::Dirt,
            "Sand" => TileKind::Sand,
            "Gravel_1" => TileKind::PebbleShore,
            "Mud_Brown" => TileKind::MudBank,
            "Rock_White" | "Rock_Gray" | "Rock_Dark" | "Rock_Black" | "Mudstone_Gray" | "Mudstone_Brown" => TileKind::MountainRock,
            "Stone_White" | "Stone_Tan" => TileKind::StonePath,
            "Soil" => TileKind::TilledSoil,
            "Water_Shallows_Dirt" | "Water_Shallows_Sand" => TileKind::ShallowWater,
            "Water" => TileKind::Water,
            "Water_Deep" => TileKind::DeepWater,
            // These families are discoverable in W81 but require the W82/W84
            // material-identity lane before direct world painting is truthful.
            "Snow_1" | "Snow_2" | "Ice" | "Ice_Melting" | "Water_Purple" | "Water_Green" | "Lava" | "Hole_Brown" | "Hole_Black" => return None,
            _ => return None,
        })
    }

    pub(crate) fn direct_paint_ready(entry: &TerrainMaterialEntry) -> bool {
        entry.runtime_status == "runtime_enabled" && Self::legacy_tile_for_code(&entry.code).is_some()
    }
}

pub(crate) fn browser_button_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + 62.0, rect.y + 358.0, (rect.w - 124.0).max(92.0), 30.0)
}

fn browser_rect() -> Rect {
    let w = screen_width().min(620.0).max(460.0);
    let h = screen_height().min(720.0).max(460.0);
    Rect::new((screen_width() - w) * 0.5, (screen_height() - h) * 0.5, w, h)
}
fn close_rect(rect: Rect) -> Rect { Rect::new(rect.x + rect.w - 42.0, rect.y + 12.0, 28.0, 28.0) }
fn up_rect(rect: Rect) -> Rect { Rect::new(rect.x + 14.0, rect.y + rect.h - 42.0, 72.0, 28.0) }
fn down_rect(rect: Rect) -> Rect { Rect::new(rect.x + 92.0, rect.y + rect.h - 42.0, 72.0, 28.0) }
fn row_rect(rect: Rect, visible_index: usize) -> Rect {
    Rect::new(rect.x + 14.0, rect.y + HEADER_H + visible_index as f32 * ROW_H, rect.w - 28.0, ROW_H - 2.0)
}

impl EditorApp {
    pub(crate) fn draw_world_terrain_material_browser(&self) {
        if !self.world_terrain_browser_open { return; }
        draw_rectangle(0.0, 0.0, screen_width(), screen_height(), Color::new(0.0,0.0,0.0,0.42));
        let rect = browser_rect();
        draw_rectangle(rect.x, rect.y, rect.w, rect.h, editor_theme::colors::PANEL_RAISED);
        draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.0, editor_theme::colors::BORDER_STRONG);
        draw_editor_text("Terrain Material Library", rect.x + 16.0, rect.y + 34.0, 17.0, editor_theme::colors::TEXT_PRIMARY);
        draw_editor_widget_tone(close_rect(rect), "×", false, WidgetTone::Quiet);
        let capacity = (((rect.h - HEADER_H - FOOTER_H) / ROW_H).floor().max(1.0)) as usize;
        let start = self.world_terrain_browser_scroll.min(self.terrain_material_catalog.len().saturating_sub(1));
        for (visible, entry) in self.terrain_material_catalog.materials.iter().skip(start).take(capacity).enumerate() {
            let row = row_rect(rect, visible);
            let ready = TerrainMaterialCatalog::direct_paint_ready(entry);
            let selected = self.world_selected_material_code().is_some_and(|code| code == entry.code);
            draw_editor_widget_tone(row, "", selected, if ready { WidgetTone::Standard } else { WidgetTone::Quiet });
            draw_scissored_text(&entry.label, row.x + 8.0, row.y + 18.0, row.w * 0.42, 12.0, editor_theme::colors::TEXT_PRIMARY);
            draw_scissored_text(&entry.category, row.x + row.w * 0.45, row.y + 18.0, row.w * 0.22, 11.0, editor_theme::colors::TEXT_SECONDARY);
            let status = if ready { "Paint" } else if entry.runtime_status == "runtime_enabled" { "Needs material identity" } else { "Catalogued" };
            draw_scissored_text(status, row.x + row.w * 0.69, row.y + 18.0, row.w * 0.29 - 8.0, 11.0, if ready { editor_theme::colors::GOOD } else { editor_theme::colors::TEXT_SECONDARY });
        }
        draw_editor_widget_tone(up_rect(rect), "Up", false, WidgetTone::Quiet);
        draw_editor_widget_tone(down_rect(rect), "Down", false, WidgetTone::Quiet);
        draw_scissored_text(
            &format!("{} materials catalogued • W81 exposes the full LPC/V7 family; W82/W84 promote stable per-cell identity for the remaining families.", self.terrain_material_catalog.len()),
            rect.x + 178.0, rect.y + rect.h - 23.0, rect.w - 194.0, 11.0, editor_theme::colors::TEXT_SECONDARY);
    }

    pub(crate) fn handle_world_terrain_material_browser_click(&mut self, point: Vec2) -> bool {
        if !self.world_terrain_browser_open { return false; }
        let rect = browser_rect();
        if close_rect(rect).contains(point) || !rect.contains(point) {
            self.world_terrain_browser_open = false;
            return true;
        }
        if up_rect(rect).contains(point) {
            self.world_terrain_browser_scroll = self.world_terrain_browser_scroll.saturating_sub(6);
            return true;
        }
        if down_rect(rect).contains(point) {
            let max = self.terrain_material_catalog.len().saturating_sub(1);
            self.world_terrain_browser_scroll = (self.world_terrain_browser_scroll + 6).min(max);
            return true;
        }
        let capacity = (((rect.h - HEADER_H - FOOTER_H) / ROW_H).floor().max(1.0)) as usize;
        let start = self.world_terrain_browser_scroll.min(self.terrain_material_catalog.len().saturating_sub(1));
        for visible in 0..capacity {
            if !row_rect(rect, visible).contains(point) { continue; }
            let index = start + visible;
            let Some(entry) = self.terrain_material_catalog.get(index).cloned() else { return true; };
            if let Some(tile) = TerrainMaterialCatalog::legacy_tile_for_code(&entry.code).filter(|_| TerrainMaterialCatalog::direct_paint_ready(&entry)) {
                if let Some(tile_index) = TileKind::ALL.iter().position(|candidate| *candidate == tile) {
                    self.selected_tile = tile_index;
                    self.status_message = format!("Terrain material selected: {} ({})", entry.label, entry.code);
                }
            } else {
                self.status_message = format!("{} is catalogued and visible, but direct painting waits for stable material identity rather than substituting unrelated TileKind artwork", entry.label);
            }
            return true;
        }
        true
    }

    pub(crate) fn world_selected_material_code(&self) -> Option<&str> {
        let tile = self.selected_tile_kind();
        match tile {
            TileKind::Grass => Some("Grass"), TileKind::Dirt => Some("Dirt_Brown"), TileKind::Sand => Some("Sand"),
            TileKind::PebbleShore => Some("Gravel_1"), TileKind::MudBank => Some("Mud_Brown"), TileKind::MountainRock => Some("Rock_Dark"),
            TileKind::StonePath => Some("Stone_Tan"), TileKind::TilledSoil => Some("Soil"), TileKind::ShallowWater => Some("Water_Shallows_Dirt"),
            TileKind::Water => Some("Water"), TileKind::DeepWater => Some("Water_Deep"), _ => None,
        }
    }

    pub(crate) fn terrain_material_browser_tooltip(&self) -> Option<(Rect, String)> {
        if self.viewport_mode != EditorViewportMode::SceneRectangles || self.world_layer_mode != WorldLayerMode::Terrain || self.world_terrain_browser_open { return None; }
        let rect = self.shell_layout().inspector_content;
        let button = browser_button_rect(rect);
        button.contains(vec2(mouse_position().0, mouse_position().1)).then(|| (button, "Terrain Materials — browse every catalogued LPC/V7 surface family".to_string()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn complete_catalog_is_not_the_old_twelve_material_palette() {
        let catalog = TerrainMaterialCatalog::load_default().expect("terrain standard");
        assert!(catalog.len() >= 34);
        assert!(catalog.materials.iter().any(|entry| entry.code == "Lava"));
        assert!(catalog.materials.iter().any(|entry| entry.code == "Ice"));
        assert!(catalog.materials.iter().any(|entry| entry.code == "Rock_Black"));
    }
}
