#![allow(dead_code)] // Asset authority contracts are consumed incrementally.
use super::*;
use super::render_helpers::{draw_editor_widget, draw_list_row, draw_tab_widget};
use haven_assets::asset_palette::{AssetPaletteCatalog, AssetPaletteEntry, AssetPaletteKind};
use haven_assets::placeable_asset_registry::{PublishedWorldAssetDefinition, PublishedWorldAssetRegistry};
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Path, PathBuf};

pub(crate) const PCC_ASSET_CATALOG_PATH: &str = "artifacts/asset-intake/asset-catalog.json";

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub(crate) enum AssetsStudioSection {
    #[default]
    Inbox,
    Library,
    Sources,
    Families,
    Usage,
    Review,
}

impl AssetsStudioSection {
    pub(crate) const ALL: [Self; 6] = [
        Self::Inbox,
        Self::Library,
        Self::Sources,
        Self::Families,
        Self::Usage,
        Self::Review,
    ];

    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Inbox => "Inbox",
            Self::Library => "Library",
            Self::Sources => "Sources",
            Self::Families => "Families",
            Self::Usage => "Usage",
            Self::Review => "Review",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub(crate) enum AssetAuthorityState {
    Discovered,
    Identified,
    Mapped,
    Validated,
    Certified,
    Deprecated,
    Broken,
}

impl AssetAuthorityState {
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Discovered => "Discovered",
            Self::Identified => "Identified",
            Self::Mapped => "Mapped",
            Self::Validated => "Validated",
            Self::Certified => "Certified",
            Self::Deprecated => "Deprecated",
            Self::Broken => "Broken",
        }
    }
}

/// Human-facing lifecycle for asset understanding.
///
/// This deliberately separates mechanical source discovery from gameplay
/// authority. A sheet or 32x32 addressable cell is not a runtime asset until
/// its component boundary, semantic role, footprint/topology and provenance
/// are understood and certified.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum AssetUnderstandingStage {
    SourceOnly,
    Sliced,
    SemanticallyMapped,
    RuntimeCertified,
    RejectedOrDeprecated,
}

impl AssetUnderstandingStage {
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::SourceOnly => "SOURCE ONLY",
            Self::Sliced => "SLICED",
            Self::SemanticallyMapped => "SEMANTICALLY MAPPED",
            Self::RuntimeCertified => "RUNTIME CERTIFIED",
            Self::RejectedOrDeprecated => "REJECTED / DEPRECATED",
        }
    }

    pub(crate) fn from_assembly(assembly: &AssetAssemblySummary) -> Self {
        if matches!(assembly.certification.as_str(), "rejected" | "deprecated") {
            return Self::RejectedOrDeprecated;
        }
        if assembly.certification == "runtime_certified" {
            return Self::RuntimeCertified;
        }
        if !assembly.semantic_role.trim().is_empty() {
            return Self::SemanticallyMapped;
        }
        if !assembly.assembly_id.trim().is_empty() {
            return Self::Sliced;
        }
        Self::SourceOnly
    }
}

#[derive(Clone, Debug, Default)]
pub(crate) struct AssetsStudioCatalog {
    pub path: PathBuf,
    pub generated_utc: String,
    pub detail_store: String,
    pub discovered_files: u64,
    pub png_files: u64,
    pub sheet_count: u64,
    pub assembly_count: u64,
    pub error_count: u64,
    pub sheets: Vec<AssetSheetSummary>,
    pub assemblies: Vec<AssetAssemblySummary>,
    pub family_counts: BTreeMap<String, usize>,
}

#[derive(Clone, Debug, Default)]
pub(crate) struct AssetSheetSummary {
    pub source: String,
    pub sha256: String,
    pub width: u64,
    pub height: u64,
    pub classification: String,
    pub assemblies: u64,
}

#[derive(Clone, Debug, Default)]
pub(crate) struct AssetAssemblySummary {
    pub asset_id: String,
    pub source: String,
    pub assembly_id: String,
    pub semantic_role: String,
    pub certification: String,
    pub footprint: String,
}

#[derive(Default)]
pub(crate) struct AssetsStudioState {
    pub section: AssetsStudioSection,
    pub catalog: AssetsStudioCatalog,
    pub load_error: Option<String>,
    pub selected_row: usize,
    pub scroll: usize,
    pub loaded: bool,
}

impl AssetsStudioState {
    pub(crate) fn ensure_loaded(&mut self, repo_root: &Path) {
        if self.loaded {
            return;
        }
        self.reload(repo_root);
    }

    pub(crate) fn reload(&mut self, repo_root: &Path) {
        let path = repo_root.join(PCC_ASSET_CATALOG_PATH);
        self.loaded = true;
        match load_compact_catalog(&path) {
            Ok(catalog) => {
                self.catalog = catalog;
                self.load_error = None;
                self.selected_row = 0;
                self.scroll = 0;
            }
            Err(error) => {
                self.catalog = AssetsStudioCatalog {
                    path,
                    ..Default::default()
                };
                self.load_error = Some(error);
            }
        }
    }

    pub(crate) fn review_count(&self) -> usize {
        self.catalog
            .assemblies
            .iter()
            .filter(|a| {
                !matches!(
                    AssetUnderstandingStage::from_assembly(a),
                    AssetUnderstandingStage::RuntimeCertified
                        | AssetUnderstandingStage::RejectedOrDeprecated
                )
            })
            .count()
    }

