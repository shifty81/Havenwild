use super::brush_authoring::BrushMode;
use super::pixel_studio::PALETTE;
use super::*;
use haven_assets::asset_intake::repo_root_dir;
use haven_assets::asset_palette::AssetPaletteEntry;
use haven_assets::category_metadata::TerrainMatchMode;
use haven_assets::terrain_variant_authoring::TerrainVariantDraft;
use haven_pixel::{NewPixelDocumentSpec, PixelDocument, PixelDocumentKind, PixelLicense, PixelSelection};
use std::path::{Path, PathBuf};

const DRAFT_ROOT: &str = ".local/editor/terrain_variant_drafts";
const OUTPUT_ROOT: &str = "assets/source/original/pixel_studio/terrain_variants";

pub(crate) fn terrain_palette_actions_available(mode: BrushMode) -> bool {
    matches!(
        mode,
        BrushMode::SemanticTerrain
            | BrushMode::Autotile
            | BrushMode::TerrainElevation
            | BrushMode::ExactTile
            | BrushMode::Hydrology
    )
}

pub(crate) fn terrain_new_tile_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + rect.w - 238.0, rect.y + 3.0, 66.0, 22.0)
}

pub(crate) fn terrain_variant_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + rect.w - 168.0, rect.y + 3.0, 78.0, 22.0)
}

pub(crate) fn terrain_coverage_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + rect.w - 86.0, rect.y + 3.0, 78.0, 22.0)
}

impl EditorApp {
    pub(crate) fn selected_canvas_asset_entry(&self) -> Option<AssetPaletteEntry> {
        let selected = self.canvas_authoring_context.source_id.as_deref()?;
        self.canvas_brush_asset_entries()
            .into_iter()
            .find(|entry| entry.stable_id == selected)
    }

    pub(crate) fn create_blank_terrain_tile_draft(&mut self) {
        let semantic = self
            .world_selected_material_code()
            .unwrap_or("Terrain_New")
            .to_string();
        let terrain_set = terrain_set_for_semantic(&semantic).to_string();
        let slug = slugify(&semantic);
        let root = repo_root_dir();
        let (draft_id, output_path) = next_draft_identity(&root, &slug, "tile");
        let display_name = format!("{} Tile Draft", humanize(&semantic));

        let mut spec = NewPixelDocumentSpec::for_kind(PixelDocumentKind::Tile);
        spec.display_name = display_name.clone();
        let mut document = match spec.create_document() {
            Ok(document) => document,
            Err(error) => {
                self.status_message = format!("Unable to create terrain tile draft: {error}");
                return;
            }
        };
        document.metadata.asset_id = draft_id.clone();
        document.metadata.output_path = output_path.clone();
        document.metadata.palette = PALETTE.to_vec();
        document.metadata.tags.extend([
            "terrain_authoring_draft".to_string(),
            "terrain_new_tile".to_string(),
            format!("semantic_terrain:{}", semantic),
            format!("terrain_set:{}", terrain_set),
            "variant_weight:1".to_string(),
            "pcg_approved:false".to_string(),
        ]);
        document.dirty = true;

        let draft = TerrainVariantDraft::blank_tile(
            draft_id.clone(),
            display_name,
            semantic.clone(),
            terrain_set,
            TerrainMatchMode::SidesOnly,
            output_path,
        );
        if let Err(error) = save_draft_record(&root, &draft) {
            self.status_message = format!("Unable to record terrain tile draft: {error}");
            return;
        }
        self.open_terrain_draft_in_pixel_studio(document);
        self.status_message = format!(
            "New {} tile draft opened in Pixel Studio — semantic/gameplay authority stays separate until promotion",
            humanize(&semantic)
        );
    }

