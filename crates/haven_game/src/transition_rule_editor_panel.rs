use super::*;
use haven_world::{
    apply_transition_rule_draft_auto_fixes, apply_transition_rule_draft_edit,
    compare_transition_rule_draft_to_live, export_transition_rule_draft_from_manifest,
    promote_transition_rule_draft_to_manifest, reload_terrain_transition_rule_manifest,
    reset_transition_rule_draft_from_live_manifest, restore_transition_rule_draft_from_undo,
    transition_rule_catalog_rows, transition_rule_catalog_summary,
    transition_rule_draft_auto_fix_lines, transition_rule_draft_auto_fix_status,
    transition_rule_draft_compare_lines, transition_rule_draft_compare_status,
    transition_rule_draft_selected_summary, transition_rule_draft_selected_validation_lines,
    transition_rule_draft_status, transition_rule_draft_undo_lines,
    transition_rule_draft_undo_status, transition_rule_draft_validation_status,
    validate_transition_rule_draft_for_editor, TransitionRuleCatalogRow, TransitionRuleDraftEdit,
    TransitionRulePhase,
};

const RULE_ROW_COUNT: usize = 8;

impl Game {
    pub(super) fn handle_transition_rules_tab_click(
        &mut self,
        mx: f32,
        my: f32,
        panel_x: f32,
    ) -> bool {
        if button_hit(mx, my, panel_x + 18.0, 126.0, 74.0, 24.0) {
            self.cycle_transition_rule_editor_filter(-1);
            return true;
        }
        if button_hit(mx, my, panel_x + 98.0, 126.0, 74.0, 24.0) {
            self.cycle_transition_rule_editor_filter(1);
            return true;
        }
        if button_hit(mx, my, panel_x + 178.0, 126.0, 74.0, 24.0) {
            self.select_transition_rule_editor_row(-1);
            return true;
        }
        if button_hit(mx, my, panel_x + 258.0, 126.0, 74.0, 24.0) {
            self.select_transition_rule_editor_row(1);
            return true;
        }
        if button_hit(mx, my, panel_x + 342.0, 126.0, 74.0, 24.0) {
            self.show_transition_rule_preview = !self.show_transition_rule_preview;
            self.sync_transition_rule_preview_to_editor_selection();
            self.status_message = if self.show_transition_rule_preview {
                "Transition rule preview overlay enabled from editor tab".to_string()
            } else {
                "Transition rule preview overlay hidden".to_string()
            };
            self.log.event(&self.status_message);
            return true;
        }
        if button_hit(mx, my, panel_x + 422.0, 126.0, 74.0, 24.0) {
            self.show_transition_rule_inspector = !self.show_transition_rule_inspector;
            self.status_message = if self.show_transition_rule_inspector {
                "Selected-cell transition inspector enabled from editor tab".to_string()
            } else {
                "Selected-cell transition inspector hidden".to_string()
            };
            self.log.event(&self.status_message);
            return true;
        }

        for (index, edit) in [
            None,
            Some(TransitionRuleDraftEdit::PriorityDelta(-1)),
            Some(TransitionRuleDraftEdit::PriorityDelta(1)),
            Some(TransitionRuleDraftEdit::CycleMaterial(1)),
            Some(TransitionRuleDraftEdit::CycleCenter(1)),
            Some(TransitionRuleDraftEdit::CycleNeighbor(1)),
            Some(TransitionRuleDraftEdit::SyncAtlasGroup),
        ]
        .into_iter()
        .enumerate()
        {
            let x = panel_x + 18.0 + index as f32 * 70.0;
            if button_hit(mx, my, x, 154.0, 64.0, 22.0) {
                match edit {
                    None => self.export_transition_rule_draft(),
                    Some(edit) => self.apply_selected_transition_rule_draft_edit(edit),
                }
                return true;
            }
        }
        for (label_index, x, w) in [
            (0usize, panel_x + 18.0, 70.0),
            (1usize, panel_x + 92.0, 78.0),
            (2usize, panel_x + 174.0, 64.0),
            (3usize, panel_x + 242.0, 76.0),
            (4usize, panel_x + 322.0, 70.0),
            (5usize, panel_x + 396.0, 54.0),
            (6usize, panel_x + 454.0, 58.0),
        ] {
            if button_hit(mx, my, x, 180.0, w, 22.0) {
                match label_index {
                    0 => self.compare_transition_rule_draft(),
                    1 => self.promote_transition_rule_draft(),
                    2 => self.reload_transition_rule_manifest_cache(),
                    3 => self.validate_transition_rule_draft_editor(),
                    4 => self.apply_transition_rule_draft_auto_fixes_editor(),
                    5 => self.restore_transition_rule_draft_from_undo_editor(),
                    6 => self.reset_transition_rule_draft_from_live_editor(),
                    _ => {}
                }
                return true;
            }
        }

        if let Ok(rows) = transition_rule_catalog_rows(self.transition_rule_editor_filter) {
            let row_start_y = 312.0;
            let row_h = 22.0;
            for visible in 0..RULE_ROW_COUNT {
                let y = row_start_y + visible as f32 * row_h;
                if my >= y - 15.0 && my <= y + 4.0 && mx >= panel_x + 18.0 && mx <= panel_x + 500.0
                {
                    let absolute = self.transition_rule_editor_scroll + visible;
                    if absolute < rows.len() {
                        self.transition_rule_editor_index = absolute;
                        self.sync_transition_rule_preview_to_editor_selection();
                        let row = &rows[absolute];
                        self.status_message = format!("Selected transition rule: {}", row.id);
                        return true;
                    }
                }
            }
        }
        true
    }

