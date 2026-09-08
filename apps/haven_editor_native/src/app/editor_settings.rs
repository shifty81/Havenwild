use super::render_helpers::{draw_editor_widget_tone, draw_scissored_text, WidgetTone};
use super::*;
use serde::{Deserialize, Serialize};
use std::{fs, path::Path};

pub(crate) const NATIVE_EDITOR_SETTINGS_PATH: &str =
    "WORKSPACE/editor/native_editor_settings_v0_1.json";

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub(crate) enum SettingsSection {
    #[default]
    General,
    Appearance,
    Interface,
    Input,
    Canvas,
    PixelAnimation,
    WorldScene,
    Character,
    Play,
    Validation,
    Advanced,
}

impl SettingsSection {
    pub(crate) const ALL: [Self; 11] = [
        Self::General,
        Self::Appearance,
        Self::Interface,
        Self::Input,
        Self::Canvas,
        Self::PixelAnimation,
        Self::WorldScene,
        Self::Character,
        Self::Play,
        Self::Validation,
        Self::Advanced,
    ];

    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::General => "General",
            Self::Appearance => "Appearance",
            Self::Interface => "Interface",
            Self::Input => "Input & Shortcuts",
            Self::Canvas => "Canvas",
            Self::PixelAnimation => "Pixel & Animation",
            Self::WorldScene => "World & Scene",
            Self::Character => "Character",
            Self::Play => "Play / Runtime",
            Self::Validation => "Validation",
            Self::Advanced => "Advanced",
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(default)]
pub(crate) struct EditorSettingsState {
    pub schema: String,
    pub section: SettingsSection,
    pub ui_text_scale: f32,
    pub tooltips_enabled: bool,
    pub compact_button_labels: bool,
    pub autosave_recovery_enabled: bool,
    pub show_validation_details: bool,
    #[serde(skip)]
    pub open: bool,
}

impl Default for EditorSettingsState {
    fn default() -> Self {
        Self {
            schema: "havenwild.native_editor.settings.v0_1".to_string(),
            section: SettingsSection::General,
            ui_text_scale: 1.10,
            tooltips_enabled: true,
            compact_button_labels: true,
            autosave_recovery_enabled: true,
            show_validation_details: true,
            open: false,
        }
    }
}

impl EditorSettingsState {
    pub(crate) fn load_default() -> Self {
        let path = Path::new(NATIVE_EDITOR_SETTINGS_PATH);
        let Ok(text) = fs::read_to_string(path) else {
            return Self::default();
        };
        serde_json::from_str::<Self>(&text)
            .map(Self::normalized)
            .unwrap_or_default()
    }

    pub(crate) fn save_default(&self) -> Result<(), String> {
        let path = Path::new(NATIVE_EDITOR_SETTINGS_PATH);
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)
                .map_err(|error| format!("could not create settings directory: {error}"))?;
        }
        let normalized = self.clone().normalized();
        let text = serde_json::to_string_pretty(&normalized)
            .map_err(|error| format!("could not serialize editor settings: {error}"))?;
        fs::write(path, format!("{text}\n"))
            .map_err(|error| format!("could not save editor settings: {error}"))
    }

    fn normalized(mut self) -> Self {
        self.schema = "havenwild.native_editor.settings.v0_1".to_string();
        self.ui_text_scale = self.ui_text_scale.clamp(0.90, 1.35);
        self.open = false;
        self
    }
}

pub(crate) fn settings_button_rect(width: f32) -> Rect {
    Rect::new(width - 42.0, 7.0, 32.0, 30.0)
}

fn settings_panel_rect() -> Rect {
    let width = screen_width().min(820.0).max(520.0);
    let height = screen_height().min(620.0).max(420.0);
    Rect::new(
        (screen_width() - width) * 0.5,
        (screen_height() - height) * 0.5,
        width,
        height,
    )
}

fn close_rect(panel: Rect) -> Rect {
    Rect::new(panel.x + panel.w - 42.0, panel.y + 10.0, 28.0, 28.0)
}

fn section_rect(panel: Rect, index: usize) -> Rect {
    Rect::new(panel.x + 14.0, panel.y + 58.0 + index as f32 * 34.0, 190.0, 30.0)
}

fn option_rect(panel: Rect, row: usize) -> Rect {
    Rect::new(panel.x + 226.0, panel.y + 92.0 + row as f32 * 44.0, panel.w - 246.0, 34.0)
}

fn draw_toggle(panel: Rect, row: usize, label: &str, enabled: bool) {
    let rect = option_rect(panel, row);
    draw_editor_widget_tone(
        rect,
        &format!("{}  {}", if enabled { "ON" } else { "OFF" }, label),
        enabled,
        WidgetTone::Quiet,
    );
}

impl EditorApp {
    pub(crate) fn open_editor_settings(&mut self) {
        self.editor_settings.open = true;
        self.open_menu = None;
        self.status_message = "Editor Settings opened".to_string();
    }

