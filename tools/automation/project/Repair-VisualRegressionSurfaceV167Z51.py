#!/usr/bin/env python3
"""Restore the title/creator/object visual contracts after the LPC foundation merge.

The active Pass Z10 files live in the workstation baseline rather than every
cumulative payload, so this repair is deliberately narrow and idempotent. It
never replaces an entire frontend or footprint module.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REVISION = "167Z51-structural-character-preview-repair-v1"


def read(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(f"required source file missing: {relative}")
    return path.read_text(encoding="utf-8")


def write_if_changed(relative: str, original: str, updated: str, changes: list[str]) -> None:
    if updated == original:
        return
    (ROOT / relative).write_text(updated, encoding="utf-8", newline="\n")
    changes.append(relative)


def matching_brace(text: str, open_index: int) -> int:
    depth = 0
    quote: str | None = None
    escaped = False
    line_comment = False
    block_comment = 0
    index = open_index
    while index < len(text):
        char = text[index]
        nxt = text[index + 1] if index + 1 < len(text) else ""
        if line_comment:
            if char == "\n":
                line_comment = False
            index += 1
            continue
        if block_comment:
            if char == "/" and nxt == "*":
                block_comment += 1
                index += 2
                continue
            if char == "*" and nxt == "/":
                block_comment -= 1
                index += 2
                continue
            index += 1
            continue
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if char == "/" and nxt == "/":
            line_comment = True
            index += 2
            continue
        if char == "/" and nxt == "*":
            block_comment = 1
            index += 2
            continue
        if char == '"':
            quote = char
            index += 1
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    raise ValueError(f"unbalanced Rust block beginning at byte {open_index}")


def replace_function(text: str, name: str, replacement: str) -> tuple[str, bool]:
    match = re.search(
        rf"(?m)^[ \t]*(?:(?:pub(?:\([^\n)]*\))?\s+))?(?:async\s+)?fn\s+{re.escape(name)}\s*\(",
        text,
    )
    if not match:
        return text, False
    brace = text.find("{", match.end())
    if brace < 0:
        raise ValueError(f"function {name} has no body")
    close = matching_brace(text, brace)
    line_start = text.rfind("\n", 0, match.start()) + 1
    line_end = text.find("\n", close)
    if line_end < 0:
        line_end = len(text)
    else:
        line_end += 1
    return text[:line_start] + replacement.rstrip() + "\n" + text[line_end:], True


def repair_preview_draw(changes: list[str]) -> None:
    relative = "crates/haven_game/src/client_character_frontend_draw.rs"
    original = read(relative)
    updated = original

    impl_start = updated.find("impl CharacterPreviewTextures {")
    draw_start = updated.find("pub(crate) fn draw_character_preview(")
    if impl_start < 0 or draw_start < 0:
        raise ValueError("character preview implementation was not found")
    impl_brace = updated.find("{", impl_start)
    impl_end = matching_brace(updated, impl_brace)
    new_impl = r'''impl CharacterPreviewTextures {
    fn get(&self, id: &str) -> Option<&Texture2D> {
        self.layers.get(id)
    }

    fn body_family(appearance: &CharacterAppearance) -> &'static str {
        match variant(appearance, "body/base") {
            Some("female_neutral") => "female",
            Some("muscular_neutral") => "muscular",
            Some("pregnant_neutral") => "pregnant",
            Some("teen_neutral") => "teen",
            Some("child_neutral") => "child",
            _ => "male",
        }
    }

    fn compatible(&self, appearance: &CharacterAppearance, id: &str) -> Option<&Texture2D> {
        let family = Self::body_family(appearance);
        if family != "male" {
            let family_id = format!("{id}_{family}");
            if let Some(texture) = self.layers.get(&family_id) {
                return Some(texture);
            }
        }
        self.get(id)
    }

    fn body(&self, appearance: &CharacterAppearance) -> Option<&Texture2D> {
        let family = Self::body_family(appearance);
        self.get(&format!("body_{family}"))
            .or(self.get("body_male"))
    }

    fn variant_layer(&self, appearance: &CharacterAppearance, slot: &str) -> Option<&Texture2D> {
        variant(appearance, slot).and_then(|id| self.compatible(appearance, id))
    }

    fn feet(&self, appearance: &CharacterAppearance) -> Option<&Texture2D> {
        let id = match variant(appearance, "clothing/feet") {
            Some("starter_shoes") => "feet_shoes",
            Some("starter_sandals") => "feet_sandals",
            Some("none") | None => return None,
            _ => "feet_boots",
        };
        self.compatible(appearance, id)
    }

    fn legs(&self, appearance: &CharacterAppearance) -> Option<&Texture2D> {
        let id = match variant(appearance, "clothing/legs") {
            Some("starter_skirt") => "legs_skirt",
            Some("starter_shorts") => "legs_shorts",
            Some("starter_long_skirt") => "legs_long_skirt",
            _ => "legs_pants",
        };
        self.compatible(appearance, id)
    }

    fn torso(&self, appearance: &CharacterAppearance) -> Option<&Texture2D> {
        let id = match variant(appearance, "clothing/torso") {
            Some("starter_long_shirt") => "torso_long_shirt",
            Some("starter_tunic") => "torso_tunic",
            Some("starter_vest") => "torso_vest",
            Some("starter_apron") => "torso_apron",
            _ => "torso_tshirt",
        };
        self.compatible(appearance, id)
    }

    fn headwear(&self, appearance: &CharacterAppearance) -> Option<&Texture2D> {
        match variant(appearance, "headwear") {
            Some("headwear_hat") => self.compatible(appearance, "headwear_hat"),
            Some("headwear_hood") => self.compatible(appearance, "headwear_hood"),
            _ => None,
        }
    }
}'''
    updated = updated[:impl_start] + new_impl + updated[impl_end + 1 :]

    # Replace the whole preview function by Rust item boundaries. Earlier
    # passes attempted to identify one historical Rect::new expression and
    # failed after local source evolution. The function signature is the
    # stable API; replacing the complete implementation is deterministic and
    # independent of whitespace, formatting, temporary locals, or comments.
    preview_function = r'''pub(crate) fn draw_character_preview(
    card: Rect,
    appearance: &CharacterAppearance,
    preview_layers: Option<&CharacterPreviewTextures>,
) {
    let area = Rect::new(card.x + 18.0, card.y + 18.0, card.w - 36.0, card.h - 96.0);
    draw_rectangle(
        area.x,
        area.y,
        area.w,
        area.h,
        Color::from_rgba(20, 34, 43, 255),
    );

    if let Some(layers) = preview_layers {
        let facing_row = appearance
            .layers
            .iter()
            .find(|layer| layer.slot == "preview/facing")
            .and_then(|layer| layer.asset.variant_id.as_deref())
            .unwrap_or("south");
        let row = match facing_row {
            "north" => 0.0,
            "west" => 1.0,
            "east" => 3.0,
            _ => 2.0,
        };
        let walking = appearance.layers.iter().any(|layer| {
            layer.slot == "preview/animation"
                && layer.asset.variant_id.as_deref() == Some("walk")
        });
        let column = if walking {
            1.0 + ((get_time() * 8.0) as i32).rem_euclid(8) as f32
        } else {
            0.0
        };

        // Universal LPC runtime caches use 64x96 directional frames. A 64x64
        // source rectangle drops the lower third of every body and clothing
        // layer, which made the creator look undressed while gameplay worked.
        let frame = Rect::new(column * 64.0, row * 96.0, 64.0, 96.0);
        let preview_h = area.h.min(area.w * 1.5).min(288.0);
        let preview_w = preview_h * (2.0 / 3.0);
        let x = area.x + (area.w - preview_w) * 0.5;
        let y = area.y + (area.h - preview_h) * 0.5;
        let params = || DrawTextureParams {
            source: Some(frame),
            dest_size: Some(vec2(preview_w, preview_h)),
            ..Default::default()
        };

        if let Some(texture) = layers.body(appearance) {
            draw_texture_ex(
                texture,
                x,
                y,
                layer_color(appearance, "body/base", WHITE),
                params(),
            );
        }
        if let Some(texture) = layers.compatible(appearance, "eyes") {
            draw_texture_ex(
                texture,
                x,
                y,
                layer_color(appearance, "face/eyes", WHITE),
                params(),
            );
        }
        if let Some(texture) = layers.variant_layer(appearance, "face/eyebrows") {
            draw_texture_ex(
                texture,
                x,
                y,
                layer_color(appearance, "hair", WHITE),
                params(),
            );
        }
        if let Some(texture) = layers.legs(appearance) {
            draw_texture_ex(
                texture,
                x,
                y,
                layer_color(appearance, "clothing/legs", WHITE),
                params(),
            );
        }
        if let Some(texture) = layers.feet(appearance) {
            draw_texture_ex(
                texture,
                x,
                y,
                layer_color(appearance, "clothing/feet", WHITE),
                params(),
            );
        }
        if let Some(texture) = layers.torso(appearance) {
            draw_texture_ex(
                texture,
                x,
                y,
                layer_color(appearance, "clothing/torso", WHITE),
                params(),
            );
        }
        if let Some(texture) = layers.variant_layer(appearance, "face/facial_hair") {
            draw_texture_ex(
                texture,
                x,
                y,
                layer_color(appearance, "hair", WHITE),
                params(),
            );
        }
        let hood_occludes_hair = variant(appearance, "headwear") == Some("headwear_hood");
        if !hood_occludes_hair {
            if let Some(texture) = layers.variant_layer(appearance, "hair") {
                draw_texture_ex(
                    texture,
                    x,
                    y,
                    layer_color(appearance, "hair", WHITE),
                    params(),
                );
            }
        }
        if let Some(texture) = layers.headwear(appearance) {
            draw_texture_ex(texture, x, y, WHITE, params());
        }
    } else {
        draw_layered_starter_preview(area, appearance);
        draw_text(
            "Modular LPC layers unavailable",
            area.x + 8.0,
            area.y + 20.0,
            15.0,
            Color::from_rgba(245, 168, 82, 255),
        );
    }

    let layer_count = appearance
        .layers
        .iter()
        .filter(|layer| layer.enabled && !layer.slot.starts_with("preview/"))
        .count();
    let diagnostics = appearance_diagnostics(appearance);
    let resolved = diagnostics
        .iter()
        .filter(|line| line.ends_with("resolved"))
        .count();
    draw_text(
        &format!(
            "Modular LPC preview • {layer_count} active • {resolved}/{} core resolved",
            diagnostics.len()
        ),
        area.x + 8.0,
        area.y + area.h - 8.0,
        15.0,
        LIGHTGRAY,
    );
    if let Some(note) = StarterCreatorSelection::from_appearance(appearance)
        .compatibility_notes()
        .first()
    {
        draw_text(
            note,
            area.x + 8.0,
            area.y + area.h - 28.0,
            14.0,
            Color::from_rgba(245, 198, 112, 255),
        );
    }
}'''
    updated, replaced = replace_function(updated, "draw_character_preview", preview_function)
    if not replaced:
        raise ValueError("draw_character_preview function was not found")

    title_helper = r'''

// Pass 167Z49: the production title screen is a structured game portal, not
// the temporary three-button fallback that replaced the completed frontend.
pub(crate) fn draw_main_menu_shell(status: &str) {
    draw_title("HAVENWILD");
    draw_text_centered(
        "A living open world of exploration, settlement, craft, and family",
        screen_width() * 0.5,
        112.0,
        19.0,
        Color::from_rgba(221, 213, 193, 255),
    );

    let side_w = ((screen_width() - 760.0) * 0.5).clamp(238.0, 330.0);
    let left = Rect::new(28.0, 154.0, side_w, 382.0);
    let right = Rect::new(screen_width() - side_w - 28.0, 154.0, side_w, 382.0);
    let center = Rect::new(screen_width() * 0.5 - 188.0, 212.0, 376.0, 302.0);

    draw_section_panel(left, "YOUR HAVEN");
    for (index, line) in [
        "Explore a seed-built open world",
        "Build homes, farms, and businesses",
        "Meet, befriend, and marry villagers",
        "Raise a family or play together",
        "Travel between persistent worlds",
    ]
    .iter()
    .enumerate()
    {
        draw_circle(
            left.x + 24.0,
            left.y + 63.0 + index as f32 * 49.0,
            3.5,
            Color::from_rgba(185, 139, 73, 255),
        );
        draw_text(
            line,
            left.x + 36.0,
            left.y + 69.0 + index as f32 * 49.0,
            15.0,
            Color::from_rgba(225, 219, 199, 255),
        );
    }
    draw_text(
        "Characters remain yours across compatible worlds and servers.",
        left.x + 16.0,
        left.y + left.h - 34.0,
        13.0,
        Color::from_rgba(164, 181, 174, 255),
    );

    draw_panel(center, true);
    draw_text_centered(
        "BEGIN YOUR STORY",
        center.x + center.w * 0.5,
        center.y + 35.0,
        18.0,
        Color::from_rgba(246, 225, 177, 255),
    );

    draw_section_panel(right, "NEWS & UPDATES");
    draw_text(
        "LPC FOUNDATION ONLINE",
        right.x + 16.0,
        right.y + 66.0,
        16.0,
        Color::from_rgba(194, 222, 156, 255),
    );
    draw_text(
        "Terrain, characters, clothing,",
        right.x + 16.0,
        right.y + 94.0,
        14.0,
        Color::from_rgba(219, 213, 195, 255),
    );
    draw_text(
        "tools, structures, and nature are",
        right.x + 16.0,
        right.y + 116.0,
        14.0,
        Color::from_rgba(219, 213, 195, 255),
    );
    draw_text(
        "routed through the pinned LPC base.",
        right.x + 16.0,
        right.y + 138.0,
        14.0,
        Color::from_rgba(219, 213, 195, 255),
    );
    draw_line(
        right.x + 16.0,
        right.y + 164.0,
        right.x + right.w - 16.0,
        right.y + 164.0,
        1.0,
        Color::from_rgba(104, 83, 57, 255),
    );
    draw_text(
        "WORLD CREATION",
        right.x + 16.0,
        right.y + 194.0,
        16.0,
        Color::from_rgba(194, 222, 156, 255),
    );
    draw_text(
        "Land, water, biomes, settlements,",
        right.x + 16.0,
        right.y + 222.0,
        14.0,
        Color::from_rgba(219, 213, 195, 255),
    );
    draw_text(
        "housing, and family rules are now",
        right.x + 16.0,
        right.y + 244.0,
        14.0,
        Color::from_rgba(219, 213, 195, 255),
    );
    draw_text(
        "part of the world setup contract.",
        right.x + 16.0,
        right.y + 266.0,
        14.0,
        Color::from_rgba(219, 213, 195, 255),
    );
    draw_text(
        "COMMUNITY / DISCORD",
        right.x + 16.0,
        right.y + right.h - 42.0,
        13.0,
        Color::from_rgba(164, 181, 174, 255),
    );

    draw_text_centered(
        status,
        screen_width() * 0.5,
        screen_height() - 30.0,
        14.0,
        Color::from_rgba(185, 191, 184, 255),
    );
}
'''
    if "pub(crate) fn draw_main_menu_shell" not in updated:
        insert_at = updated.find("pub(crate) fn main_new_rect")
        if insert_at < 0:
            updated += title_helper
        else:
            updated = updated[:insert_at] + title_helper + "\n" + updated[insert_at:]

    write_if_changed(relative, original, updated, changes)

def repair_preview_loader_and_title_call(changes: list[str]) -> None:
    relative = "crates/haven_game/src/client_frontend.rs"
    original = read(relative)
    updated = original

    import_match = re.search(
        r"use crate::client_character_frontend_draw::\{(?P<body>.*?)\};",
        updated,
        re.S,
    )
    if not import_match:
        raise ValueError("client_character_frontend_draw import group was not found")
    import_body = import_match.group("body")
    if "draw_main_menu_shell" not in import_body:
        if "draw_character_preview" not in import_body:
            raise ValueError("draw_character_preview import anchor was not found")
        import_body = import_body.replace(
            "draw_character_preview",
            "draw_character_preview, draw_main_menu_shell",
            1,
        )
        updated = (
            updated[: import_match.start("body")]
            + import_body
            + updated[import_match.end("body") :]
        )

    old_loop = '''    for id in ids {
        let path = format!("{CHARACTER_PREVIEW_LAYER_ROOT}/havenwild_player_{id}_walk_64.png");
        if let Ok(texture) = load_texture(&runtime_path(&path)).await {
            layers.insert(id.to_string(), texture);
        }
    }'''
    new_loop = '''    for id in ids {
        let path = format!("{CHARACTER_PREVIEW_LAYER_ROOT}/havenwild_player_{id}_walk_64.png");
        if let Ok(texture) = load_texture(&runtime_path(&path)).await {
            layers.insert(id.to_string(), texture);
        }
        // Runtime caches are body-specific. Load female-compatible layers so
        // the creator resolves the same clothing geometry as live gameplay.
        let female_id = format!("{id}_female");
        let female_path = format!(
            "{CHARACTER_PREVIEW_LAYER_ROOT}/havenwild_player_{female_id}_walk_64.png"
        );
        if let Ok(texture) = load_texture(&runtime_path(&female_path)).await {
            layers.insert(female_id, texture);
        }
    }'''
    loader_pattern = re.compile(
        r"for\s+id\s+in\s+ids\s*\{\s*"
        r"let\s+path\s*=\s*format!\(\s*"
        r"\"\{CHARACTER_PREVIEW_LAYER_ROOT\}/havenwild_player_\{id\}_walk_64\.png\"\s*\)\s*;\s*"
        r"if\s+let\s+Ok\(texture\)\s*=\s*load_texture\(&runtime_path\(&path\)\)\.await\s*\{\s*"
        r"layers\.insert\(id\.to_string\(\),\s*texture\)\s*;\s*\}\s*\}",
        re.S,
    )
    if "let female_id = format!" not in updated:
        updated, count = loader_pattern.subn(new_loop, updated, count=1)
        if count != 1:
            raise ValueError("character preview loader loop was not recognized")

    replacement = '''    fn draw_main_menu(&self) {
        draw_main_menu_shell(&self.status);
        draw_button(main_new_rect(), "New Game", true);
        draw_button(main_load_rect(), "Load Game", true);
        draw_button(main_quit_rect(), "Quit", false);
    }'''
    updated, replaced = replace_function(updated, "draw_main_menu", replacement)
    if not replaced:
        raise ValueError("ClientFrontend::draw_main_menu was not found")

    write_if_changed(relative, original, updated, changes)


def repair_object_footprints(changes: list[str]) -> None:
    relative = "crates/haven_core/src/foundation/object_footprint.rs"
    original = read(relative)
    updated = original
    if re.search(
        r"ObjectKind::Bush\s*=>\s*ObjectFootprint\s*\{.*?blocks_movement:\s*true",
        updated,
        re.S,
    ) is None:
        pattern = re.compile(
            r"ObjectKind::Bush\s*\|\s*ObjectKind::Mushroom\s*\|\s*"
            r"ObjectKind::Herb\s*\|\s*ObjectKind::Lamp\s*\|\s*"
            r"ObjectKind::Sign\s*=>\s*ObjectFootprint\s*\{.*?"
            r"\.\.ObjectFootprint::single_tile\(\)\s*\}\s*,",
            re.S,
        )
        replacement = """ObjectKind::Bush => ObjectFootprint {
                // Bushes are full one-tile obstacles. Their prior nonblocking
                // footprint let the player walk beneath dense bush artwork.
                blocks_movement: true,
                ..ObjectFootprint::single_tile()
            },
            ObjectKind::Mushroom | ObjectKind::Herb | ObjectKind::Lamp | ObjectKind::Sign => {
                ObjectFootprint {
                    blocks_movement: false,
                    ..ObjectFootprint::single_tile()
                }
            },"""
        updated, count = pattern.subn(replacement, updated, count=1)
        if count != 1:
            raise ValueError("combined bush/forage footprint branch was not recognized")
    write_if_changed(relative, original, updated, changes)


def validate_surface() -> None:
    preview = read("crates/haven_game/src/client_character_frontend_draw.rs")
    frontend = read("crates/haven_game/src/client_frontend.rs")
    footprint = read("crates/haven_core/src/foundation/object_footprint.rs")
    object_draw = read("crates/haven_game/src/runtime_object_draw.rs")
    runtime_draw = read("crates/haven_game/src/runtime_draw.rs")
    terrain_pass = read("crates/haven_game/src/runtime_terrain_pass.rs")
    promoter = read("tools/automation/assets/Promote-LpcRuntimeAssets.py")
    checks = {
        "creator uses 64x96 source cells": "row * 96.0" in preview and "64.0, 96.0" in preview,
        "creator has body-compatible layer resolver": "fn compatible(" in preview and '"{id}_female"' in frontend,
        "structured title screen is active": "draw_main_menu_shell(&self.status);" in frontend and "NEWS & UPDATES" in preview,
        "temporary title fallback is gone": 'draw_text_centered(\n            "Persistent characters travel between worlds and servers"' not in frontend,
        "bush collision blocks movement": re.search(r"ObjectKind::Bush\s*=>\s*ObjectFootprint\s*\{.*?blocks_movement:\s*true", footprint, re.S) is not None,
        "object art anchors to collision bottom center": "fn object_foot_world" in object_draw and "object.collision_rect()" in object_draw,
        "floor plants render below actors": "ObjectKind::Mushroom | ObjectKind::Herb" in runtime_draw and "continue;" in runtime_draw,
        "nature sheets use authored grid cells": "def grid_alpha_cells" in promoter and "lpc_32x32_grid_cell_native_scale_large_cell" in promoter,
        "ocean and freshwater render identities remain distinct": "TileKind::OceanDeep => TileKind::OceanDeep" in terrain_pass and "TileKind::OceanShallow => TileKind::OceanShallow" in terrain_pass,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise RuntimeError("visual regression repair incomplete: " + "; ".join(failed))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    changes: list[str] = []
    if not args.validate_only:
        repair_preview_draw(changes)
        repair_preview_loader_and_title_call(changes)
        repair_object_footprints(changes)
    validate_surface()
    if changes:
        print(f"Applied {REVISION} to {len(changes)} source file(s):")
        for relative in changes:
            print(f"  - {relative}")
    else:
        print(f"Visual regression surface already matches {REVISION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
