//! Candidate-only terrain/scene preflight. Never certifies the ElizaWy visual grammar.
use std::collections::{BTreeMap, BTreeSet};
use serde::Serialize;
use super::{AssemblyPiece, SourceAssetDocument, TerrainHeightCell, TILE_SIZE};

#[derive(Serialize)]
pub(super) struct SceneFinding {
    pub severity: &'static str,
    pub code: &'static str,
    pub coordinate: [i32; 2],
    pub detail: String,
}

#[derive(Serialize)]
pub(super) struct SceneAudit {
    pub schema: &'static str,
    pub certification_stage: &'static str,
    pub sources: usize,
    pub placements: usize,
    pub height_cells: usize,
    pub elevation_boundaries: usize,
    pub warnings: usize,
    pub errors: usize,
    pub findings: Vec<SceneFinding>,
}

pub(super) fn audit_scene(
    pieces: &[AssemblyPiece], cells: &[TerrainHeightCell], sources: &[SourceAssetDocument],
) -> SceneAudit {
    let known_sources: BTreeSet<&str> = sources.iter().map(|s| s.id.as_str()).collect();
    let mut unique_ids = BTreeSet::new();
    let mut heights = BTreeMap::new();
    let mut findings = Vec::new();
    for cell in cells {
        if heights.insert((cell.x, cell.y), cell.elevation).is_some() {
            findings.push(SceneFinding { severity: "error", code: "duplicate_height_cell",
                coordinate: [cell.x, cell.y], detail: "Two height records describe one grid cell.".into() });
        }
        if cell.elevation > 30 || cell.water_surface.is_some_and(|water| water > 30) {
            findings.push(SceneFinding { severity: "error", code: "elevation_out_of_range",
                coordinate: [cell.x, cell.y], detail: "Only real levels 0 through +30 are supported.".into() });
        }
    }
    for piece in pieces {
        let position = [piece.canvas_grid_x, piece.canvas_grid_y];
        if !unique_ids.insert(piece.id) {
            findings.push(SceneFinding { severity: "error", code: "duplicate_piece_id", coordinate: position,
                detail: format!("Piece ID {} is reused.", piece.id) });
        }
        if !known_sources.contains(piece.source_asset_id.as_str()) {
            findings.push(SceneFinding { severity: "error", code: "missing_source", coordinate: position,
                detail: format!("Piece {} has no activated source {}.", piece.id, piece.source_asset_id) });
        }
        if piece.source_rect[2] != TILE_SIZE || piece.source_rect[3] != TILE_SIZE
            || piece.source_rect[0] < 0 || piece.source_rect[1] < 0
            || piece.rotation_degrees.rem_euclid(90) != 0
        {
            findings.push(SceneFinding { severity: "error", code: "invalid_source_transform", coordinate: position,
                detail: format!("Piece {} uses an unsupported source crop/rotation.", piece.id) });
        }
    }
    let mut boundaries = 0;
    for (&(x, y), &elevation) in &heights {
        // Count each physical boundary once; no old minimum-two-cliff normalization.
        for neighbor in [(x.saturating_add(1), y), (x, y.saturating_add(1))] {
            if let Some(&adjacent) = heights.get(&neighbor) {
                if adjacent != elevation { boundaries += 1; }
            }
        }
    }
    if boundaries > 0 {
        findings.push(SceneFinding { severity: "warning", code: "height_boundary_recipe_pending",
            coordinate: [0, 0], detail: format!(
                "{boundaries} elevation boundaries require source-exact cliff/contact recipes, including +1, ocean feet and traversal. This audit does not invent them."
            ) });
    }
    if cells.iter().any(|cell| cell.water_surface.is_some()) {
        findings.push(SceneFinding { severity: "warning", code: "hydrology_recipe_pending",
            coordinate: [0, 0], detail: "Water marked on the heightmap; verify bank, basin, waterfall, source connectivity and collision in the scene before approval.".into() });
    }
    let errors = findings.iter().filter(|finding| finding.severity == "error").count();
    let warnings = findings.iter().filter(|finding| finding.severity == "warning").count();
    SceneAudit {
        schema: "havenwild.mapper_scene_audit.v0_1",
        certification_stage: "unreviewed_candidate_no_runtime_publication",
        sources: sources.len(), placements: pieces.len(), height_cells: cells.len(),
        elevation_boundaries: boundaries, warnings, errors, findings,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn one_level_ocean_facing_cliff_is_a_real_boundary_not_an_error() {
        let cells = vec![
            TerrainHeightCell { x: 0, y: 0, elevation: 0, water_surface: Some(0) },
            TerrainHeightCell { x: 1, y: 0, elevation: 1, water_surface: None },
            TerrainHeightCell { x: 2, y: 0, elevation: 30, water_surface: None },
        ];
        let report = audit_scene(&[], &cells, &[]);
        assert_eq!(report.errors, 0);
        assert_eq!(report.elevation_boundaries, 2);
        assert!(report.warnings > 0); // Not visually certified.
    }
    #[test]
    fn repeated_height_cell_is_a_hard_error() {
        let cell = TerrainHeightCell { x: 0, y: 0, elevation: 1, water_surface: None };
        assert_eq!(audit_scene(&[], &[cell.clone(), cell], &[]).errors, 1);
    }
}
