use super::*;
use haven_assets::{
    asset_local_import_instructions::{
        asset_local_import_instruction_for_source, build_asset_local_import_instruction_index,
        load_asset_local_import_instructions, AssetLocalImportInstructionRecord,
        ASSET_LOCAL_IMPORT_INSTRUCTIONS_PATH,
    },
    asset_reference_preview::{
        asset_reference_preview_for_source, asset_reference_preview_summary_line,
        build_asset_reference_preview_index, load_asset_reference_preview_catalog,
        AssetReferencePreviewRecord, ASSET_REFERENCE_PREVIEW_CATALOG_PATH,
    },
    asset_source_availability::{
        asset_source_availability_summary_line, availability_for_donor_record,
        build_asset_source_availability_index, load_asset_source_availability_report,
        AssetSourceAvailabilityRecord, AssetSourceAvailabilityState,
    },
    donor_reference_catalog::{
        load_donor_reference_asset_catalog, DonorReferenceAssetRecord,
        DONOR_REFERENCE_ASSET_CATALOG_PATH,
    },
    prototype_bake::PROTOTYPE_ASSET_LOCAL_BAKE_REPORT_PATH,
};

const ASSET_ROW_COUNT: usize = 11;

#[derive(Clone, Copy, PartialEq, Eq)]
pub(crate) enum AssetReferenceGridFilter {
    All,
    Grid16,
    Grid32,
    Grid40,
    Grid48,
}

impl AssetReferenceGridFilter {
    pub(crate) fn label(self) -> &'static str {
        match self {
            AssetReferenceGridFilter::All => "All grids",
            AssetReferenceGridFilter::Grid16 => "16px",
            AssetReferenceGridFilter::Grid32 => "32px",
            AssetReferenceGridFilter::Grid40 => "40px",
            AssetReferenceGridFilter::Grid48 => "48px",
        }
    }

    pub(crate) fn next(self, delta: i32) -> Self {
        let values = [
            AssetReferenceGridFilter::All,
            AssetReferenceGridFilter::Grid16,
            AssetReferenceGridFilter::Grid32,
            AssetReferenceGridFilter::Grid40,
            AssetReferenceGridFilter::Grid48,
        ];
        let index = values.iter().position(|value| *value == self).unwrap_or(0) as i32;
        values[(index + delta).rem_euclid(values.len() as i32) as usize]
    }

    fn matches(self, record: &DonorReferenceAssetRecord) -> bool {
        match self {
            AssetReferenceGridFilter::All => true,
            AssetReferenceGridFilter::Grid16 => record_has_grid(record, 16),
            AssetReferenceGridFilter::Grid32 => record_has_grid(record, 32),
            AssetReferenceGridFilter::Grid40 => record_has_grid(record, 40),
            AssetReferenceGridFilter::Grid48 => record_has_grid(record, 48),
        }
    }
}

#[derive(Clone, Copy, PartialEq, Eq)]
pub(crate) enum AssetReferenceFamilyFilter {
    All,
    Terrain,
    Water,
    Object,
    Foliage,
    Character,
    Icon,
    Tiled,
}

impl AssetReferenceFamilyFilter {
    pub(crate) fn label(self) -> &'static str {
        match self {
            AssetReferenceFamilyFilter::All => "All families",
            AssetReferenceFamilyFilter::Terrain => "Terrain",
            AssetReferenceFamilyFilter::Water => "Water",
            AssetReferenceFamilyFilter::Object => "Objects",
            AssetReferenceFamilyFilter::Foliage => "Foliage",
            AssetReferenceFamilyFilter::Character => "Character",
            AssetReferenceFamilyFilter::Icon => "Icons",
            AssetReferenceFamilyFilter::Tiled => "Tiled",
        }
    }

    pub(crate) fn next(self, delta: i32) -> Self {
        let values = [
            AssetReferenceFamilyFilter::All,
            AssetReferenceFamilyFilter::Terrain,
            AssetReferenceFamilyFilter::Water,
            AssetReferenceFamilyFilter::Object,
            AssetReferenceFamilyFilter::Foliage,
            AssetReferenceFamilyFilter::Character,
            AssetReferenceFamilyFilter::Icon,
            AssetReferenceFamilyFilter::Tiled,
        ];
        let index = values.iter().position(|value| *value == self).unwrap_or(0) as i32;
        values[(index + delta).rem_euclid(values.len() as i32) as usize]
    }

    fn matches(self, record: &DonorReferenceAssetRecord) -> bool {
        match self {
            AssetReferenceFamilyFilter::All => true,
            AssetReferenceFamilyFilter::Terrain => record_has_family_prefix(record, "terrain."),
            AssetReferenceFamilyFilter::Water => record_has_family_contains(record, "water"),
            AssetReferenceFamilyFilter::Object => record_has_family_prefix(record, "object."),
            AssetReferenceFamilyFilter::Foliage => record_has_family_prefix(record, "foliage."),
            AssetReferenceFamilyFilter::Character => record_has_family_prefix(record, "character."),
            AssetReferenceFamilyFilter::Icon => record_has_family_contains(record, "icon"),
            AssetReferenceFamilyFilter::Tiled => record_has_family_prefix(record, "tiled."),
        }
    }
}