    pub(crate) fn certified_count(&self) -> usize {
        self.catalog
            .assemblies
            .iter()
            .filter(|a| {
                AssetUnderstandingStage::from_assembly(a)
                    == AssetUnderstandingStage::RuntimeCertified
            })
            .count()
    }

    pub(crate) fn sliced_count(&self) -> usize {
        self.catalog
            .assemblies
            .iter()
            .filter(|a| {
                AssetUnderstandingStage::from_assembly(a) == AssetUnderstandingStage::Sliced
            })
            .count()
    }

    pub(crate) fn mapped_count(&self) -> usize {
        self.catalog
            .assemblies
            .iter()
            .filter(|a| {
                AssetUnderstandingStage::from_assembly(a)
                    == AssetUnderstandingStage::SemanticallyMapped
            })
            .count()
    }
}

// A fixed selection inspector lives below the scrollable list. Keep input,
// rendering and wheel clamping in agreement so no invisible row is selectable.
fn asset_studio_list_capacity(body_height: f32, row_height: f32) -> usize {
    ((body_height - 252.0).max(0.0) / row_height).floor().max(1.0) as usize
}

fn asset_studio_max_scroll(count: usize, visible: usize) -> usize {
    count.saturating_sub(visible)
}

fn asset_studio_reload_rect(body: Rect) -> Rect {
    Rect::new(
        body.x + (body.w - 154.0).max(4.0),
        body.y + 5.0,
        142.0,
        28.0,
    )
}

fn asset_studio_selection_rect(body: Rect) -> Rect {
    Rect::new(
        body.x + 8.0,
        body.y + body.h - 164.0,
        (body.w - 16.0).max(1.0),
        156.0,
    )
}

fn asset_studio_use_on_canvas_rect(selection: Rect) -> Rect {
    Rect::new(
        selection.x + (selection.w - 176.0).max(88.0),
        selection.y + 8.0,
        166.0,
        28.0,
    )
}

// A visually sampled roof module belongs to a building recipe. An object-kind
// compatibility adapter (often Crate) is not permission to stamp it onto soil.
fn asset_studio_requires_building_recipe(definition: &PublishedWorldAssetDefinition) -> bool {
    definition.placement_tags.iter().any(|tag| tag == "roof")
        && !definition.allowed_surfaces.is_empty()
        && definition.allowed_surfaces.iter().all(|surface| surface == "roof" || surface == "building")
}

fn asset_studio_handoff_warning(
    stable_id: &str,
    registry: &PublishedWorldAssetRegistry,
) -> Option<String> {
    let definition = registry.entry(stable_id)?;
    asset_studio_requires_building_recipe(definition).then(|| format!(
        "{} is a {:?} roof component ({:?}); use building/roof recipe authoring, not free placement on an overworld tile",
        definition.label, definition.role, definition.certification,
    ))
}

fn asset_studio_published_label(
    stable_id: &str,
    registry: &PublishedWorldAssetRegistry,
) -> String {
    registry.entry(stable_id).map(|definition| {
        format!("{:?} / {:?}", definition.role, definition.certification)
    }).unwrap_or_else(|| "texture ready".to_string())
}

fn palette_runtime_entries(catalog: &AssetPaletteCatalog) -> Vec<&AssetPaletteEntry> {
    catalog
        .entries()
        .iter()
        .filter(|entry| {
            entry.runtime_ready() && !matches!(entry.kind, AssetPaletteKind::SourceReference)
        })
        .collect()
}

fn palette_source_entries(catalog: &AssetPaletteCatalog) -> Vec<&AssetPaletteEntry> {
    catalog
        .entries()
        .iter()
        .filter(|entry| matches!(entry.kind, AssetPaletteKind::SourceReference))
        .collect()
}

fn u64_at(v: &Value, key: &str) -> u64 {
    v.get(key).and_then(Value::as_u64).unwrap_or(0)
}

fn str_at(v: &Value, key: &str) -> String {
    v.get(key)
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string()
}

fn display_json(v: Option<&Value>) -> String {
    match v {
        Some(Value::String(s)) => s.clone(),
        Some(v) => v.to_string(),
        None => String::new(),
    }
}

// The existing published topology registry is the authoritative source of
// runtime-certified terrain/water/cliff IDs in both full and fallback views.
fn append_published_world_assets(
    assemblies: &mut Vec<AssetAssemblySummary>,
    family_counts: &mut BTreeMap<String, usize>,
) -> Result<(), String> {
    let published = haven_assets::published_world_topology::published_world_topology_registry_v1()
        .map_err(|error| error.to_string())?;
    for entry in published.entries() {
        if assemblies
            .iter()
            .any(|existing| existing.asset_id == entry.id)
        {
            continue;
        }
        *family_counts
            .entry(format!("{:?}", entry.domain).to_ascii_lowercase())
            .or_insert(0) += 1;
        assemblies.push(AssetAssemblySummary {
            asset_id: entry.id.clone(),
            source: entry.source_path.clone(),
            assembly_id: format!(
                "rect:{}:{}:{}:{}",
                entry.source_rect_cells[0],
                entry.source_rect_cells[1],
                entry.source_rect_cells[2],
                entry.source_rect_cells[3]
            ),
            semantic_role: entry.semantic_role.clone(),
            certification: "runtime_certified".to_string(),
            footprint: format!(
                "{}x{} source cells",
                entry.source_rect_cells[2],
                entry.source_rect_cells[3]
            ),
        });
    }
    Ok(())
}

