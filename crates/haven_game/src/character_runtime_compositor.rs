use haven_assets::{
    universal_lpc_animation::frame_for_progress,
    universal_lpc_character_builder::UniversalLpcCharacterBuilderCatalog,
    universal_lpc_character_recipe::{
        universal_lpc_body_type_for_identity, UniversalLpcCharacterRecipe, UniversalLpcSelection,
        UNIVERSAL_LPC_ACTIVE_SOURCE_COMMIT,
    },
    universal_lpc_resolver::UniversalLpcCharacterResolver,
    universal_lpc_sheet_definition::DEFAULT_ULPC_SOURCE_ROOT,
    asset_pack::{AssetCategory, AssetId, AssetPackId, AssetSourceId, StableAssetRef},
    runtime_asset_cache::RuntimeAssetSession,
};
use haven_save::{
    load_character_profile, CharacterAppearance, CharacterId, CharacterVitalsState,
    PortableAssetRef,
};
use macroquad::prelude::*;
use std::{collections::HashMap, path::Path};

use crate::character_visual_policy::{
    enforce_nearest_character_filter, load_optional_project_character_texture,
    LPC_RUNTIME_FRAME_HEIGHT, LPC_RUNTIME_FRAME_WIDTH,
};
use crate::runtime_texture_cache::StableTextureCache;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum CharacterFacing {
    North,
    West,
    South,
    East,
}

/// Cardinal LPC sheets have four authored rows. Diagonal movement therefore
/// resolves to a cardinal row, but horizontal motion wins unless vertical input
/// is meaningfully stronger. This prevents rapid north/south flipping while the
/// player travels on diagonals.
const CHARACTER_VERTICAL_DOMINANCE_RATIO: f32 = 1.20;