#[derive(Clone, Copy, PartialEq, Eq)]
pub(crate) enum AssetReferencePolicyFilter {
    All,
    PrototypeCandidate,
    ReferenceOnly,
    Blocked,
}

impl AssetReferencePolicyFilter {
    pub(crate) fn label(self) -> &'static str {
        match self {
            AssetReferencePolicyFilter::All => "All policies",
            AssetReferencePolicyFilter::PrototypeCandidate => "Prototype OK",
            AssetReferencePolicyFilter::ReferenceOnly => "Reference only",
            AssetReferencePolicyFilter::Blocked => "Blocked",
        }
    }

    pub(crate) fn next(self, delta: i32) -> Self {
        let values = [
            AssetReferencePolicyFilter::All,
            AssetReferencePolicyFilter::PrototypeCandidate,
            AssetReferencePolicyFilter::ReferenceOnly,
            AssetReferencePolicyFilter::Blocked,
        ];
        let index = values.iter().position(|value| *value == self).unwrap_or(0) as i32;
        values[(index + delta).rem_euclid(values.len() as i32) as usize]
    }

    fn matches(self, record: &DonorReferenceAssetRecord) -> bool {
        match self {
            AssetReferencePolicyFilter::All => true,
            AssetReferencePolicyFilter::PrototypeCandidate => {
                record_policy(record) == AssetReferencePolicy::PrototypeCandidate
            }
            AssetReferencePolicyFilter::ReferenceOnly => {
                record_policy(record) == AssetReferencePolicy::ReferenceOnly
            }
            AssetReferencePolicyFilter::Blocked => {
                record_policy(record) == AssetReferencePolicy::Blocked
            }
        }
    }
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum AssetReferencePolicy {
    PrototypeCandidate,
    ReferenceOnly,
    Blocked,
}

impl Game {
    pub(super) fn handle_asset_reference_browser_click(
        &mut self,
        mx: f32,
        my: f32,
        panel_x: f32,
    ) -> bool {
        if button_hit(mx, my, panel_x + 18.0, 124.0, 86.0, 24.0) {
            self.cycle_asset_reference_grid_filter(-1);
            return true;
        }
        if button_hit(mx, my, panel_x + 108.0, 124.0, 86.0, 24.0) {
            self.cycle_asset_reference_grid_filter(1);
            return true;
        }
        if button_hit(mx, my, panel_x + 208.0, 124.0, 86.0, 24.0) {
            self.cycle_asset_reference_family_filter(-1);
            return true;
        }
        if button_hit(mx, my, panel_x + 298.0, 124.0, 86.0, 24.0) {
            self.cycle_asset_reference_family_filter(1);
            return true;
        }
        if button_hit(mx, my, panel_x + 398.0, 124.0, 86.0, 24.0) {
            self.cycle_asset_reference_policy_filter(-1);
            return true;
        }
        if button_hit(mx, my, panel_x + 488.0, 124.0, 86.0, 24.0) {
            self.cycle_asset_reference_policy_filter(1);
            return true;
        }
        if button_hit(mx, my, panel_x + 18.0, 154.0, 72.0, 24.0) {
            self.select_asset_reference_row(-1);
            return true;
        }
        if button_hit(mx, my, panel_x + 96.0, 154.0, 72.0, 24.0) {
            self.select_asset_reference_row(1);
            return true;
        }
        if button_hit(mx, my, panel_x + 178.0, 154.0, 94.0, 24.0) {
            self.status_message = self.asset_reference_browser_summary_line();
            self.log.event(&self.status_message);
            return true;
        }
        if button_hit(mx, my, panel_x + 282.0, 154.0, 94.0, 24.0) {
            self.show_asset_reference_import_instruction_status();
            return true;
        }
        if button_hit(mx, my, panel_x + 386.0, 154.0, 94.0, 24.0) {
            self.show_asset_reference_preview_status();
            return true;
        }

        let Ok(rows) = self.asset_reference_browser_rows() else {
            return true;
        };
        let row_start_y = 226.0;
        let row_h = 24.0;
        for visible in 0..ASSET_ROW_COUNT {
            let y = row_start_y + visible as f32 * row_h;
            if my >= y - 16.0 && my <= y + 5.0 && mx >= panel_x + 18.0 && mx <= panel_x + 610.0 {
                let absolute = self.asset_reference_scroll + visible;
                if absolute < rows.len() {
                    self.asset_reference_index = absolute;
                    self.ensure_asset_reference_selection_visible(rows.len());
                    let row = &rows[absolute];
                    self.status_message = format!(
                        "Asset donor {}/{}: {}",
                        self.asset_reference_index + 1,
                        rows.len(),
                        row.display_name
                    );
                    self.log.event(&self.status_message);
                }
                return true;
            }
        }
        true
    }