    pub(crate) fn draw_editor_settings(&self) {
        if !self.editor_settings.open {
            return;
        }
        draw_rectangle(0.0, 0.0, screen_width(), screen_height(), Color::new(0.0, 0.0, 0.0, 0.42));
        let panel = settings_panel_rect();
        draw_rectangle(panel.x, panel.y, panel.w, panel.h, editor_theme::colors::PANEL_RAISED);
        draw_rectangle_lines(panel.x, panel.y, panel.w, panel.h, 1.0, editor_theme::colors::BORDER_STRONG);
        draw_editor_text("Editor Settings", panel.x + 16.0, panel.y + 34.0, 17.0, editor_theme::colors::TEXT_PRIMARY);
        draw_editor_widget_tone(close_rect(panel), "×", false, WidgetTone::Quiet);

        for (index, section) in SettingsSection::ALL.into_iter().enumerate() {
            draw_editor_widget_tone(
                section_rect(panel, index),
                section.label(),
                self.editor_settings.section == section,
                WidgetTone::Quiet,
            );
        }

        let x = panel.x + 226.0;
        let content_w = (panel.w - 246.0).max(120.0);
        draw_editor_text(
            self.editor_settings.section.label(),
            x,
            panel.y + 70.0,
            16.0,
            editor_theme::colors::TEXT_PRIMARY,
        );

        match self.editor_settings.section {
            SettingsSection::Appearance | SettingsSection::Interface => {
                draw_scissored_text(
                    &format!("UI text scale: {:.2} (applies after restart)", self.editor_settings.ui_text_scale),
                    x,
                    panel.y + 110.0,
                    content_w,
                    12.0,
                    editor_theme::colors::TEXT_SECONDARY,
                );
                draw_editor_widget_tone(option_rect(panel, 1), "Text size -", false, WidgetTone::Quiet);
                draw_editor_widget_tone(option_rect(panel, 2), "Text size +", false, WidgetTone::Quiet);
                draw_toggle(panel, 3, "Compact button labels", self.editor_settings.compact_button_labels);
                draw_toggle(panel, 4, "Tooltips", self.editor_settings.tooltips_enabled);
            }
            SettingsSection::General => {
                draw_toggle(panel, 0, "Autosave / crash recovery", self.editor_settings.autosave_recovery_enabled);
                draw_scissored_text(
                    "Settings are split between user/editor preferences, project authority, and persisted workspace layout. Studio-specific options are surfaced here instead of accumulating duplicate buttons in every panel.",
                    x,
                    panel.y + 160.0,
                    content_w,
                    12.0,
                    editor_theme::colors::TEXT_SECONDARY,
                );
            }
            SettingsSection::Validation => {
                draw_toggle(panel, 0, "Show detailed validation rows", self.editor_settings.show_validation_details);
                draw_scissored_text(
                    "Validation has one report owner in the right Workspace Dock. Bottom Activity shows operational jobs/progress only; it does not duplicate the validation report.",
                    x,
                    panel.y + 160.0,
                    content_w,
                    12.0,
                    editor_theme::colors::TEXT_SECONDARY,
                );
            }
            _ => {
                draw_scissored_text(
                    "This settings category is now reserved in the single project-wide Settings authority. Feature-specific controls will be promoted here as their production systems are completed.",
                    x,
                    panel.y + 112.0,
                    content_w,
                    12.0,
                    editor_theme::colors::TEXT_SECONDARY,
                );
            }
        }
    }

    pub(crate) fn handle_editor_settings_click(&mut self, point: Vec2) -> bool {
        if !self.editor_settings.open {
            return false;
        }
        let panel = settings_panel_rect();
        if close_rect(panel).contains(point) || !panel.contains(point) {
            self.editor_settings.open = false;
            let _ = self.editor_settings.save_default();
            return true;
        }
        for (index, section) in SettingsSection::ALL.into_iter().enumerate() {
            if section_rect(panel, index).contains(point) {
                self.editor_settings.section = section;
                let _ = self.editor_settings.save_default();
                self.editor_settings.open = true;
                return true;
            }
        }
        match self.editor_settings.section {
            SettingsSection::Appearance | SettingsSection::Interface => {
                if option_rect(panel, 1).contains(point) {
                    self.editor_settings.ui_text_scale = (self.editor_settings.ui_text_scale - 0.05).clamp(0.90, 1.35);
                } else if option_rect(panel, 2).contains(point) {
                    self.editor_settings.ui_text_scale = (self.editor_settings.ui_text_scale + 0.05).clamp(0.90, 1.35);
                } else if option_rect(panel, 3).contains(point) {
                    self.editor_settings.compact_button_labels = !self.editor_settings.compact_button_labels;
                } else if option_rect(panel, 4).contains(point) {
                    self.editor_settings.tooltips_enabled = !self.editor_settings.tooltips_enabled;
                } else {
                    return true;
                }
            }
            SettingsSection::General => {
                if option_rect(panel, 0).contains(point) {
                    self.editor_settings.autosave_recovery_enabled = !self.editor_settings.autosave_recovery_enabled;
                } else {
                    return true;
                }
            }
            SettingsSection::Validation => {
                if option_rect(panel, 0).contains(point) {
                    self.editor_settings.show_validation_details = !self.editor_settings.show_validation_details;
                } else {
                    return true;
                }
            }
            _ => return true,
        }
        let _ = self.editor_settings.save_default();
        self.editor_settings.open = true;
        true
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn settings_normalization_keeps_text_scale_bounded() {
        let low = EditorSettingsState { ui_text_scale: 0.1, ..Default::default() }.normalized();
        let high = EditorSettingsState { ui_text_scale: 9.0, ..Default::default() }.normalized();
        assert_eq!(low.ui_text_scale, 0.90);
        assert_eq!(high.ui_text_scale, 1.35);
    }

    #[test]
    fn settings_have_one_nested_project_wide_section_list() {
        assert!(SettingsSection::ALL.len() >= 10);
        assert_eq!(SettingsSection::PixelAnimation.label(), "Pixel & Animation");
        assert_eq!(SettingsSection::WorldScene.label(), "World & Scene");
    }
}