    pub(super) fn cycle_transition_rule_editor_filter(&mut self, delta: i32) {
        self.transition_rule_editor_filter = self.transition_rule_editor_filter.next(delta);
        self.transition_rule_editor_index = 0;
        self.transition_rule_editor_scroll = 0;
        let summary = transition_rule_catalog_summary(self.transition_rule_editor_filter)
            .unwrap_or_else(|error| format!("Transition rule manifest unavailable: {error}"));
        self.status_message = summary;
        self.log.event(&self.status_message);
    }

    pub(super) fn select_transition_rule_editor_row(&mut self, delta: i32) {
        let Ok(rows) = transition_rule_catalog_rows(self.transition_rule_editor_filter) else {
            self.status_message = "Transition rule manifest unavailable".to_string();
            return;
        };
        if rows.is_empty() {
            self.transition_rule_editor_index = 0;
            self.transition_rule_editor_scroll = 0;
            self.status_message = "No transition rules match this filter".to_string();
            return;
        }
        let current = self.transition_rule_editor_index.min(rows.len() - 1) as i32;
        self.transition_rule_editor_index =
            (current + delta).rem_euclid(rows.len() as i32) as usize;
        self.ensure_transition_rule_editor_selection_visible(rows.len());
        self.sync_transition_rule_preview_to_editor_selection();
        self.status_message = format!(
            "Transition rule {}/{}: {}",
            self.transition_rule_editor_index + 1,
            rows.len(),
            rows[self.transition_rule_editor_index].id
        );
    }

    pub(super) fn ensure_transition_rule_editor_selection_visible(&mut self, row_count: usize) {
        if row_count == 0 {
            self.transition_rule_editor_index = 0;
            self.transition_rule_editor_scroll = 0;
            return;
        }
        self.transition_rule_editor_index = self.transition_rule_editor_index.min(row_count - 1);
        if self.transition_rule_editor_index < self.transition_rule_editor_scroll {
            self.transition_rule_editor_scroll = self.transition_rule_editor_index;
        }
        if self.transition_rule_editor_index >= self.transition_rule_editor_scroll + RULE_ROW_COUNT
        {
            self.transition_rule_editor_scroll = self
                .transition_rule_editor_index
                .saturating_sub(RULE_ROW_COUNT - 1);
        }
    }

