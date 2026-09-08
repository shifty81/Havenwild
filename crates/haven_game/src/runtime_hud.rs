use super::*;

const HUD_WOOD_DARK: Color = Color { r: 0.18, g: 0.10, b: 0.045, a: 0.96 };
const HUD_WOOD: Color = Color { r: 0.34, g: 0.18, b: 0.07, a: 0.97 };
const HUD_BRASS_DARK: Color = Color { r: 0.47, g: 0.27, b: 0.055, a: 1.0 };
const HUD_BRASS: Color = Color { r: 0.88, g: 0.62, b: 0.15, a: 1.0 };
const HUD_GOLD: Color = Color { r: 1.0, g: 0.82, b: 0.30, a: 1.0 };
const HUD_INSET: Color = Color { r: 0.035, g: 0.070, b: 0.065, a: 0.94 };

impl Game {
    /// Player-facing HUD has no full-width bottom dock. It is composed from
    /// independent anchored surfaces: player card top-left, minimap top-right,
    /// and player-authored hotbar bottom-center.
    pub(super) fn draw_player_hud_frame(&self) {
        self.draw_player_card();
        self.draw_top_right_minimap();
        self.draw_player_hotbar();
    }

    fn draw_player_card(&self) {
        let rect = Rect::new(14.0, 14.0, 330.0_f32.min(screen_width() * 0.42), 128.0);
        draw_havenwild_panel_frame(rect);

        let portrait = Rect::new(rect.x + 12.0, rect.y + 12.0, 78.0, 92.0);
        draw_rectangle(portrait.x, portrait.y, portrait.w, portrait.h, HUD_INSET);
        draw_havenwild_slot_frame(portrait, false);
        if let Some(appearance) = self.runtime_character_appearance.as_ref() {
            let portrait_frame = character_runtime_compositor::RuntimeCharacterAppearance::frame(
                vec2(0.0, 1.0),
                character_runtime_compositor::CharacterAnimationKind::Idle,
                0.0,
                None,
                0.0,
            );
            appearance.draw_portrait(portrait, portrait_frame);
        }

        let bars_x = portrait.x + portrait.w + 14.0;
        let bars_w = (rect.x + rect.w - 13.0 - bars_x).max(92.0);
        let health_ratio = if self.character_vitals.health_max <= f32::EPSILON {
            0.0
        } else {
            (self.character_vitals.health / self.character_vitals.health_max).clamp(0.0, 1.0)
        };
        let stamina = self.character_stamina_current().max(0.0);
        let stamina_max = self.character_vitals.stamina_current_max.max(1.0);
        let stamina_ratio = (stamina / stamina_max).clamp(0.0, 1.0);
        let hunger_ratio = (self.character_vitals.hunger / 100.0).clamp(0.0, 1.0);
        let thirst_ratio = (self.character_vitals.thirst / 100.0).clamp(0.0, 1.0);

        draw_vital_bar(
            Rect::new(bars_x, rect.y + 18.0, bars_w, 20.0),
            "Health",
            health_ratio,
            Color::from_rgba(177, 59, 48, 255),
        );
        draw_vital_bar(
            Rect::new(bars_x, rect.y + 44.0, bars_w, 20.0),
            "Stamina",
            stamina_ratio,
            Color::from_rgba(210, 173, 65, 255),
        );

        // Secondary survival needs stay compact instead of competing with the
        // core combat/locomotion bars. The card has room to unfold additional
        // needs later without changing the anchored HUD contract.
        draw_vital_bar(
            Rect::new(bars_x, rect.y + 72.0, bars_w * 0.49, 14.0),
            "Hunger",
            hunger_ratio,
            Color::from_rgba(173, 124, 63, 255),
        );
        draw_vital_bar(
            Rect::new(bars_x + bars_w * 0.51, rect.y + 72.0, bars_w * 0.49, 14.0),
            "Thirst",
            thirst_ratio,
            Color::from_rgba(73, 151, 180, 255),
        );

        if self.character_vitals.fatigue_capacity_loss > 0.25 {
            let text = format!(
                "Fatigue -{:.0}% max stamina",
                100.0 * self.character_vitals.fatigue_capacity_loss
                    / self.character_vitals.stamina_base_max.max(1.0)
            );
            draw_text(
                &text,
                bars_x,
                rect.y + 108.0,
                12.0,
                Color::from_rgba(220, 207, 169, 255),
            );
        }
    }

