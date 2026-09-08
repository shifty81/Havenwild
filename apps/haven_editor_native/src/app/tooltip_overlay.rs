use super::render_helpers::draw_control_tooltip;
use super::*;

impl EditorApp {
    /// W81: tooltips are a final editor overlay, never children of Tool/Layer rails.
    /// New controls register requests here (or through one of the rail request helpers)
    /// so later panels cannot paint over help text.
    pub(crate) fn draw_global_tooltip_overlay(&self) {
        if !self.editor_settings.tooltips_enabled
            || self.editor_settings.open
            || self.pending_document_close.is_some()
            || self.authoring_session.is_some()
            || self.pixel_studio.new_dialog.is_some()
            || self.world_terrain_browser_open
        {
            return;
        }
        let request = self
            .canvas_tool_tooltip_request()
            .or_else(|| self.canvas_layer_tooltip_request())
            .or_else(|| self.terrain_material_browser_tooltip())
            .or_else(|| {
                let rect = super::editor_settings::settings_button_rect(screen_width());
                rect.contains(vec2(mouse_position().0, mouse_position().1))
                    .then(|| (rect, "Editor Settings".to_string()))
            });
        if let Some((anchor, label)) = request {
            draw_control_tooltip(anchor, &label);
        }
    }
}