    pub(super) fn sync_transition_rule_preview_to_editor_selection(&mut self) {
        let Ok(rows) = transition_rule_catalog_rows(self.transition_rule_editor_filter) else {
            return;
        };
        if rows.is_empty() {
            self.transition_rule_preview_index = 0;
            return;
        }
        let row = &rows[self.transition_rule_editor_index.min(rows.len() - 1)];
        self.transition_rule_preview_index = row.manifest_index;
    }

    pub(super) fn export_transition_rule_draft(&mut self) {
        match export_transition_rule_draft_from_manifest() {
            Ok(report) => {
                self.status_message = report.status_line();
                self.log.event(&self.status_message);
            }
            Err(error) => {
                self.status_message = format!("Draft export failed: {error}");
                self.log.event(&self.status_message);
            }
        }
    }

    pub(super) fn apply_selected_transition_rule_draft_edit(
        &mut self,
        edit: TransitionRuleDraftEdit,
    ) {
        let Ok(rows) = transition_rule_catalog_rows(self.transition_rule_editor_filter) else {
            self.status_message =
                "Transition rule manifest unavailable; draft edit skipped".to_string();
            return;
        };
        if rows.is_empty() {
            self.status_message = "No transition rule selected for draft edit".to_string();
            return;
        }
        let row = &rows[self.transition_rule_editor_index.min(rows.len() - 1)];
        match apply_transition_rule_draft_edit(row.manifest_index, edit) {
            Ok(report) => {
                self.status_message = report.status_line();
                self.log.event(&self.status_message);
            }
            Err(error) => {
                self.status_message = format!("Draft edit failed: {error}");
                self.log.event(&self.status_message);
            }
        }
    }

    pub(super) fn apply_transition_rule_draft_auto_fixes_editor(&mut self) {
        match apply_transition_rule_draft_auto_fixes() {
            Ok(report) => {
                self.status_message = report.status_line();
                self.log.event(&self.status_message);
                for line in report.compact_lines(4) {
                    self.log.event(&line);
                }
                self.ensure_selected_transition_rule_still_valid();
            }
            Err(error) => {
                self.status_message = format!("Draft auto-fix failed: {error}");
                self.log.event(&self.status_message);
            }
        }
    }

    pub(super) fn restore_transition_rule_draft_from_undo_editor(&mut self) {
        match restore_transition_rule_draft_from_undo() {
            Ok(report) => {
                self.status_message = report.status_line();
                self.log.event(&self.status_message);
                for line in transition_rule_draft_undo_lines(3) {
                    self.log.event(&format!("Draft undo: {line}"));
                }
                self.ensure_selected_transition_rule_still_valid();
            }
            Err(error) => {
                self.status_message = format!("Draft undo restore failed: {error}");
                self.log.event(&self.status_message);
            }
        }
    }

    pub(super) fn reset_transition_rule_draft_from_live_editor(&mut self) {
        match reset_transition_rule_draft_from_live_manifest() {
            Ok(report) => {
                self.status_message = report.status_line();
                self.log.event(&self.status_message);
                self.ensure_selected_transition_rule_still_valid();
            }
            Err(error) => {
                self.status_message = format!("Draft live restore failed: {error}");
                self.log.event(&self.status_message);
            }
        }
    }

    pub(super) fn compare_transition_rule_draft(&mut self) {
        match compare_transition_rule_draft_to_live() {
            Ok(report) => {
                self.status_message = report.status_line();
                self.log.event(&self.status_message);
                for line in report.compact_lines(4) {
                    self.log.event(&format!("Draft diff: {line}"));
                }
            }
            Err(error) => {
                self.status_message = format!("Draft compare failed: {error}");
                self.log.event(&self.status_message);
            }
        }
    }