    pub(super) fn draw_player_hotbar(&self) {
        let slots = gameplay_hotbar::hotbar_slot_rects(screen_width(), screen_height());
        let Some((_, first)) = slots.first().copied() else { return; };
        let Some((_, last)) = slots.last().copied() else { return; };
        // Frame padding is bounded from the same canonical slot geometry so
        // shrinking the player-authored strip cannot detach its decorative chrome.
        let frame_pad_x = (first.w * 0.24).clamp(8.0, 12.0);
        let frame_pad_y = (first.h * 0.20).clamp(6.0, 10.0);
        let frame = Rect::new(
            first.x - frame_pad_x,
            first.y - frame_pad_y,
            last.x + last.w - first.x + frame_pad_x * 2.0,
            first.h + frame_pad_y * 2.0,
        );
        draw_havenwild_panel_frame(frame);
        self.draw_hotbar_main_hand_context(frame);
        self.draw_runtime_progress(frame);

        for (slot, rect) in slots {
            let selected = slot == self.selected_gameplay_tool;
            draw_havenwild_slot_frame(rect, selected);
            if let Some(binding) = self.hotbar_binding(slot) {
                let available = self.hotbar_binding_is_available(&binding.item_id);
                if !self.draw_hotbar_item_icon(&binding.item_id, rect) {
                    let marker = compact_item_marker(&binding.display_name);
                    let m = measure_text(&marker, None, 15, 1.0);
                    draw_text(
                        &marker,
                        rect.x + (rect.w - m.width) * 0.5,
                        rect.y + rect.h * 0.58,
                        15.0,
                        if available {
                            Color::from_rgba(238, 226, 191, 255)
                        } else {
                            Color::from_rgba(146, 112, 104, 255)
                        },
                    );
                }
                if let Some(quantity) = self.hotbar_item_quantity(&binding.item_id) {
                    if quantity > 1 {
                        let q = quantity.to_string();
                        let m = measure_text(&q, None, 12, 1.0);
                        draw_text(&q, rect.x + rect.w - m.width - 4.0, rect.y + rect.h - 4.0, 12.0, WHITE);
                    }
                }
            }

            let number = if slot == 9 { "0".to_string() } else { (slot + 1).to_string() };
            draw_text(
                &number,
                rect.x + 4.0,
                rect.y + 13.0,
                12.0,
                Color::from_rgba(245, 215, 133, 255),
            );
        }
    }

    fn draw_hotbar_item_icon(&self, item_id: &str, rect: Rect) -> bool {
        // AB41 item-art authority is shared with Inventory. The hotbar never
        // invents a tool glyph when a canonical item-art entry exists.
        if !crate::runtime_item_icons::has_item_icon(&self.item_icon_rects, item_id) {
            return false;
        }
        let (Some(atlas), Some(source)) = (
            self.item_icon_atlas.as_ref(),
            self.item_icon_rects.get(item_id),
        ) else {
            return false;
        };
        let pad = 7.0;
        draw_texture_ex(
            atlas,
            rect.x + pad,
            rect.y + pad,
            WHITE,
            DrawTextureParams {
                dest_size: Some(vec2(rect.w - pad * 2.0, rect.h - pad * 2.0)),
                source: Some(Rect::new(source[0], source[1], source[2], source[3])),
                ..Default::default()
            },
        );
        true
    }


    fn draw_hotbar_main_hand_context(&self, frame: Rect) {
        // Equipment remains the gameplay authority. The hotbar is only a player-
        // authored shortcut surface, so this read reports the real equipped item.
        let Some(main_hand) = self.player_inventory_ui.equipped_items().get("main_hand") else {
            return;
        };
        let label = format!("Main Hand · {}", main_hand.display_name);
        let metrics = measure_text(&label, None, 13, 1.0);
        let icon_size = 28.0;
        let icon_gap = 5.0;
        let has_icon = crate::runtime_item_icons::has_item_icon(&self.item_icon_rects, &main_hand.item_id)
            && self.item_icon_atlas.is_some();
        let total_w = metrics.width + if has_icon { icon_size + icon_gap } else { 0.0 };
        let x = frame.x + (frame.w - total_w) * 0.5;
        if has_icon {
            let icon_rect = Rect::new(x, frame.y - icon_size - 7.0, icon_size, icon_size);
            let _ = crate::runtime_item_icons::draw_item_icon(
                self.item_icon_atlas.as_ref(),
                &self.item_icon_rects,
                &main_hand.item_id,
                icon_rect,
                WHITE,
            );
        }
        draw_text(
            &label,
            x + if has_icon { icon_size + icon_gap } else { 0.0 },
            frame.y - 13.0,
            13.0,
            Color::from_rgba(232, 215, 166, 255),
        );
    }

