use macroquad::prelude::*;

use haven_editor::ObjectId;

use super::editor_text::draw_editor_text;
use super::render_helpers::draw_editor_widget;
use super::{PANEL_BG, PANEL_EDGE, TEXT};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum SceneAssetContextAction {
    EditAssetSource,
    EditCellVariant,
    EditSelection,
    EditBuildingComposite,
    EditSceneChunk,
    InspectBinding,
    RebuildNeighborhood,
    RevealSource,
}

#[derive(Clone, Copy, Debug)]
pub(crate) struct SceneAssetContextMenu {
    pub screen_position: Vec2,
    pub cell: [i32; 2],
    /// Object under the context-click, if any. This binds Edit Source to the
    /// visible placeable rather than silently falling back to the ground tile.
    pub object_id: Option<ObjectId>,
    pub has_building: bool,
}

pub(crate) fn context_menu_rect(menu: SceneAssetContextMenu) -> Rect {
    let width = 252.0;
    let height = 8.0 + actions().len() as f32 * 30.0;
    let x = menu
        .screen_position
        .x
        .clamp(8.0, (screen_width() - width - 8.0).max(8.0));
    let y = menu
        .screen_position
        .y
        .clamp(48.0, (screen_height() - height - 8.0).max(48.0));
    Rect::new(x, y, width, height)
}

pub(crate) fn action_at(
    menu: SceneAssetContextMenu,
    point: Vec2,
) -> Option<SceneAssetContextAction> {
    let rect = context_menu_rect(menu);
    if !rect.contains(point) {
        return None;
    }
    let index = ((point.y - rect.y - 4.0) / 30.0).floor() as usize;
    actions().get(index).map(|(_, action)| *action)
}

pub(crate) fn draw(menu: SceneAssetContextMenu) {
    let rect = context_menu_rect(menu);
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, PANEL_BG);
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.0, PANEL_EDGE);
    for (index, (label, _)) in actions().iter().enumerate() {
        let row = Rect::new(
            rect.x + 4.0,
            rect.y + 4.0 + index as f32 * 30.0,
            rect.w - 8.0,
            26.0,
        );
        draw_editor_widget(row, label, false);
    }
    draw_editor_text(
        if menu.has_building { "Building / canvas authoring scopes" } else if menu.object_id.is_some() { "Object / canvas authoring scopes" } else { "Terrain / canvas authoring scopes" },
        rect.x + 8.0,
        rect.y - 7.0,
        13.0,
        TEXT,
    );
}

fn actions() -> &'static [(&'static str, SceneAssetContextAction)] {
    &[
        ("Edit asset source (shared)", SceneAssetContextAction::EditAssetSource),
        ("Edit this cell / instance variant", SceneAssetContextAction::EditCellVariant),
        ("Edit selected region in Pixel Studio", SceneAssetContextAction::EditSelection),
        ("Edit building composite in Pixel Studio", SceneAssetContextAction::EditBuildingComposite),
        ("Edit entire scene chunk in Pixel Studio", SceneAssetContextAction::EditSceneChunk),
        ("Inspect asset binding", SceneAssetContextAction::InspectBinding),
        ("Rebuild affected neighborhood", SceneAssetContextAction::RebuildNeighborhood),
        ("Reveal source path", SceneAssetContextAction::RevealSource),
    ]
}
