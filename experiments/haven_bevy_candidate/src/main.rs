//! EXPERIMENTAL ONLY. Original-source GPU preview, read-only semantic world and
//! Bevy GPU draft scene using UNAPPROVED historic source coordinates (NOT certified art).
//! No canonical saves, asset recipes, world editing, or production game integration.
use bevy::{
    camera::{visibility::RenderLayers, RenderTarget},
    image::ImagePlugin,
    prelude::*,
    render::render_resource::{
        Extent3d, TextureDescriptor, TextureDimension, TextureFormat, TextureUsages,
    },
};
use bevy_egui::{
    egui, EguiContexts, EguiPlugin, EguiPrimaryContextPass, EguiTextureHandle, EguiUserTextures,
};
use forge_gui_chrome::{ModularSurfaceState, ShellProfile, SurfaceDock};
use forge_gui_shell::{
    show_application_shell, ForgeApplicationSpec, ForgeShellContent, ForgeShellState,
};
use forge_gui_theme::{ForgeTheme, ForgeThemePreset};
use sha2::{Digest, Sha256};
use std::{fs, path::Path};

const SOURCE_REL: &str = "source/Terrain/terrain_summer.png";
const SOURCE_SHA: &str = "1251a6ea556330190ccb1e3af166eb69fbec4b7a3f7d51c1f54728abd75bd752";
const SCENE_REL: &str = "content/worldgen/scenes/terrain_acceptance/river_scene_v1.json";
const SOURCE_W: u32 = 512;
const SOURCE_H: u32 = 832;
const DRAFT_MAPPING_REL: &str = "content/assets/intake/lpc_terrain_family_mapping_v0_3.json";
const DRAFT_BINDINGS_REL: &str = "content/architecture/havenwild_bevy_draft_role_bindings_v0_1.json";
const DRAFT_MAPPING_SHA: &str = "280735da3be341cbbb6a085d45fc14673886a94d24d2b34473ff48878f038307";

#[derive(Resource)]
struct PreviewTarget(Handle<Image>);
#[derive(Resource)]
struct DraftTarget(Handle<Image>);

#[derive(Resource)]
struct Shell {
    spec: ForgeApplicationSpec,
    shell: ForgeShellState,
    theme: ForgeTheme,
    content: CandidateContent,
}

#[derive(Default)]
struct CandidateContent {
    preview: Option<egui::TextureId>,
    draft_preview: Option<egui::TextureId>,
    draft_source_cells: Vec<[u32; 2]>,
    scene_id: String,
    scene_size: [usize; 2],
    terrain_counts: Vec<(String, usize)>,
    terrain_grid: Vec<Vec<String>>,
    scene_sha: String,
    cell: [usize; 2], // source atlas selection
    world_cell: [usize; 2], // independent semantic scene selection
    status: String,
}

impl ForgeShellContent for CandidateContent {
    fn menu(&mut self, ui: &mut egui::Ui) {
        ui.menu_button("File", |ui| { ui.label("Read-only evidence candidate. Saving, publication and PIE disabled."); });
        ui.menu_button("View", |ui| { ui.label("Use the surface's Dock menu to float the Inspector."); });
        ui.menu_button("Help", |ui| { ui.label("GPU draft = actual original source pixels / historically assigned, UNAPPROVED tile roles. Not certified game rendering or PIE."); });
    }

    fn toolbar(&mut self, ui: &mut egui::Ui) {
        ui.label("B48R28C3 / Bevy 0.19 / UNAPPROVED exact-pixel GPU draft");
        ui.separator();
        ui.label("Read-only");
    }

    fn status(&mut self, ui: &mut egui::Ui) {
        ui.horizontal_wrapped(|ui| {
            ui.label("Original source and fixture verified at startup");
            ui.separator();
            ui.label("GPU draft uses original pixels; role assignments and transitions UNAPPROVED");
            ui.separator();
            ui.label("No Macroquad dependency in candidate");
            ui.separator();
            ui.label("PCC Full Gate: NOT RUN by this application");
        });
    }