    pub(super) fn validate_transition_rule_draft_editor(&mut self) {
        match validate_transition_rule_draft_for_editor() {
            Ok(report) => {
                self.status_message = report.status_line();
                self.log.event(&self.status_message);
                for line in report.compact_lines(5) {
                    self.log.event(&format!("Draft validation: {line}"));
                }
                if !report.can_promote() {
                    self.log.event(
                        "Draft promotion is blocked until transition-rule diagnostics are fixed",
                    );
                }
            }
            Err(error) => {
                self.status_message = format!("Draft validation failed: {error}");
                self.log.event(&self.status_message);
            }
        }
    }

    pub(super) fn promote_transition_rule_draft(&mut self) {
        match promote_transition_rule_draft_to_manifest() {
            Ok(report) => {
                self.log.event(&report.status_line());
                match reload_terrain_transition_rule_manifest() {
                    Ok(reload) => {
                        self.status_message =
                            format!("{}; {}", report.status_line(), reload.status_line());
                        self.log.event(&reload.status_line());
                        self.log.event(&format!(
                            "Transition rules refreshed from {}",
                            reload.manifest_path.display()
                        ));
                    }
                    Err(error) => {
                        self.status_message =
                            format!("{}; runtime reload failed: {error}", report.status_line());
                        self.log.event(&self.status_message);
                    }
                }
            }
            Err(error) => {
                self.status_message = format!("Draft promotion failed: {error}");
                self.log.event(&self.status_message);
            }
        }
    }

    pub(super) fn reload_transition_rule_manifest_cache(&mut self) {
        match reload_terrain_transition_rule_manifest() {
            Ok(report) => {
                self.status_message = report.status_line();
                self.log.event(&self.status_message);
                self.log.event(&format!(
                    "Old transition rule cache: {}",
                    report.old_summary
                ));
                self.log.event(&format!(
                    "New transition rule cache: {}",
                    report.new_summary
                ));
                self.ensure_selected_transition_rule_still_valid();
            }
            Err(error) => {
                self.status_message =
                    format!("Transition rule reload failed; cached rules preserved: {error}");
                self.log.event(&self.status_message);
            }
        }
    }

    pub(super) fn ensure_selected_transition_rule_still_valid(&mut self) {
        if let Ok(rows) = transition_rule_catalog_rows(self.transition_rule_editor_filter) {
            self.ensure_transition_rule_editor_selection_visible(rows.len());
            self.sync_transition_rule_preview_to_editor_selection();
        }
    }

    pub(super) fn handle_transition_rule_editor_hotkeys(&mut self) {
        if is_key_pressed(KeyCode::J) {
            self.select_transition_rule_editor_row(-1);
        }
        if is_key_pressed(KeyCode::K) {
            self.select_transition_rule_editor_row(1);
        }
        if is_key_pressed(KeyCode::LeftBracket) {
            self.cycle_transition_rule_editor_filter(-1);
        }
        if is_key_pressed(KeyCode::RightBracket) {
            self.cycle_transition_rule_editor_filter(1);
        }
        if is_key_pressed(KeyCode::D) {
            self.export_transition_rule_draft();
        }
        if is_key_pressed(KeyCode::C) {
            self.compare_transition_rule_draft();
        }
        if is_key_pressed(KeyCode::R) {
            self.reload_transition_rule_manifest_cache();
        }
        if is_key_pressed(KeyCode::V) {
            self.validate_transition_rule_draft_editor();
        }
        if is_key_down(KeyCode::LeftControl) && is_key_pressed(KeyCode::A) {
            self.apply_transition_rule_draft_auto_fixes_editor();
        }
        if is_key_down(KeyCode::LeftControl) && is_key_pressed(KeyCode::Z) {
            self.restore_transition_rule_draft_from_undo_editor();
        }
        if is_key_down(KeyCode::LeftControl) && is_key_pressed(KeyCode::L) {
            self.reset_transition_rule_draft_from_live_editor();
        }
    }