fn load_compact_catalog(path: &Path) -> Result<AssetsStudioCatalog, String> {
    let raw = match fs::read_to_string(path) {
        Ok(raw) => raw,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            // The canonical intake catalog is generated on demand, not a
            // source-controlled prerequisite for opening the Assets studio.
            // Publish only assets from the existing validated runtime registry;
            // never relabel arbitrary sheet cells as runtime-certified.
            let mut catalog = AssetsStudioCatalog {
                path: path.to_path_buf(),
                generated_utc: "PCC intake scan not generated (published registry only)".to_string(),
                ..Default::default()
            };
            append_published_world_assets(
                &mut catalog.assemblies,
                &mut catalog.family_counts,
            ).map_err(|registry_error| format!(
                "Asset intake catalog unavailable at {}; published registry: {registry_error}",
                path.display(),
            ))?;
            return Ok(catalog);
        }
        Err(error) => return Err(format!(
            "Asset catalog unavailable at {}: {error}", path.display(),
        )),
    };
    let root: Value =
        serde_json::from_str(&raw).map_err(|e| format!("Asset catalog parse failed: {e}"))?;
    let summary = root.get("summary").unwrap_or(&Value::Null);
    let detail_store = root
        .get("storage")
        .and_then(|s| s.get("detailStore"))
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();

    let mut sheets = Vec::new();
    for sheet in root
        .get("sheets")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
    {
        let source = sheet.get("source").unwrap_or(&Value::Null);
        sheets.push(AssetSheetSummary {
            source: str_at(source, "relativePath"),
            sha256: str_at(source, "sha256"),
            width: u64_at(source, "width"),
            height: u64_at(source, "height"),
            classification: display_json(sheet.get("classification")),
            assemblies: u64_at(sheet, "assemblyCount"),
        });
    }

    let mut assemblies = Vec::new();
    let mut family_counts = BTreeMap::new();
    for item in root
        .get("assemblyIndex")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
    {
        let source = str_at(item, "source");
        let family = source
            .rsplit_once('/')
            .map(|(parent, _)| parent.rsplit('/').next().unwrap_or(parent))
            .unwrap_or("root")
            .to_string();
        *family_counts.entry(family).or_insert(0) += 1;
        assemblies.push(AssetAssemblySummary {
            asset_id: str_at(item, "assetId"),
            source,
            assembly_id: str_at(item, "assembly_id"),
            semantic_role: display_json(item.get("semantic_role")),
            certification: str_at(item, "certification"),
            footprint: display_json(item.get("footprint")),
        });
    }

    append_published_world_assets(&mut assemblies, &mut family_counts)
        .map_err(|error| format!("Published world asset registry unavailable: {error}"))?;

    Ok(AssetsStudioCatalog {
        path: path.to_path_buf(),
        generated_utc: str_at(&root, "generatedUtc"),
        detail_store,
        discovered_files: u64_at(summary, "discoveredFileCount"),
        png_files: u64_at(summary, "pngFileCount"),
        sheet_count: u64_at(summary, "pngSheetCount"),
        assembly_count: u64_at(summary, "assemblyCandidateCount"),
        error_count: u64_at(summary, "errorCount"),
        sheets,
        assemblies,
        family_counts,
    })
}

impl EditorApp {
    pub(crate) fn open_assets_studio(&mut self) {
        self.asset_studio_open = true;
        self.text_focus = EditorTextFocus::None;
        self.assets_studio.ensure_loaded(&repo_root_dir());
        let palette_ready = palette_runtime_entries(&self.asset_catalog).len();
        let source_refs = palette_source_entries(&self.asset_catalog).len();
        self.status_message = format!(
            "Assets workspace | {palette_ready} runtime-ready palette assets | {source_refs} LPC source references | {} topology certified",
            self.assets_studio.certified_count()
        );
    }

    pub(crate) fn close_assets_studio(&mut self) {
        self.asset_studio_open = false;
    }

    pub(crate) fn draw_assets_workspace(&mut self, rect: Rect) {
        self.assets_studio.ensure_loaded(&repo_root_dir());
        let pad = 12.0;
        let tabs_y = rect.y + 8.0;
        let tab_w = ((rect.w - pad * 2.0 - 5.0 * 6.0) / 6.0).max(70.0);
        for (i, section) in AssetsStudioSection::ALL.into_iter().enumerate() {
            let r = Rect::new(
                rect.x + pad + i as f32 * (tab_w + 5.0),
                tabs_y,
                tab_w,
                28.0,
            );
            draw_tab_widget(r, section.label(), self.assets_studio.section == section);
        }
        let body = Rect::new(
            rect.x + pad,
            tabs_y + 38.0,
            (rect.w - pad * 2.0).max(1.0),
            (rect.h - 52.0).max(1.0),
        );
        draw_rectangle(
            body.x,
            body.y,
            body.w,
            body.h,
            editor_theme::colors::PANEL_BG,
        );
        // Refresh is an explicit action: never rescan sources during drawing.
        draw_editor_widget(asset_studio_reload_rect(body), "Refresh Catalog", false);
        if let Some(error) = self.assets_studio.load_error.as_ref() {
            draw_editor_text(
                "Assets catalog unavailable",
                body.x + 12.0,
                body.y + 24.0,
                18.0,
                editor_theme::colors::WARN,
            );
            draw_scissored_text(
                error,
                body.x + 12.0,
                body.y + 48.0,
                body.w - 24.0,
                13.0,
                TEXT,
            );
            draw_scissored_text(
                "Run PCC Asset Authority scan/refresh; the editor does not silently invent replacement assets.",
                body.x + 12.0,
                body.y + 72.0,
                body.w - 24.0,
                13.0,
                MUTED,
            );
            return;
        }
        self.draw_assets_section(body);
    }