    fn surface(&mut self, id: &str, ui: &mut egui::Ui) {
        match id {
            "source_library" => {
                ui.heading("Source Library");
                ui.label("ElizaWy / Terrain / terrain_summer.png");
                ui.label(format!("SHA-256: {SOURCE_SHA}"));
                ui.separator();
                ui.label("Original atlas bytes staged from Terrain.zip. No generated pixels.");
                ui.label("A source sheet is not an approved semantic map.");
            }
            "source_preview" => {
                ui.heading("Bevy off-screen render target — original ElizaWy atlas");
                ui.label("Source preview only; terrain recipe, cliff collision and game parity NOT wired.");
                if let Some(texture_id) = self.preview {
                    let available = ui.available_size();
                    let scale = (available.x / SOURCE_W as f32)
                        .min((available.y - 15.0).max(32.0) / SOURCE_H as f32)
                        .clamp(0.1, 4.0);
                    let size = egui::vec2(SOURCE_W as f32 * scale, SOURCE_H as f32 * scale);
                    let response = ui.image(egui::load::SizedTexture::new(texture_id, size));
                    if response.clicked() {
                        if let Some(pos) = response.interact_pointer_pos() {
                            let local = pos - response.rect.min;
                            self.cell = [
                                ((local.x / scale) as usize / 32).min(15),
                                ((local.y / scale) as usize / 32).min(25),
                            ];
                        }
                    }
                    let cell_min = response.rect.min
                        + egui::vec2(self.cell[0] as f32 * 32.0 * scale, self.cell[1] as f32 * 32.0 * scale);
                    let cell_rect = egui::Rect::from_min_size(cell_min, egui::vec2(32.0 * scale, 32.0 * scale));
                    ui.painter().rect_stroke(cell_rect, 0.0, egui::Stroke::new(1.5, egui::Color32::YELLOW), egui::StrokeKind::Inside);
                } else {
                    ui.label("Waiting for verified Bevy render target.");
                }
            }
            "world_draft" => {
                ui.heading("UNAPPROVED DRAFT — original ElizaWy pixels on actual river fixture");
                ui.label("Historical first-cell role addresses only. NOT mapper-certified: banks, transitions, animation, elevations, physics, PIE unresolved.");
                ui.label(format!("{} × {} / {} unreviewed GPU tiles / 0 approved draw calls",
                    self.scene_size[0], self.scene_size[1], self.draft_source_cells.len()));
                if let Some(texture_id) = self.draft_preview {
                    let native = egui::vec2(self.scene_size[0] as f32 * 32.0, self.scene_size[1] as f32 * 32.0);
                    let available = ui.available_size();
                    let scale = (available.x / native.x).min((available.y - 12.0).max(32.0) / native.y).clamp(0.1, 2.0);
                    let result = ui.image(egui::load::SizedTexture::new(texture_id, native * scale));
                    if result.clicked() {
                        if let Some(point) = result.interact_pointer_pos() {
                            let offset = point - result.rect.min;
                            self.world_cell = [
                                ((offset.x / (32.0 * scale)) as usize).min(self.scene_size[0].saturating_sub(1)),
                                ((offset.y / (32.0 * scale)) as usize).min(self.scene_size[1].saturating_sub(1)),
                            ];
                        }
                    }
                    let cell = egui::Rect::from_min_size(
                        result.rect.min + egui::vec2(self.world_cell[0] as f32 * 32.0 * scale,
                                                     self.world_cell[1] as f32 * 32.0 * scale),
                        egui::vec2(32.0 * scale, 32.0 * scale));
                    ui.painter().rect_stroke(cell, 0.0, egui::Stroke::new(2.0, egui::Color32::YELLOW), egui::StrokeKind::Inside);
                } else { ui.label("Waiting for Bevy GPU draft texture."); }
            }
            "world_semantics" => {
                ui.heading("Actual river fixture — SEMANTIC DEBUG canvas");
                ui.label("Every square is an original scene role, NOT source art. Terrain mapping, cliffs, water rendering and collision are UNRESOLVED.");
                ui.label(format!("Scene {} | {} x {} | no authoring writes", self.scene_id, self.scene_size[0], self.scene_size[1]));
                const STEP: f32 = 18.0;
                egui::ScrollArea::both().auto_shrink([false, false]).show(ui, |ui| {
                    let size = egui::vec2(self.scene_size[0] as f32 * STEP, self.scene_size[1] as f32 * STEP);
                    let (rect, response) = ui.allocate_exact_size(size, egui::Sense::click());
                    for (y, row) in self.terrain_grid.iter().enumerate() {
                        for (x, role) in row.iter().enumerate() {
                            let cell = egui::Rect::from_min_size(
                                rect.min + egui::vec2(x as f32 * STEP, y as f32 * STEP),
                                egui::vec2(STEP, STEP),
                            );
                            if !ui.is_rect_visible(cell) { continue; }
                            // Distinct diagnostic colors identify role topology ONLY.
                            // Never reinterpret these swatches as source-pixel mapping.
                            let color = match role.as_str() {
                                "Grass" => egui::Color32::from_rgb(77, 111, 72),
                                "RiverWater" => egui::Color32::from_rgb(55, 101, 147),
                                "MudBank" => egui::Color32::from_rgb(134, 105, 72),
                                _ => egui::Color32::from_rgb(135, 35, 125),
                            };
                            ui.painter().rect_filled(cell, 0.0, color);
                            ui.painter().rect_stroke(cell, 0.0, egui::Stroke::new(0.5, egui::Color32::from_gray(25)), egui::StrokeKind::Inside);
                        }
                    }
                    if response.clicked() {
                        if let Some(pos) = response.interact_pointer_pos() {
                            let local = pos - rect.min;
                            self.world_cell = [
                                ((local.x / STEP).floor().max(0.0) as usize).min(self.scene_size[0].saturating_sub(1)),
                                ((local.y / STEP).floor().max(0.0) as usize).min(self.scene_size[1].saturating_sub(1)),
                            ];
                        }
                    }
                    let selected = egui::Rect::from_min_size(
                        rect.min + egui::vec2(self.world_cell[0] as f32 * STEP, self.world_cell[1] as f32 * STEP),
                        egui::vec2(STEP, STEP),
                    );
                    ui.painter().rect_stroke(selected, 0.0, egui::Stroke::new(2.0, egui::Color32::YELLOW), egui::StrokeKind::Inside);
                });
            }
            "inspector" => {
                ui.heading("Inspector — independent selections");
                let [x, y] = self.world_cell;
                let world_role = self.terrain_grid.get(y).and_then(|row| row.get(x)).map(String::as_str).unwrap_or("<missing>");
                ui.label(format!("World cell: ({x}, {y}) / role: {world_role}"));
                ui.label(format!("Scene ID: {}", self.scene_id));
                ui.label(format!("Scene SHA-256: {}", self.scene_sha));
                ui.label("World elevation: UNKNOWN in this fixture; no implicit level 0");
                let source = self.draft_source_cells.get(y * self.scene_size[0] + x);
                ui.label(format!("GPU DRAFT source cell: {:?} / NOT APPROVED", source));
                ui.label("Production source binding: UNMAPPED — mapper/Asset Authority approval required");
                ui.separator();
                ui.label(format!("Source sheet cell: ({}, {})", self.cell[0], self.cell[1]));
                ui.label(format!("Source pixel origin: ({}, {})", self.cell[0] * 32, self.cell[1] * 32));
                ui.label("Selections are independent; this does not assign a tile role.");
                ui.label("Read-only. No game state, source image, or project document changes.");
            }
            "scene_evidence" => {
                ui.heading("Existing Havenwild fixture — semantic evidence");
                ui.label(format!("Scene: {}", self.scene_id));
                ui.label(format!("Size: {} × {} tiles", self.scene_size[0], self.scene_size[1]));
                ui.label(format!("Fixture path: {SCENE_REL}"));
                ui.label(format!("Scene SHA-256: {}", self.scene_sha));
                ui.label("Status: all scene cells require certified ElizaWy draw-plan mapping.");
                ui.separator();
                for (name, count) in &self.terrain_counts {
                    ui.label(format!("{name}: {count}"));
                }
                ui.separator();
                ui.label("The existing terrain resolver must connect these roles to approved source recipes in the next pass.");
            }
            "activity" => {
                ui.heading("Architecture experiment");
                ui.monospace(&self.status);
                ui.monospace("[DRAFT] Bevy GPU sprites from original pixels; historical role coordinates UNAPPROVED");
                ui.monospace("[PENDING] Mapper-authorized source exact draw plan and adjacency parity");
                ui.monospace("[DEBUG ONLY] Real semantic grid / selection; NOT a Bevy world render");
                ui.monospace("[PENDING] Source-exact world canvas and actual game PIE");
                ui.monospace("[PENDING] Windows build + PCC Full Gate");
            }
            _ => { ui.label(format!("Unregistered surface: {id}")); }
        }
    }
}