    pub(super) fn handle_asset_reference_browser_hotkeys(&mut self) {
        if is_key_pressed(KeyCode::J) {
            self.select_asset_reference_row(-1);
        }
        if is_key_pressed(KeyCode::K) {
            self.select_asset_reference_row(1);
        }
        if is_key_pressed(KeyCode::LeftBracket) {
            self.cycle_asset_reference_grid_filter(-1);
        }
        if is_key_pressed(KeyCode::RightBracket) {
            self.cycle_asset_reference_grid_filter(1);
        }
        if is_key_pressed(KeyCode::F) {
            self.cycle_asset_reference_family_filter(1);
        }
        if is_key_pressed(KeyCode::P) {
            self.cycle_asset_reference_policy_filter(1);
        }
        if is_key_pressed(KeyCode::R) {
            self.status_message = self.asset_reference_browser_summary_line();
            self.log.event(&self.status_message);
        }
        if is_key_pressed(KeyCode::I) {
            self.show_asset_reference_import_instruction_status();
        }
        if is_key_pressed(KeyCode::V) {
            self.show_asset_reference_preview_status();
        }
    }

    pub(super) fn cycle_asset_reference_grid_filter(&mut self, delta: i32) {
        self.asset_reference_grid_filter = self.asset_reference_grid_filter.next(delta);
        self.reset_asset_reference_selection_for_filter();
        self.status_message = format!(
            "Asset grid filter: {}",
            self.asset_reference_grid_filter.label()
        );
        self.log.event(&self.status_message);
    }

    pub(super) fn cycle_asset_reference_family_filter(&mut self, delta: i32) {
        self.asset_reference_family_filter = self.asset_reference_family_filter.next(delta);
        self.reset_asset_reference_selection_for_filter();
        self.status_message = format!(
            "Asset family filter: {}",
            self.asset_reference_family_filter.label()
        );
        self.log.event(&self.status_message);
    }

    pub(super) fn cycle_asset_reference_policy_filter(&mut self, delta: i32) {
        self.asset_reference_policy_filter = self.asset_reference_policy_filter.next(delta);
        self.reset_asset_reference_selection_for_filter();
        self.status_message = format!(
            "Asset policy filter: {}",
            self.asset_reference_policy_filter.label()
        );
        self.log.event(&self.status_message);
    }

    pub(super) fn reset_asset_reference_selection_for_filter(&mut self) {
        self.asset_reference_index = 0;
        self.asset_reference_scroll = 0;
        if let Ok(rows) = self.asset_reference_browser_rows() {
            self.ensure_asset_reference_selection_visible(rows.len());
        }
    }

