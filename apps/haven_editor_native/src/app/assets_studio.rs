#![allow(dead_code)] // HW-ASSETS-10 staged authority contracts are consumed incrementally.
use super::*;
use super::render_helpers::{draw_list_row, draw_tab_widget};
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
    pub(crate) const ALL: [Self; 6] = [Self::Inbox, Self::Library, Self::Sources, Self::Families, Self::Usage, Self::Review];
    pub(crate) fn label(self) -> &'static str { match self {
        Self::Inbox => "Inbox", Self::Library => "Library", Self::Sources => "Sources",
        Self::Families => "Families", Self::Usage => "Usage", Self::Review => "Review",
    }}
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub(crate) enum AssetAuthorityState { Discovered, Identified, Mapped, Validated, Certified, Deprecated, Broken }
impl AssetAuthorityState { pub(crate) fn label(self) -> &'static str { match self {
    Self::Discovered=>"Discovered", Self::Identified=>"Identified", Self::Mapped=>"Mapped", Self::Validated=>"Validated",
    Self::Certified=>"Certified", Self::Deprecated=>"Deprecated", Self::Broken=>"Broken",
}}}

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
    pub source: String, pub sha256: String, pub width: u64, pub height: u64, pub classification: String, pub assemblies: u64,
}
#[derive(Clone, Debug, Default)]
pub(crate) struct AssetAssemblySummary {
    pub asset_id: String, pub source: String, pub assembly_id: String, pub semantic_role: String,
    pub certification: String, pub footprint: String,
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
        if self.loaded { return; }
        self.reload(repo_root);
    }
    pub(crate) fn reload(&mut self, repo_root: &Path) {
        let path = repo_root.join(PCC_ASSET_CATALOG_PATH);
        self.loaded = true;
        match load_compact_catalog(&path) {
            Ok(catalog) => { self.catalog = catalog; self.load_error = None; self.selected_row = 0; self.scroll = 0; }
            Err(error) => { self.catalog = AssetsStudioCatalog { path, ..Default::default() }; self.load_error = Some(error); }
        }
    }
    pub(crate) fn review_count(&self) -> usize {
        self.catalog.assemblies.iter().filter(|a| !matches!(a.certification.as_str(), "runtime_certified"|"rejected"|"deprecated")).count()
    }
    pub(crate) fn certified_count(&self) -> usize {
        self.catalog.assemblies.iter().filter(|a| a.certification == "runtime_certified").count()
    }
}

fn u64_at(v: &Value, key: &str) -> u64 { v.get(key).and_then(Value::as_u64).unwrap_or(0) }
fn str_at(v: &Value, key: &str) -> String { v.get(key).and_then(Value::as_str).unwrap_or_default().to_string() }
fn display_json(v: Option<&Value>) -> String {
    match v { Some(Value::String(s)) => s.clone(), Some(v) => v.to_string(), None => String::new() }
}

fn load_compact_catalog(path: &Path) -> Result<AssetsStudioCatalog, String> {
    let raw = fs::read_to_string(path).map_err(|e| format!("Asset catalog unavailable at {}: {e}", path.display()))?;
    let root: Value = serde_json::from_str(&raw).map_err(|e| format!("Asset catalog parse failed: {e}"))?;
    let summary = root.get("summary").unwrap_or(&Value::Null);
    let detail_store = root.get("storage").and_then(|s| s.get("detailStore")).and_then(Value::as_str).unwrap_or_default().to_string();
    let mut sheets = Vec::new();
    for sheet in root.get("sheets").and_then(Value::as_array).into_iter().flatten() {
        let source = sheet.get("source").unwrap_or(&Value::Null);
        sheets.push(AssetSheetSummary {
            source: str_at(source, "relativePath"), sha256: str_at(source, "sha256"), width: u64_at(source, "width"), height: u64_at(source, "height"),
            classification: display_json(sheet.get("classification")), assemblies: u64_at(sheet, "assemblyCount"),
        });
    }
    let mut assemblies = Vec::new();
    let mut family_counts = BTreeMap::new();
    for item in root.get("assemblyIndex").and_then(Value::as_array).into_iter().flatten() {
        let source = str_at(item, "source");
        let family = source.rsplit_once('/').map(|(parent, _)| parent.rsplit('/').next().unwrap_or(parent)).unwrap_or("root").to_string();
        *family_counts.entry(family).or_insert(0) += 1;
        assemblies.push(AssetAssemblySummary {
            asset_id: str_at(item, "assetId"), source, assembly_id: str_at(item, "assembly_id"),
            semantic_role: display_json(item.get("semantic_role")), certification: str_at(item, "certification"),
            footprint: display_json(item.get("footprint")),
        });
    }
    Ok(AssetsStudioCatalog {
        path: path.to_path_buf(), generated_utc: str_at(&root, "generatedUtc"), detail_store,
        discovered_files: u64_at(summary, "discoveredFileCount"), png_files: u64_at(summary, "pngFileCount"),
        sheet_count: u64_at(summary, "pngSheetCount"), assembly_count: u64_at(summary, "assemblyCandidateCount"), error_count: u64_at(summary, "errorCount"),
        sheets, assemblies, family_counts,
    })
}