fn verify_source_and_scene() -> Result<CandidateContent, String> {
    let candidate = Path::new(env!("CARGO_MANIFEST_DIR"));
    let source = candidate.join("assets").join(SOURCE_REL);
    let raw = fs::read(&source)
        .map_err(|e| format!("Missing original source {}: {e}; run prepare_source.py first", source.display()))?;
    let sha = format!("{:x}", Sha256::digest(&raw));
    if sha != SOURCE_SHA { return Err(format!("Source hash mismatch, fail closed: {source:?}: {sha}")); }
    let receipt: serde_json::Value = serde_json::from_slice(
        &fs::read(candidate.join("evidence/source_stage.json")).map_err(|e| e.to_string())?
    ).map_err(|e| e.to_string())?;
    if receipt["sourceSha256"].as_str() != Some(SOURCE_SHA) || receipt["publicationStatus"].as_str() != Some("candidate_only") {
        return Err("Source receipt missing, altered, or improperly published".into());
    }
    let credits = fs::read(candidate.join("assets/source/Terrain/Credits.txt"))
        .map_err(|e| format!("Original source credits are missing: {e}"))?;
    let credits_sha = format!("{:x}", Sha256::digest(&credits));
    if receipt["creditsSha256"].as_str() != Some(credits_sha.as_str()) {
        return Err("Original source credits changed after staging".into());
    }
    let scene_path = candidate.join("../../").join(SCENE_REL);
    let scene_raw = fs::read(&scene_path).map_err(|e| format!("Missing real fixture {}: {e}", scene_path.display()))?;
    let scene_sha = format!("{:x}", Sha256::digest(&scene_raw));
    if receipt["fixture"]["sha256"].as_str() != Some(scene_sha.as_str()) {
        return Err("Scene SHA differs from original source-stage receipt; refuse stale scene".into());
    }
    let scene: serde_json::Value = serde_json::from_slice(&scene_raw).map_err(|e| e.to_string())?;
    if scene["kind"] != "worldgen_scene" || scene["tileSize"] != serde_json::json!([32,32]) {
        return Err("Unsupported scene fixture kind/tile size".into());
    }
    let scene_id = scene["sceneId"].as_str().ok_or("Scene fixture ID missing")?.to_string();
    let sizes = scene["sceneSize"].as_array().ok_or("Scene dimensions missing")?;
    let width = sizes.first().and_then(|v| v.as_u64()).ok_or("Width absent")? as usize;
    let height = sizes.get(1).and_then(|v| v.as_u64()).ok_or("Height absent")? as usize;
    let grid = scene["layers"]["terrain"].as_array().ok_or("Terrain layer absent")?;
    if grid.len() != height || width == 0 || height == 0 || width > 2048 || height > 2048 {
        return Err("Terrain grid has unexpected dimensions".into());
    }
    let mut counts = std::collections::BTreeMap::<String,usize>::new();
    let mut terrain_grid = Vec::with_capacity(height);
    for row in grid {
        let cells = row.as_array().ok_or("Terrain row is not an array")?;
        if cells.len() != width { return Err("Terrain row width mismatch".into()); }
        let mut normalized = Vec::with_capacity(width);
        for value in cells {
            let role = value.as_str().filter(|text| !text.trim().is_empty()).ok_or("Terrain cell not a nonempty semantic role")?;
            *counts.entry(role.to_owned()).or_default() += 1;
            normalized.push(role.to_owned());
        }
        terrain_grid.push(normalized);
    }
    // This candidate-only receipt is produced by the SAME PCC-gated source
    // and scene verifier. Reconcile every cell before displaying its debug role:
    // a stale semantic view must not be mistaken for the current project.
    let plan_raw = fs::read(candidate.join("evidence/semantic_scene_plan.json"))
        .map_err(|e| format!("Semantic plan missing: {e}; use PCC experimental.bevy.scene-plan"))?;
    let plan: serde_json::Value = serde_json::from_slice(&plan_raw)
        .map_err(|e| format!("Semantic plan unreadable: {e}"))?;
    if plan["schema"] != "havenwild.experimental.semantic_scene_plan.v0_1"
        || plan["status"] != "SEMANTIC_DEBUG_ONLY_NOT_RENDERER_PARITY"
        || plan["sceneId"].as_str() != Some(scene_id.as_str())
        || plan["scenePath"].as_str() != Some(SCENE_REL)
        || plan["tileSizePx"] != serde_json::json!([32, 32])
        || plan["sceneSha256"].as_str() != Some(scene_sha.as_str())
        || plan["originalSourceSha256"].as_str() != Some(SOURCE_SHA)
        || plan["sizeTiles"] != serde_json::json!([width, height])
        || plan["semanticCellCount"].as_u64() != Some((width * height) as u64)
        || plan["unmappedCellCount"].as_u64() != Some((width * height) as u64)
        || plan["approvedDrawCallCount"].as_u64() != Some(0)
        || plan["sourceExactArtApproved"].as_bool() != Some(false)
        || plan["worldRendererParity"].as_bool() != Some(false)
        || plan["pieCertified"].as_bool() != Some(false)
        || plan["roleCounts"] != serde_json::json!(&counts) {
        return Err("Semantic evidence mismatch or misleading artwork certification claim".into());
    }
    let plan_cells = plan["cells"].as_array().ok_or("Semantic cells missing")?;
    if plan_cells.len() != width * height { return Err("Semantic cell count mismatch".into()); }
    for (y, row) in terrain_grid.iter().enumerate() {
        for (x, role) in row.iter().enumerate() {
            let cell = &plan_cells[y * width + x];
            let neighbor = |nx: i32, ny: i32| -> Option<&str> {
                if nx < 0 || ny < 0 { return None; }
                terrain_grid.get(ny as usize)
                    .and_then(|r| r.get(nx as usize))
                    .map(String::as_str)
            };
            let expected_neighbors = serde_json::json!([
                neighbor(x as i32, y as i32 - 1),
                neighbor(x as i32 + 1, y as i32),
                neighbor(x as i32, y as i32 + 1),
                neighbor(x as i32 - 1, y as i32),
            ]);
            if cell["x"].as_u64() != Some(x as u64)
                || cell["y"].as_u64() != Some(y as u64)
                || cell["terrainRole"].as_str() != Some(role.as_str())
                || cell["neighborsNESW"] != expected_neighbors
                || !cell["sourceRectPx"].is_null()
                || cell["visualStatus"] != "UNMAPPED_ELIZAWY_REVIEW_REQUIRED" {
                return Err(format!("Semantic evidence mismatch at cell ({x},{y})"));
            }
        }
    }
    // Independently verify every draft cell against ORIGINAL project-owned mapping
    // and explicit candidate-only role bindings. Do not trust editable evidence
    // alone; no approval claims, implicit transitions, transforms or second catalog.
    let root = candidate.join("../../");
    let mapping_bytes = fs::read(root.join(DRAFT_MAPPING_REL)).map_err(|e| format!("Historical mapping missing: {e}"))?;
    let mapping_sha = format!("{:x}", Sha256::digest(&mapping_bytes));
    if mapping_sha != DRAFT_MAPPING_SHA { return Err("Historical source coordinates changed; review required".into()); }
    let bindings_bytes = fs::read(root.join(DRAFT_BINDINGS_REL)).map_err(|e| format!("Explicit draft bindings missing: {e}"))?;
    let mapping: serde_json::Value = serde_json::from_slice(&mapping_bytes).map_err(|e| e.to_string())?;
    let bindings: serde_json::Value = serde_json::from_slice(&bindings_bytes).map_err(|e| e.to_string())?;
    if bindings["schema"] != "havenwild.experimental.manual_draft_role_bindings.v0_1"
        || bindings["sourceFamily"] != "ElizaWy"
        || bindings["source"] != "Terrain/terrain_summer.png"
        || bindings["sourceSha256"] != SOURCE_SHA
        || bindings["historicalMappingSha256"] != DRAFT_MAPPING_SHA
        || bindings["selectionPolicy"] != "EXPLICIT_FIRST_CELL_ONLY_NO_ADJACENCY_NO_AUTOTILE"
        || bindings["reviewStatus"] != "DRAFT_SOURCE_COORDINATES_NOT_VISUALLY_APPROVED"
        || bindings["sourceArtApproval"] != false || bindings["runtimePublicationAllowed"] != false
        || bindings["worldRendererParity"] != false {
        return Err("Draft bindings cannot be treated as asset approval".into());
    }
    let binding_entries = bindings["roleBindings"].as_array().ok_or("Draft bindings absent")?;
    if binding_entries.len() != 3 { return Err("Expected exactly three explicit historical role bindings".into()); }
    let mut roles = std::collections::BTreeMap::<String, [u32;2]>::new();
    for binding in binding_entries {
        let role = binding["sceneRole"].as_str().ok_or("Binding role missing")?;
        let name = binding["historicalBaseTile"].as_str().ok_or("Historical tile name missing")?;
        if binding["sourceVariantIndex"].as_u64() != Some(0) { return Err("Only explicitly selected first historic tile supported".into()); }
        let coords = mapping["baseTiles"][name]["cells"][0].as_array().ok_or("Historic tile missing")?;
        let sx = coords.first().and_then(|v| v.as_u64()).ok_or("Invalid historical x")? as u32;
        let sy = coords.get(1).and_then(|v| v.as_u64()).ok_or("Invalid historical y")? as u32;
        if sx >= SOURCE_W / 32 || sy >= SOURCE_H / 32 || roles.insert(role.to_owned(), [sx,sy]).is_some() {
            return Err("Historical role coordinate invalid or duplicate".into());
        }
    }
    if roles.len() != 3 || !["Grass", "MudBank", "RiverWater"].iter().all(|role| roles.contains_key(*role)) {
        return Err("Unsupported explicit role set".into());
    }
    let draft_raw = fs::read(candidate.join("evidence/draft_source_draw_plan.json"))
        .map_err(|e| format!("Draft plan missing; run PCC draft-plan: {e}"))?;
    let draft: serde_json::Value = serde_json::from_slice(&draft_raw).map_err(|e| e.to_string())?;
    let binding_sha = format!("{:x}", Sha256::digest(&bindings_bytes));
    if draft["schema"] != "havenwild.experimental.draft_source_draw_plan.v0_1"
        || draft["status"] != "UNAPPROVED_GPU_DRAFT_NOT_GAME_RENDERER"
        || draft["sceneId"] != scene_id || draft["sceneSha256"] != scene_sha
        || draft["originalSourceSha256"] != SOURCE_SHA
        || draft["historicalMappingSha256"] != DRAFT_MAPPING_SHA
        || draft["bindingSha256"] != binding_sha
        || draft["sizeTiles"] != serde_json::json!([width,height])
        || draft["tileSizePx"] != serde_json::json!([32,32])
        || draft["unreviewedDrawCount"].as_u64() != Some((width*height) as u64)
        || draft["approvedDrawCallCount"].as_u64() != Some(0)
        || draft["sourceExactPixels"] != true
        || draft["sourceExactArtApproved"] != false
        || draft["worldRendererParity"] != false || draft["pieCertified"] != false
        || draft["runtimePublicationAllowed"] != false {
        return Err("Draft evidence invalid or claims unearned approval".into());
    }
    let draw_entries = draft["draws"].as_array().ok_or("Draft draws absent")?;
    if draw_entries.len() != width*height { return Err("Draft draw count changed".into()); }
    let mut draft_source_cells = Vec::with_capacity(width*height);
    for (i, draw) in draw_entries.iter().enumerate() {
        let x=i%width; let y=i/width;
        let role=&terrain_grid[y][x];
        let coord=roles.get(role).ok_or("Unbound terrain role")?;
        if draw["x"].as_u64() != Some(x as u64)
            || draw["y"].as_u64() != Some(y as u64)
            || draw["terrainRole"].as_str() != Some(role.as_str())
            || draw["sourceRectPx"] != serde_json::json!([coord[0]*32,coord[1]*32,32,32])
            || draw["visualStatus"] != "HISTORICAL_COORDINATE_DRAFT_UNREVIEWED" {
            return Err(format!("Untrusted draft rect at world cell {x},{y}"));
        }
        draft_source_cells.push(*coord);
    }
    Ok(CandidateContent {
        draft_source_cells, scene_id, scene_size: [width,height], terrain_counts: counts.into_iter().collect(),
        terrain_grid, scene_sha,
        status: format!("[PASS] Source SHA verified {sha}; fixture dimensions and {} cells verified", width*height),
        ..Default::default()
    })
}