    pub(super) fn select_asset_reference_row(&mut self, delta: i32) {
        let Ok(rows) = self.asset_reference_browser_rows() else {
            self.status_message = "Donor reference catalog unavailable".to_string();
            self.log.event(&self.status_message);
            return;
        };
        if rows.is_empty() {
            self.asset_reference_index = 0;
            self.asset_reference_scroll = 0;
            self.status_message = "No donor/reference assets match this filter".to_string();
            self.log.event(&self.status_message);
            return;
        }
        let current = self.asset_reference_index.min(rows.len() - 1) as i32;
        self.asset_reference_index = (current + delta).rem_euclid(rows.len() as i32) as usize;
        self.ensure_asset_reference_selection_visible(rows.len());
        self.status_message = format!(
            "Asset donor {}/{}: {}",
            self.asset_reference_index + 1,
            rows.len(),
            rows[self.asset_reference_index].display_name
        );
    }

    pub(super) fn ensure_asset_reference_selection_visible(&mut self, row_count: usize) {
        if row_count == 0 {
            self.asset_reference_index = 0;
            self.asset_reference_scroll = 0;
            return;
        }
        self.asset_reference_index = self.asset_reference_index.min(row_count - 1);
        if self.asset_reference_index < self.asset_reference_scroll {
            self.asset_reference_scroll = self.asset_reference_index;
        }
        if self.asset_reference_index >= self.asset_reference_scroll + ASSET_ROW_COUNT {
            self.asset_reference_scroll = self
                .asset_reference_index
                .saturating_sub(ASSET_ROW_COUNT - 1);
        }
    }

    pub(super) fn asset_reference_browser_rows(
        &self,
    ) -> Result<Vec<DonorReferenceAssetRecord>, String> {
        let catalog = load_donor_reference_asset_catalog(".")?;
        let mut rows: Vec<DonorReferenceAssetRecord> = catalog
            .records
            .into_iter()
            .filter(|record| self.asset_reference_grid_filter.matches(record))
            .filter(|record| self.asset_reference_family_filter.matches(record))
            .filter(|record| self.asset_reference_policy_filter.matches(record))
            .collect();
        rows.sort_by(|left, right| {
            left.display_name
                .cmp(&right.display_name)
                .then(left.id.cmp(&right.id))
        });
        Ok(rows)
    }

    pub(super) fn asset_reference_browser_summary_line(&self) -> String {
        match self.asset_reference_browser_rows() {
            Ok(rows) => {
                let prototype = rows
                    .iter()
                    .filter(|record| {
                        record_policy(record) == AssetReferencePolicy::PrototypeCandidate
                    })
                    .count();
                let blocked = rows
                    .iter()
                    .filter(|record| record_policy(record) == AssetReferencePolicy::Blocked)
                    .count();
                let availability = match load_asset_source_availability_report(".") {
                    Ok(report) => asset_source_availability_summary_line(&report),
                    Err(error) => format!("source availability report unavailable: {error}"),
                };
                let preview = match load_asset_reference_preview_catalog(".") {
                    Ok(catalog) => asset_reference_preview_summary_line(&catalog, "."),
                    Err(error) => format!("asset previews unavailable: {error}"),
                };
                format!(
                    "Donor catalog: {} shown | {} prototype candidate(s) | {} blocked/reference-gated | filters: {}, {}, {} | {} | {}",
                    rows.len(),
                    prototype,
                    blocked,
                    self.asset_reference_grid_filter.label(),
                    self.asset_reference_family_filter.label(),
                    self.asset_reference_policy_filter.label(),
                    availability,
                    preview
                )
            }
            Err(error) => format!("Donor reference catalog unavailable: {error}"),
        }
    }

    pub(super) fn asset_source_availability_for_record(
        &self,
        record: &DonorReferenceAssetRecord,
    ) -> AssetSourceAvailabilityRecord {
        match load_asset_source_availability_report(".") {
            Ok(report) => {
                let index = build_asset_source_availability_index(&report);
                availability_for_donor_record(record, &index)
            }
            Err(error) => AssetSourceAvailabilityRecord {
                external_source_id: record.external_source_id.clone(),
                state: AssetSourceAvailabilityState::Unknown,
                inputs_found: 0,
                inputs_total: 0,
                dry_run_entry_count: 0,
                report_path: PROTOTYPE_ASSET_LOCAL_BAKE_REPORT_PATH.to_string(),
                reason: format!("source availability report unavailable: {error}"),
            },
        }
    }

