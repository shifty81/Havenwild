use super::*;
use haven_world::{
    preview_transition_rules, TerrainFamily, TerrainTransitionRulePreview, TransitionMaterial,
    TransitionPreviewCell, TransitionPreviewCellRole, TransitionPreviewSample,
};

impl Game {
    pub(super) fn cycle_transition_rule_preview(&mut self, delta: i32) {
        let Ok(previews) = preview_transition_rules() else {
            self.status_message = "Transition rule preview manifest unavailable".to_string();
            return;
        };
        if previews.is_empty() {
            self.transition_rule_preview_index = 0;
            self.status_message = "No terrain transition rules to preview".to_string();
            return;
        }
        let len = previews.len() as i32;
        let current = self.transition_rule_preview_index.min(previews.len() - 1) as i32;
        self.transition_rule_preview_index = (current + delta).rem_euclid(len) as usize;
        let preview = &previews[self.transition_rule_preview_index];
        self.status_message = format!(
            "Transition preview {}/{}: {}",
            self.transition_rule_preview_index + 1,
            previews.len(),
            preview.rule_id
        );
    }

    pub(super) fn draw_transition_rule_preview_overlay(&self) {
        if !self.dev_mode || !self.show_transition_rule_preview {
            return;
        }

        let panel_w = 610.0;
        let panel_h = 318.0;
        let x = 22.0;
        let y = screen_height() - panel_h - 24.0;
        draw_rectangle(x, y, panel_w, panel_h, Color::from_rgba(20, 24, 22, 235));
        draw_rectangle_lines(
            x,
            y,
            panel_w,
            panel_h,
            2.0,
            Color::from_rgba(142, 218, 172, 230),
        );
        draw_text(
            "Transition Rule Preview Grid",
            x + 14.0,
            y + 26.0,
            19.0,
            Color::from_rgba(192, 245, 202, 255),
        );

        let previews = match preview_transition_rules() {
            Ok(previews) => previews,
            Err(error) => {
                draw_text(
                    &format!("Rule manifest unavailable: {error}"),
                    x + 14.0,
                    y + 58.0,
                    13.0,
                    Color::from_rgba(255, 166, 122, 255),
                );
                return;
            }
        };
        if previews.is_empty() {
            draw_text(
                "No transition rules were loaded from the manifest.",
                x + 14.0,
                y + 58.0,
                13.0,
                Color::from_rgba(255, 214, 150, 255),
            );
            return;
        }

        let index = self.transition_rule_preview_index.min(previews.len() - 1);
        let preview = &previews[index];
        draw_preview_header(preview, index, previews.len(), x + 14.0, y + 54.0);

        let mut sample_x = x + 18.0;
        let sample_y = y + 114.0;
        for sample in preview.samples.iter().take(2) {
            draw_preview_sample(sample, sample_x, sample_y);
            sample_x += 214.0;
        }

        let legend_x = x + panel_w - 164.0;
        draw_preview_legend(legend_x, y + 118.0);
        if let Some(reason) = preview.reason.as_deref() {
            draw_text(
                &format!("reason: {}", shorten_preview_text(reason, 76)),
                x + 14.0,
                y + panel_h - 42.0,
                12.0,
                Color::from_rgba(221, 225, 200, 255),
            );
        }
        draw_text(
            "U toggles preview | J/K cycle rules | Y shows selected-cell rule inspector | T shows masks",
            x + 14.0,
            y + panel_h - 17.0,
            12.0,
            Color::from_rgba(171, 218, 255, 255),
        );
    }
}

fn draw_preview_header(
    preview: &TerrainTransitionRulePreview,
    index: usize,
    total: usize,
    x: f32,
    y: f32,
) {
    draw_text(
        &format!("rule {}/{}: {}", index + 1, total, preview.rule_id),
        x,
        y,
        14.0,
        Color::from_rgba(244, 238, 198, 255),
    );
    draw_text(
        &format!(
            "{} -> {} | representative {} -> {} | material {} | atlas {} | priority {}",
            preview.center_selector,
            preview.neighbor_selector,
            preview.center_family.code(),
            preview.neighbor_family.code(),
            preview.material.code(),
            preview.atlas_group,
            preview.priority
        ),
        x,
        y + 20.0,
        12.0,
        Color::from_rgba(203, 220, 216, 255),
    );
}

fn draw_preview_sample(sample: &TransitionPreviewSample, x: f32, y: f32) {
    draw_text(
        sample.kind.label(),
        x,
        y - 12.0,
        13.0,
        Color::from_rgba(214, 238, 189, 255),
    );
    let cell = 42.0;
    for preview_cell in &sample.cells {
        draw_preview_cell(preview_cell, x, y, cell);
    }
    draw_rectangle_lines(
        x,
        y,
        cell * 3.0,
        cell * 3.0,
        2.0,
        Color::from_rgba(228, 216, 152, 180),
    );
    draw_text(
        &sample.summary_line(),
        x,
        y + cell * 3.0 + 18.0,
        11.0,
        Color::from_rgba(197, 214, 211, 255),
    );
}

