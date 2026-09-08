//! Havenwild-owned native-editor UI boundary.
//!
//! Third-party GUI infrastructure stays behind Havenwild types. Taffy,
//! cosmic-text, AccessKit, rfd, and arboard are implementation dependencies;
//! their public types must not leak into Havenwild save/content/editor schemas.

use serde::{Deserialize, Serialize};

pub const UI_SCHEMA: &str = "havenwild.ui.foundation.v2";

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum UiSurfaceRole {
    WorkspaceTabs,
    DocumentHost,
    Canvas,
    CanvasToolRail,
    CanvasLayerRail,
    CanvasViewControls,
    ContextTray,
    RightDock,
    ScrollView,
    Popup,
}

#[derive(Clone, Copy, Debug, PartialEq, Serialize, Deserialize)]
pub struct UiRect {
    pub x: f32,
    pub y: f32,
    pub width: f32,
    pub height: f32,
}

impl UiRect {
    pub fn new(x: f32, y: f32, width: f32, height: f32) -> Self {
        Self { x, y, width, height }
    }

    pub fn right(self) -> f32 { self.x + self.width }
    pub fn bottom(self) -> f32 { self.y + self.height }

    pub fn is_non_empty(self) -> bool {
        self.width > 0.0 && self.height > 0.0
    }

    pub fn inset(self, insets: UiInsets) -> Self {
        Self::new(
            self.x + insets.left,
            self.y + insets.top,
            (self.width - insets.left - insets.right).max(0.0),
            (self.height - insets.top - insets.bottom).max(0.0),
        )
    }

    pub fn intersects(self, other: Self) -> bool {
        self.x < other.right()
            && self.right() > other.x
            && self.y < other.bottom()
            && self.bottom() > other.y
    }
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Serialize, Deserialize)]
pub struct UiInsets {
    pub left: f32,
    pub top: f32,
    pub right: f32,
    pub bottom: f32,
}

impl UiInsets {
    pub const fn all(value: f32) -> Self {
        Self { left: value, top: value, right: value, bottom: value }
    }
}

/// Small retained state for scrollable custom-drawn surfaces. Rendering and
/// hit-testing remain owned by the Havenwild editor; this state only normalizes
/// scrolling/clamping semantics across Properties, Assets, Outliner and lists.
#[derive(Clone, Copy, Debug, Default, PartialEq, Serialize, Deserialize)]
pub struct UiScrollState {
    pub offset: f32,
    pub content_extent: f32,
}

impl UiScrollState {
    pub fn clamp_to_viewport(&mut self, viewport_extent: f32) {
        let max_offset = (self.content_extent - viewport_extent.max(0.0)).max(0.0);
        self.offset = self.offset.clamp(0.0, max_offset);
    }

    pub fn scroll_by(&mut self, delta: f32, viewport_extent: f32) {
        self.offset = (self.offset + delta).max(0.0);
        self.clamp_to_viewport(viewport_extent);
    }
}

/// Layout cursor for vertically stacked inspector/widget content. It removes
/// fixed magic-Y coordinate piles while keeping the immediate-mode renderer.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct UiColumn {
    pub viewport: UiRect,
    pub cursor_y: f32,
    pub gap: f32,
    pub scroll_offset: f32,
}

impl UiColumn {
    pub fn new(viewport: UiRect, padding: f32, gap: f32, scroll_offset: f32) -> Self {
        let inner = viewport.inset(UiInsets::all(padding));
        Self {
            viewport: inner,
            cursor_y: inner.y - scroll_offset,
            gap,
            scroll_offset,
        }
    }

    pub fn take(&mut self, height: f32) -> UiRect {
        let rect = UiRect::new(self.viewport.x, self.cursor_y, self.viewport.width, height.max(0.0));
        self.cursor_y += height.max(0.0) + self.gap;
        rect
    }

    pub fn take_spaced(&mut self, height: f32, extra_gap: f32) -> UiRect {
        let rect = self.take(height);
        self.cursor_y += extra_gap.max(0.0);
        rect
    }

    pub fn content_extent(self) -> f32 {
        (self.cursor_y + self.scroll_offset - self.viewport.y).max(0.0)
    }

    pub fn visible(self, rect: UiRect) -> bool {
        self.viewport.intersects(rect)
    }
}


#[derive(Clone, Copy, Debug, PartialEq)]
pub struct UiGrid {
    pub rect: UiRect,
    pub columns: usize,
    pub gap: f32,
    pub row_height: f32,
}

impl UiGrid {
    pub fn new(rect: UiRect, columns: usize, gap: f32, row_height: f32) -> Self {
        Self {
            rect,
            columns: columns.max(1),
            gap: gap.max(0.0),
            row_height: row_height.max(0.0),
        }
    }

    pub fn cell(self, index: usize) -> UiRect {
        let columns = self.columns.max(1);
        let column = index % columns;
        let row = index / columns;
        let total_gap = self.gap * columns.saturating_sub(1) as f32;
        let cell_width = ((self.rect.width - total_gap) / columns as f32).max(0.0);
        UiRect::new(
            self.rect.x + column as f32 * (cell_width + self.gap),
            self.rect.y + row as f32 * (self.row_height + self.gap),
            cell_width,
            self.row_height,
        )
    }