    pub(super) fn draw_transition_rules_editor_tab(&self, panel_x: f32) {
        draw_text(
            "Terrain Transition Rules",
            panel_x + 18.0,
            104.0,
            17.0,
            Color::from_rgba(162, 228, 255, 255),
        );
        draw_text(
            "Browse manifest-authored coast, edge, corner, road, cliff, cave, and water rules.",
            panel_x + 18.0,
            120.0,
            11.5,
            Color::from_rgba(202, 218, 216, 255),
        );

        for (label, x, y, w) in [
            ("Filter-", panel_x + 18.0, 126.0, 74.0),
            ("Filter+", panel_x + 98.0, 126.0, 74.0),
            ("Rule-", panel_x + 178.0, 126.0, 74.0),
            ("Rule+", panel_x + 258.0, 126.0, 74.0),
            ("Preview", panel_x + 342.0, 126.0, 74.0),
            ("Inspect", panel_x + 422.0, 126.0, 74.0),
        ] {
            draw_editor_button(label, x, y, w, 24.0);
        }
        for (label, index) in [
            ("Draft", 0usize),
            ("Pri-", 1),
            ("Pri+", 2),
            ("Mat+", 3),
            ("Ctr+", 4),
            ("Nbr+", 5),
            ("Atlas", 6),
        ] {
            draw_editor_button(
                label,
                panel_x + 18.0 + index as f32 * 70.0,
                154.0,
                64.0,
                22.0,
            );
        }
        for (label, x, w) in [
            ("Compare", panel_x + 18.0, 70.0),
            ("Promote", panel_x + 92.0, 78.0),
            ("Reload", panel_x + 174.0, 64.0),
            ("Validate", panel_x + 242.0, 76.0),
            ("AutoFix", panel_x + 322.0, 70.0),
            ("Undo", panel_x + 396.0, 54.0),
            ("Live", panel_x + 454.0, 58.0),
        ] {
            draw_editor_button(label, x, 180.0, w, 22.0);
        }

        let rows = match transition_rule_catalog_rows(self.transition_rule_editor_filter) {
            Ok(rows) => rows,
            Err(error) => {
                draw_text(
                    &format!("Rule manifest unavailable: {error}"),
                    panel_x + 18.0,
                    214.0,
                    13.0,
                    Color::from_rgba(255, 166, 122, 255),
                );
                return;
            }
        };
        let summary = transition_rule_catalog_summary(self.transition_rule_editor_filter)
            .unwrap_or_else(|error| format!("Transition rule manifest unavailable: {error}"));
        draw_text(
            &format!(
                "Filter {} | {} | preview {} | inspector {}",
                self.transition_rule_editor_filter.label(),
                summary,
                on_off(self.show_transition_rule_preview),
                on_off(self.show_transition_rule_inspector)
            ),
            panel_x + 18.0,
            214.0,
            11.5,
            Color::from_rgba(244, 238, 201, 255),
        );
        draw_text(
            &shorten_rule_editor_text(&transition_rule_draft_status(), 92),
            panel_x + 18.0,
            230.0,
            11.0,
            Color::from_rgba(178, 223, 189, 255),
        );
        draw_text(
            &shorten_rule_editor_text(&transition_rule_draft_compare_status(), 92),
            panel_x + 18.0,
            244.0,
            10.5,
            Color::from_rgba(188, 214, 255, 255),
        );
        draw_text(
            &shorten_rule_editor_text(&transition_rule_draft_validation_status(), 92),
            panel_x + 18.0,
            258.0,
            10.5,
            Color::from_rgba(255, 205, 146, 255),
        );
        draw_text(
            &shorten_rule_editor_text(&transition_rule_draft_auto_fix_status(), 92),
            panel_x + 18.0,
            272.0,
            10.5,
            Color::from_rgba(255, 221, 174, 255),
        );
        draw_text(
            &shorten_rule_editor_text(&transition_rule_draft_undo_status(), 92),
            panel_x + 18.0,
            286.0,
            10.5,
            Color::from_rgba(207, 196, 255, 255),
        );

        if rows.is_empty() {
            draw_text(
                "No rules match the selected filter.",
                panel_x + 18.0,
                304.0,
                13.0,
                Color::from_rgba(224, 204, 151, 255),
            );
            return;
        }

        let selected = self.transition_rule_editor_index.min(rows.len() - 1);
        let scroll = self.transition_rule_editor_scroll.min(selected);
        draw_text(
            "rule id / pair                       material        group             phase    pri",
            panel_x + 18.0,
            304.0,
            11.0,
            Color::from_rgba(168, 190, 197, 255),
        );
        for visible in 0..RULE_ROW_COUNT {
            let row_index = scroll + visible;
            if row_index >= rows.len() {
                break;
            }
            let row = &rows[row_index];
            let y = 312.0 + visible as f32 * 22.0;
            let active = row_index == selected;
            if active {
                draw_rectangle(
                    panel_x + 15.0,
                    y - 15.0,
                    488.0,
                    19.0,
                    Color::from_rgba(76, 101, 78, 205),
                );
            }
            draw_transition_rule_catalog_row(row, panel_x + 20.0, y, active);
        }

        let row = &rows[selected];
        let detail_y = 490.0;
        draw_rectangle(
            panel_x + 16.0,
            detail_y - 17.0,
            488.0,
            154.0,
            Color::from_rgba(18, 24, 24, 170),
        );
        draw_rectangle_lines(
            panel_x + 16.0,
            detail_y - 17.0,
            488.0,
            154.0,
            1.0,
            Color::from_rgba(112, 148, 138, 210),
        );
        draw_text(
            &format!(
                "Selected {}/{} manifest#{}: {}",
                selected + 1,
                rows.len(),
                row.manifest_index,
                row.id
            ),
            panel_x + 24.0,
            detail_y,
            13.0,
            Color::from_rgba(255, 232, 144, 255),
        );
        draw_text(
            &format!(
                "{} -> {} | material {} | atlas {} | phases {} | priority {}",
                row.center_selector,
                row.neighbor_selector,
                row.material.code(),
                row.atlas_group,
                row.phases_label(),
                row.priority
            ),
            panel_x + 24.0,
            detail_y + 20.0,
            12.0,
            Color::from_rgba(220, 231, 226, 255),
        );
        if let Some(reason) = row.reason.as_deref() {
            draw_text(
                &format!("reason: {}", shorten_rule_editor_text(reason, 82)),
                panel_x + 24.0,
                detail_y + 41.0,
                11.5,
                Color::from_rgba(212, 220, 202, 255),
            );
        }
        draw_text(
            &shorten_rule_editor_text(
                &transition_rule_draft_selected_summary(row.manifest_index),
                86,
            ),
            panel_x + 24.0,
            detail_y + 64.0,
            11.0,
            Color::from_rgba(178, 223, 189, 255),
        );
        let diff_lines = transition_rule_draft_compare_lines(1);
        for (index, line) in diff_lines.iter().enumerate() {
            draw_text(
                &shorten_rule_editor_text(line, 86),
                panel_x + 24.0,
                detail_y + 80.0 + index as f32 * 13.0,
                10.5,
                Color::from_rgba(188, 214, 255, 255),
            );
        }
        let validation_lines =
            transition_rule_draft_selected_validation_lines(row.manifest_index, 2);
        for (index, line) in validation_lines.iter().enumerate() {
            draw_text(
                &shorten_rule_editor_text(line, 86),
                panel_x + 24.0,
                detail_y + 96.0 + index as f32 * 13.0,
                10.5,
                Color::from_rgba(255, 205, 146, 255),
            );
        }
        for (index, line) in transition_rule_draft_auto_fix_lines(1).iter().enumerate() {
            draw_text(
                &shorten_rule_editor_text(line, 86),
                panel_x + 24.0,
                detail_y + 122.0 + index as f32 * 12.0,
                10.0,
                Color::from_rgba(255, 221, 174, 255),
            );
        }
        draw_text(
            "Promote to live manifest manually after review: Compare + Validate first. AutoFix only applies conservative draft cleanups. Undo restores last draft snapshot; Live resets draft from live manifest. Backup is written first, then runtime cache reloads. Reload refreshes live rules.",
            panel_x + 24.0,
            detail_y + 144.0,
            10.5,
            Color::from_rgba(171, 218, 255, 255),
        );
    }
}