fn draw_preview_cell(cell: &TransitionPreviewCell, origin_x: f32, origin_y: f32, size: f32) {
    let x = origin_x + cell.grid_x as f32 * size;
    let y = origin_y + cell.grid_y as f32 * size;
    draw_rectangle(
        x + 1.0,
        y + 1.0,
        size - 2.0,
        size - 2.0,
        family_preview_color(cell.family),
    );
    let border_color = match cell.role {
        TransitionPreviewCellRole::Center => Color::from_rgba(255, 247, 181, 255),
        TransitionPreviewCellRole::NeighborCardinal => Color::from_rgba(143, 220, 255, 245),
        TransitionPreviewCellRole::NeighborDiagonal => Color::from_rgba(222, 149, 255, 245),
        TransitionPreviewCellRole::SameFamily => Color::from_rgba(98, 118, 110, 210),
    };
    draw_rectangle_lines(x + 1.0, y + 1.0, size - 2.0, size - 2.0, 1.5, border_color);
    draw_text(
        family_preview_code(cell.family),
        x + 5.0,
        y + 15.0,
        12.0,
        Color::from_rgba(255, 255, 245, 255),
    );
    draw_text(
        role_preview_code(cell.role),
        x + 5.0,
        y + size - 5.0,
        9.5,
        Color::from_rgba(228, 232, 222, 245),
    );
    if let Some(material) = cell.material {
        draw_circle(
            x + size - 9.0,
            y + 9.0,
            5.0,
            material_preview_color(material),
        );
    }
}

fn draw_preview_legend(x: f32, y: f32) {
    draw_text("Legend", x, y, 14.0, Color::from_rgba(221, 241, 198, 255));
    let rows = [
        ("C", "center tile"),
        ("N", "neighbor sample"),
        ("S", "same family"),
        ("dot", "resolved material"),
        ("edge", "cardinal transition"),
        ("corner", "inner-corner transition"),
    ];
    for (i, (code, text)) in rows.iter().enumerate() {
        let row_y = y + 22.0 + i as f32 * 18.0;
        draw_text(code, x, row_y, 11.0, Color::from_rgba(255, 232, 156, 255));
        draw_text(
            text,
            x + 38.0,
            row_y,
            11.0,
            Color::from_rgba(208, 224, 218, 255),
        );
    }
}

fn family_preview_color(family: TerrainFamily) -> Color {
    match family {
        TerrainFamily::Grass => Color::from_rgba(61, 139, 54, 230),
        TerrainFamily::Dirt => Color::from_rgba(128, 82, 44, 230),
        TerrainFamily::Sand => Color::from_rgba(198, 174, 94, 230),
        TerrainFamily::WetSand => Color::from_rgba(176, 142, 88, 230),
        TerrainFamily::PebblePath => Color::from_rgba(132, 130, 120, 230),
        TerrainFamily::Road => Color::from_rgba(139, 113, 75, 230),
        TerrainFamily::WoodFloor => Color::from_rgba(145, 86, 42, 230),
        TerrainFamily::StoneFloor => Color::from_rgba(137, 140, 139, 230),
        TerrainFamily::Farm => Color::from_rgba(117, 73, 35, 230),
        TerrainFamily::ShallowWater => Color::from_rgba(62, 161, 201, 230),
        TerrainFamily::Water => Color::from_rgba(45, 130, 194, 230),
        TerrainFamily::DeepWater => Color::from_rgba(24, 72, 119, 230),
        TerrainFamily::RockWall => Color::from_rgba(77, 79, 85, 230),
        TerrainFamily::Cave => Color::from_rgba(49, 45, 50, 230),
        TerrainFamily::Greenhouse => Color::from_rgba(66, 150, 82, 230),
        TerrainFamily::Void => Color::from_rgba(8, 8, 8, 120),
    }
}

fn material_preview_color(material: TransitionMaterial) -> Color {
    match material {
        TransitionMaterial::WetSand => Color::from_rgba(207, 174, 103, 255),
        TransitionMaterial::Foam => Color::from_rgba(235, 252, 255, 255),
        TransitionMaterial::ShallowWaterEdge => Color::from_rgba(107, 206, 247, 255),
        TransitionMaterial::SandBlend => Color::from_rgba(231, 205, 116, 255),
        TransitionMaterial::GrassFringe => Color::from_rgba(111, 213, 94, 255),
        TransitionMaterial::DirtBlend => Color::from_rgba(158, 101, 51, 255),
        TransitionMaterial::RoadShoulder => Color::from_rgba(176, 140, 84, 255),
        TransitionMaterial::StoneShoulder => Color::from_rgba(192, 192, 184, 255),
        TransitionMaterial::RockShadow => Color::from_rgba(116, 119, 129, 255),
    }
}

fn family_preview_code(family: TerrainFamily) -> &'static str {
    match family {
        TerrainFamily::Grass => "gr",
        TerrainFamily::Dirt => "di",
        TerrainFamily::Sand => "sa",
        TerrainFamily::WetSand => "ws",
        TerrainFamily::PebblePath => "pp",
        TerrainFamily::Road => "rd",
        TerrainFamily::WoodFloor => "wd",
        TerrainFamily::StoneFloor => "st",
        TerrainFamily::Farm => "fm",
        TerrainFamily::ShallowWater => "sw",
        TerrainFamily::Water => "wa",
        TerrainFamily::DeepWater => "dw",
        TerrainFamily::RockWall => "rw",
        TerrainFamily::Cave => "cv",
        TerrainFamily::Greenhouse => "gh",
        TerrainFamily::Void => "--",
    }
}

fn role_preview_code(role: TransitionPreviewCellRole) -> &'static str {
    match role {
        TransitionPreviewCellRole::Center => "C",
        TransitionPreviewCellRole::SameFamily => "S",
        TransitionPreviewCellRole::NeighborCardinal
        | TransitionPreviewCellRole::NeighborDiagonal => "N",
    }
}

fn shorten_preview_text(value: &str, max_chars: usize) -> String {
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