    pub(super) fn asset_local_import_instruction_for_record(
        &self,
        record: &DonorReferenceAssetRecord,
    ) -> AssetLocalImportInstructionRecord {
        match load_asset_local_import_instructions(".") {
            Ok(catalog) => {
                let index = build_asset_local_import_instruction_index(&catalog);
                asset_local_import_instruction_for_source(&record.external_source_id, &index)
            }
            Err(error) => AssetLocalImportInstructionRecord {
                external_source_id: record.external_source_id.clone(),
                display_name: record.display_name.clone(),
                local_import_status: "instruction_catalog_unavailable".to_string(),
                preferred_workspace_import_path: "WORKSPACE/imports/third_party/".to_string(),
                preferred_quarantine_path: "assets/reference_quarantine/third_party/".to_string(),
                accepted_input_files: Vec::new(),
                accepted_input_notes: vec![format!("instruction catalog unavailable: {error}")],
                dry_run_command: "python tools/automation/assets/DryRun-PrototypeAssetBakeV29.py"
                    .to_string(),
                editor_display: "show_error".to_string(),
                runtime_use_rule: "reference_only_until_instruction_catalog_loads".to_string(),
                instruction:
                    "Fix the local import instruction catalog before importing this source."
                        .to_string(),
            },
        }
    }

    pub(super) fn asset_reference_preview_for_record(
        &self,
        record: &DonorReferenceAssetRecord,
    ) -> AssetReferencePreviewRecord {
        match load_asset_reference_preview_catalog(".") {
            Ok(catalog) => {
                let index = build_asset_reference_preview_index(&catalog);
                asset_reference_preview_for_source(
                    &record.external_source_id,
                    &record.display_name,
                    &index,
                )
            }
            Err(error) => AssetReferencePreviewRecord {
                external_source_id: record.external_source_id.clone(),
                display_name: record.display_name.clone(),
                preview_status: "preview_catalog_unavailable".to_string(),
                preview_kind: "none".to_string(),
                safe_preview_path: "WORKSPACE/generated/asset_reference_previews/".to_string(),
                thumbnail_path: String::new(),
                contact_sheet_path: String::new(),
                generated_by: format!("preview catalog unavailable: {error}"),
                source_policy: "reference_only_until_preview_catalog_loads".to_string(),
                editor_display: "show_error".to_string(),
                notes: vec![
                    "Fix the asset reference preview catalog before previewing this source."
                        .to_string(),
                ],
            },
        }
    }

    pub(super) fn show_asset_reference_import_instruction_status(&mut self) {
        let Ok(rows) = self.asset_reference_browser_rows() else {
            self.status_message =
                "Donor reference catalog unavailable; cannot show import path".to_string();
            self.log.event(&self.status_message);
            return;
        };
        if rows.is_empty() {
            self.status_message =
                "No donor/reference asset selected for import instructions".to_string();
            self.log.event(&self.status_message);
            return;
        }
        let selected = self.asset_reference_index.min(rows.len() - 1);
        let instruction = self.asset_local_import_instruction_for_record(&rows[selected]);
        self.status_message = format!(
            "Place source at {} | expected {}",
            instruction.preferred_path_label(),
            shorten_asset_reference_text(&instruction.primary_input_label(), 70)
        );
        self.log.event(&self.status_message);
    }

    pub(super) fn show_asset_reference_preview_status(&mut self) {
        let Ok(rows) = self.asset_reference_browser_rows() else {
            self.status_message =
                "Donor reference catalog unavailable; cannot show preview path".to_string();
            self.log.event(&self.status_message);
            return;
        };
        if rows.is_empty() {
            self.status_message = "No donor/reference asset selected for preview".to_string();
            self.log.event(&self.status_message);
            return;
        }
        let selected = self.asset_reference_index.min(rows.len() - 1);
        let preview = self.asset_reference_preview_for_record(&rows[selected]);
        self.status_message = format!(
            "Preview {}: {} | {}",
            preview.availability_label("."),
            shorten_asset_reference_text(preview.preview_path_label(), 82),
            shorten_asset_reference_text(&preview.source_policy, 48)
        );
        self.log.event(&self.status_message);
    }

