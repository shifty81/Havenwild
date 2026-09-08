use super::*;
use haven_assets::universal_lpc_character_recipe::UNIVERSAL_LPC_CHARACTER_BUILDER_CATEGORIES;

pub(crate) const CHARACTER_MAX_ROWS: usize = 18;
const CHARACTER_ROW_H: f32 = 27.0;
const CHARACTER_LIST_TOP: f32 = 98.0;
pub(crate) const CHARACTER_LIST_FOOTER: f32 = 18.0;
const CHARACTER_CATEGORY_MENU_COLUMNS: usize = 3;

pub(crate) const CHARACTER_CREATE_CATEGORY_IDS: [&str; 13] = [
    "body", "head", "hair", "eyebrows", "eyes", "nose", "ears", "beards",
    "expression", "wings", "tail", "mobility", "effects",
];
pub(crate) const CHARACTER_WARDROBE_CATEGORY_IDS: [&str; 12] = [
    "torso", "arms", "hands", "legs", "feet", "hat", "neck", "back",
    "accessory", "weapon", "shield", "tools",
];

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum CharacterCatalogSection {
    Create,
    WardrobeGear,
}

impl CharacterCatalogSection {
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Create => "Create",
            Self::WardrobeGear => "Wardrobe & Gear",
        }
    }

    pub(crate) fn category_ids(self) -> &'static [&'static str] {
        match self {
            Self::Create => &CHARACTER_CREATE_CATEGORY_IDS,
            Self::WardrobeGear => &CHARACTER_WARDROBE_CATEGORY_IDS,
        }
    }

    pub(crate) fn contains(self, category: &str) -> bool {
        self.category_ids().contains(&category)
    }
}


pub(crate) const CHARACTER_CARD_MIN_W: f32 = 88.0;
pub(crate) const CHARACTER_CARD_H: f32 = 112.0;
pub(crate) const CHARACTER_CARD_GAP: f32 = 6.0;

pub(crate) fn character_grid_columns(rect: Rect) -> usize {
    ((rect.w + CHARACTER_CARD_GAP) / (CHARACTER_CARD_MIN_W + CHARACTER_CARD_GAP))
        .floor()
        .max(1.0) as usize
}

pub(crate) fn character_visible_cards(rect: Rect) -> usize {
    let columns = character_grid_columns(rect);
    let available = (rect.h - CHARACTER_LIST_TOP - CHARACTER_LIST_FOOTER).max(CHARACTER_CARD_H);
    let rows = ((available + CHARACTER_CARD_GAP) / (CHARACTER_CARD_H + CHARACTER_CARD_GAP))
        .floor()
        .max(1.0) as usize;
    columns * rows
}

pub(crate) fn character_card_rect(rect: Rect, visible_card: usize) -> Rect {
    let columns = character_grid_columns(rect);
    let column = visible_card % columns;
    let row = visible_card / columns;
    let width = (rect.w - CHARACTER_CARD_GAP * columns.saturating_sub(1) as f32) / columns as f32;
    Rect::new(
        rect.x + column as f32 * (width + CHARACTER_CARD_GAP),
        rect.y + CHARACTER_LIST_TOP + row as f32 * (CHARACTER_CARD_H + CHARACTER_CARD_GAP),
        width,
        CHARACTER_CARD_H,
    )
}

pub(crate) fn character_catalog_section_rect(rect: Rect, index: usize) -> Rect {
    let gap = 6.0;
    let width = (rect.w - gap) * 0.5;
    Rect::new(rect.x + index as f32 * (width + gap), rect.y, width, 28.0)
}

pub(crate) fn character_search_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + 34.0, rect.w, 30.0)
}

pub(crate) fn character_visible_rows(rect: Rect) -> usize {
    (((rect.h - CHARACTER_LIST_TOP - CHARACTER_LIST_FOOTER).max(CHARACTER_ROW_H)
        / CHARACTER_ROW_H)
        .floor() as usize)
        .clamp(1, CHARACTER_MAX_ROWS)
}

pub(crate) fn character_row_rect(rect: Rect, row: usize) -> Rect {
    Rect::new(
        rect.x,
        rect.y + CHARACTER_LIST_TOP + row as f32 * CHARACTER_ROW_H,
        rect.w,
        CHARACTER_ROW_H - 2.0,
    )
}

pub(crate) fn center_button_rect(rect: Rect, row: usize, column: usize, columns: usize) -> Rect {
    let gap = 6.0;
    let width = (rect.w - gap * (columns.saturating_sub(1)) as f32) / columns as f32;
    Rect::new(
        rect.x + column as f32 * (width + gap),
        rect.y + row as f32 * 32.0,
        width,
        27.0,
    )
}

pub(crate) fn character_category_menu_rect(rect: Rect) -> Rect {
    let anchor = center_button_rect(rect, 4, 1, 3);
    let rows = (UNIVERSAL_LPC_CHARACTER_BUILDER_CATEGORIES.len()
        + CHARACTER_CATEGORY_MENU_COLUMNS
        - 1)
        / CHARACTER_CATEGORY_MENU_COLUMNS;
    Rect::new(rect.x, anchor.y + anchor.h + 4.0, rect.w, 34.0 + rows as f32 * 27.0)
}

pub(crate) fn character_category_all_rect(rect: Rect) -> Rect {
    let menu = character_category_menu_rect(rect);
    Rect::new(menu.x + 6.0, menu.y + 6.0, menu.w - 12.0, 23.0)
}

pub(crate) fn character_category_option_rect(rect: Rect, index: usize) -> Rect {
    let menu = character_category_menu_rect(rect);
    let gap = 4.0;
    let columns = CHARACTER_CATEGORY_MENU_COLUMNS;
    let width = (menu.w - 12.0 - gap * (columns.saturating_sub(1)) as f32) / columns as f32;
    let row = index / columns;
    let column = index % columns;
    Rect::new(
        menu.x + 6.0 + column as f32 * (width + gap),
        menu.y + 34.0 + row as f32 * 27.0,
        width,
        23.0,
    )
}

pub(crate) fn character_wardrobe_layout(host: Rect) -> (Rect, Rect, Rect) {
    let body = Rect::new(
        host.x + 10.0,
        host.y + 8.0,
        (host.w - 20.0).max(1.0),
        (host.h - 16.0).max(1.0),
    );
    let gap = 10.0;
    let controls_w = if body.w >= 760.0 {
        390.0
    } else {
        (body.w * 0.48).max(280.0)
    };
    let controls = Rect::new(body.x, body.y, controls_w.min(body.w), body.h);
    let preview = Rect::new(
        controls.x + controls.w + gap,
        body.y,
        (body.w - controls.w - gap).max(1.0),
        body.h,
    );
    let content = Rect::new(
        controls.x + 10.0,
        controls.y + 54.0,
        (controls.w - 20.0).max(1.0),
        (controls.h - 64.0).max(1.0),
    );
    (controls, preview, content)
}

pub(crate) fn character_reload_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + rect.h - 34.0, rect.w, 30.0)
}

pub(crate) fn character_runtime_context_rect(rect: Rect) -> Rect {
    let footer = character_reload_rect(rect);
    Rect::new(rect.x, footer.y - 66.0, rect.w, 28.0)
}

pub(crate) fn character_variant_rect(rect: Rect, column: usize) -> Rect {
    let footer = character_reload_rect(rect);
    let gap = 4.0;
    let width = (rect.w - gap * 2.0) / 3.0;
    Rect::new(rect.x + column as f32 * (width + gap), footer.y - 32.0, width, 27.0)
}
