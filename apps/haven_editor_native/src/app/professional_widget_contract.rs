#![allow(dead_code)]

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub(crate) enum EditorSurfaceKind {
    CanvasDocument,
    DockedPanel,
    FloatingPanel,
    CanvasOverlay,
    Modal,
    StatusBar,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub(crate) enum WidgetRole {
    Button,
    IconButton,
    ToggleButton,
    Tab,
    SearchBox,
    TextField,
    TreeView,
    ListView,
    PropertyGrid,
    InspectorRow,
    Dropdown,
    Checkbox,
    Slider,
    ColorSwatch,
    ContextMenu,
    Tooltip,
    Toast,
    Splitter,
    ScrollArea,
    PanelChrome,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub(crate) enum WidgetInteractionState {
    Normal,
    Hovered,
    Pressed,
    Active,
    Focused,
    Disabled,
    Warning,
    Error,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub(crate) enum DockPlacement {
    Left,
    Right,
    Bottom,
    Floating,
    CanvasOverlay,
    Hidden,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub(crate) enum CanvasOverlayId {
    ToolRail,
    LayerRail,
    TilePalette,
    BrushSettings,
    TransformGizmo,
    SelectionToolbar,
    PieControlStrip,
    MiniInspector,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct WidgetContract {
    pub role: WidgetRole,
    pub surface: EditorSurfaceKind,
    pub receives_keyboard_focus: bool,
    pub receives_mouse_capture: bool,
    pub uses_theme_tokens: bool,
    pub supports_tooltip: bool,
    pub supports_disabled_state: bool,
}

impl WidgetContract {
    pub(crate) const fn new(role: WidgetRole, surface: EditorSurfaceKind) -> Self {
        Self {
            role,
            surface,
            receives_keyboard_focus: false,
            receives_mouse_capture: true,
            uses_theme_tokens: true,
            supports_tooltip: true,
            supports_disabled_state: true,
        }
    }

    pub(crate) const fn keyboard_focus(mut self) -> Self {
        self.receives_keyboard_focus = true;
        self
    }

    pub(crate) const fn no_mouse_capture(mut self) -> Self {
        self.receives_mouse_capture = false;
        self
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct OverlayContract {
    pub id: CanvasOverlayId,
    pub default_visible: bool,
    pub default_collapsed: bool,
    pub auto_hide_in_pie: bool,
    pub placement: DockPlacement,
    pub opaque: bool,
}

impl OverlayContract {
    pub(crate) const fn canvas_overlay(id: CanvasOverlayId, default_visible: bool) -> Self {
        Self {
            id,
            default_visible,
            default_collapsed: false,
            auto_hide_in_pie: true,
            placement: DockPlacement::CanvasOverlay,
            opaque: true,
        }
    }

    pub(crate) const fn persistent_in_pie(mut self) -> Self {
        self.auto_hide_in_pie = false;
        self
    }
}

pub(crate) const PROFESSIONAL_WIDGET_CONTRACTS: &[WidgetContract] = &[
    WidgetContract::new(WidgetRole::Button, EditorSurfaceKind::DockedPanel).keyboard_focus(),
    WidgetContract::new(WidgetRole::IconButton, EditorSurfaceKind::DockedPanel).keyboard_focus(),
    WidgetContract::new(WidgetRole::ToggleButton, EditorSurfaceKind::CanvasOverlay).keyboard_focus(),
    WidgetContract::new(WidgetRole::Tab, EditorSurfaceKind::DockedPanel).keyboard_focus(),
    WidgetContract::new(WidgetRole::SearchBox, EditorSurfaceKind::DockedPanel).keyboard_focus(),
    WidgetContract::new(WidgetRole::TextField, EditorSurfaceKind::DockedPanel).keyboard_focus(),
    WidgetContract::new(WidgetRole::TreeView, EditorSurfaceKind::DockedPanel).keyboard_focus(),
    WidgetContract::new(WidgetRole::ListView, EditorSurfaceKind::DockedPanel).keyboard_focus(),
    WidgetContract::new(WidgetRole::PropertyGrid, EditorSurfaceKind::DockedPanel),
    WidgetContract::new(WidgetRole::InspectorRow, EditorSurfaceKind::DockedPanel),
    WidgetContract::new(WidgetRole::Dropdown, EditorSurfaceKind::DockedPanel).keyboard_focus(),
    WidgetContract::new(WidgetRole::Checkbox, EditorSurfaceKind::DockedPanel).keyboard_focus(),
    WidgetContract::new(WidgetRole::Slider, EditorSurfaceKind::DockedPanel).keyboard_focus(),
    WidgetContract::new(WidgetRole::ColorSwatch, EditorSurfaceKind::DockedPanel).keyboard_focus(),
    WidgetContract::new(WidgetRole::ContextMenu, EditorSurfaceKind::FloatingPanel),
    WidgetContract::new(WidgetRole::Tooltip, EditorSurfaceKind::FloatingPanel).no_mouse_capture(),
    WidgetContract::new(WidgetRole::Toast, EditorSurfaceKind::FloatingPanel).no_mouse_capture(),
    WidgetContract::new(WidgetRole::Splitter, EditorSurfaceKind::DockedPanel),
    WidgetContract::new(WidgetRole::ScrollArea, EditorSurfaceKind::DockedPanel),
    WidgetContract::new(WidgetRole::PanelChrome, EditorSurfaceKind::DockedPanel),
];

pub(crate) const CANVAS_OVERLAY_CONTRACTS: &[OverlayContract] = &[
    OverlayContract::canvas_overlay(CanvasOverlayId::ToolRail, true),
    OverlayContract::canvas_overlay(CanvasOverlayId::LayerRail, true),
    OverlayContract::canvas_overlay(CanvasOverlayId::TilePalette, true),
    OverlayContract::canvas_overlay(CanvasOverlayId::BrushSettings, false),
    OverlayContract::canvas_overlay(CanvasOverlayId::TransformGizmo, true),
    OverlayContract::canvas_overlay(CanvasOverlayId::SelectionToolbar, true),
    OverlayContract::canvas_overlay(CanvasOverlayId::PieControlStrip, false).persistent_in_pie(),
    OverlayContract::canvas_overlay(CanvasOverlayId::MiniInspector, false),
];

pub(crate) fn widget_contract(role: WidgetRole) -> Option<&'static WidgetContract> {
    PROFESSIONAL_WIDGET_CONTRACTS
        .iter()
        .find(|contract| contract.role == role)
}

pub(crate) fn overlay_contract(id: CanvasOverlayId) -> Option<&'static OverlayContract> {
    CANVAS_OVERLAY_CONTRACTS
        .iter()
        .find(|contract| contract.id == id)
}

pub(crate) fn overlay_hides_in_pie(id: CanvasOverlayId) -> bool {
    overlay_contract(id)
        .map(|contract| contract.auto_hide_in_pie)
        .unwrap_or(true)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn all_professional_widgets_use_theme_tokens_and_disabled_state() {
        assert!(!PROFESSIONAL_WIDGET_CONTRACTS.is_empty());
        assert!(PROFESSIONAL_WIDGET_CONTRACTS.iter().all(|contract| contract.uses_theme_tokens));
        assert!(PROFESSIONAL_WIDGET_CONTRACTS.iter().all(|contract| contract.supports_disabled_state));
    }

    #[test]
    fn canvas_tool_and_layer_rails_are_opaque_overlays() {
        for id in [CanvasOverlayId::ToolRail, CanvasOverlayId::LayerRail] {
            let contract = overlay_contract(id).expect("overlay contract exists");
            assert_eq!(contract.placement, DockPlacement::CanvasOverlay);
            assert!(contract.opaque);
            assert!(contract.auto_hide_in_pie);
        }
    }

    #[test]
    fn pie_control_strip_is_the_only_default_pie_overlay() {
        let pie_strip = overlay_contract(CanvasOverlayId::PieControlStrip).expect("pie strip exists");
        assert!(!pie_strip.auto_hide_in_pie);
        assert!(CANVAS_OVERLAY_CONTRACTS
            .iter()
            .filter(|contract| !contract.auto_hide_in_pie)
            .all(|contract| contract.id == CanvasOverlayId::PieControlStrip));
    }

    #[test]
    fn core_interactive_widgets_accept_keyboard_focus() {
        for role in [
            WidgetRole::Button,
            WidgetRole::IconButton,
            WidgetRole::ToggleButton,
            WidgetRole::Tab,
            WidgetRole::SearchBox,
            WidgetRole::TextField,
            WidgetRole::TreeView,
            WidgetRole::ListView,
            WidgetRole::Dropdown,
            WidgetRole::Checkbox,
            WidgetRole::Slider,
            WidgetRole::ColorSwatch,
        ] {
            assert!(
                widget_contract(role).expect("widget role exists").receives_keyboard_focus,
                "{role:?} should be keyboard-focusable"
            );
        }
    }
}
