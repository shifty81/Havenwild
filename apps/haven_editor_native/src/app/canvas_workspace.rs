use super::*;

/// W76A/W76B/W76I — one vertical ownership contract for every canvas-capable studio.
///
/// Editor chrome (global menu + studio tabs) ends before `host`. Inside the host,
/// document tabs are always first, followed by contextual controls, then rulers,
/// then the authored canvas. Bottom palette space is reserved instead of drawn over
/// the viewport when the shared palette is visible.
pub(crate) const DOCUMENT_TAB_H: f32 = 30.0;
pub(crate) const CONTEXT_TOOLBAR_H: f32 = 32.0;
pub(crate) const CHROME_GAP: f32 = 2.0;
pub(crate) const RULER_H: f32 = super::canvas_view::CANVAS_RULER_THICKNESS;
pub(crate) const RULER_W: f32 = super::canvas_view::CANVAS_RULER_THICKNESS;

#[derive(Clone, Copy, Debug, PartialEq)]
pub(crate) struct CanvasWorkspaceLayout {
    pub host: Rect,
    pub document_tabs: Rect,
    pub context_toolbar: Rect,
    /// Generic body below document tabs. Non-ruler graph/character studios use this.
    pub workspace_body: Rect,
    /// Ruler-safe drawable viewport. `draw_canvas_rulers` draws immediately above/left
    /// of this rectangle and therefore remains entirely inside `host`.
    pub viewport: Rect,
    pub palette_reserved: Rect,
}

impl CanvasWorkspaceLayout {
    pub(crate) fn calculate(host: Rect, palette_height: f32) -> Self {
        let palette_height = palette_height.clamp(0.0, host.h.max(0.0));
        let document_tabs = Rect::new(host.x, host.y, host.w, DOCUMENT_TAB_H.min(host.h));
        let context_y = document_tabs.y + document_tabs.h + CHROME_GAP;
        let remaining_after_tabs = (host.y + host.h - context_y - palette_height).max(1.0);
        let context_h = CONTEXT_TOOLBAR_H.min(remaining_after_tabs);
        let context_toolbar = Rect::new(host.x, context_y, host.w, context_h);
        let body_y = context_toolbar.y + context_toolbar.h + CHROME_GAP;
        let body_bottom = (host.y + host.h - palette_height).max(body_y + 1.0);
        let workspace_body = Rect::new(host.x, body_y, host.w, (body_bottom - body_y).max(1.0));

        // The ruler implementation draws its top strip at viewport.y - RULER_H and
        // left strip at viewport.x - RULER_W. Reserve those dimensions explicitly so
        // neither can ever invade DocumentTabBar, ContextToolbar, Tool Rail, or Layers.
        let viewport_x = host.x + RULER_W;
        let viewport_y = body_y + RULER_H;
        let viewport_right = host.x + host.w;
        let viewport_bottom = body_bottom;
        let viewport = Rect::new(
            viewport_x,
            viewport_y,
            (viewport_right - viewport_x).max(1.0),
            (viewport_bottom - viewport_y).max(1.0),
        );
        let palette_reserved = if palette_height > 0.0 {
            Rect::new(host.x, host.y + host.h - palette_height, host.w, palette_height)
        } else {
            Rect::new(host.x, host.y + host.h, host.w, 0.0)
        };
        Self { host, document_tabs, context_toolbar, workspace_body, viewport, palette_reserved }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn overlaps(a: Rect, b: Rect) -> bool {
        a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y
    }

    #[test]
    fn ruler_and_canvas_never_overlap_document_tabs() {
        for (w, h) in [(320.0, 240.0), (800.0, 600.0), (1600.0, 900.0), (2560.0, 1440.0)] {
            let layout = CanvasWorkspaceLayout::calculate(Rect::new(0.0, 0.0, w, h), 78.0);
            let top_ruler = Rect::new(layout.viewport.x, layout.viewport.y - RULER_H, layout.viewport.w, RULER_H);
            let left_ruler = Rect::new(layout.viewport.x - RULER_W, layout.viewport.y, RULER_W, layout.viewport.h);
            assert!(!overlaps(layout.document_tabs, top_ruler));
            assert!(!overlaps(layout.document_tabs, left_ruler));
            assert!(!overlaps(layout.document_tabs, layout.viewport));
        }
    }

    #[test]
    fn palette_reservation_never_covers_viewport() {
        let layout = CanvasWorkspaceLayout::calculate(Rect::new(20.0, 40.0, 900.0, 700.0), 78.0);
        assert!(layout.viewport.y + layout.viewport.h <= layout.palette_reserved.y + 0.01);
    }
}