    fn draw_runtime_progress(&self, frame: Rect) {
        let character = self.player_character_state();
        if character.action.is_none() || character.action_duration <= f32::EPSILON {
            return;
        }

        // Tool/contact animation progress is presentation-only. The canonical
        // gameplay commit still occurs in gameplay_tool_runtime at the authored
        // LPC contact point; this bar merely exposes that timing to the player.
        let progress = character.action_progress().clamp(0.0, 1.0);
        let width = (frame.w * 0.46).clamp(150.0, 300.0);
        let bar = Rect::new(frame.x + (frame.w - width) * 0.5, frame.y - 8.0, width, 5.0);
        draw_rectangle(bar.x, bar.y, bar.w, bar.h, HUD_INSET);
        draw_rectangle(bar.x, bar.y, bar.w * progress, bar.h, HUD_GOLD);
        draw_rectangle_lines(bar.x, bar.y, bar.w, bar.h, 1.0, HUD_BRASS_DARK);
    }

    fn hotbar_item_quantity(&self, item_id: &str) -> Option<u32> {
        let inventory = self
            .player_inventory_ui
            .slots
            .iter()
            .flatten()
            .filter(|stack| stack.item_id == item_id)
            .map(|stack| u32::from(stack.quantity))
            .sum::<u32>();
        let equipped = self
            .player_inventory_ui
            .equipped_items()
            .values()
            .filter(|stack| stack.item_id == item_id)
            .map(|stack| u32::from(stack.quantity))
            .sum::<u32>();
        let total = inventory + equipped;
        (total > 0).then_some(total)
    }

    fn draw_top_right_minimap(&self) {
        let size = 286.0_f32.min(screen_width() * 0.22).max(224.0);
        let frame = Rect::new(screen_width() - size - 10.0, 8.0, size, size);

        // The actual world map is circular before the decorative frame is drawn.
        // AC2's minimap renderer rejects cells/markers outside this circle.
        let map = Rect::new(
            frame.x + size * 0.175,
            frame.y + size * 0.145,
            size * 0.69,
            size * 0.69,
        );
        self.draw_player_centered_minimap(map);

        // The clock housing is part of the production frame, but its internals
        // remain live code: rotating day/night dial + authoritative game time.
        let clock_center = vec2(frame.x + size * 0.165, frame.y + size * 0.755);
        let clock_radius = size * 0.108;
        draw_day_night_clock(clock_center, clock_radius, self.day_clock);

        draw_hud_frame_texture(self.hud_minimap_frame.as_ref(), frame);
    }
}

/// Shared code-generated border. Player card and hotbar consume it now; chat,
/// dialogue, inventory, crafting, and generic panels can use the exact same
/// scalable visual grammar without baking a unique frame texture per window.
pub(crate) fn draw_havenwild_panel_frame(rect: Rect) {
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, HUD_WOOD_DARK);
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 4.0, HUD_BRASS_DARK);
    draw_rectangle_lines(rect.x + 3.0, rect.y + 3.0, rect.w - 6.0, rect.h - 6.0, 2.0, HUD_GOLD);
    draw_rectangle_lines(rect.x + 7.0, rect.y + 7.0, rect.w - 14.0, rect.h - 14.0, 2.0, HUD_WOOD);
    for &(x, y) in &[
        (rect.x + 7.0, rect.y + 7.0),
        (rect.x + rect.w - 7.0, rect.y + 7.0),
        (rect.x + 7.0, rect.y + rect.h - 7.0),
        (rect.x + rect.w - 7.0, rect.y + rect.h - 7.0),
    ] {
        draw_poly(x, y, 4, 6.0, 45.0, HUD_GOLD);
        draw_poly_lines(x, y, 4, 6.0, 45.0, 1.0, HUD_BRASS_DARK);
    }
}