    fn draw_assets_section(&self, body: Rect) {
        let c = &self.assets_studio.catalog;
        draw_editor_text(
            self.assets_studio.section.label(),
            body.x + 12.0,
            body.y + 24.0,
            18.0,
            TEXT,
        );
        draw_scissored_text(
            &format!(
                "Catalog {} | {} palette ready | {} LPC sources | {} topology certified | {} intake review",
                c.generated_utc,
                palette_runtime_entries(&self.asset_catalog).len(),
                palette_source_entries(&self.asset_catalog).len(),
                self.assets_studio.certified_count(),
                self.assets_studio.review_count()
            ),
            body.x + 12.0,
            body.y + 47.0,
            (body.w - 24.0).max(1.0),
            12.0,
            MUTED,
        );
        let mut y = body.y + 72.0;

        match self.assets_studio.section {
            AssetsStudioSection::Inbox => {
                for line in [
                    format!("PCC intake catalog: {}", c.path.display()),
                    if c.generated_utc.contains("not generated") {
                        "Intake scan has not been run; canonical palette and published runtime registries remain available.".to_string()
                    } else {
                        "Intake catalog loaded; Library uses the same canonical palette authority as Game Canvas.".to_string()
                    },
                    format!(
                        "Canonical editor palette: {} runtime-ready assets | {} LPC source references",
                        palette_runtime_entries(&self.asset_catalog).len(),
                        palette_source_entries(&self.asset_catalog).len()
                    ),
                    format!(
                        "Detailed authority store: {}",
                        if c.detail_store.is_empty() {
                            "not declared"
                        } else {
                            &c.detail_store
                        }
                    ),
                    format!(
                        "Discovered files: {} | PNG: {} | errors: {}",
                        c.discovered_files, c.png_files, c.error_count
                    ),
                    "Raw source is immutable. Mechanical 32x32 indexing is only an address system, not gameplay authority.".to_string(),
                    "Promotion lifecycle: SOURCE ONLY -> SLICED -> SEMANTICALLY MAPPED -> RUNTIME CERTIFIED.".to_string(),
                ] {
                    draw_scissored_text(
                        &line,
                        body.x + 12.0,
                        y,
                        body.w - 24.0,
                        14.0,
                        TEXT,
                    );
                    y += 25.0;
                }
            }
            AssetsStudioSection::Library => {
                let ready = palette_runtime_entries(&self.asset_catalog);
                let start = self.assets_studio.scroll.min(ready.len());
                for (slot, entry) in ready
                    .into_iter()
                    .skip(start)
                    .take(asset_studio_list_capacity(body.h, 38.0))
                    .enumerate()
                {
                    let r = Rect::new(body.x + 12.0, y - 18.0, body.w - 24.0, 34.0);
                    let sheet = entry.sheet.as_deref().unwrap_or("no sheet");
                    draw_list_row(
                        r,
                        &entry.label,
                        Some(&format!(
                            "TEXTURE | {} | {} | {} | {}",
                            entry.stable_id,
                            asset_studio_published_label(&entry.stable_id, &self.placeable_registry),
                            entry.provenance.label(),
                            sheet
                        )),
                        self.assets_studio.selected_row == start + slot,
                    );
                    y += 38.0;
                }
            }
            AssetsStudioSection::Sources => {
                let sources = palette_source_entries(&self.asset_catalog);
                let start = self.assets_studio.scroll.min(sources.len());
                for (slot, entry) in sources
                    .into_iter()
                    .skip(start)
                    .take(asset_studio_list_capacity(body.h, 34.0))
                    .enumerate()
                {
                    let r = Rect::new(body.x + 12.0, y - 18.0, body.w - 24.0, 30.0);
                    let source = entry.sheet.as_deref().unwrap_or("source mount unavailable");
                    draw_list_row(
                        r,
                        &entry.label,
                        Some(&format!(
                            "LPC SOURCE | {} | {} | {}",
                            entry.stable_id,
                            entry.category.label(),
                            source
                        )),
                        self.assets_studio.selected_row == start + slot,
                    );
                    y += 34.0;
                }
            }
            AssetsStudioSection::Families => {
                for (slot, (family, count)) in c
                    .family_counts
                    .iter()
                    .skip(self.assets_studio.scroll)
                    .take(asset_studio_list_capacity(body.h, 34.0))
                    .enumerate()
                {
                    let r = Rect::new(body.x + 12.0, y - 18.0, body.w - 24.0, 30.0);
                    draw_list_row(
                        r,
                        family,
                        Some(&format!(
                            "{count} candidate assemblies | certification is semantic, not filename-driven"
                        )),
                        self.assets_studio.selected_row == self.assets_studio.scroll + slot,
                    );
                    y += 34.0;
                }
            }
            AssetsStudioSection::Usage => {
                for line in [
                    "Where Used authority is dependency-driven; filename guesses are not treated as usage evidence.",
                    "Assets Studio and Game Canvas now share the canonical AssetPaletteCatalog; selection is no longer a parallel inventory.",
                    "Runtime-ready palette entries can be armed here and placed with the existing Game Canvas authoring path.",
                    "LPC source references remain read-only until promotion/binding; worldgen still consumes certified topology, never anonymous grid cells.",
                ] {
                    draw_scissored_text(
                        line,
                        body.x + 12.0,
                        y,
                        body.w - 24.0,
                        14.0,
                        TEXT,
                    );
                    y += 25.0;
                }
            }
            AssetsStudioSection::Review => {
                let review = c
                    .assemblies
                    .iter()
                    .filter(|a| {
                        !matches!(
                            AssetUnderstandingStage::from_assembly(a),
                            AssetUnderstandingStage::RuntimeCertified
                                | AssetUnderstandingStage::RejectedOrDeprecated
                        )
                    })
                    .collect::<Vec<_>>();
                let start = self.assets_studio.scroll.min(review.len());
                for (slot, a) in review
                    .into_iter()
                    .skip(start)
                    .take(asset_studio_list_capacity(body.h, 38.0))
                    .enumerate()
                {
                    let r = Rect::new(body.x + 12.0, y - 18.0, body.w - 24.0, 34.0);
                    let stage = AssetUnderstandingStage::from_assembly(a);
                    let role = if a.semantic_role.is_empty() {
                        "semantic role unresolved"
                    } else {
                        &a.semantic_role
                    };
                    draw_list_row(
                        r,
                        &a.asset_id,
                        Some(&format!(
                            "{} | {} | footprint {} | {}",
                            stage.label(),
                            role,
                            a.footprint,
                            a.source
                        )),
                        self.assets_studio.selected_row == start + slot,
                    );
                    y += 38.0;
                }
            }
        }

        if matches!(
            self.assets_studio.section,
            AssetsStudioSection::Inbox | AssetsStudioSection::Usage
        ) {
            return;
        }
        let selection = asset_studio_selection_rect(body);
        draw_rectangle(
            selection.x,
            selection.y,
            selection.w,
            selection.h,
            editor_theme::colors::CONTROL_BG,
        );
        draw_rectangle_lines(
            selection.x,
            selection.y,
            selection.w,
            selection.h,
            1.0,
            editor_theme::colors::BORDER_SUBTLE,
        );
        draw_editor_text(
            "SELECTION / SOURCE AUTHORITY",
            selection.x + 10.0,
            selection.y + 20.0,
            12.0,
            MUTED,
        );
        let details: Option<[String; 3]> = match self.assets_studio.section {
            AssetsStudioSection::Library => palette_runtime_entries(&self.asset_catalog)
                .get(self.assets_studio.selected_row)
                .map(|entry| {
                    [
                        format!("TEXTURE AVAILABLE: {} | {}", entry.label, entry.stable_id),
                        format!(
                            "Category: {} | Provenance: {} | {}",
                            entry.category.label(), entry.provenance.label(),
                            self.placeable_registry.entry(&entry.stable_id)
                                .map(|definition| format!(
                                    "Semantic: {} | Role: {:?} | Certification: {:?}",
                                    definition.semantic_id, definition.role, definition.certification,
                                ))
                                .unwrap_or_else(|| format!("Kind: {:?}", entry.kind))
                        ),
                        format!(
                            "Source: {} | Rect: {}",
                            entry.sheet.as_deref().unwrap_or("not declared"),
                            entry.rect
                                .map(|r| format!("{},{} {}x{}", r.x, r.y, r.w, r.h))
                                .unwrap_or_else(|| "not declared".to_string())
                        ),
                    ]
                }),
            AssetsStudioSection::Review => c
                .assemblies
                .iter()
                .filter(|asset| {
                    !matches!(
                        AssetUnderstandingStage::from_assembly(asset),
                        AssetUnderstandingStage::RuntimeCertified
                            | AssetUnderstandingStage::RejectedOrDeprecated
                    )
                })
                .nth(self.assets_studio.selected_row)
                .map(|asset| {
                    [
                        format!(
                            "ID: {} | {}",
                            asset.asset_id,
                            AssetUnderstandingStage::from_assembly(asset).label()
                        ),
                        format!(
                            "Role: {} | Footprint: {} | Assembly: {}",
                            asset.semantic_role, asset.footprint, asset.assembly_id
                        ),
                        format!("Source: {}", asset.source),
                    ]
                }),
            AssetsStudioSection::Sources => palette_source_entries(&self.asset_catalog)
                .get(self.assets_studio.selected_row)
                .map(|entry| {
                    [
                        format!("LPC SOURCE: {} | {}", entry.label, entry.stable_id),
                        format!(
                            "Category: {} | State: source reference / binding required",
                            entry.category.label()
                        ),
                        format!(
                            "Source: {}",
                            entry.sheet.as_deref().unwrap_or("mount unavailable")
                        ),
                    ]
                }),
            AssetsStudioSection::Families => c
                .family_counts
                .iter()
                .nth(self.assets_studio.selected_row)
                .map(|(name, count)| {
                    [
                        format!("Family: {}", name),
                        format!(
                            "{} candidate assemblies; individual assets require semantic certification",
                            count
                        ),
                        "Use Library for certified content, Review for incomplete bindings."
                            .to_string(),
                    ]
                }),
            AssetsStudioSection::Inbox | AssetsStudioSection::Usage => None,
        };
        let selected_library_entry = if self.assets_studio.section == AssetsStudioSection::Library {
            palette_runtime_entries(&self.asset_catalog)
                .get(self.assets_studio.selected_row)
                .copied()
        } else {
            None
        };
        let text_left = if let Some(entry) = selected_library_entry {
            let preview = Rect::new(selection.x + 10.0, selection.y + 39.0, 70.0, 70.0);
            draw_rectangle(preview.x, preview.y, preview.w, preview.h, Color::new(0.06, 0.07, 0.08, 1.0));
            draw_rectangle_lines(preview.x, preview.y, preview.w, preview.h, 1.0, PANEL_EDGE);
            if !self.editor_textures.draw_palette_thumbnail(entry, preview) {
                draw_editor_text("NO PREVIEW", preview.x + 5.0, preview.y + 41.0, 11.0, WARN);
            }
            if asset_studio_handoff_warning(&entry.stable_id, &self.placeable_registry).is_some() {
                draw_scissored_text(
                    "Roof recipe required — not standalone placeable",
                    asset_studio_use_on_canvas_rect(selection).x - 215.0,
                    asset_studio_use_on_canvas_rect(selection).y + 19.0,
                    380.0, 11.0, WARN,
                );
            } else {
                draw_editor_widget(asset_studio_use_on_canvas_rect(selection), "Use on Game Canvas", false);
            }
            selection.x + 90.0
        } else {
            selection.x + 10.0
        };
        if let Some(lines) = details {
            for (index, line) in lines.iter().enumerate() {
                let y = selection.y + 48.0 + index as f32 * 28.0;
                draw_scissored_text(
                    line,
                    text_left,
                    y,
                    (selection.x + selection.w - text_left - 10.0).max(1.0),
                    11.5,
                    TEXT,
                );
            }
        } else {
            draw_scissored_text(
                "Select a row to inspect its existing metadata.",
                selection.x + 10.0,
                selection.y + 50.0,
                (selection.w - 20.0).max(1.0),
                12.0,
                MUTED,
            );
        }
    }

