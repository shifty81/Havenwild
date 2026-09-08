pub(crate) struct CharacterPreviewTextures {
    pub(crate) layers: HashMap<String, Texture2D>,
}

impl CharacterPreviewTextures {
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
}

pub(crate) fn draw_character_preview(
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
            layer.slot == "preview/animation" && layer.asset.variant_id.as_deref() == Some("walk")
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
}

fn variant<'a>(appearance: &'a CharacterAppearance, slot: &str) -> Option<&'a str> {
    appearance
        .layers
        .iter()
        .find(|layer| layer.enabled && layer.slot == slot)
        .and_then(|layer| layer.asset.variant_id.as_deref())
}

fn draw_layered_starter_preview(area: Rect, appearance: &CharacterAppearance) {
    let center = area.x + area.w * 0.5;
    let scale = (area.h / 250.0).clamp(0.65, 1.45);
    let skin = layer_color(
        appearance,
        "body/base",
        Color::from_rgba(218, 164, 120, 255),
    );
    let shirt = layer_color(
        appearance,
        "clothing/torso",
        Color::from_rgba(67, 117, 82, 255),
    );
    let bottom = layer_color(
        appearance,
        "clothing/legs",
        Color::from_rgba(58, 62, 69, 255),
    );
    let feet = layer_color(
        appearance,
        "clothing/feet",
        Color::from_rgba(91, 60, 39, 255),
    );
    let top = area.y + 32.0 * scale;
    draw_circle(center, top + 22.0 * scale, 20.0 * scale, skin);
    draw_rectangle(
        center - 12.0 * scale,
        top + 39.0 * scale,
        24.0 * scale,
        13.0 * scale,
        skin,
    );
    draw_rectangle(
        center - 31.0 * scale,
        top + 50.0 * scale,
        62.0 * scale,
        70.0 * scale,
        shirt,
    );
    draw_rectangle(
        center - 43.0 * scale,
        top + 54.0 * scale,
        13.0 * scale,
        64.0 * scale,
        skin,
    );
    draw_rectangle(
        center + 30.0 * scale,
        top + 54.0 * scale,
        13.0 * scale,
        64.0 * scale,
        skin,
    );
    let skirt = appearance.layers.iter().any(|layer| {
        layer.slot == "clothing/legs" && layer.asset.variant_id.as_deref() == Some("starter_skirt")
    });
    if skirt {
        draw_triangle(
            vec2(center - 34.0 * scale, top + 116.0 * scale),
            vec2(center + 34.0 * scale, top + 116.0 * scale),
            vec2(center + 42.0 * scale, top + 177.0 * scale),
            bottom,
        );
        draw_triangle(
            vec2(center - 34.0 * scale, top + 116.0 * scale),
            vec2(center - 42.0 * scale, top + 177.0 * scale),
            vec2(center + 42.0 * scale, top + 177.0 * scale),
            bottom,
        );
        draw_rectangle(
            center - 25.0 * scale,
            top + 170.0 * scale,
            16.0 * scale,
            45.0 * scale,
            skin,
        );
        draw_rectangle(
            center + 9.0 * scale,
            top + 170.0 * scale,
            16.0 * scale,
            45.0 * scale,
            skin,
        );
    } else {
        draw_rectangle(
            center - 30.0 * scale,
            top + 116.0 * scale,
            26.0 * scale,
            91.0 * scale,
            bottom,
        );
        draw_rectangle(
            center + 4.0 * scale,
            top + 116.0 * scale,
            26.0 * scale,
            91.0 * scale,
            bottom,
        );
    }
    draw_rectangle(
        center - 33.0 * scale,
        top + 204.0 * scale,
        29.0 * scale,
        14.0 * scale,
        feet,
    );
    draw_rectangle(
        center + 4.0 * scale,
        top + 204.0 * scale,
        29.0 * scale,
        14.0 * scale,
        feet,
    );
}