fn setup(
    mut commands: Commands,
    asset_server: Res<AssetServer>,
    mut images: ResMut<Assets<Image>>,
    mut egui_textures: ResMut<EguiUserTextures>,
    mut atlas_layouts: ResMut<Assets<TextureAtlasLayout>>,
    state: Res<Shell>,
) {
    let size = Extent3d { width: SOURCE_W, height: SOURCE_H, ..default() };
    let mut target = Image {
        texture_descriptor: TextureDescriptor {
            label: Some("havenwild.source.preview"), size,
            dimension: TextureDimension::D2,
            format: TextureFormat::Bgra8UnormSrgb,
            mip_level_count: 1, sample_count: 1,
            usage: TextureUsages::TEXTURE_BINDING | TextureUsages::COPY_DST | TextureUsages::RENDER_ATTACHMENT,
            view_formats: &[],
        },
        ..default()
    };
    target.resize(size);
    let target_handle = images.add(target);
    egui_textures.add_image(EguiTextureHandle::Strong(target_handle.clone()));
    commands.insert_resource(PreviewTarget(target_handle.clone()));
    commands.spawn(Camera2d); // Primary GUI context camera.
    commands.spawn((
        Camera2d,
        Camera { order: -1, ..default() },
        RenderTarget::Image(target_handle.into()),
        RenderLayers::layer(1),
    ));
    commands.spawn((
        Sprite::from_image(asset_server.load(SOURCE_REL)),
        RenderLayers::layer(1),
    ));
    // Separate candidate-only Bevy GPU world target: every pixel comes from
    // an exact cell in the immutable source atlas, never from debug swatches.
    let (w,h)=(state.content.scene_size[0] as u32*32, state.content.scene_size[1] as u32*32);
    let world_size=Extent3d {width:w,height:h,..default()};
    let mut world_target=Image {
        texture_descriptor: TextureDescriptor {
            label: Some("havenwild.unapproved_world_draft"), size:world_size,
            dimension:TextureDimension::D2,format:TextureFormat::Bgra8UnormSrgb,
            mip_level_count:1,sample_count:1,
            usage:TextureUsages::TEXTURE_BINDING|TextureUsages::COPY_DST|TextureUsages::RENDER_ATTACHMENT,
            view_formats:&[],
        },..default()
    };
    world_target.resize(world_size);
    let handle=images.add(world_target);
    egui_textures.add_image(EguiTextureHandle::Strong(handle.clone()));
    commands.insert_resource(DraftTarget(handle.clone()));
    commands.spawn((Camera2d, Camera {order:-2,..default()},
                    RenderTarget::Image(handle.into()), RenderLayers::layer(2)));
    let sheet=asset_server.load(SOURCE_REL);
    let layout=atlas_layouts.add(TextureAtlasLayout::from_grid(UVec2::new(32,32),16,26,None,None));
    for (i,cell) in state.content.draft_source_cells.iter().enumerate() {
        let x=(i%state.content.scene_size[0]) as f32;
        let y=(i/state.content.scene_size[0]) as f32;
        commands.spawn((
            Sprite {
                image:sheet.clone(),
                texture_atlas:Some(TextureAtlas {layout:layout.clone(),index:(cell[1]*16+cell[0]) as usize}),
                ..default()
            },
            Transform::from_xyz(x*32.0+16.0-w as f32/2.0,
                                h as f32/2.0-y*32.0-16.0,0.0),
            RenderLayers::layer(2),
        ));
    }
}