    pub(crate) fn handle_assets_workspace_click(&mut self, mx: f32, my: f32) -> bool {
        if !self.asset_studio_open {
            return false;
        }
        let rect = self.shell_layout().workspace_content;
        let p = vec2(mx, my);
        if !rect.contains(p) {
            return false;
        }
        let pad = 12.0;
        let tab_w = ((rect.w - pad * 2.0 - 5.0 * 6.0) / 6.0).max(70.0);
        for (i, section) in AssetsStudioSection::ALL.into_iter().enumerate() {
            let r = Rect::new(
                rect.x + pad + i as f32 * (tab_w + 5.0),
                rect.y + 8.0,
                tab_w,
                28.0,
            );
            if r.contains(p) {
                self.assets_studio.section = section;
                self.assets_studio.scroll = 0;
                self.assets_studio.selected_row = 0;
                return true;
            }
        }
        let body = Rect::new(
            rect.x + pad,
            rect.y + 46.0,
            (rect.w - pad * 2.0).max(1.0),
            (rect.h - 52.0).max(1.0),
        );
        if asset_studio_reload_rect(body).contains(p) {
            self.assets_studio.reload(&repo_root_dir());
            let palette_result = AssetPaletteCatalog::load_default();
            self.status_message = match palette_result {
                Ok(mut palette) => {
                    palette.extend_published_placeables(&self.placeable_registry);
                    self.asset_catalog = palette;
                    self.asset_list_offset = 0;
                    let ready = palette_runtime_entries(&self.asset_catalog).len();
                    let sources = palette_source_entries(&self.asset_catalog).len();
                    match &self.assets_studio.load_error {
                        Some(error) => format!(
                            "Canonical palette refreshed ({ready} ready, {sources} LPC sources); intake catalog: {error}"
                        ),
                        None => format!(
                            "Assets refreshed: {ready} runtime-ready palette assets | {sources} LPC sources | {} topology certified | {} intake review",
                            self.assets_studio.certified_count(),
                            self.assets_studio.review_count()
                        ),
                    }
                }
                Err(error) => format!("Canonical Asset Palette refresh failed: {error}"),
            };
            return true;
        }
        if self.assets_studio.load_error.is_some() {
            return true;
        }
        let selection = asset_studio_selection_rect(body);
        if self.assets_studio.section == AssetsStudioSection::Library
            && asset_studio_use_on_canvas_rect(selection).contains(p)
        {
            if let Some(entry) = palette_runtime_entries(&self.asset_catalog)
                .get(self.assets_studio.selected_row)
            {
                let stable_id = entry.stable_id.clone();
                let kind = entry.kind;
                let label = entry.label.clone();
                if let Some(warning) = asset_studio_handoff_warning(&stable_id, &self.placeable_registry) {
                    self.status_message = warning;
                    return true;
                }
                if matches!(kind, AssetPaletteKind::Tile(TileKind::Cliff)) {
                    self.status_message = "Cliffs use structural elevation/contour authoring; a legacy cliff tile cannot be stamped directly".to_string();
                    return true;
                }
                if self.model.world.scenes.get(self.selected_scene).is_none() {
                    self.status_message = "No editable scene loaded; open a scene before placing an asset".to_string();
                    return true;
                }
                // Individual placements must never open the complete-world LOD:
                // it intentionally has no tile hit-testing. Use the existing
                // scene painting/placement path and its command/save authority.
                self.viewport_mode = EditorViewportMode::SceneMap;
                self.reopen_workspace_document(EditorViewportMode::SceneMap);
                let (layer, scene_layer, tool, canvas_tool) = match kind {
                    AssetPaletteKind::Tile(tile) => (
                        super::canvas_layers::canvas_layer_kind_for_surface_tile(tile),
                        SceneLayerMode::Terrain,
                        SceneEditTool::Paint,
                        super::tool_registry::UniversalTool::Paint,
                    ),
                    AssetPaletteKind::Object(_) | AssetPaletteKind::Stamp => (
                        super::canvas_layers::CanvasLayerKind::Objects,
                        SceneLayerMode::Objects,
                        SceneEditTool::Place,
                        super::tool_registry::UniversalTool::Place,
                    ),
                    AssetPaletteKind::SourceReference => return true,
                };
                self.set_scene_layer_mode(scene_layer);
                self.canvas_selected_layer_kinds.clear();
                self.canvas_selected_layer_kinds.insert(layer);
                self.canvas_layer_context_override = Some(layer);
                self.select_palette_asset(stable_id.clone(), kind);
                self.canvas_active_tool = canvas_tool;
                self.set_scene_edit_tool(tool);
                if matches!(kind, AssetPaletteKind::Stamp) {
                    self.canvas_authoring_context.brush_mode = super::brush_authoring::BrushMode::Stamp;
                }
                self.sync_canvas_authoring_context();
                self.canvas_authoring_context.source_id = Some(stable_id.clone());
                self.workspace_shell.shared_palette_visible = true;
                self.close_assets_studio();
                self.status_message = format!(
                    "Armed {label} ({stable_id}) in editable Scene Canvas with {}; click a scene cell to author", tool.label()
                );
            }
            return true;
        }
        let body_y = body.y;
        if my >= body_y + 54.0 && my < asset_studio_selection_rect(body).y {
            let row_h = match self.assets_studio.section {
                AssetsStudioSection::Library | AssetsStudioSection::Review => 38.0,
                _ => 34.0,
            };
            let idx = ((my - (body_y + 54.0)) / row_h).floor().max(0.0) as usize
                + self.assets_studio.scroll;
            let count = match self.assets_studio.section {
                AssetsStudioSection::Library => palette_runtime_entries(&self.asset_catalog).len(),
                AssetsStudioSection::Sources => palette_source_entries(&self.asset_catalog).len(),
                AssetsStudioSection::Families => self.assets_studio.catalog.family_counts.len(),
                AssetsStudioSection::Review => self.assets_studio.review_count(),
                AssetsStudioSection::Inbox | AssetsStudioSection::Usage => 0,
            };
            if idx < count
                && idx < self.assets_studio.scroll + asset_studio_list_capacity(body.h, row_h)
            {
                self.assets_studio.selected_row = idx;
            }
            return true;
        }
        true
    }