pub(crate) fn resolve_character_facing(facing: Vec2) -> CharacterFacing {
    let x = facing.x.abs();
    let y = facing.y.abs();
    if x < 0.001 && y < 0.001 {
        return CharacterFacing::South;
    }
    if y > x * CHARACTER_VERTICAL_DOMINANCE_RATIO {
        if facing.y < 0.0 {
            CharacterFacing::North
        } else {
            CharacterFacing::South
        }
    } else if facing.x < 0.0 {
        CharacterFacing::West
    } else {
        CharacterFacing::East
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub(crate) struct CharacterLayerAlignmentIssue {
    pub slot: String,
    pub message: String,
}

pub(crate) fn validate_character_layer_alignment(
    slot: &str,
    texture_width: u32,
    texture_height: u32,
) -> Vec<CharacterLayerAlignmentIssue> {
    let mut issues = Vec::new();
    if texture_width == 0 || texture_height == 0 {
        issues.push(CharacterLayerAlignmentIssue {
            slot: slot.to_string(),
            message: "layer texture has zero dimensions".to_string(),
        });
        return issues;
    }
    if texture_width % LPC_RUNTIME_FRAME_WIDTH as u32 != 0 {
        issues.push(CharacterLayerAlignmentIssue {
            slot: slot.to_string(),
            message: format!(
                "width {texture_width}px is not aligned to the {}px LPC frame grid",
                LPC_RUNTIME_FRAME_WIDTH as u32
            ),
        });
    }
    if texture_height % LPC_RUNTIME_FRAME_HEIGHT as u32 != 0 {
        issues.push(CharacterLayerAlignmentIssue {
            slot: slot.to_string(),
            message: format!(
                "height {texture_height}px is not aligned to the {}px LPC frame grid",
                LPC_RUNTIME_FRAME_HEIGHT as u32
            ),
        });
    }
    issues
}

fn validate_character_texture_alignment(slot: &str, texture: &Texture2D) -> Result<(), String> {
    let issues = validate_character_layer_alignment(
        slot,
        texture.width().round().max(0.0) as u32,
        texture.height().round().max(0.0) as u32,
    );
    if issues.is_empty() {
        return Ok(());
    }
    Err(issues
        .into_iter()
        .map(|issue| format!("{}: {}", issue.slot, issue.message))
        .collect::<Vec<_>>()
        .join("; "))
}

#[derive(Clone, Copy, Debug, Hash, PartialEq, Eq)]
pub(crate) enum CharacterAnimationKind {
    Idle,
    Walk,
    Run,
    Jump,
    Climb,
    Sit,
    Emote,
    Punch,
    Combat,
    OneHandSlash,
    OneHandBackslash,
    OneHandHalfslash,
    Watering,
    Thrust,
    Shoot,
    Hurt,
    Spellcast,
    Slash,
}

impl CharacterAnimationKind {
    pub(crate) const ALL: [Self; 18] = [
        Self::Idle,
        Self::Walk,
        Self::Run,
        Self::Jump,
        Self::Climb,
        Self::Sit,
        Self::Emote,
        Self::Punch,
        Self::Combat,
        Self::OneHandSlash,
        Self::OneHandBackslash,
        Self::OneHandHalfslash,
        Self::Watering,
        Self::Thrust,
        Self::Shoot,
        Self::Hurt,
        Self::Spellcast,
        Self::Slash,
    ];

    pub(crate) fn ulpc_id(self) -> &'static str {
        match self {
            Self::Punch => "1h_halfslash",
            _ => self.file_stem(),
        }
    }

    fn file_stem(self) -> &'static str {
        match self {
            Self::Idle => "idle",
            Self::Walk => "walk",
            Self::Run => "run",
            Self::Jump => "jump",
            Self::Climb => "climb",
            Self::Sit => "sit",
            Self::Emote => "emote",
            Self::Punch => "punch",
            Self::Combat => "combat",
            Self::OneHandSlash => "1h_slash",
            Self::OneHandBackslash => "1h_backslash",
            Self::OneHandHalfslash => "1h_halfslash",
            Self::Watering => "watering",
            Self::Thrust => "thrust",
            Self::Shoot => "shoot",
            Self::Hurt => "hurt",
            Self::Spellcast => "spellcast",
            Self::Slash => "slash",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct CharacterAnimationFrame {
    pub facing: CharacterFacing,
    pub animation: CharacterAnimationKind,
    pub frame: usize,
    pub moving: bool,
}

#[derive(Clone, Debug)]
pub(crate) struct RuntimeCharacterLayer {
    pub slot: String,
    pub item_id: String,
    pub layer_number: usize,
    pub z_pos: i32,
    pub walk_texture: Texture2D,
    pub idle_texture: Option<Texture2D>,
    pub action_textures: HashMap<CharacterAnimationKind, Texture2D>,
    pub tint: Color,
}

#[derive(Clone, Debug)]
pub(crate) struct RuntimeCharacterEquipmentOverlay {
    pub item_id: String,
    pub layer_number: usize,
    pub z_pos: i32,
    pub custom_animation: String,
    pub frame_size: u32,
    pub texture: Texture2D,
}

#[derive(Clone, Debug)]
pub(crate) struct RuntimeCharacterAppearance {
    pub appearance: CharacterAppearance,
    pub layers: Vec<RuntimeCharacterLayer>,
    pub equipment_overlays: Vec<RuntimeCharacterEquipmentOverlay>,
}

fn explicit_animation_fallback(
    animation: CharacterAnimationKind,
) -> Option<CharacterAnimationKind> {
    Some(match animation {
        // Punch and Watering are semantic runtime clips generated from the
        // approved authored LPC source motion. Do not silently substitute a
        // different runtime clip if a layer lacks their generated cache.
        CharacterAnimationKind::OneHandSlash
        | CharacterAnimationKind::OneHandBackslash
        | CharacterAnimationKind::OneHandHalfslash => CharacterAnimationKind::Slash,
        CharacterAnimationKind::Combat => CharacterAnimationKind::Idle,
        _ => return None,
    })
}

fn layer_texture_for_animation(
    layer: &RuntimeCharacterLayer,
    animation: CharacterAnimationKind,
) -> Option<&Texture2D> {
    match animation {
        CharacterAnimationKind::Walk => Some(&layer.walk_texture),
        CharacterAnimationKind::Idle => layer.idle_texture.as_ref().or(Some(&layer.walk_texture)),
        animation => layer.action_textures.get(&animation).or_else(|| {
            explicit_animation_fallback(animation).and_then(|fallback| match fallback {
                CharacterAnimationKind::Idle => layer.idle_texture.as_ref(),
                CharacterAnimationKind::Walk => Some(&layer.walk_texture),
                fallback => layer.action_textures.get(&fallback),
            })
        }),
    }
}

/// Whole-character presentation fallbacks. LPC source definitions legitimately
/// provide different animation coverage per garment (for example, a skirt can
/// support walk but not run). Runtime must therefore choose one coherent clip
/// for the assembled character rather than hiding unsupported layers.
fn presentation_animation_candidates(
    requested: CharacterAnimationKind,
) -> &'static [CharacterAnimationKind] {
    use CharacterAnimationKind::*;
    match requested {
        Run => &[Run, Walk, Idle],
        Walk => &[Walk, Idle],
        Climb => &[Climb, Idle],
        Jump => &[Jump, Idle],
        Sit => &[Sit, Idle],
        Emote => &[Emote, Idle],
        Combat => &[Combat, Idle],
        Punch => &[Punch, OneHandHalfslash, Slash, Idle],
        OneHandSlash => &[OneHandSlash, Slash, Idle],
        OneHandBackslash => &[OneHandBackslash, Slash, Idle],
        OneHandHalfslash => &[OneHandHalfslash, Slash, Idle],
        Watering => &[Watering, Thrust, Idle],
        Thrust => &[Thrust, Idle],
        Shoot => &[Shoot, Idle],
        Hurt => &[Hurt, Idle],
        Spellcast => &[Spellcast, Idle],
        Slash => &[Slash, Idle],
        Idle => &[Idle, Walk],
    }
}

fn remap_frame_for_presentation(
    mut frame: CharacterAnimationFrame,
    presentation: CharacterAnimationKind,
) -> CharacterAnimationFrame {
    if presentation == frame.animation {
        return frame;
    }
    frame.animation = presentation;
    frame.frame = match presentation {
        CharacterAnimationKind::Idle => 0,
        // Standard LPC walk sheets use columns 1..=8 for the authored cycle.
        CharacterAnimationKind::Walk => 1 + (frame.frame % 8),
        _ => frame.frame,
    };
    frame
}

impl RuntimeCharacterAppearance {
    fn presentation_frame(&self, frame: CharacterAnimationFrame) -> CharacterAnimationFrame {
        let presentation = presentation_animation_candidates(frame.animation)
            .iter()
            .copied()
            .find(|animation| {
                self.layers
                    .iter()
                    .all(|layer| layer_texture_for_animation(layer, *animation).is_some())
            })
            .unwrap_or(CharacterAnimationKind::Idle);
        remap_frame_for_presentation(frame, presentation)
    }

    pub(crate) fn load_profile_vitals(
        save_root: &Path,
        character_id: &CharacterId,
    ) -> Result<CharacterVitalsState, String> {
        let path = profile_path(save_root, character_id);
        let source = std::fs::read_to_string(&path)
            .map_err(|error| format!("failed to read {}: {error}", path.display()))?;
        let document: serde_json::Value = serde_json::from_str(&source)
            .map_err(|error| format!("failed to parse {}: {error}", path.display()))?;
        let Some(vitals) = document
            .get("vitals")
            .or_else(|| document.get("character_vitals"))
        else {
            return Ok(CharacterVitalsState::default());
        };
        serde_json::from_value(vitals.clone())
            .map_err(|error| format!("failed to decode vitals from {}: {error}", path.display()))
    }

    pub(crate) async fn load(
        save_root: &Path,
        character_id: &CharacterId,
        session: Option<&RuntimeAssetSession>,
        texture_cache: &mut StableTextureCache,
    ) -> Result<Self, String> {
        let profile = load_character_profile(&profile_path(save_root, character_id))?;
        let appearance = profile.appearance.clone();
        if let Some(character_recipe) = profile.character_recipe.as_ref() {
            if let Ok(mut recipe) =
                UniversalLpcCharacterRecipe::from_json_value(character_recipe.0.clone())
            {
                // AC3R4C: gameplay equipment persisted in the character profile is
                // runtime authority. Character creation recipes predate later
                // Main Hand/Off Hand changes, so merge the live persisted tool
                // references before resolving the exact ULPC layers.
                merge_profile_runtime_equipment_into_recipe(&mut recipe, &profile.equipment);
                let source_root = haven_assets::asset_intake::repo_root_dir()
                    .join(DEFAULT_ULPC_SOURCE_ROOT);
                let builder =
                    UniversalLpcCharacterBuilderCatalog::load_source_root(&source_root)?;
                let (layers, equipment_overlays) =
                    load_exact_universal_lpc_runtime_layers(&recipe, &builder).await?;
                return Ok(Self {
                    appearance,
                    layers,
                    equipment_overlays,
                });
            }
        }
        let body_family = appearance_body_family(&appearance);
        let mut layers = Vec::new();
        let hood_occludes_hair = appearance_occludes_slot(&appearance, "hair");
        for layer in appearance.layers.iter().filter(|layer| layer.enabled) {
            if hood_occludes_hair && layer.slot == "hair" {
                continue;
            }
            let generated_walk = generated_component_paths(
                &layer.slot,
                layer.asset.variant_id.as_deref(),
                body_family,
                CharacterAnimationKind::Walk,
            );
            let generated_idle = generated_component_paths(
                &layer.slot,
                layer.asset.variant_id.as_deref(),
                body_family,
                CharacterAnimationKind::Idle,
            );
            let mut walk_texture = if layer.asset.pack_id == "havenwild_starter_character" {
                load_first_generated_texture(&generated_walk).await
            } else {
                None
            };
            if walk_texture.is_none() {
                if let Some(stable_ref) = portable_to_stable_ref(&layer.asset) {
                    walk_texture = texture_cache.load_stable_ref(session, &stable_ref).await;
                }
            }
            if walk_texture.is_none() {
                walk_texture = load_first_generated_texture(&generated_walk).await;
            }
            let Some(walk_texture) = walk_texture else {
                continue;
            };
            validate_character_texture_alignment(&layer.slot, &walk_texture)?;
            enforce_nearest_character_filter(&walk_texture);
            let idle_texture = load_first_generated_texture(&generated_idle).await;
            let mut action_textures = HashMap::new();
            for animation in CharacterAnimationKind::ALL {
                if matches!(
                    animation,
                    CharacterAnimationKind::Idle | CharacterAnimationKind::Walk
                ) {
                    continue;
                }
                let paths = generated_component_paths(
                    &layer.slot,
                    layer.asset.variant_id.as_deref(),
                    body_family,
                    animation,
                );
                if let Some(texture) = load_first_generated_texture(&paths).await {
                    action_textures.insert(animation, texture);
                }
            }
            let tint = layer
                .tint_rgba
                .map(|rgba| Color::from_rgba(rgba[0], rgba[1], rgba[2], rgba[3]))
                .unwrap_or(WHITE);
            layers.push(RuntimeCharacterLayer {
                slot: layer.slot.clone(),
                item_id: layer.asset.asset_id.clone(),
                layer_number: 1,
                z_pos: layer_order(&layer.slot) as i32,
                walk_texture,
                idle_texture,
                action_textures,
                tint,
            });
        }
        if !layers.iter().any(|layer| layer.slot == "face/eyes") {
            let walk_paths = generated_component_paths(
                "face/eyes",
                None,
                body_family,
                CharacterAnimationKind::Walk,
            );
            if let Some(texture) = load_first_generated_texture(&walk_paths).await {
                validate_character_texture_alignment("face/eyes", &texture)?;
                let idle_paths = generated_component_paths(
                    "face/eyes",
                    None,
                    body_family,
                    CharacterAnimationKind::Idle,
                );
                let idle_texture = load_first_generated_texture(&idle_paths).await;
                let mut action_textures = HashMap::new();
                for animation in CharacterAnimationKind::ALL {
                    if matches!(
                        animation,
                        CharacterAnimationKind::Idle | CharacterAnimationKind::Walk
                    ) {
                        continue;
                    }
                    let action_paths =
                        generated_component_paths("face/eyes", None, body_family, animation);
                    if let Some(action_texture) =
                        load_first_generated_texture(&action_paths).await
                    {
                        action_textures.insert(animation, action_texture);
                    }
                }
                layers.push(RuntimeCharacterLayer {
                    slot: "face/eyes".to_string(),
                    item_id: "compatibility_face_eyes".to_string(),
                    layer_number: 1,
                    z_pos: layer_order("face/eyes") as i32,
                    walk_texture: texture,
                    idle_texture,
                    action_textures,
                    tint: WHITE,
                });
            }
        }
        if !layers.iter().any(|layer| layer.slot == "body/base") {
            return Err(
                "production character appearance has no resolved body/base LPC layer".to_string(),
            );
        }
        layers.sort_by(|left, right| {
            left.z_pos
                .cmp(&right.z_pos)
                .then_with(|| left.item_id.cmp(&right.item_id))
                .then_with(|| left.layer_number.cmp(&right.layer_number))
        });
        // AC3R4F: legacy/development profiles can predate the typed Character
        // Builder recipe while still carrying authoritative Main Hand/Off Hand
        // equipment. Keep their existing generated body/clothing layers, but
        // synthesize only the exact ULPC custom equipment overlay recipe so
        // tools remain visible without rewriting the saved appearance.
        let equipment_overlays =
            match load_fallback_universal_lpc_equipment_overlays(&appearance, &profile.equipment)
                .await
            {
                Ok(overlays) => overlays,
                Err(error) => {
                    eprintln!("Havenwild held-equipment overlay fallback failed: {error}");
                    Vec::new()
                }
            };
        Ok(Self {
            appearance,
            layers,
            equipment_overlays,
        })
    }

    pub(crate) fn frame(
        facing: Vec2,
        locomotion: CharacterAnimationKind,
        locomotion_phase: f32,
        action: Option<CharacterAnimationKind>,
        action_phase: f32,
    ) -> CharacterAnimationFrame {
        let facing = resolve_character_facing(facing);
        debug_assert!(matches!(
            locomotion,
            CharacterAnimationKind::Idle
                | CharacterAnimationKind::Walk
                | CharacterAnimationKind::Run
                | CharacterAnimationKind::Climb
        ));
        let animation = action.unwrap_or(locomotion);
        let frame = match animation {
            CharacterAnimationKind::Walk => {
                1 + ((locomotion_phase * 1.25).floor() as i32).rem_euclid(8) as usize
            }
            CharacterAnimationKind::Run => {
                (locomotion_phase.floor() as i32).rem_euclid(8) as usize
            }
            CharacterAnimationKind::Idle => 0,
            CharacterAnimationKind::Climb if action.is_none() => {
                // Ladder traversal is looping locomotion. `locomotion_phase`
                // advances in frame-like units, so normalize six phase units
                // into one authored six-frame ULPC climb cycle. This keeps the
                // climb visibly slower than walk/run without routing it through
                // the one-shot action progress contract.
                let loop_progress = (locomotion_phase / 6.0).rem_euclid(1.0);
                frame_for_progress(animation.ulpc_id(), loop_progress)
            }
            _ => frame_for_progress(animation.ulpc_id(), action_phase.clamp(0.0, 1.0)),
        };
        CharacterAnimationFrame {
            facing,
            animation,
            frame,
            moving: action.is_none() && !matches!(locomotion, CharacterAnimationKind::Idle),
        }
    }

    pub(crate) fn draw_portrait(&self, rect: Rect, frame: CharacterAnimationFrame) {
        let frame = self.presentation_frame(frame);
        for layer in &self.layers {
            let Some(texture) = layer_texture_for_animation(layer, frame.animation) else {
                continue;
            };
            let source = source_rect(texture, frame);
            if source.w < 1.0 || source.h < 1.0 {
                continue;
            }
            // HUD portraits are a readable bust, not the old head/hair-only
            // crop. Preserve shoulders and upper torso/equipment while keeping
            // the feet outside the portrait frame.
            let crop_width = source.w.min(60.0);
            let crop_height: f32 = if source.h >= LPC_RUNTIME_FRAME_HEIGHT {
                76.0
            } else {
                60.0
            };
            let crop = Rect::new(
                source.x + (source.w - crop_width) * 0.5,
                source.y,
                crop_width,
                crop_height.min(source.h),
            );
            draw_texture_ex(
                texture,
                rect.x,
                rect.y,
                layer.tint,
                DrawTextureParams {
                    dest_size: Some(vec2(rect.w, rect.h)),
                    source: Some(crop),
                    ..Default::default()
                },
            );
        }
    }

    pub(crate) fn draw(&self, foot: Vec2, requested_frame: CharacterAnimationFrame) {
        // AC3R4E: climbing is locomotion, not an all-or-nothing cosmetic clip.
        // Keep the authored body climb whenever the body layer supports it; a
        // garment that lacks climb may remain on its idle pose instead of forcing
        // the entire assembled character back to Idle.
        let body_supports_climb = self.layers.iter().any(|layer| {
            (layer.item_id == "body_body" || layer.slot == "body/base")
                && layer
                    .action_textures
                    .contains_key(&CharacterAnimationKind::Climb)
        });
        let frame = if requested_frame.animation == CharacterAnimationKind::Climb
            && body_supports_climb
        {
            requested_frame
        } else {
            self.presentation_frame(requested_frame)
        };

        draw_ellipse(
            foot.x,
            foot.y - 2.0,
            10.0,
            3.0,
            0.0,
            Color::new(0.0, 0.0, 0.0, 0.20),
        );

        self.draw_equipment_overlays(foot, frame, true);
        for layer in &self.layers {
            let (texture, layer_frame) = if frame.animation == CharacterAnimationKind::Climb {
                if let Some(texture) = layer.action_textures.get(&CharacterAnimationKind::Climb) {
                    (texture, frame)
                } else if let Some(texture) = layer.idle_texture.as_ref() {
                    (
                        texture,
                        remap_frame_for_presentation(frame, CharacterAnimationKind::Idle),
                    )
                } else {
                    (
                        &layer.walk_texture,
                        remap_frame_for_presentation(frame, CharacterAnimationKind::Idle),
                    )
                }
            } else {
                let Some(texture) = layer_texture_for_animation(layer, frame.animation) else {
                    continue;
                };
                (texture, frame)
            };
            let source = source_rect(texture, layer_frame);
            if source.w < 1.0 || source.h < 1.0 {
                continue;
            }
            draw_texture_ex(
                texture,
                foot.x - 32.0,
                foot.y - source.h,
                layer.tint,
                DrawTextureParams {
                    dest_size: Some(vec2(64.0, source.h)),
                    source: Some(source),
                    ..Default::default()
                },
            );
        }
        self.draw_equipment_overlays(foot, frame, false);
    }

    fn draw_equipment_overlays(
        &self,
        foot: Vec2,
        frame: CharacterAnimationFrame,
        background: bool,
    ) {
        for overlay in &self.equipment_overlays {
            if (overlay.z_pos < 100) != background {
                continue;
            }
            // ULPC custom tool sheets are explicitly action-only. The previous
            // renderer sampled frame zero during Idle/Walk, which is why an axe
            // could hover beside/above the player's head while standing still.
            // Resolve the custom sheet's declared base animation and only submit
            // it when the body is actually playing that authored action.
            if !custom_equipment_overlay_matches_frame(overlay, frame) {
                continue;
            }
            let source = custom_equipment_source_rect(overlay, frame);
            if source.w < 1.0 || source.h < 1.0 {
                continue;
            }
            let size = overlay.frame_size as f32;
            draw_texture_ex(
                &overlay.texture,
                foot.x - size * 0.5,
                foot.y - size,
                WHITE,
                DrawTextureParams {
                    dest_size: Some(vec2(size, size)),
                    source: Some(source),
                    ..Default::default()
                },
            );
        }
    }
}

fn merge_profile_runtime_equipment_into_recipe(
    recipe: &mut UniversalLpcCharacterRecipe,
    equipment: &[PortableAssetRef],
) {
    recipe.equipment.main_hand = None;
    recipe.equipment.off_hand = None;

    let seed_catalog = crate::character_equipment_runtime::universal_lpc_item_seed_catalog();
    for asset in equipment {
        if asset.pack_id != "universal_lpc_generator" {
            continue;
        }
        let Some(seed) = seed_catalog.items.iter().find(|seed| {
            seed.equipment_source_id == asset.source_id
                || seed.equipment_source_id == asset.asset_id
        }) else {
            continue;
        };
        let definition_id =
            normalized_universal_lpc_equipment_definition_id(&seed.equipment_source_id);
        let selection = UniversalLpcSelection {
            item_id: definition_id,
            display_name: seed.display_name.clone(),
            variant: asset.variant_id.clone(),
            ..Default::default()
        };
        if seed.gameplay_action.eq_ignore_ascii_case("block") {
            recipe.equipment.off_hand = Some(selection);
        } else {
            recipe.equipment.main_hand = Some(selection);
        }
    }
}

fn normalized_universal_lpc_equipment_definition_id(source_id: &str) -> String {
    source_id
        .strip_prefix("ulpc.")
        .unwrap_or(source_id)
        .to_string()
}

fn fallback_universal_lpc_identity(
    appearance: &CharacterAppearance,
) -> (&'static str, &'static str) {
    match appearance_body_family(appearance) {
        "female" | "pregnant" => ("Female", "Adult"),
        "child" => ("Male", "Child"),
        "teen" => ("Male", "Teen"),
        _ => ("Male", "Adult"),
    }
}

async fn load_fallback_universal_lpc_equipment_overlays(
    appearance: &CharacterAppearance,
    equipment: &[PortableAssetRef],
) -> Result<Vec<RuntimeCharacterEquipmentOverlay>, String> {
    if equipment.is_empty() {
        return Ok(Vec::new());
    }
    let (sex, age_group) = fallback_universal_lpc_identity(appearance);
    let mut recipe = UniversalLpcCharacterRecipe::new(
        UNIVERSAL_LPC_ACTIVE_SOURCE_COMMIT,
        universal_lpc_body_type_for_identity(sex, age_group),
    );
    recipe.apply_identity_foundations(sex, age_group);
    merge_profile_runtime_equipment_into_recipe(&mut recipe, equipment);
    if recipe.equipment.main_hand.is_none() && recipe.equipment.off_hand.is_none() {
        return Ok(Vec::new());
    }
    let source_root =
        haven_assets::asset_intake::repo_root_dir().join(DEFAULT_ULPC_SOURCE_ROOT);
    let builder = UniversalLpcCharacterBuilderCatalog::load_source_root(&source_root)?;
    load_custom_universal_lpc_equipment_overlays(&recipe, &builder).await
}

async fn load_exact_universal_lpc_runtime_layers(
    recipe: &UniversalLpcCharacterRecipe,
    builder: &UniversalLpcCharacterBuilderCatalog,
) -> Result<
    (
        Vec<RuntimeCharacterLayer>,
        Vec<RuntimeCharacterEquipmentOverlay>,
    ),
    String,
> {
    let source_root =
        haven_assets::asset_intake::repo_root_dir().join(DEFAULT_ULPC_SOURCE_ROOT);
    let resolver =
        UniversalLpcCharacterResolver::with_source_root(&source_root, &builder.definitions);
    // The exact ULPC recipe is the visual authority for body, clothing, and
    // persisted gameplay equipment. There is no second held-tool renderer;
    // stripping equipment here previously made Main Hand tools physically
    // invisible even though gameplay/equipment state was correct.
    let visual_recipe = recipe.clone();
    let walk = resolver.resolve(&visual_recipe, CharacterAnimationKind::Walk.ulpc_id())?;
    if !walk.unsupported_items.is_empty() {
        return Err(format!(
            "typed character recipe contains unsupported ULPC items: {}",
            walk.unsupported_items.join(", ")
        ));
    }
    let mut layers = Vec::new();
    for resolved in walk.layers {
        if resolved.frame_size != LPC_RUNTIME_FRAME_WIDTH as u32 {
            continue;
        }
        let texture = load_texture(resolved.source_path.to_string_lossy().as_ref())
            .await
            .map_err(|error| {
                format!(
                    "failed to load {}: {error}",
                    resolved.source_path.display()
                )
            })?;
        enforce_nearest_character_filter(&texture);
        validate_character_texture_alignment(&resolved.item_id, &texture)?;
        layers.push(RuntimeCharacterLayer {
            slot: resolved.item_id.clone(),
            item_id: resolved.item_id,
            layer_number: resolved.layer_number,
            z_pos: resolved.z_pos,
            walk_texture: texture,
            idle_texture: None,
            action_textures: HashMap::new(),
            tint: WHITE,
        });
    }
    if layers.is_empty() {
        return Err("typed Universal LPC recipe resolved no walk layers".to_string());
    }

    for animation in CharacterAnimationKind::ALL {
        if animation == CharacterAnimationKind::Walk {
            continue;
        }
        let resolved = resolver.resolve(&visual_recipe, animation.ulpc_id())?;
        for source in resolved.layers {
            if source.frame_size != LPC_RUNTIME_FRAME_WIDTH as u32 {
                continue;
            }
            let Some(layer) = layers.iter_mut().find(|layer| {
                layer.item_id == source.item_id && layer.layer_number == source.layer_number
            }) else {
                continue;
            };
            let texture = load_texture(source.source_path.to_string_lossy().as_ref())
                .await
                .map_err(|error| {
                    format!("failed to load {}: {error}", source.source_path.display())
                })?;
            enforce_nearest_character_filter(&texture);
            validate_character_texture_alignment(&source.item_id, &texture)?;
            if animation == CharacterAnimationKind::Idle {
                layer.idle_texture = Some(texture);
            } else {
                layer.action_textures.insert(animation, texture);
            }
        }
    }
    layers.sort_by(|left, right| {
        left.z_pos
            .cmp(&right.z_pos)
            .then_with(|| left.item_id.cmp(&right.item_id))
            .then_with(|| left.layer_number.cmp(&right.layer_number))
    });
    if !layers.iter().any(|layer| layer.item_id == "body_body") {
        return Err(
            "typed Universal LPC recipe resolved no required body foundation".to_string(),
        );
    }

    // Custom tool sheets are action-only in upstream ULPC definitions and do
    // not participate in Walk/Idle resolution. Resolve them through the same
    // helper used by legacy/development profile fallbacks so both profile
    // generations share one held-equipment authority.
    let equipment_overlays =
        load_custom_universal_lpc_equipment_overlays(&visual_recipe, builder).await?;
    Ok((layers, equipment_overlays))
}

async fn load_custom_universal_lpc_equipment_overlays(
    recipe: &UniversalLpcCharacterRecipe,
    builder: &UniversalLpcCharacterBuilderCatalog,
) -> Result<Vec<RuntimeCharacterEquipmentOverlay>, String> {
    let source_root =
        haven_assets::asset_intake::repo_root_dir().join(DEFAULT_ULPC_SOURCE_ROOT);
    let resolver =
        UniversalLpcCharacterResolver::with_source_root(&source_root, &builder.definitions);
    let mut equipment_overlays = Vec::new();
    for custom_animation in ["tool_axe", "tool_hammer", "tool_rod"] {
        let resolved = resolver.resolve(recipe, custom_animation)?;
        for source in resolved.layers {
            if source.custom_animation.as_deref() != Some(custom_animation)
                || source.frame_size <= LPC_RUNTIME_FRAME_WIDTH as u32
            {
                continue;
            }
            let texture = load_texture(source.source_path.to_string_lossy().as_ref())
                .await
                .map_err(|error| {
                    format!("failed to load {}: {error}", source.source_path.display())
                })?;
            enforce_nearest_character_filter(&texture);
            let frame_size = source.frame_size.max(1);
            let width = texture.width().round().max(0.0) as u32;
            let height = texture.height().round().max(0.0) as u32;
            if width == 0
                || height == 0
                || width % frame_size != 0
                || height % frame_size != 0
            {
                return Err(format!(
                    "custom equipment layer {} is not aligned to its {}px frame grid ({}x{})",
                    source.item_id, frame_size, width, height
                ));
            }
            equipment_overlays.push(RuntimeCharacterEquipmentOverlay {
                item_id: source.item_id,
                layer_number: source.layer_number,
                z_pos: source.z_pos,
                custom_animation: custom_animation.to_string(),
                frame_size,
                texture,
            });
        }
    }
    equipment_overlays.sort_by(|left, right| {
        left.z_pos
            .cmp(&right.z_pos)
            .then_with(|| left.item_id.cmp(&right.item_id))
            .then_with(|| left.layer_number.cmp(&right.layer_number))
    });
    Ok(equipment_overlays)
}

fn custom_equipment_overlay_matches_frame(
    overlay: &RuntimeCharacterEquipmentOverlay,
    frame: CharacterAnimationFrame,
) -> bool {
    haven_assets::universal_lpc_resolver::custom_base_animation(&overlay.custom_animation)
        .is_some_and(|base_animation| base_animation == frame.animation.ulpc_id())
}

fn custom_equipment_source_rect(
    overlay: &RuntimeCharacterEquipmentOverlay,
    frame: CharacterAnimationFrame,
) -> Rect {
    let size = overlay.frame_size.max(1) as f32;
    let columns = (overlay.texture.width() / size).floor().max(1.0) as usize;
    let rows = (overlay.texture.height() / size).floor().max(1.0) as usize;
    let row = if rows >= 4 {
        match frame.facing {
            CharacterFacing::North => 0,
            CharacterFacing::West => 1,
            CharacterFacing::South => 2,
            CharacterFacing::East => 3,
        }
    } else {
        0
    }
    .min(rows.saturating_sub(1));
    let action_animates_tool = matches!(
        frame.animation,
        CharacterAnimationKind::Slash
            | CharacterAnimationKind::OneHandSlash
            | CharacterAnimationKind::OneHandBackslash
            | CharacterAnimationKind::OneHandHalfslash
            | CharacterAnimationKind::Thrust
            | CharacterAnimationKind::Watering
    );
    let column = if action_animates_tool {
        frame.frame % columns
    } else {
        0
    };
    Rect::new(
        column as f32 * size,
        row as f32 * size,
        size,
        size,
    )
}

fn profile_path(save_root: &Path, character_id: &CharacterId) -> std::path::PathBuf {
    save_root
        .parent()
        .unwrap_or(save_root)
        .join("profiles")
        .join("characters")
        .join(&character_id.0)
        .join("profile.json")
}

fn appearance_occludes_slot(appearance: &CharacterAppearance, slot: &str) -> bool {
    slot == "hair"
        && appearance.layers.iter().any(|layer| {
            layer.enabled
                && layer.slot == "headwear"
                && layer.asset.variant_id.as_deref() == Some("headwear_hood")
        })
}

fn component_asset(name: &str, animation: CharacterAnimationKind) -> String {
    format!(
        "assets/generated/lpc/characters/layers/havenwild_player_{name}_{}_64.png",
        animation.file_stem()
    )
}

fn appearance_body_family(appearance: &CharacterAppearance) -> &'static str {
    appearance
        .layers
        .iter()
        .find(|layer| layer.enabled && layer.slot == "body/base")
        .and_then(|layer| layer.asset.variant_id.as_deref())
        .map(|variant| match variant {
            "female_neutral" | "female" => "female",
            "pregnant" | "pregnancy" => "pregnant",
            "teen" => "teen",
            "child" => "child",
            "muscular" => "muscular",
            _ => "male",
        })
        .unwrap_or("male")
}

async fn load_first_generated_texture(paths: &[String]) -> Option<Texture2D> {
    for path in paths {
        if let Some(texture) = load_optional_project_character_texture(path).await {
            return Some(texture);
        }
    }
    None
}

fn generated_component_paths(
    slot: &str,
    variant: Option<&str>,
    body_family: &str,
    animation: CharacterAnimationKind,
) -> Vec<String> {
    let (component, body_specific) = match slot {
        "body/base" => (
            match variant {
                Some("female_neutral") | Some("female") => "body_female",
                Some("pregnant") | Some("pregnancy") => "body_pregnant",
                Some("teen") => "body_teen",
                Some("child") => "body_child",
                Some("muscular") => "body_muscular",
                _ => "body_male",
            },
            false,
        ),
        "face/eyes" => ("eyes", true),
        "clothing/feet" => (
            match variant {
                Some("starter_shoes") => "feet_shoes",
                Some("starter_sandals") => "feet_sandals",
                Some("none") | None => return Vec::new(),
                _ => "feet_boots",
            },
            true,
        ),
        "clothing/legs" => (
            match variant {
                Some("starter_skirt") => "legs_skirt",
                Some("starter_shorts") => "legs_shorts",
                Some("starter_long_skirt") => "legs_long_skirt",
                _ => "legs_pants",
            },
            true,
        ),
        "clothing/torso" => (
            match variant {
                Some("starter_long_shirt") => "torso_long_shirt",
                Some("starter_tunic") => "torso_tunic",
                Some("starter_vest") => "torso_vest",
                Some("starter_apron") => "torso_apron",
                _ => "torso_tshirt",
            },
            true,
        ),
        "hair" => (
            variant
                .filter(|value| value.starts_with("hair_"))
                .unwrap_or(""),
            true,
        ),
        "face/eyebrows" => (
            variant
                .filter(|value| value.starts_with("eyebrows_"))
                .unwrap_or(""),
            true,
        ),
        "headwear" => (
            match variant {
                Some("headwear_hat") => "headwear_hat",
                Some("headwear_hood") => "headwear_hood",
                _ => return Vec::new(),
            },
            true,
        ),
        "face/facial_hair" => (
            variant
                .filter(|value| value.starts_with("facial_hair_"))
                .unwrap_or(""),
            true,
        ),
        _ => return Vec::new(),
    };
    if component.is_empty() {
        return Vec::new();
    }
    let mut paths = Vec::new();
    if body_specific {
        paths.push(component_asset(
            &format!("{component}_{body_family}"),
            animation,
        ));
    }
    paths.push(component_asset(component, animation));
    paths.dedup();
    paths
}

fn portable_to_stable_ref(reference: &PortableAssetRef) -> Option<StableAssetRef> {
    Some(StableAssetRef {
        pack_id: AssetPackId(reference.pack_id.clone()),
        category: parse_asset_category(&reference.category)?,
        asset_id: AssetId(reference.asset_id.clone()),
        source_id: AssetSourceId(reference.source_id.clone()),
        variant_id: reference.variant_id.clone(),
    })
}

fn parse_asset_category(value: &str) -> Option<AssetCategory> {
    Some(match value {
        "terrain" => AssetCategory::Terrain,
        "tile_object" => AssetCategory::TileObject,
        "building" => AssetCategory::Building,
        "wall" => AssetCategory::Wall,
        "floor" => AssetCategory::Floor,
        "door" => AssetCategory::Door,
        "furniture" => AssetCategory::Furniture,
        "crop" => AssetCategory::Crop,
        "tree" => AssetCategory::Tree,
        "foliage" => AssetCategory::Foliage,
        "character" => AssetCategory::Character,
        "clothing" => AssetCategory::Clothing,
        "armor" => AssetCategory::Armor,
        "tool" => AssetCategory::Tool,
        "weapon" => AssetCategory::Weapon,
        "animal" => AssetCategory::Animal,
        "npc" => AssetCategory::Npc,
        "animation" => AssetCategory::Animation,
        "effect" => AssetCategory::Effect,
        "ui" => AssetCategory::Ui,
        "audio" => AssetCategory::Audio,
        "music" => AssetCategory::Music,
        "item" => AssetCategory::Item,
        "recipe" => AssetCategory::Recipe,
        "biome" => AssetCategory::Biome,
        "world_generation" => AssetCategory::WorldGeneration,
        "scene" => AssetCategory::Scene,
        "interior" => AssetCategory::Interior,
        "cave" => AssetCategory::Cave,
        "dungeon" => AssetCategory::Dungeon,
        "editor_template" => AssetCategory::EditorTemplate,
        "other" => AssetCategory::Other,
        _ => return None,
    })
}

fn layer_order(slot: &str) -> usize {
    match slot {
        "shadow" => 0,
        "wings/back" | "weapon/behind" | "shield/behind" => 5,
        "body/base" => 10,
        "body/state_overlay" | "head/base" => 15,
        "face/eyes" => 20,
        "face/eyebrows" => 21,
        "face/facial_hair" => 75,
        "clothing/legs" => 30,
        "clothing/feet" => 40,
        "clothing/torso" | "clothing/accessory" => 50,
        "armor/legs" => 60,
        "armor/feet" => 65,
        "armor/torso" => 70,
        "hair" => 80,
        "headwear" => 90,
        "tool/behind" | "tool/front" | "tool" => 100,
        "weapon/front" | "weapon" | "shield/front" => 110,
        "effect/front" => 120,
        _ => 100,
    }
}

fn source_rect(texture: &Texture2D, frame: CharacterAnimationFrame) -> Rect {
    let frame_height = if texture.height() >= LPC_RUNTIME_FRAME_HEIGHT * 4.0
        && (texture.height() as i32).rem_euclid(LPC_RUNTIME_FRAME_HEIGHT as i32) == 0
    {
        LPC_RUNTIME_FRAME_HEIGHT
    } else {
        64.0
    };
    let columns = (texture.width() / LPC_RUNTIME_FRAME_WIDTH).floor() as usize;
    let rows = (texture.height() / frame_height).floor() as usize;
    if columns == 0 || rows == 0 {
        return Rect::new(0.0, 0.0, 0.0, 0.0);
    }
    let row = match frame.facing {
        CharacterFacing::North => 0,
        CharacterFacing::West => 1,
        CharacterFacing::South => 2,
        CharacterFacing::East => 3,
    }
    .min(rows.saturating_sub(1));
    let column = match frame.animation {
        CharacterAnimationKind::Walk if columns >= 9 => frame.frame.min(8),
        CharacterAnimationKind::Idle => 0,
        _ => frame.frame % columns,
    }
    .min(columns.saturating_sub(1));
    Rect::new(
        column as f32 * LPC_RUNTIME_FRAME_WIDTH,
        row as f32 * frame_height,
        LPC_RUNTIME_FRAME_WIDTH,
        frame_height,
    )
}

#[cfg(test)]
#[path = "character_runtime_compositor_tests.rs"]
mod tests;
