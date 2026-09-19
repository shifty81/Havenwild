//! EXPERIMENTAL ONLY. Source-exact atlas preview; NOT a resolved Havenwild world scene.
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

#[derive(Resource)]
struct PreviewTarget(Handle<Image>);

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
    scene_id: String,
    scene_size: [usize; 2],
    terrain_counts: Vec<(String, usize)>,
    cell: [usize; 2],
    status: String,
}

impl ForgeShellContent for CandidateContent {
    fn menu(&mut self, ui: &mut egui::Ui) {
        ui.menu_button("File", |ui| { ui.label("Source-only candidate. Saving and publication disabled."); });
        ui.menu_button("View", |ui| { ui.label("Use the surface's Dock menu to float the Inspector."); });
        ui.menu_button("Help", |ui| { ui.label("This previews original ElizaWy bytes, NOT a world scene or PIE."); });
    }

    fn toolbar(&mut self, ui: &mut egui::Ui) {
        ui.label("B48R28B / Bevy 0.19 / source-preview candidate");
        ui.separator();
        ui.label("Read-only");
    }

    fn status(&mut self, ui: &mut egui::Ui) {
        ui.horizontal_wrapped(|ui| {
            ui.label("Original source verified at startup");
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
            "inspector" => {
                ui.heading("Inspector — source cell");
                ui.label(format!("Cell: ({}, {})", self.cell[0], self.cell[1]));
                ui.label(format!("Pixel origin: ({}, {})", self.cell[0] * 32, self.cell[1] * 32));
                ui.label("32 × 32 pixels; no assigned terrain role");
                ui.separator();
                ui.label("Selection changes only this preview, never a project document.");
            }
            "scene_evidence" => {
                ui.heading("Existing Havenwild fixture — semantic evidence");
                ui.label(format!("Scene: {}", self.scene_id));
                ui.label(format!("Size: {} × {} tiles", self.scene_size[0], self.scene_size[1]));
                ui.label(format!("Fixture path: {SCENE_REL}"));
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
                ui.monospace("[PENDING] Source-region / semantic recipe parity");
                ui.monospace("[PENDING] World canvas and actual game PIE");
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
    let scene_path = candidate.join("../../").join(SCENE_REL);
    let scene_raw = fs::read(&scene_path).map_err(|e| format!("Missing real fixture {}: {e}", scene_path.display()))?;
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
    for row in grid {
        let cells = row.as_array().ok_or("Terrain row is not an array")?;
        if cells.len() != width { return Err("Terrain row width mismatch".into()); }
        for value in cells {
            let role = value.as_str().ok_or("Terrain cell not a semantic role")?;
            *counts.entry(role.to_owned()).or_default() += 1;
        }
    }
    Ok(CandidateContent {
        scene_id, scene_size: [width,height], terrain_counts: counts.into_iter().collect(),
        status: format!("[PASS] Source SHA verified {sha}; fixture dimensions and {} cells verified", width*height),
        ..Default::default()
    })
}

fn setup(
    mut commands: Commands,
    asset_server: Res<AssetServer>,
    mut images: ResMut<Assets<Image>>,
    mut egui_textures: ResMut<EguiUserTextures>,
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
}

fn gui(
    mut contexts: EguiContexts,
    image: Res<PreviewTarget>,
    mut state: ResMut<Shell>,
) -> Result {
    let texture_id = contexts.image_id(&image.0);
    state.content.preview = texture_id;
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
            spec: ForgeApplicationSpec::new("Havenwild", "B48R28B Experimental"),
            shell, theme, content: source,
        })
        .add_systems(Startup, setup)
        .add_systems(EguiPrimaryContextPass, gui)
        .run();
}