    pub(crate) fn create_selected_terrain_variant_draft(&mut self) {
        let Some(entry) = self.selected_canvas_asset_entry() else {
            self.status_message = "Select a terrain tile in the Palette before creating a variant".to_string();
            return;
        };
        let (Some(sheet), Some(rect)) = (entry.sheet.clone(), entry.rect) else {
            self.status_message = format!("{} does not expose an editable atlas source", entry.label);
            return;
        };
        let source_path = resolve_project_path(&sheet);
        let source_region = PixelSelection {
            x: rect.x.round().max(0.0) as u32,
            y: rect.y.round().max(0.0) as u32,
            width: rect.w.round().max(1.0) as u32,
            height: rect.h.round().max(1.0) as u32,
        };
        let semantic = self
            .world_selected_material_code()
            .map(str::to_string)
            .unwrap_or_else(|| entry.stable_id.clone());
        let terrain_set = terrain_set_for_semantic(&semantic).to_string();
        let root = repo_root_dir();
        let base_slug = slugify(&entry.stable_id);
        let (draft_id, output_path) = next_draft_identity(&root, &base_slug, "variant");
        let display_name = format!("{} Variant", entry.label);

        let mut document = match PixelDocument::load_source_region(
            &source_path,
            source_region,
            display_name.clone(),
            PixelLicense::default(),
        ) {
            Ok(document) => document,
            Err(error) => {
                self.status_message = format!("Unable to derive terrain variant from {}: {error}", entry.label);
                return;
            }
        };
        document.metadata.asset_id = draft_id.clone();
        document.metadata.output_path = output_path.clone();
        document.metadata.palette = if document.metadata.palette.is_empty() {
            PALETTE.to_vec()
        } else {
            document.metadata.palette.clone()
        };
        let document_width = document.width();
        let document_height = document.height();
        document.metadata.grid.cell_width = document_width.min(32).max(1);
        document.metadata.grid.cell_height = document_height.min(32).max(1);
        document.metadata.selection = PixelSelection {
            x: 0,
            y: 0,
            width: document_width,
            height: document_height,
        };
        document.metadata.tags.extend([
            "terrain_authoring_draft".to_string(),
            "terrain_derived_variant".to_string(),
            format!("parent_asset:{}", entry.stable_id),
            format!("semantic_terrain:{}", semantic),
            format!("terrain_set:{}", terrain_set),
            "inherit:semantic_identity".to_string(),
            "inherit:terrain_pattern".to_string(),
            "inherit:gameplay_properties".to_string(),
            "inherit:provenance".to_string(),
            "inherit:pcg_tags".to_string(),
            "variant_weight:1".to_string(),
            "pcg_approved:false".to_string(),
        ]);
        document.dirty = true;

        let draft = TerrainVariantDraft::derived_variant(
            draft_id,
            display_name,
            entry.stable_id.clone(),
            semantic,
            terrain_set,
            TerrainMatchMode::SidesOnly,
            sheet,
            [
                rect.x.round().max(0.0) as u32,
                rect.y.round().max(0.0) as u32,
                rect.w.round().max(1.0) as u32,
                rect.h.round().max(1.0) as u32,
            ],
            output_path,
        );
        if let Err(error) = save_draft_record(&root, &draft) {
            self.status_message = format!("Unable to record terrain variant draft: {error}");
            return;
        }
        self.open_terrain_draft_in_pixel_studio(document);
        self.status_message = format!(
            "Created non-destructive variant of {} — parent atlas pixels remain immutable; save/edit this project-owned draft in Pixel Studio",
            entry.label
        );
    }

    pub(crate) fn open_terrain_pattern_coverage(&mut self) {
        self.reveal_terrain_transition_lab();
        self.status_message = format!(
            "Terrain Coverage — inspect exact/missing transition patterns in the existing W77 authoring lab; missing patterns open as Pixel Studio repair documents. {}",
            self.status_message
        );
    }

    fn open_terrain_draft_in_pixel_studio(&mut self, document: PixelDocument) {
        self.pixel_studio.open_document_session(document);
        self.pixel_studio.reset_authoring_defaults();
        self.pixel_studio.world_asset_context = None;
        self.pixel_studio.animation_context = None;
        self.pixel_studio.show_atlas_grid = false;
        self.pixel_studio.refresh_texture();
        self.viewport_mode = EditorViewportMode::PixelStudio;
        self.pixel_studio.frame_document(self.pixel_canvas_rect());
    }
}

fn save_draft_record(root: &Path, draft: &TerrainVariantDraft) -> Result<(), String> {
    draft.save(root.join(DRAFT_ROOT).join(format!("{}.json", draft.draft_id)))
}

fn next_draft_identity(root: &Path, base: &str, role: &str) -> (String, String) {
    for index in 1..=9_999u32 {
        let id = format!("terrain_{}_{}_{:03}", base, role, index);
        let output = format!("{OUTPUT_ROOT}/{id}.png");
        if !root.join(&output).exists()
            && !root.join(DRAFT_ROOT).join(format!("{id}.json")).exists()
        {
            return (id, output);
        }
    }
    let id = format!("terrain_{}_{}_overflow", base, role);
    (id.clone(), format!("{OUTPUT_ROOT}/{id}.png"))
}

fn terrain_set_for_semantic(semantic: &str) -> &'static str {
    let value = semantic.to_ascii_lowercase();
    if value.contains("water") || value.contains("ocean") || value.contains("shore") {
        "water"
    } else if value.contains("road") || value.contains("path") || value.contains("gravel") {
        "path"
    } else {
        "natural_ground"
    }
}

fn resolve_project_path(path: &str) -> PathBuf {
    let candidate = PathBuf::from(path);
    if candidate.is_absolute() { candidate } else { repo_root_dir().join(candidate) }
}

fn slugify(value: &str) -> String {
    let slug = value
        .chars()
        .map(|ch| if ch.is_ascii_alphanumeric() { ch.to_ascii_lowercase() } else { '_' })
        .collect::<String>();
    let slug = slug
        .split('_')
        .filter(|part| !part.is_empty())
        .collect::<Vec<_>>()
        .join("_");
    if slug.is_empty() { "terrain".to_string() } else { slug }
}

fn humanize(value: &str) -> String {
    value.replace('_', " ")
}