impl EditorApp {
    pub(crate) fn open_assets_studio(&mut self) {
        self.asset_studio_open = true;
        self.assets_studio.ensure_loaded(&repo_root_dir());
        self.status_message = format!("Assets workspace | {} source PNGs | {} assembly candidates", self.assets_studio.catalog.png_files, self.assets_studio.catalog.assembly_count);
    }
    pub(crate) fn close_assets_studio(&mut self) { self.asset_studio_open = false; }

    pub(crate) fn draw_assets_workspace(&mut self, rect: Rect) {
        self.assets_studio.ensure_loaded(&repo_root_dir());
        let pad = 12.0;
        let tabs_y = rect.y + 8.0;
        let tab_w = ((rect.w - pad * 2.0 - 5.0 * 6.0) / 6.0).max(70.0);
        for (i, section) in AssetsStudioSection::ALL.into_iter().enumerate() {
            let r = Rect::new(rect.x + pad + i as f32 * (tab_w + 5.0), tabs_y, tab_w, 28.0);
            draw_tab_widget(r, section.label(), self.assets_studio.section == section);
        }
        let body = Rect::new(rect.x + pad, tabs_y + 38.0, (rect.w - pad*2.0).max(1.0), (rect.h - 52.0).max(1.0));
        draw_rectangle(body.x, body.y, body.w, body.h, editor_theme::colors::PANEL_BG);
        if let Some(error) = self.assets_studio.load_error.as_ref() {
            draw_editor_text("Assets catalog unavailable", body.x + 12.0, body.y + 24.0, 18.0, editor_theme::colors::WARN);
            draw_scissored_text(error, body.x + 12.0, body.y + 48.0, body.w - 24.0, 13.0, TEXT);
            draw_scissored_text("Run PCC Asset Authority scan/refresh; the editor does not silently invent replacement assets.", body.x + 12.0, body.y + 72.0, body.w - 24.0, 13.0, MUTED);
            return;
        }
        self.draw_assets_section(body);
    }

    fn draw_assets_section(&self, body: Rect) {
        let c = &self.assets_studio.catalog;
        draw_editor_text(self.assets_studio.section.label(), body.x + 12.0, body.y + 24.0, 18.0, TEXT);
        draw_scissored_text(&format!("Catalog {} | {} PNGs | {} sheets | {} assemblies | {} certified | {} review", c.generated_utc, c.png_files, c.sheet_count, c.assembly_count, self.assets_studio.certified_count(), self.assets_studio.review_count()), body.x + 12.0, body.y + 47.0, body.w - 24.0, 12.0, MUTED);
        let mut y = body.y + 72.0;
        match self.assets_studio.section {
            AssetsStudioSection::Inbox => {
                for line in [
                    format!("PCC catalog: {}", c.path.display()),
                    format!("Detailed authority store: {}", if c.detail_store.is_empty() { "not declared" } else { &c.detail_store }),
                    format!("Discovered files: {} | PNG: {} | errors: {}", c.discovered_files, c.png_files, c.error_count),
                    "New source packs enter through PCC intake; existing 64k source inventory is reused, not rescanned on workspace open.".to_string(),
                    "Raw source remains immutable. Project edits create derived assets with lineage.".to_string(),
                ] { draw_scissored_text(&line, body.x+12.0, y, body.w-24.0, 14.0, TEXT); y += 25.0; }
            }
            AssetsStudioSection::Library | AssetsStudioSection::Sources => {
                let start = self.assets_studio.scroll.min(c.sheets.len());
                for (slot, sheet) in c.sheets.iter().skip(start).take(((body.h-88.0)/34.0).max(1.0) as usize).enumerate() {
                    let r=Rect::new(body.x+12.0,y-18.0,body.w-24.0,30.0);
                    let secondary=format!("{}x{} | {} assemblies | {} | sha {}",sheet.width,sheet.height,sheet.assemblies,sheet.classification,&sheet.sha256.chars().take(10).collect::<String>());
                    draw_list_row(r,&sheet.source,Some(&secondary),self.assets_studio.selected_row==start+slot); y+=34.0;
                }
            }
            AssetsStudioSection::Families => {
                for (slot,(family,count)) in c.family_counts.iter().skip(self.assets_studio.scroll).take(((body.h-88.0)/34.0).max(1.0) as usize).enumerate() {
                    let r=Rect::new(body.x+12.0,y-18.0,body.w-24.0,30.0);
                    draw_list_row(r,family,Some(&format!("{count} assembly candidates | completeness requires semantic role certification")),self.assets_studio.selected_row==self.assets_studio.scroll+slot); y+=34.0;
                }
            }
            AssetsStudioSection::Usage => {
                for line in ["Where Used authority is dependency-driven; filename guesses are not treated as usage evidence.", "Current project mappings, intake recipes, runtime-ready palette entries and future composition dependencies converge here.", "Selecting an asset/family will expose source → family → document/content → runtime usage as dependency edges." ] {
                    draw_scissored_text(line,body.x+12.0,y,body.w-24.0,14.0,TEXT); y+=25.0;
                }
            }
            AssetsStudioSection::Review => {
                for (slot,a) in c.assemblies.iter().filter(|a| !matches!(a.certification.as_str(),"runtime_certified"|"rejected"|"deprecated")).skip(self.assets_studio.scroll).take(((body.h-88.0)/38.0).max(1.0) as usize).enumerate() {
                    let r=Rect::new(body.x+12.0,y-18.0,body.w-24.0,34.0);
                    let role=if a.semantic_role.is_empty(){"semantic role unresolved"}else{&a.semantic_role};
                    draw_list_row(r,&a.asset_id,Some(&format!("{} | {} | footprint {}",a.certification,role,a.footprint)),self.assets_studio.selected_row==self.assets_studio.scroll+slot); y+=38.0;
                }
            }
        }
    }