fn gui(
    mut contexts: EguiContexts,
    image: Res<PreviewTarget>,
    draft_image: Res<DraftTarget>,
    mut state: ResMut<Shell>,
) -> Result {
    let texture_id = contexts.image_id(&image.0);
    state.content.preview = texture_id;
    state.content.draft_preview = contexts.image_id(&draft_image.0);
    let ctx = contexts.ctx_mut()?;
    let Shell { spec, shell, theme, content } = &mut *state;
    egui::CentralPanel::default().show(ctx, |root| {
        show_application_shell(root, ctx, spec, shell, theme, content);
    });
    Ok(())
}

fn main() {
    let source = verify_source_and_scene().unwrap_or_else(|e| {
        eprintln!("[BLOCKED] Havenwild Bevy candidate source/fixture proof: {e}");
        std::process::exit(2);
    });
    let theme = ForgeTheme::from_preset(ForgeThemePreset::MidnightMint);
    let shell = ForgeShellState::new(ShellProfile::Standard, vec![
        ModularSurfaceState::new("source_library", "Source Library", SurfaceDock::Left),
        ModularSurfaceState::new("world_draft", "River Scene (GPU DRAFT UNAPPROVED)", SurfaceDock::Center),
        ModularSurfaceState::new("world_semantics", "River Scene (Semantic Debug)", SurfaceDock::Center),
        ModularSurfaceState::new("source_preview", "Bevy Original Source View", SurfaceDock::Center),
        ModularSurfaceState::new("inspector", "Inspector", SurfaceDock::Right),
        ModularSurfaceState::new("scene_evidence", "Actual Scene Semantics", SurfaceDock::Right),
        ModularSurfaceState::new("activity", "Activity / Parity", SurfaceDock::Bottom),
    ]);
    App::new()
        .add_plugins(DefaultPlugins
            .set(ImagePlugin::default_nearest())
            .set(AssetPlugin { file_path: format!("{}/assets", env!("CARGO_MANIFEST_DIR")), ..default() })
            .set(WindowPlugin { primary_window: Some(Window { title: "Havenwild — Bevy / ForgeGUI candidate".into(), resolution: (1280, 820).into(), ..default() }), ..default() }))
        .add_plugins(EguiPlugin::default())
        .insert_resource(ClearColor(Color::srgb(0.10, 0.13, 0.17)))
        .insert_resource(Shell {
            spec: ForgeApplicationSpec::new("Havenwild", "B48R28C3 Experimental"),
            shell, theme, content: source,
        })
        .add_systems(Startup, setup)
        .add_systems(EguiPrimaryContextPass, gui)
        .run();
}