    pub(crate) fn update_assets_workspace_scroll(&mut self) -> bool {
        if !self.asset_studio_open {
            return false;
        }
        let rect = self.shell_layout().workspace_content;
        let p = vec2(mouse_position().0, mouse_position().1);
        if !rect.contains(p) {
            return false;
        }
        let (_, wheel) = mouse_wheel();
        if wheel.abs() < 0.01 {
            return false;
        }
        let max = match self.assets_studio.section {
            AssetsStudioSection::Library => palette_runtime_entries(&self.asset_catalog).len(),
            AssetsStudioSection::Sources => palette_source_entries(&self.asset_catalog).len(),
            AssetsStudioSection::Families => self.assets_studio.catalog.family_counts.len(),
            AssetsStudioSection::Review => self.assets_studio.review_count(),
            _ => 0,
        };
        let row_h = if matches!(
            self.assets_studio.section,
            AssetsStudioSection::Library | AssetsStudioSection::Review
        ) {
            38.0
        } else {
            34.0
        };
        let body_h = (rect.h - 52.0).max(1.0);
        let last_start = asset_studio_max_scroll(max, asset_studio_list_capacity(body_h, row_h));
        if wheel < 0.0 {
            self.assets_studio.scroll = self.assets_studio.scroll.saturating_add(3).min(last_start);
        } else {
            self.assets_studio.scroll = self.assets_studio.scroll.saturating_sub(3).min(last_start);
        }
        true
    }
}

