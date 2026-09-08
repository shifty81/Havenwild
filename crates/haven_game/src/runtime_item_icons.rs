use std::collections::HashMap;

use macroquad::prelude::*;

pub(crate) fn draw_item_icon(
    atlas: Option<&Texture2D>,
    rects: &HashMap<String, [f32; 4]>,
    item_id: &str,
    destination: Rect,
    tint: Color,
) -> bool {
    let (Some(atlas), Some(source)) = (atlas, rects.get(item_id)) else {
        return false;
    };
    let inset = (destination.w.min(destination.h) * 0.08).max(2.0);
    let dest = Rect::new(
        destination.x + inset,
        destination.y + inset,
        (destination.w - inset * 2.0).max(1.0),
        (destination.h - inset * 2.0).max(1.0),
    );
    draw_texture_ex(
        atlas,
        dest.x,
        dest.y,
        tint,
        DrawTextureParams {
            dest_size: Some(vec2(dest.w, dest.h)),
            source: Some(Rect::new(source[0], source[1], source[2], source[3])),
            ..Default::default()
        },
    );
    true
}

pub(crate) fn has_item_icon(rects: &HashMap<String, [f32; 4]>, item_id: &str) -> bool {
    rects.contains_key(item_id)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn icon_lookup_is_item_identity_based() {
        let mut rects = HashMap::new();
        rects.insert("item.ulpc.tools_tool_axe".to_string(), [0.0, 0.0, 64.0, 64.0]);
        assert!(has_item_icon(&rects, "item.ulpc.tools_tool_axe"));
        assert!(!has_item_icon(&rects, "axe_placeholder"));
    }
}