fn draw_transition_rule_catalog_row(row: &TransitionRuleCatalogRow, x: f32, y: f32, active: bool) {
    let text_color = if active {
        Color::from_rgba(255, 246, 190, 255)
    } else {
        Color::from_rgba(220, 231, 236, 255)
    };
    draw_text(
        &shorten_rule_editor_text(&row.id, 24),
        x,
        y,
        11.5,
        text_color,
    );
    draw_text(
        &shorten_rule_editor_text(&row.short_pair_label(), 21),
        x + 154.0,
        y,
        11.5,
        Color::from_rgba(204, 222, 218, 255),
    );
    draw_text(
        row.material.code(),
        x + 286.0,
        y,
        11.5,
        transition_rule_material_color(row.material),
    );
    draw_text(
        &shorten_rule_editor_text(&row.atlas_group, 15),
        x + 364.0,
        y,
        11.5,
        Color::from_rgba(195, 218, 229, 255),
    );
    draw_text(
        &phase_flags(&row.applies_to),
        x + 446.0,
        y,
        11.5,
        Color::from_rgba(238, 224, 184, 255),
    );
    draw_text(
        &row.priority.to_string(),
        x + 484.0,
        y,
        11.5,
        Color::from_rgba(255, 210, 132, 255),
    );
}

