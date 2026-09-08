use super::*;


/// W76G/W76R — shared control hierarchy. Studios choose semantic control roles;
/// visual state is resolved centrally so normal selection never borrows warning colors.
#[allow(dead_code)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum GuiControlClass {
    Primary,
    Secondary,
    Toolbar,
    Toggle,
    Segmented,
    Quiet,
    Danger,
}

pub(crate) fn draw_control(
    rect: Rect,
    label: &str,
    class: GuiControlClass,
    selected: bool,
    enabled: bool,
) {
    let tone = if !enabled {
        super::render_helpers::WidgetTone::Disabled
    } else {
        match class {
            GuiControlClass::Primary => super::render_helpers::WidgetTone::Primary,
            GuiControlClass::Quiet | GuiControlClass::Toolbar => super::render_helpers::WidgetTone::Quiet,
            GuiControlClass::Danger => super::render_helpers::WidgetTone::Destructive,
            GuiControlClass::Secondary | GuiControlClass::Toggle | GuiControlClass::Segmented => {
                super::render_helpers::WidgetTone::Standard
            }
        }
    };
    super::render_helpers::draw_editor_widget_tone(rect, label, selected, tone);
}

/// W76C/W76D — gesture-scoped pointer ownership for shared controls.
/// Canvas painting must never receive a pointer while a slider/color control owns it.
#[derive(Clone, Copy, Debug)]
pub(crate) enum GuiPointerCapture {
    BrushSlider(Rect),
    ColorPicker(Rect),
    LayerOpacity(Rect),
}

#[derive(Clone, Copy, Debug, Default)]
pub(crate) struct GuiInteractionState {
    pub capture: Option<GuiPointerCapture>,
}

#[derive(Clone, Copy, Debug)]
pub(crate) struct SliderSpec<'a> {
    pub rect: Rect,
    pub normalized: f32,
    pub label: &'a str,
    pub vertical: bool,
    pub enabled: bool,
}

pub(crate) fn draw_slider(spec: SliderSpec<'_>, captured: bool) {
    let t = spec.normalized.clamp(0.0, 1.0);
    let mouse = vec2(mouse_position().0, mouse_position().1);
    let hovered = spec.rect.contains(mouse);
    let track = if spec.vertical {
        let x = spec.rect.x + spec.rect.w * 0.5;
        Rect::new(x - 1.5, spec.rect.y + 12.0, 3.0, (spec.rect.h - 34.0).max(1.0))
    } else {
        let y = spec.rect.y + spec.rect.h * 0.5;
        Rect::new(spec.rect.x + 12.0, y - 1.5, (spec.rect.w - 24.0).max(1.0), 3.0)
    };
    let track_color = if spec.enabled { editor_theme::colors::BORDER_STRONG } else { editor_theme::colors::TEXT_DISABLED };
    draw_rectangle(track.x, track.y, track.w, track.h, track_color);
    let (cx, cy) = if spec.vertical {
        (track.x + track.w * 0.5, track.y + track.h * (1.0 - t))
    } else {
        (track.x + track.w * t, track.y + track.h * 0.5)
    };
    let thumb = if captured { editor_theme::colors::ACCENT_PRESSED }
        else if hovered { editor_theme::colors::ACCENT_HOVER }
        else { editor_theme::colors::ACCENT };
    draw_circle(cx, cy, if captured { 7.0 } else { 6.0 }, thumb);
    draw_circle_lines(cx, cy, if captured { 8.0 } else { 7.0 }, 1.0, editor_theme::colors::BORDER_STRONG);
    if !spec.label.is_empty() {
        let width = measure_editor_text(spec.label, None, 9, 1.0).width;
        draw_editor_text(
            spec.label,
            spec.rect.x + (spec.rect.w - width) * 0.5,
            spec.rect.y + spec.rect.h - 4.0,
            9.0,
            if spec.enabled { editor_theme::colors::TEXT_SECONDARY } else { editor_theme::colors::TEXT_DISABLED },
        );
    }
}

impl EditorApp {
    pub(crate) fn begin_brush_slider_drag(&mut self, slider: Rect) {
        self.gui_interaction.capture = Some(GuiPointerCapture::BrushSlider(slider));
        self.primary_pointer_owned_by_ui = true;
        self.apply_contextual_brush_slider(mouse_position().1, slider);
    }

    pub(crate) fn begin_color_picker_drag(&mut self, content: Rect) {
        self.gui_interaction.capture = Some(GuiPointerCapture::ColorPicker(content));
        self.primary_pointer_owned_by_ui = true;
        let mouse = vec2(mouse_position().0, mouse_position().1);
        let _ = super::pixel_color_panel::update_color_from_pointer(self, mouse, content);
    }

    pub(crate) fn begin_layer_opacity_drag(&mut self, slider: Rect) {
        self.gui_interaction.capture = Some(GuiPointerCapture::LayerOpacity(slider));
        self.primary_pointer_owned_by_ui = true;
        self.apply_pixel_layer_opacity_slider(mouse_position().0, slider);
    }

    /// Returns true while a shared control owns the primary pointer gesture.
    pub(crate) fn update_gui_pointer_capture(&mut self) -> bool {
        let Some(capture) = self.gui_interaction.capture else { return false; };
        let mouse = vec2(mouse_position().0, mouse_position().1);
        if is_mouse_button_down(MouseButton::Left) || is_mouse_button_pressed(MouseButton::Left) {
            match capture {
                GuiPointerCapture::BrushSlider(slider) => self.apply_contextual_brush_slider(mouse.y, slider),
                GuiPointerCapture::ColorPicker(content) => {
                    let _ = super::pixel_color_panel::update_color_from_pointer(self, mouse, content);
                }
                GuiPointerCapture::LayerOpacity(slider) => {
                    self.apply_pixel_layer_opacity_slider(mouse.x, slider);
                }
            }
            self.primary_pointer_owned_by_ui = true;
            return true;
        }
        if is_mouse_button_released(MouseButton::Left) || !is_mouse_button_down(MouseButton::Left) {
            self.gui_interaction.capture = None;
            self.primary_pointer_owned_by_ui = false;
            return true;
        }
        true
    }
}