    pub(crate) fn handle_assets_workspace_click(&mut self, mx: f32, my: f32) -> bool {
        if !self.asset_studio_open { return false; }
        let rect=self.shell_layout().workspace_content; let p=vec2(mx,my); if !rect.contains(p){return false;}
        let pad=12.0; let tab_w=((rect.w-pad*2.0-5.0*6.0)/6.0).max(70.0);
        for (i,section) in AssetsStudioSection::ALL.into_iter().enumerate(){let r=Rect::new(rect.x+pad+i as f32*(tab_w+5.0),rect.y+8.0,tab_w,28.0);if r.contains(p){self.assets_studio.section=section;self.assets_studio.scroll=0;self.assets_studio.selected_row=0;return true;}}
        let body_y=rect.y+46.0; if my>=body_y+54.0 { let row_h=if self.assets_studio.section==AssetsStudioSection::Review{38.0}else{34.0}; let idx=((my-(body_y+54.0))/row_h).floor().max(0.0) as usize+self.assets_studio.scroll; self.assets_studio.selected_row=idx; return true; }
        true
    }

    pub(crate) fn update_assets_workspace_scroll(&mut self) -> bool {
        if !self.asset_studio_open { return false; }
        let rect=self.shell_layout().workspace_content; let p=vec2(mouse_position().0,mouse_position().1); if !rect.contains(p){return false;}
        let (_,wheel)=mouse_wheel(); if wheel.abs()<0.01{return false;} let max=match self.assets_studio.section{AssetsStudioSection::Library|AssetsStudioSection::Sources=>self.assets_studio.catalog.sheets.len(),AssetsStudioSection::Families=>self.assets_studio.catalog.family_counts.len(),AssetsStudioSection::Review=>self.assets_studio.review_count(),_=>0};
        if wheel<0.0 { self.assets_studio.scroll=(self.assets_studio.scroll+3).min(max.saturating_sub(1)); } else { self.assets_studio.scroll=self.assets_studio.scroll.saturating_sub(3); } true
    }
}

pub(crate) fn family_completeness_roles() -> BTreeMap<&'static str, BTreeSet<&'static str>> {
    BTreeMap::from([
        ("structural_cliff", BTreeSet::from(["straight","inner_corner","outer_corner","cap","junction","ramp","transition"])),
        ("tool_visual", BTreeSet::from(["inventory","world","held","icon"])),
        ("humanoid_animation", BTreeSet::from(["idle","walk","run","jump","climb","sit","tool_use"])),
    ])
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn asset_sections_are_the_frozen_six(){assert_eq!(AssetsStudioSection::ALL.len(),6);assert_eq!(AssetsStudioSection::ALL[3],AssetsStudioSection::Families);}
    #[test] fn family_contracts_include_cliff_and_tool_roles(){let r=family_completeness_roles();assert!(r["structural_cliff"].contains("ramp"));assert!(r["tool_visual"].contains("held"));}
    #[test] fn certification_state_keeps_broken_and_deprecated_explicit(){assert_eq!(AssetAuthorityState::Broken.label(),"Broken");assert_eq!(AssetAuthorityState::Deprecated.label(),"Deprecated");}
}
