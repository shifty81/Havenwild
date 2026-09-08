use super::*;
use haven_world::{
    inspect_terrain_transition_rules, TerrainTransitionRuleHit, TransitionRulePhase,
};

impl Game {
    pub(super) fn draw_transition_rule_inspector_overlay(&self) {
        if !self.dev_mode || !self.show_transition_rule_inspector {
            return;
        }

        let map = &self.world.active().map;
        let (tx, ty) = self.selected_cell;
        let Some(inspection) = inspect_terrain_transition_rules(map, tx, ty) else {
            return;
        };

        let panel_w = 470.0;
        let panel_h = 284.0;
        let x = screen_width() - panel_w - 18.0;
        let y = screen_height() - panel_h - 24.0;
        draw_rectangle(x, y, panel_w, panel_h, Color::from_rgba(22, 20, 18, 232));
        draw_rectangle_lines(
            x,
            y,
            panel_w,
            panel_h,
            2.0,
            Color::from_rgba(224, 190, 112, 230),
        );
        draw_text(
            "Transition Rule Inspector",
            x + 14.0,
            y + 25.0,
            18.0,
            Color::from_rgba(255, 225, 151, 255),
        );
        draw_text(
            &format!(
                "cell {},{} | center {} | {}",
                inspection.x,
                inspection.y,
                inspection.center.code(),
                inspection.summary_line()
            ),
            x + 14.0,
            y + 49.0,
            13.0,
            Color::from_rgba(235, 235, 215, 255),
        );
        draw_text(
            &inspection.manifest_status,
            x + 14.0,
            y + 68.0,
            12.0,
            Color::from_rgba(196, 215, 221, 255),
        );

        let mut row_y = y + 94.0;
        if inspection.hits.is_empty() {
            draw_text(
                "No adjacent family transition is active for this tile.",
                x + 14.0,
                row_y,
                13.0,
                Color::from_rgba(205, 205, 190, 255),
            );
        } else {
            draw_text(
                "phase/dir     neighbor       material        atlas group       rule / priority",
                x + 14.0,
                row_y,
                12.0,
                Color::from_rgba(168, 190, 197, 255),
            );
            row_y += 18.0;
            for hit in inspection.hits.iter().take(7) {
                draw_transition_rule_hit_row(hit, x + 14.0, row_y);
                row_y += 22.0;
            }
            if inspection.hits.len() > 7 {
                draw_text(
                    &format!(
                        "... {} more transition rule hit(s)",
                        inspection.hits.len() - 7
                    ),
                    x + 14.0,
                    row_y,
                    12.0,
                    Color::from_rgba(224, 204, 151, 255),
                );
            }
        }

        let reason_y = y + panel_h - 47.0;
        if let Some(reason) = first_visible_reason(&inspection.hits) {
            draw_text(
                &format!("reason: {}", shorten(reason, 78)),
                x + 14.0,
                reason_y,
                12.0,
                Color::from_rgba(212, 220, 202, 255),
            );
        }
        draw_text(
            "Y toggles inspector | T toggles terrain masks | select tiles with the editor cursor",
            x + 14.0,
            y + panel_h - 18.0,
            12.0,
            Color::from_rgba(170, 215, 255, 255),
        );
    }
}

fn draw_transition_rule_hit_row(hit: &TerrainTransitionRuleHit, x: f32, y: f32) {
    let phase = match hit.phase {
        TransitionRulePhase::Edge => "edge",
        TransitionRulePhase::Corner => "corner",
    };
    let rule_color = if hit.used_builtin_fallback {
        Color::from_rgba(255, 176, 112, 255)
    } else {
        Color::from_rgba(174, 231, 168, 255)
    };

    draw_text(
        &format!("{:<6} {:<9}", phase, hit.direction),
        x,
        y,
        12.0,
        Color::from_rgba(238, 224, 184, 255),
    );
    draw_text(
        hit.neighbor.code(),
        x + 112.0,
        y,
        12.0,
        Color::from_rgba(220, 226, 228, 255),
    );
    draw_text(
        hit.material_code(),
        x + 204.0,
        y,
        12.0,
        material_color(hit.material),
    );
    draw_text(
        hit.atlas_group_label(),
        x + 304.0,
        y,
        12.0,
        Color::from_rgba(195, 218, 229, 255),
    );
    draw_text(
        &format!(
            "{} / {}",
            shorten(hit.rule_label(), 18),
            hit.priority_label()
        ),
        x + 392.0,
        y,
        12.0,
        rule_color,
    );
}

fn material_color(material: Option<haven_world::TransitionMaterial>) -> Color {
    match material {
        Some(haven_world::TransitionMaterial::WetSand) => Color::from_rgba(203, 169, 96, 255),
        Some(haven_world::TransitionMaterial::Foam) => Color::from_rgba(230, 251, 255, 255),
        Some(haven_world::TransitionMaterial::ShallowWaterEdge) => {
            Color::from_rgba(109, 206, 246, 255)
        }
        Some(haven_world::TransitionMaterial::SandBlend) => Color::from_rgba(232, 205, 117, 255),
        Some(haven_world::TransitionMaterial::GrassFringe) => Color::from_rgba(109, 211, 97, 255),
        Some(haven_world::TransitionMaterial::DirtBlend) => Color::from_rgba(158, 101, 51, 255),
        Some(haven_world::TransitionMaterial::RoadShoulder) => Color::from_rgba(174, 138, 82, 255),
        Some(haven_world::TransitionMaterial::StoneShoulder) => {
            Color::from_rgba(190, 190, 182, 255)
        }
        Some(haven_world::TransitionMaterial::RockShadow) => Color::from_rgba(135, 138, 150, 255),
        None => Color::from_rgba(180, 180, 180, 255),
    }
}

fn first_visible_reason(hits: &[TerrainTransitionRuleHit]) -> Option<&str> {
    hits.iter().find_map(|hit| hit.rule_reason.as_deref())
}

fn shorten(value: &str, max_chars: usize) -> String {
    let mut out = String::new();
    for (index, ch) in value.chars().enumerate() {
        if index >= max_chars {
            out.push_str("...");
            return out;
        }
        out.push(ch);
    }
    out
}