fn button_hit(mx: f32, my: f32, x: f32, y: f32, w: f32, h: f32) -> bool {
    mx >= x && mx <= x + w && my >= y && my <= y + h
}

fn on_off(value: bool) -> &'static str {
    if value {
        "on"
    } else {
        "off"
    }
}

fn phase_flags(phases: &[TransitionRulePhase]) -> String {
    let edge = phases.contains(&TransitionRulePhase::Edge);
    let corner = phases.contains(&TransitionRulePhase::Corner);
    match (edge, corner) {
        (true, true) => "E+C".to_string(),
        (true, false) => "E".to_string(),
        (false, true) => "C".to_string(),
        (false, false) => "-".to_string(),
    }
}

fn transition_rule_material_color(material: haven_world::TransitionMaterial) -> Color {
    match material {
        haven_world::TransitionMaterial::WetSand => Color::from_rgba(203, 169, 96, 255),
        haven_world::TransitionMaterial::Foam => Color::from_rgba(230, 251, 255, 255),
        haven_world::TransitionMaterial::ShallowWaterEdge => Color::from_rgba(109, 206, 246, 255),
        haven_world::TransitionMaterial::SandBlend => Color::from_rgba(232, 205, 117, 255),
        haven_world::TransitionMaterial::GrassFringe => Color::from_rgba(109, 211, 97, 255),
        haven_world::TransitionMaterial::DirtBlend => Color::from_rgba(158, 101, 51, 255),
        haven_world::TransitionMaterial::RoadShoulder => Color::from_rgba(174, 138, 82, 255),
        haven_world::TransitionMaterial::StoneShoulder => Color::from_rgba(190, 190, 182, 255),
        haven_world::TransitionMaterial::RockShadow => Color::from_rgba(135, 138, 150, 255),
    }
}

fn shorten_rule_editor_text(value: &str, max_chars: usize) -> String {
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