fn draw_havenwild_slot_frame(rect: Rect, selected: bool) {
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, HUD_INSET);
    draw_rectangle_lines(
        rect.x,
        rect.y,
        rect.w,
        rect.h,
        if selected { 3.0 } else { 1.5 },
        if selected { HUD_GOLD } else { HUD_BRASS },
    );
    draw_rectangle_lines(rect.x + 3.0, rect.y + 3.0, rect.w - 6.0, rect.h - 6.0, 1.0, HUD_WOOD);
}

fn draw_vital_bar(rect: Rect, label: &str, ratio: f32, fill: Color) {
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, HUD_INSET);
    draw_rectangle(
        rect.x + 2.0,
        rect.y + 2.0,
        (rect.w - 4.0) * ratio.clamp(0.0, 1.0),
        rect.h - 4.0,
        fill,
    );
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.5, HUD_BRASS);
    if rect.h >= 18.0 {
        draw_text(label, rect.x + 6.0, rect.y + 14.0, 12.0, Color::from_rgba(247, 235, 199, 255));
    }
}

fn draw_day_night_clock(center: Vec2, radius: f32, hour: f32) {
    let rotation = (hour.rem_euclid(24.0) / 24.0) * std::f32::consts::TAU;
    draw_circle(center.x, center.y, radius + 2.0, HUD_BRASS_DARK);
    draw_half_disc(
        center,
        radius,
        rotation,
        rotation + std::f32::consts::PI,
        Color::from_rgba(66, 139, 186, 255),
    );
    draw_half_disc(
        center,
        radius,
        rotation + std::f32::consts::PI,
        rotation + std::f32::consts::TAU,
        Color::from_rgba(14, 31, 64, 255),
    );

    let sun_angle = rotation + std::f32::consts::FRAC_PI_2;
    let moon_angle = sun_angle + std::f32::consts::PI;
    let orbit = radius * 0.52;
    let sun = center + vec2(sun_angle.cos(), sun_angle.sin()) * orbit;
    let moon = center + vec2(moon_angle.cos(), moon_angle.sin()) * orbit;
    draw_circle(sun.x, sun.y, radius * 0.16, Color::from_rgba(255, 210, 73, 255));
    for index in 0..8 {
        let a = index as f32 / 8.0 * std::f32::consts::TAU;
        let inner = sun + vec2(a.cos(), a.sin()) * radius * 0.22;
        let outer = sun + vec2(a.cos(), a.sin()) * radius * 0.30;
        draw_line(inner.x, inner.y, outer.x, outer.y, 1.5, HUD_GOLD);
    }
    draw_circle(moon.x, moon.y, radius * 0.17, Color::from_rgba(238, 219, 148, 255));
    draw_circle(
        moon.x + radius * 0.075,
        moon.y - radius * 0.025,
        radius * 0.15,
        Color::from_rgba(14, 31, 64, 255),
    );

    let label = clock_label(hour);
    let metrics = measure_text(&label, None, 12, 1.0);
    let label_y = center.y + radius * 0.72;
    draw_rectangle(
        center.x - metrics.width * 0.5 - 4.0,
        label_y - 11.0,
        metrics.width + 8.0,
        14.0,
        Color::from_rgba(7, 15, 22, 190),
    );
    draw_text(
        &label,
        center.x - metrics.width * 0.5,
        label_y,
        12.0,
        Color::from_rgba(255, 222, 123, 255),
    );
}

fn draw_half_disc(center: Vec2, radius: f32, start: f32, end: f32, color: Color) {
    const SEGMENTS: usize = 24;
    let step = (end - start) / SEGMENTS as f32;
    for index in 0..SEGMENTS {
        let a0 = start + index as f32 * step;
        let a1 = a0 + step;
        draw_triangle(
            center,
            center + vec2(a0.cos(), a0.sin()) * radius,
            center + vec2(a1.cos(), a1.sin()) * radius,
            color,
        );
    }
}

fn compact_item_marker(label: &str) -> String {
    let words = label.split_whitespace().collect::<Vec<_>>();
    if words.len() > 1 {
        words
            .iter()
            .filter_map(|word| word.chars().next())
            .take(3)
            .collect::<String>()
            .to_uppercase()
    } else {
        label.chars().take(4).collect::<String>()
    }
}

fn draw_hud_frame_texture(texture: Option<&Texture2D>, rect: Rect) {
    let Some(texture) = texture else { return; };
    draw_texture_ex(
        texture,
        rect.x,
        rect.y,
        WHITE,
        DrawTextureParams {
            dest_size: Some(vec2(rect.w, rect.h)),
            ..Default::default()
        },
    );
}