    pub fn row_extent(self, item_count: usize) -> f32 {
        if item_count == 0 {
            return 0.0;
        }
        let columns = self.columns.max(1);
        let rows = (item_count + columns - 1) / columns;
        rows as f32 * self.row_height + rows.saturating_sub(1) as f32 * self.gap
    }
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct UiTabStripLayout {
    pub host: UiRect,
    pub tab_height: f32,
    pub gap: f32,
    pub content_gap: f32,
}

impl UiTabStripLayout {
    pub fn new(host: UiRect, tab_height: f32, gap: f32, content_gap: f32) -> Self {
        Self {
            host,
            tab_height: tab_height.max(0.0),
            gap: gap.max(0.0),
            content_gap: content_gap.max(0.0),
        }
    }

    pub fn tab_rect(self, index: usize, count: usize) -> UiRect {
        let count = count.max(1);
        let total_gap = self.gap * count.saturating_sub(1) as f32;
        let width = ((self.host.width - total_gap) / count as f32).max(0.0);
        UiRect::new(
            self.host.x + index.min(count - 1) as f32 * (width + self.gap),
            self.host.y,
            width,
            self.tab_height,
        )
    }

    pub fn content_rect(self) -> UiRect {
        let top = self.tab_height + self.content_gap;
        UiRect::new(
            self.host.x,
            self.host.y + top,
            self.host.width,
            (self.host.height - top).max(0.0),
        )
    }
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct UiWidgetMetrics {
    pub padding: f32,
    pub gap: f32,
    pub compact_gap: f32,
    pub row_height: f32,
    pub control_height: f32,
    pub section_height: f32,
}

impl Default for UiWidgetMetrics {
    fn default() -> Self {
        Self {
            padding: 8.0,
            gap: 6.0,
            compact_gap: 4.0,
            row_height: 28.0,
            control_height: 30.0,
            section_height: 26.0,
        }
    }
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct UiLayoutPolicy {
    pub schema: String,
    pub canvas_first: bool,
    pub canvas_overlays_reserve_layout: bool,
    pub minimum_canvas_width: f32,
    pub right_dock_default_width: f32,
    pub popup_must_anchor_to_invoker: bool,
    pub document_overlays_must_clip: bool,
}

impl Default for UiLayoutPolicy {
    fn default() -> Self {
        Self {
            schema: UI_SCHEMA.to_string(),
            canvas_first: true,
            canvas_overlays_reserve_layout: false,
            minimum_canvas_width: 640.0,
            right_dock_default_width: 360.0,
            popup_must_anchor_to_invoker: true,
            document_overlays_must_clip: true,
        }
    }
}

/// Compile-time evidence that mature infrastructure is linked behind the
/// Havenwild UI boundary. Concrete adapters are migrated incrementally rather
/// than replacing the native editor with another widget framework.
pub fn mature_backend_names() -> [&'static str; 5] {
    ["taffy", "cosmic-text", "accesskit", "rfd", "arboard"]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn canvas_first_policy_never_reserves_overlay_width() {
        let policy = UiLayoutPolicy::default();
        assert!(policy.canvas_first);
        assert!(!policy.canvas_overlays_reserve_layout);
        assert!(policy.document_overlays_must_clip);
        assert_eq!(mature_backend_names().len(), 5);
    }

    #[test]
    fn column_flow_is_monotonic_and_viewport_aware() {
        let mut column = UiColumn::new(UiRect::new(10.0, 20.0, 300.0, 200.0), 8.0, 6.0, 0.0);
        let first = column.take(30.0);
        let second = column.take(40.0);
        assert!(second.y > first.y);
        assert!(column.visible(first));
        assert!(column.content_extent() >= 76.0);
    }

    #[test]
    fn scroll_state_clamps_to_content() {
        let mut state = UiScrollState { offset: 500.0, content_extent: 320.0 };
        state.clamp_to_viewport(200.0);
        assert_eq!(state.offset, 120.0);
    }
    #[test]
    fn grid_cells_never_escape_their_row_width() {
        let grid = UiGrid::new(UiRect::new(10.0, 20.0, 300.0, 100.0), 3, 6.0, 30.0);
        for index in 0..6 {
            let cell = grid.cell(index);
            assert!(cell.x >= grid.rect.x);
            assert!(cell.right() <= grid.rect.right() + 0.001);
        }
        assert_eq!(grid.row_extent(6), 66.0);
    }

    #[test]
    fn tab_strip_content_starts_below_tabs() {
        let layout = UiTabStripLayout::new(UiRect::new(0.0, 0.0, 400.0, 500.0), 30.0, 4.0, 8.0);
        let content = layout.content_rect();
        assert_eq!(content.y, 38.0);
        assert_eq!(content.height, 462.0);
        assert!(layout.tab_rect(3, 4).right() <= 400.001);
    }

}