    pub(super) fn draw_asset_reference_browser_tab(&self, panel_x: f32) {
        draw_text(
            "Donor / Reference Asset Browser",
            panel_x + 18.0,
            104.0,
            17.0,
            Color::from_rgba(162, 228, 255, 255),
        );
        draw_text(
            "Browse local donor/reference sources for tile-size adaptation, editor reference, and safe prototype intake.",
            panel_x + 18.0,
            120.0,
            11.5,
            Color::from_rgba(202, 218, 216, 255),
        );

        for (label, x, w) in [
            ("Grid-", panel_x + 18.0, 86.0),
            ("Grid+", panel_x + 108.0, 86.0),
            ("Family-", panel_x + 208.0, 86.0),
            ("Family+", panel_x + 298.0, 86.0),
            ("Policy-", panel_x + 398.0, 86.0),
            ("Policy+", panel_x + 488.0, 86.0),
        ] {
            draw_editor_button(label, x, 124.0, w, 24.0);
        }
        for (label, x, w) in [
            ("Prev", panel_x + 18.0, 72.0),
            ("Next", panel_x + 96.0, 72.0),
            ("Refresh", panel_x + 178.0, 94.0),
            ("Path", panel_x + 282.0, 94.0),
            ("Preview", panel_x + 386.0, 94.0),
        ] {
            draw_editor_button(label, x, 154.0, w, 24.0);
        }

        draw_text(
            &format!(
                "Grid: {} | Family: {} | Policy: {}",
                self.asset_reference_grid_filter.label(),
                self.asset_reference_family_filter.label(),
                self.asset_reference_policy_filter.label()
            ),
            panel_x + 18.0,
            196.0,
            12.5,
            Color::from_rgba(244, 238, 201, 255),
        );
        draw_text(
            &format!(
                "Catalog: {} | Instructions: {} | Previews: {}",
                DONOR_REFERENCE_ASSET_CATALOG_PATH,
                ASSET_LOCAL_IMPORT_INSTRUCTIONS_PATH,
                ASSET_REFERENCE_PREVIEW_CATALOG_PATH
            ),
            panel_x + 18.0,
            212.0,
            10.5,
            Color::from_rgba(168, 190, 197, 255),
        );

        let rows = match self.asset_reference_browser_rows() {
            Ok(rows) => rows,
            Err(error) => {
                draw_text(
                    &format!("Donor reference catalog unavailable: {error}"),
                    panel_x + 18.0,
                    236.0,
                    13.0,
                    Color::from_rgba(255, 166, 122, 255),
                );
                return;
            }
        };

        if rows.is_empty() {
            draw_text(
                "No donor/reference assets match the current filters.",
                panel_x + 18.0,
                236.0,
                13.0,
                Color::from_rgba(224, 204, 151, 255),
            );
            return;
        }

        let selected = self.asset_reference_index.min(rows.len() - 1);
        let scroll = self.asset_reference_scroll.min(selected);
        draw_text(
            "source / display name                         grids  avail    policy       families",
            panel_x + 18.0,
            220.0,
            11.0,
            Color::from_rgba(168, 190, 197, 255),
        );
        for visible in 0..ASSET_ROW_COUNT {
            let row_index = scroll + visible;
            if row_index >= rows.len() {
                break;
            }
            let row = &rows[row_index];
            let y = 226.0 + visible as f32 * 24.0;
            let active = row_index == selected;
            if active {
                draw_rectangle(
                    panel_x + 15.0,
                    y - 16.0,
                    606.0,
                    21.0,
                    Color::from_rgba(76, 101, 78, 205),
                );
            }
            let availability = self.asset_source_availability_for_record(row);
            draw_asset_reference_browser_row(row, &availability, panel_x + 20.0, y, active);
        }

        let row = &rows[selected];
        let selected_availability = self.asset_source_availability_for_record(row);
        let selected_instruction = self.asset_local_import_instruction_for_record(row);
        let selected_preview = self.asset_reference_preview_for_record(row);
        let detail_y = 502.0;
        draw_rectangle(
            panel_x + 16.0,
            detail_y - 18.0,
            606.0,
            196.0,
            Color::from_rgba(18, 24, 24, 170),
        );
        draw_rectangle_lines(
            panel_x + 16.0,
            detail_y - 18.0,
            606.0,
            196.0,
            1.0,
            Color::from_rgba(112, 148, 138, 210),
        );
        draw_text(
            &format!(
                "Selected {}/{}: {}",
                selected + 1,
                rows.len(),
                row.display_name
            ),
            panel_x + 24.0,
            detail_y,
            13.0,
            Color::from_rgba(255, 232, 144, 255),
        );
        draw_text(
            &format!(
                "id {} | source {} | role {}",
                shorten_asset_reference_text(&row.id, 28),
                shorten_asset_reference_text(&row.external_source_id, 40),
                shorten_asset_reference_text(&row.catalog_role, 32)
            ),
            panel_x + 24.0,
            detail_y + 18.0,
            11.5,
            Color::from_rgba(220, 231, 226, 255),
        );
        draw_text(
            &format!(
                "grids {} | scale {} | policy {}",
                grids_label(row),
                shorten_asset_reference_text(&row.scale_adapter_modes.join(", "), 38),
                policy_label(record_policy(row))
            ),
            panel_x + 24.0,
            detail_y + 36.0,
            11.5,
            policy_color(record_policy(row)),
        );
        draw_text(
            &format!(
                "availability {} | inputs {}/{} | entries {}",
                selected_availability.state.label(),
                selected_availability.inputs_found,
                selected_availability.inputs_total,
                selected_availability.dry_run_entry_count
            ),
            panel_x + 24.0,
            detail_y + 54.0,
            10.5,
            availability_color(selected_availability.state),
        );
        draw_text(
            &format!(
                "editor {} | game-dev {} | lite-pixel {} | runtime {}",
                shorten_asset_reference_text(&row.editor_visibility.standalone_editor, 20),
                shorten_asset_reference_text(&row.editor_visibility.in_game_editor_dev_mode, 22),
                shorten_asset_reference_text(&row.editor_visibility.lite_pixel_editor_panel, 22),
                shorten_asset_reference_text(&row.editor_visibility.runtime_game_default, 26)
            ),
            panel_x + 24.0,
            detail_y + 72.0,
            10.5,
            Color::from_rgba(188, 214, 255, 255),
        );
        draw_text(
            &format!(
                "families: {}",
                shorten_asset_reference_text(&row.families.join(", "), 88)
            ),
            panel_x + 24.0,
            detail_y + 90.0,
            10.5,
            Color::from_rgba(207, 228, 196, 255),
        );
        let note = row
            .notes
            .first()
            .map(String::as_str)
            .unwrap_or("No notes recorded.");
        draw_text(
            &format!("note: {}", shorten_asset_reference_text(note, 92)),
            panel_x + 24.0,
            detail_y + 108.0,
            10.5,
            Color::from_rgba(212, 220, 202, 255),
        );
        draw_text(
            &format!(
                "bake note: {}",
                shorten_asset_reference_text(&selected_availability.reason, 88)
            ),
            panel_x + 24.0,
            detail_y + 124.0,
            10.0,
            availability_color(selected_availability.state),
        );
        draw_text(
            &format!(
                "local path: {}",
                shorten_asset_reference_text(&selected_instruction.preferred_path_label(), 84)
            ),
            panel_x + 24.0,
            detail_y + 140.0,
            10.0,
            Color::from_rgba(201, 232, 255, 255),
        );
        draw_text(
            &format!(
                "expected: {}",
                shorten_asset_reference_text(&selected_instruction.primary_input_label(), 86)
            ),
            panel_x + 24.0,
            detail_y + 156.0,
            10.0,
            import_instruction_color(&selected_instruction),
        );
        draw_text(
            &format!(
                "preview {}: {}",
                selected_preview.availability_label("."),
                shorten_asset_reference_text(selected_preview.preview_path_label(), 78)
            ),
            panel_x + 24.0,
            detail_y + 172.0,
            10.0,
            preview_color(selected_preview.preview_path_exists("."), &selected_preview),
        );
        draw_text(
            "Runtime use still requires bake + metadata + license approval.",
            panel_x + 24.0,
            detail_y + 188.0,
            10.0,
            Color::from_rgba(171, 218, 255, 255),
        );
    }
}