pub(crate) fn family_completeness_roles() -> BTreeMap<&'static str, BTreeSet<&'static str>> {
    BTreeMap::from([
        (
            "structural_cliff",
            BTreeSet::from([
                "straight",
                "inner_corner",
                "outer_corner",
                "cap",
                "junction",
                "ramp",
                "transition",
            ]),
        ),
        (
            "tool_visual",
            BTreeSet::from(["inventory", "world", "held", "icon"]),
        ),
        (
            "humanoid_animation",
            BTreeSet::from(["idle", "walk", "run", "jump", "climb", "sit", "tool_use"]),
        ),
    ])
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn asset_list_never_scrolls_into_blank_space() {
        assert_eq!(asset_studio_max_scroll(3, 8), 0);
        assert_eq!(asset_studio_max_scroll(20, 8), 12);
        assert_eq!(asset_studio_list_capacity(390.0, 38.0), 3);
        assert_eq!(asset_studio_list_capacity(120.0, 34.0), 1);
    }

    #[test]
    fn reload_and_selection_do_not_overlap() {
        let body = Rect::new(0.0, 0.0, 700.0, 450.0);
        assert!(asset_studio_reload_rect(body).y + 28.0 < asset_studio_selection_rect(body).y);
    }

    #[test]
    fn asset_sections_are_the_frozen_six() {
        assert_eq!(AssetsStudioSection::ALL.len(), 6);
        assert_eq!(AssetsStudioSection::ALL[3], AssetsStudioSection::Families);
    }

    #[test]
    fn family_contracts_include_cliff_and_tool_roles() {
        let r = family_completeness_roles();
        assert!(r["structural_cliff"].contains("ramp"));
        assert!(r["tool_visual"].contains("held"));
    }

    #[test]
    fn certification_state_keeps_broken_and_deprecated_explicit() {
        assert_eq!(AssetAuthorityState::Broken.label(), "Broken");
        assert_eq!(AssetAuthorityState::Deprecated.label(), "Deprecated");
    }

    #[test]
    fn lifecycle_does_not_treat_slice_or_semantic_mapping_as_runtime_certification() {
        let sliced = AssetAssemblySummary {
            assembly_id: "rect-0-0-32-32".to_string(),
            ..Default::default()
        };
        assert_eq!(
            AssetUnderstandingStage::from_assembly(&sliced),
            AssetUnderstandingStage::Sliced
        );

        let mapped = AssetAssemblySummary {
            assembly_id: "roof-3x2".to_string(),
            semantic_role: "structure.roof.gable".to_string(),
            ..Default::default()
        };
        assert_eq!(
            AssetUnderstandingStage::from_assembly(&mapped),
            AssetUnderstandingStage::SemanticallyMapped
        );

        let certified = AssetAssemblySummary {
            certification: "runtime_certified".to_string(),
            ..Default::default()
        };
        assert_eq!(
            AssetUnderstandingStage::from_assembly(&certified),
            AssetUnderstandingStage::RuntimeCertified
        );
    }

    #[test]
    fn missing_optional_intake_catalog_still_exposes_published_assets() {
        let missing = std::env::temp_dir().join(format!(
            "havenwild_assets_studio_missing_catalog_{}",
            std::process::id()
        )).join("asset-catalog.json");
        let catalog = load_compact_catalog(&missing)
            .expect("published runtime registry must work without a generated PCC intake scan");
        assert!(catalog.generated_utc.contains("not generated"));
        assert!(catalog.sheets.is_empty());
        assert!(catalog.assemblies.iter().any(|asset|
            asset.asset_id == "terrain.ground.grass.v7"
                && asset.certification == "runtime_certified"
        ));
        assert!(catalog.assemblies.iter().any(|asset|
            asset.asset_id == "cliff.ramp.rise_right.grass"
        ));
    }

    #[test]
    fn published_world_topology_feeds_runtime_certified_library_authority() {
        let published =
            haven_assets::published_world_topology::published_world_topology_registry_v1()
                .expect("published world topology registry");
        assert!(published.entry("terrain.ground.grass.v7").is_some());
        assert!(published.entry("water.deep.v7").is_some());
        assert!(published.entry("cliff.ramp.rise_right.grass").is_some());
        assert!(published
            .entries()
            .iter()
            .all(|entry| entry.certification == "runtime_certified"));
    }

    #[test]
    fn canonical_palette_bridge_exposes_ready_assets_and_lpc_sources() {
        let catalog = AssetPaletteCatalog::load_default().expect("canonical asset palette");
        assert!(!palette_runtime_entries(&catalog).is_empty());
        assert!(palette_source_entries(&catalog).len() >= 300);
        assert!(palette_runtime_entries(&catalog)
            .iter()
            .all(|entry| entry.runtime_ready()));
    }

    #[test]
    fn roof_candidate_remains_recipe_owned_instead_of_falling_back_to_crate() {
        let session = haven_assets::runtime_asset_cache::RuntimeAssetSession::discover_tolerant(&repo_root_dir());
        let registry = PublishedWorldAssetRegistry::load_discovered(&session)
            .expect("project published asset registry");
        let roof = registry.entries().iter()
            .find(|definition| definition.entry_id == "roof_flat_gray_north_eave")
            .expect("exact north eave module");
        assert!(asset_studio_requires_building_recipe(roof));
        assert!(asset_studio_handoff_warning(&roof.stable_id, &registry)
            .expect("roof must have explicit workflow warning").contains("roof recipe authoring"));
    }

    #[test]
    fn ordinary_non_roof_assets_are_not_blocked_by_roof_workflow() {
        let registry = PublishedWorldAssetRegistry::default();
        assert!(asset_studio_handoff_warning("tile/grass", &registry).is_none());
    }

    #[test]
    fn use_on_canvas_action_stays_inside_selection_panel() {
        let body = Rect::new(0.0, 0.0, 900.0, 600.0);
        let selection = asset_studio_selection_rect(body);
        let action = asset_studio_use_on_canvas_rect(selection);
        assert!(selection.contains(vec2(action.x + 1.0, action.y + 1.0)));
        assert!(selection.contains(vec2(action.x + action.w - 1.0, action.y + action.h - 1.0)));
    }

}