fn draw_asset_reference_browser_row(
    record: &DonorReferenceAssetRecord,
    availability: &AssetSourceAvailabilityRecord,
    x: f32,
    y: f32,
    active: bool,
) {
    let text_color = if active {
        Color::from_rgba(255, 246, 190, 255)
    } else {
        Color::from_rgba(220, 231, 236, 255)
    };
    draw_text(
        &shorten_asset_reference_text(&record.display_name, 34),
        x,
        y,
        11.5,
        text_color,
    );
    draw_text(
        &grids_label(record),
        x + 238.0,
        y,
        11.5,
        Color::from_rgba(204, 222, 218, 255),
    );
    draw_text(
        availability.state.short_label(),
        x + 292.0,
        y,
        11.5,
        availability_color(availability.state),
    );
    draw_text(
        policy_label(record_policy(record)),
        x + 356.0,
        y,
        11.5,
        policy_color(record_policy(record)),
    );
    draw_text(
        &shorten_asset_reference_text(&record.families.join(", "), 28),
        x + 438.0,
        y,
        11.5,
        Color::from_rgba(195, 218, 229, 255),
    );
}

fn record_has_grid(record: &DonorReferenceAssetRecord, size: u32) -> bool {
    record
        .tile_grid_profiles
        .iter()
        .any(|[w, h]| *w == size && *h == size)
}

fn record_has_family_prefix(record: &DonorReferenceAssetRecord, prefix: &str) -> bool {
    record.families.iter().any(|tag| tag.starts_with(prefix))
}

fn record_has_family_contains(record: &DonorReferenceAssetRecord, needle: &str) -> bool {
    record.families.iter().any(|tag| tag.contains(needle))
}

fn record_policy(record: &DonorReferenceAssetRecord) -> AssetReferencePolicy {
    let policy = record.prototype_ingest_policy.to_ascii_lowercase();
    let runtime = record
        .editor_visibility
        .runtime_game_default
        .to_ascii_lowercase();
    if policy.contains("blocked")
        || policy.contains("unverified")
        || policy.contains("non-commercial")
        || runtime == "blocked"
    {
        AssetReferencePolicy::Blocked
    } else if policy.contains("candidate") || runtime.contains("optional_prototype_runtime") {
        AssetReferencePolicy::PrototypeCandidate
    } else {
        AssetReferencePolicy::ReferenceOnly
    }
}

fn policy_label(policy: AssetReferencePolicy) -> &'static str {
    match policy {
        AssetReferencePolicy::PrototypeCandidate => "prototype",
        AssetReferencePolicy::ReferenceOnly => "reference",
        AssetReferencePolicy::Blocked => "blocked",
    }
}

fn policy_color(policy: AssetReferencePolicy) -> Color {
    match policy {
        AssetReferencePolicy::PrototypeCandidate => Color::from_rgba(178, 223, 189, 255),
        AssetReferencePolicy::ReferenceOnly => Color::from_rgba(255, 221, 174, 255),
        AssetReferencePolicy::Blocked => Color::from_rgba(255, 152, 128, 255),
    }
}

fn availability_color(state: AssetSourceAvailabilityState) -> Color {
    match state {
        AssetSourceAvailabilityState::Ready => Color::from_rgba(153, 235, 178, 255),
        AssetSourceAvailabilityState::MissingSource => Color::from_rgba(255, 213, 145, 255),
        AssetSourceAvailabilityState::RefusedBlockedSource => Color::from_rgba(255, 145, 128, 255),
        AssetSourceAvailabilityState::PlanError => Color::from_rgba(255, 110, 132, 255),
        AssetSourceAvailabilityState::Unknown => Color::from_rgba(176, 194, 204, 255),
    }
}

fn import_instruction_color(instruction: &AssetLocalImportInstructionRecord) -> Color {
    let status = instruction.local_import_status.to_ascii_lowercase();
    if status.contains("blocked") || status.contains("unverified") {
        Color::from_rgba(255, 148, 128, 255)
    } else if status.contains("candidate") {
        Color::from_rgba(173, 230, 186, 255)
    } else {
        Color::from_rgba(224, 210, 168, 255)
    }
}

fn preview_color(exists: bool, preview: &AssetReferencePreviewRecord) -> Color {
    if exists {
        Color::from_rgba(161, 229, 188, 255)
    } else if preview.is_reference_only() {
        Color::from_rgba(255, 201, 139, 255)
    } else {
        Color::from_rgba(183, 206, 217, 255)
    }
}

fn grids_label(record: &DonorReferenceAssetRecord) -> String {
    let mut parts = Vec::new();
    for [w, h] in &record.tile_grid_profiles {
        if w == h {
            parts.push(format!("{}", w));
        } else {
            parts.push(format!("{}x{}", w, h));
        }
    }
    if parts.is_empty() {
        "-".to_string()
    } else {
        parts.join("/")
    }
}

fn button_hit(mx: f32, my: f32, x: f32, y: f32, w: f32, h: f32) -> bool {
    mx >= x && mx <= x + w && my >= y && my <= y + h
}

fn shorten_asset_reference_text(value: &str, max_chars: usize) -> String {
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
