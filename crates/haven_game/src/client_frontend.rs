use std::path::Path;

use haven_save::{
    delete_world_save, load_character_world_link, migrate_legacy_client_save_slots,
    save_character_world_link, scan_world_saves, touch_world_save_metadata, CharacterAppearance,
    CharacterId, CharacterProfile, CharacterProfileStore, CharacterWorldLink, WorldSaveId,
    WorldSaveSummary, MAX_PERSISTENT_CHARACTERS,
};
use macroquad::{
    audio::{load_sound, play_sound, stop_sound, PlaySoundParams, Sound},
    prelude::*,
};

use crate::character_creator_model::{
    migrate_legacy_appearance, StarterCreatorSelection, BOTTOM_PALETTES, EYE_PALETTES,
    FOOTWEAR_PALETTES, HAIR_PALETTES, SHIRT_PALETTES, SKIN_PALETTES,
};
use crate::character_visual_policy::load_optional_project_character_texture;
use crate::client_character_frontend_draw::{
    character_card_rect, character_delete_rect, character_edit_rect, creator_cancel_rect,
    creator_color_rect, creator_confirm_rect, creator_layout, creator_name_rect,
    creator_option_rect, creator_preview_animation_rect, creator_preview_direction_rect,
    draw_button, draw_character_preview, draw_color_selector, draw_frontend_backdrop, draw_panel,
    draw_section_panel, draw_text_centered, draw_title, draw_title_menu_background,
    draw_title_menu_hover, frontend_back_rect, main_continue_rect, main_load_rect,
    main_multiplayer_rect, main_new_rect, main_quit_rect, main_settings_rect, mouse_vec,
    open_folder, title_continue_visual_source, title_load_visual_source,
    title_multiplayer_visual_source, title_new_visual_source, title_quit_visual_source,
    title_settings_visual_source, world_card_rect, world_create_rect, world_delete_rect,
    world_folder_rect, world_play_rect, CharacterPreviewTextures,
};
use crate::client_save_generation::{create_seeded_world_save_with_settings, suggested_world_seed};
use crate::runtime_config::{runtime_path, runtime_save_root};
use crate::world_creation_wizard::{WorldCreationWizard, WorldCreationWizardAction};

const CHARACTER_PREVIEW_LAYER_ROOT: &str = "assets/generated/lpc/characters/layers";

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum FrontendIntent {
    NewGame,
    LoadGame,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum FrontendScreen {
    MainMenu,
    Characters,
    Creator,
    Worlds,
    WorldCreator,
    Settings,
    Multiplayer,
    Credits,
}

#[derive(Clone, Debug)]
pub(crate) struct WorldLaunchRequest {
    pub character_id: CharacterId,
    pub world_id: WorldSaveId,
}

#[derive(Clone, Debug)]
struct CreatorState {
    editing: Option<CharacterId>,
    name: String,
    appearance: CharacterAppearance,
    selection: StarterCreatorSelection,
    name_focused: bool,
}

pub(crate) struct ClientFrontend {
    screen: FrontendScreen,
    intent: FrontendIntent,
    profile_store: CharacterProfileStore,
    profiles: Vec<CharacterProfile>,
    selected_character: Option<CharacterId>,
    creator: CreatorState,
    worlds: Vec<WorldSaveSummary>,
    world_page: usize,
    world_creator: WorldCreationWizard,
    preview_layers: Option<CharacterPreviewTextures>,
    title_screen: Option<Texture2D>,
    title_button_hover: Option<Texture2D>,
    frontend_music: Option<Sound>,
    frontend_music_playing: bool,
    status: String,
    save_root: String,
}

async fn load_character_preview_layers() -> Option<CharacterPreviewTextures> {
    let ids = [
        "body_male",
        "body_female",
        "eyes",
        "feet_boots",
        "feet_shoes",
        "legs_pants",
        "legs_skirt",
        "torso_tshirt",
        "torso_long_shirt",
        "torso_tunic",
        "torso_vest",
        "torso_apron",
        "legs_shorts",
        "legs_long_skirt",
        "feet_sandals",
        "headwear_hat",
        "headwear_hood",
        "hair_medium_01_page",
        "hair_medium_02_curly",
        "hair_medium_03_idol",
        "hair_medium_04_bangs_bun",
        "hair_medium_05_cornrows",
        "hair_medium_06_dreadlocks",
        "hair_medium_07_bob_side_part",
        "hair_medium_08_bob_bangs",
        "hair_medium_09_twists",
        "hair_medium_10_twists_fade",
        "hair_short_01_buzzcut",
        "hair_short_02_parted",
        "hair_short_03_curly",
        "hair_short_04_cowlick",
        "hair_short_05_natural",
        "hair_short_06_balding",
        "hair_short_07_flat_top",
        "hair_short_08_flat_top_fade",
        "eyebrows_01_thin",
        "eyebrows_02_thick",
        "facial_hair_01_walrus_mustache",
        "facial_hair_02_chevron_mustache",
        "facial_hair_03_handlebar_mustache",
        "facial_hair_04_lampshade_mustache",
        "facial_hair_05_horseshoe_mustache",
        "facial_hair_06_trimmed_beard",
        "facial_hair_07_medium_beard",
    ];
    let mut layers = std::collections::HashMap::new();
    for id in ids {
        let path = format!("{CHARACTER_PREVIEW_LAYER_ROOT}/havenwild_player_{id}_walk_64.png");
        if let Some(texture) = load_optional_project_character_texture(&path).await {
            layers.insert(id.to_string(), texture);
        }
        // Non-body layers may have body-family-specific generated variants.
        // Body ids already encode their family, so never probe nonsense names
        // such as body_male_female or body_female_female.
        if !id.starts_with("body_") {
            let female_id = format!("{id}_female");
            let female_path =
                format!("{CHARACTER_PREVIEW_LAYER_ROOT}/havenwild_player_{female_id}_walk_64.png");
            if let Some(texture) = load_optional_project_character_texture(&female_path).await {
                layers.insert(female_id, texture);
            }
        }
    }
    (!layers.is_empty()).then_some(CharacterPreviewTextures { layers })
}

fn credits_button_rect_for_viewport(width: f32, height: f32) -> Rect {
    Rect::new(
        (width - 168.0).max(16.0),
        (height - 46.0).max(16.0),
        152.0,
        30.0,
    )
}

fn credits_button_rect() -> Rect {
    credits_button_rect_for_viewport(screen_width(), screen_height())
}

impl ClientFrontend {
    pub(crate) async fn new() -> Self {
        let save_root = runtime_save_root();
        let profile_store = CharacterProfileStore::new(
            Path::new(&save_root)
                .parent()
                .unwrap_or_else(|| Path::new(&save_root))
                .join("profiles")
                .join("characters"),
        );
        let preview_layers = load_character_preview_layers().await;
        let title_screen = load_texture(&runtime_path("content/ui/havenwild_title_screen.png"))
            .await
            .ok();
        let title_button_hover =
            load_texture(&runtime_path("content/ui/havenwild_title_button_hover.png"))
                .await
                .ok();
        let frontend_music =
            match load_sound(&runtime_path("content/audio/music/frontend/Harp.ogg")).await {
                Ok(sound) => Some(sound),
                Err(_) => load_sound(&runtime_path("content/audio/music/frontend/Harp.wav"))
                    .await
                    .ok(),
            };
        let mut frontend = Self {
            screen: FrontendScreen::MainMenu,
            intent: FrontendIntent::NewGame,
            profiles: Vec::new(),
            selected_character: None,
            creator: CreatorState {
                editing: None,
                name: "New Character".to_string(),
                appearance: default_appearance(),
                selection: StarterCreatorSelection::default(),
                name_focused: true,
            },
            worlds: Vec::new(),
            world_page: 0,
            world_creator: WorldCreationWizard::new(1_337, "Havenwild World"),
            preview_layers,
            title_screen,
            title_button_hover,
            frontend_music,
            frontend_music_playing: false,
            status: "Choose New Game or Load Game".to_string(),
            save_root,
            profile_store,
        };
        frontend.refresh_all();
        frontend.start_frontend_music();
        frontend
    }

    pub(crate) fn refresh_slots(&mut self) {
        self.refresh_all();
        self.start_frontend_music();
    }

    fn refresh_all(&mut self) {
        self.profiles = self.profile_store.scan().unwrap_or_else(|error| {
            self.status = format!("Could not scan character profiles: {error}");
            Vec::new()
        });
        for profile in &mut self.profiles {
            if let Some(migrated) = migrate_legacy_appearance(&profile.appearance) {
                profile.appearance = migrated;
                if let Err(error) = self.profile_store.update(profile) {
                    self.status = format!(
                        "Could not migrate character {}: {error}",
                        profile.character_id.0
                    );
                }
            }
        }
        let _ = migrate_legacy_client_save_slots(&self.save_root);
        self.worlds = scan_world_saves(&self.save_root).unwrap_or_else(|error| {
            self.status = format!("Could not scan worlds: {error}");
            Vec::new()
        });
        let max_page = self.worlds.len() / 3;
        self.world_page = self.world_page.min(max_page);
    }

    pub(crate) fn update(&mut self) -> Option<WorldLaunchRequest> {
        if is_key_pressed(KeyCode::Escape) {
            match self.screen {
                FrontendScreen::MainMenu => std::process::exit(0),
                FrontendScreen::Characters => self.screen = FrontendScreen::MainMenu,
                FrontendScreen::Creator => self.screen = FrontendScreen::Characters,
                FrontendScreen::Worlds => self.screen = FrontendScreen::Characters,
                FrontendScreen::WorldCreator => self.screen = FrontendScreen::Worlds,
                FrontendScreen::Settings
                | FrontendScreen::Multiplayer
                | FrontendScreen::Credits => self.screen = FrontendScreen::MainMenu,
            }
            return None;
        }

        let launch = match self.screen {
            FrontendScreen::MainMenu => self.update_main_menu(),
            FrontendScreen::Characters => self.update_character_list(),
            FrontendScreen::Creator => self.update_creator(),
            FrontendScreen::Worlds => self.update_world_list(),
            FrontendScreen::WorldCreator => self.update_world_creator(),
            FrontendScreen::Settings => self.update_settings(),
            FrontendScreen::Multiplayer => self.update_multiplayer(),
            FrontendScreen::Credits => self.update_credits(),
        };
        if launch.is_some() {
            self.stop_frontend_music();
        }
        launch
    }

    pub(crate) fn draw(&self) {
        if self.screen == FrontendScreen::MainMenu {
            self.draw_main_menu();
            return;
        }

        draw_frontend_backdrop(self.title_screen.as_ref());
        match self.screen {
            FrontendScreen::MainMenu => unreachable!("main menu returned above"),
            FrontendScreen::Characters => self.draw_character_list(),
            FrontendScreen::Creator => self.draw_creator(),
            FrontendScreen::Worlds => self.draw_world_list(),
            FrontendScreen::WorldCreator => self.world_creator.draw(),
            FrontendScreen::Settings => self.draw_settings(),
            FrontendScreen::Multiplayer => self.draw_multiplayer(),
            FrontendScreen::Credits => self.draw_credits(),
        }
        draw_text_centered(
            &self.status,
            screen_width() * 0.5,
            screen_height() - 26.0,
            16.0,
            Color::from_rgba(234, 221, 191, 255),
        );
    }

    fn update_main_menu(&mut self) -> Option<WorldLaunchRequest> {
        if is_key_pressed(KeyCode::C) {
            self.screen = FrontendScreen::Credits;
            self.status = "Havenwild credits and third-party attribution".to_string();
            return None;
        }
        if !is_mouse_button_pressed(MouseButton::Left) {
            return None;
        }
        let mouse = mouse_vec();
        if main_continue_rect().contains(mouse) {
            if self.profiles.is_empty() || self.worlds.is_empty() {
                self.status =
                    "No existing character and world are available to continue".to_string();
            } else {
                self.intent = FrontendIntent::LoadGame;
                self.screen = FrontendScreen::Characters;
                self.status = "Choose the persistent character to continue".to_string();
            }
        } else if main_new_rect().contains(mouse) {
            self.intent = FrontendIntent::NewGame;
            self.screen = FrontendScreen::Characters;
            self.status = "Choose one of five persistent characters".to_string();
        } else if main_load_rect().contains(mouse) {
            self.intent = FrontendIntent::LoadGame;
            self.screen = FrontendScreen::Characters;
            self.status = "Choose a character, then choose a world".to_string();
        } else if main_settings_rect().contains(mouse) {
            self.screen = FrontendScreen::Settings;
            self.status = "Havenwild settings".to_string();
        } else if main_multiplayer_rect().contains(mouse) {
            self.screen = FrontendScreen::Multiplayer;
            self.status = "Host or join a Havenwild world".to_string();
        } else if credits_button_rect().contains(mouse) {
            self.screen = FrontendScreen::Credits;
            self.status = "Havenwild credits and third-party attribution".to_string();
        } else if main_quit_rect().contains(mouse) {
            std::process::exit(0);
        }
        None
    }

    fn update_settings(&mut self) -> Option<WorldLaunchRequest> {
        if is_mouse_button_pressed(MouseButton::Left) && frontend_back_rect().contains(mouse_vec())
        {
            self.screen = FrontendScreen::MainMenu;
            self.status = "Choose New Game or Load Game".to_string();
        }
        None
    }

    fn update_multiplayer(&mut self) -> Option<WorldLaunchRequest> {
        if is_mouse_button_pressed(MouseButton::Left) && frontend_back_rect().contains(mouse_vec())
        {
            self.screen = FrontendScreen::MainMenu;
            self.status = "Choose New Game or Load Game".to_string();
        }
        None
    }

    fn update_credits(&mut self) -> Option<WorldLaunchRequest> {
        if is_key_pressed(KeyCode::C)
            || (is_mouse_button_pressed(MouseButton::Left)
                && frontend_back_rect().contains(mouse_vec()))
        {
            self.screen = FrontendScreen::MainMenu;
            self.status = "Choose New Game or Load Game".to_string();
        }
        None
    }

    fn update_character_list(&mut self) -> Option<WorldLaunchRequest> {
        if !is_mouse_button_pressed(MouseButton::Left) {
            return None;
        }
        let mouse = mouse_vec();
        for index in 0..MAX_PERSISTENT_CHARACTERS {
            let card = character_card_rect(index);
            if !card.contains(mouse) {
                continue;
            }
            if let Some(profile) = self.profiles.get(index).cloned() {
                if character_edit_rect(card).contains(mouse) {
                    self.creator = CreatorState {
                        editing: Some(profile.character_id),
                        name: profile.display_name,
                        selection: StarterCreatorSelection::from_appearance(&profile.appearance),
                        appearance: profile.appearance,
                        name_focused: true,
                    };
                    self.screen = FrontendScreen::Creator;
                    self.status = "Editing persistent character".to_string();
                } else if character_delete_rect(card).contains(mouse) {
                    if let Err(error) = self.profile_store.delete(&profile.character_id) {
                        self.status = format!("Could not delete character: {error}");
                    } else {
                        self.selected_character = None;
                        self.refresh_all();
                        self.status = "Character deleted; world saves were preserved".to_string();
                    }
                } else {
                    self.selected_character = Some(profile.character_id);
                    self.screen = FrontendScreen::Worlds;
                    self.status = "Choose a world or create a new one".to_string();
                }
            } else {
                self.creator = CreatorState {
                    editing: None,
                    name: "New Character".to_string(),
                    appearance: default_appearance(),
                    selection: StarterCreatorSelection::default(),
                    name_focused: true,
                };
                self.screen = FrontendScreen::Creator;
                self.status = "Create a modular LPC character".to_string();
            }
            break;
        }
        None
    }

    fn update_creator(&mut self) -> Option<WorldLaunchRequest> {
        if self.creator.name_focused {
            while let Some(character) = get_char_pressed() {
                if !character.is_control() && self.creator.name.chars().count() < 28 {
                    self.creator.name.push(character);
                }
            }
            if is_key_pressed(KeyCode::Backspace) {
                self.creator.name.pop();
            }
        }

        let enter_pressed = is_key_pressed(KeyCode::Enter);
        if !is_mouse_button_pressed(MouseButton::Left) && !enter_pressed {
            return None;
        }
        let mouse = mouse_vec();
        if is_mouse_button_pressed(MouseButton::Left) {
            self.creator.name_focused = creator_name_rect().contains(mouse);
            for row in 0..8 {
                if creator_option_rect(row).contains(mouse) {
                    match row {
                        0 => self.creator.selection.body = self.creator.selection.body.cycle(1),
                        1 => self.creator.selection.hair = self.creator.selection.hair.cycle(1),
                        2 => {
                            self.creator.selection.eyebrows =
                                self.creator.selection.eyebrows.cycle(1)
                        }
                        3 => {
                            self.creator.selection.facial_hair =
                                self.creator.selection.facial_hair.cycle(1)
                        }
                        4 => self.creator.selection.torso = self.creator.selection.torso.cycle(1),
                        5 => self.creator.selection.legs = self.creator.selection.legs.cycle(1),
                        6 => {
                            self.creator.selection.footwear =
                                self.creator.selection.footwear.cycle(1)
                        }
                        _ => {
                            self.creator.selection.headwear =
                                self.creator.selection.headwear.cycle(1)
                        }
                    }
                    self.creator.selection.normalize_compatibility();
                    self.sync_creator_appearance();
                    return None;
                }
            }
            if creator_preview_direction_rect().contains(mouse) {
                self.creator.selection.preview_facing =
                    self.creator.selection.preview_facing.cycle(1);
                self.sync_creator_appearance();
                return None;
            }
            if creator_preview_animation_rect().contains(mouse) {
                self.creator.selection.preview_walking = !self.creator.selection.preview_walking;
                self.sync_creator_appearance();
                return None;
            }
            for row in 0..6 {
                let (left, right) = creator_color_rect(row);
                if left.contains(mouse) || right.contains(mouse) {
                    let delta = if left.contains(mouse) { -1 } else { 1 };
                    match row {
                        0 => self.creator.selection.cycle_skin(delta),
                        1 => self.creator.selection.cycle_eyes(delta),
                        2 => self.creator.selection.cycle_shirt(delta),
                        3 => self.creator.selection.cycle_bottom(delta),
                        4 => self.creator.selection.cycle_footwear(delta),
                        _ => self.creator.selection.cycle_hair_color(delta),
                    }
                    self.sync_creator_appearance();
                    return None;
                }
            }
        }
        if creator_cancel_rect().contains(mouse) {
            self.screen = FrontendScreen::Characters;
            return None;
        }
        if creator_confirm_rect().contains(mouse) || enter_pressed {
            let name = self.creator.name.trim();
            if name.is_empty() {
                self.status = "Character name cannot be empty".to_string();
                return None;
            }
            let result = if let Some(character_id) = self.creator.editing.clone() {
                let profile = self
                    .profiles
                    .iter()
                    .find(|profile| profile.character_id == character_id)
                    .cloned();
                match profile {
                    Some(mut profile) => {
                        profile.display_name = name.to_string();
                        profile.appearance = self.creator.selection.appearance();
                        self.profile_store
                            .update(&profile)
                            .map(|_| profile.character_id)
                    }
                    None => Err("character profile disappeared during editing".to_string()),
                }
            } else {
                let profile = CharacterProfile::new(name, self.creator.selection.appearance());
                let character_id = profile.character_id.clone();
                self.profile_store.create(&profile).map(|_| character_id)
            };
            match result {
                Ok(character_id) => {
                    self.selected_character = Some(character_id);
                    self.refresh_all();
                    self.screen = FrontendScreen::Worlds;
                    self.status = "Character saved. Choose a world.".to_string();
                }
                Err(error) => self.status = format!("Could not save character: {error}"),
            }
        }
        None
    }

    fn sync_creator_appearance(&mut self) {
        self.creator.appearance = self.creator.selection.appearance();
        let facing = self.creator.selection.preview_facing.variant();
        self.creator
            .appearance
            .layers
            .push(haven_save::CharacterAppearanceLayer {
                slot: "preview/facing".to_string(),
                asset: haven_save::PortableAssetRef {
                    pack_id: "preview".to_string(),
                    category: "other".to_string(),
                    asset_id: "facing".to_string(),
                    source_id: "creator".to_string(),
                    variant_id: Some(facing.to_string()),
                },
                palette_id: None,
                tint_rgba: None,
                enabled: true,
            });
        self.creator
            .appearance
            .layers
            .push(haven_save::CharacterAppearanceLayer {
                slot: "preview/animation".to_string(),
                asset: haven_save::PortableAssetRef {
                    pack_id: "preview".to_string(),
                    category: "other".to_string(),
                    asset_id: "animation".to_string(),
                    source_id: "creator".to_string(),
                    variant_id: Some(
                        if self.creator.selection.preview_walking {
                            "walk"
                        } else {
                            "idle"
                        }
                        .to_string(),
                    ),
                },
                palette_id: None,
                tint_rgba: None,
                enabled: true,
            });
    }

    fn update_world_list(&mut self) -> Option<WorldLaunchRequest> {
        if is_key_pressed(KeyCode::PageDown) {
            let max_page = self.worlds.len() / 3;
            self.world_page = (self.world_page + 1).min(max_page);
        }
        if is_key_pressed(KeyCode::PageUp) {
            self.world_page = self.world_page.saturating_sub(1);
        }
        if !is_mouse_button_pressed(MouseButton::Left) {
            return None;
        }
        let mouse = mouse_vec();
        let start = self.world_page * 3;
        for local_index in 0..3 {
            let card = world_card_rect(local_index);
            if !card.contains(mouse) {
                continue;
            }
            if let Some(summary) = self.worlds.get(start + local_index).cloned() {
                if summary.occupied() && world_play_rect(card).contains(mouse) {
                    if let Some(character_id) = self.selected_character.clone() {
                        let _ = touch_world_save_metadata(&summary.paths.metadata);
                        let world_root = Path::new(&summary.paths.root);
                        let mut link = load_character_world_link(world_root, &character_id)
                            .unwrap_or_else(|_| {
                                CharacterWorldLink::new(
                                    character_id.clone(),
                                    summary.world_id.clone(),
                                )
                            });
                        link.touch();
                        let _ = save_character_world_link(world_root, &link);
                        self.status =
                            format!("Launching {} as {}", summary.world_id.0, character_id.0);
                        return Some(WorldLaunchRequest {
                            character_id,
                            world_id: summary.world_id,
                        });
                    }
                } else if world_folder_rect(card).contains(mouse) {
                    open_folder(&summary.paths.root, &mut self.status);
                } else if summary.occupied() && world_delete_rect(card).contains(mouse) {
                    match delete_world_save(&self.save_root, &summary.world_id) {
                        Ok(_) => {
                            self.refresh_all();
                            self.status =
                                "World deleted; character profiles were preserved".to_string();
                        }
                        Err(error) => self.status = format!("Could not delete world: {error}"),
                    }
                }
            } else if world_create_rect(card).contains(mouse) {
                let draft_world_id = WorldSaveId::new_unique();
                let seed = suggested_world_seed(&draft_world_id);
                let display_name = format!("Havenwild World {}", self.worlds.len() + 1);
                self.world_creator = WorldCreationWizard::new(seed, display_name);
                self.screen = FrontendScreen::WorldCreator;
                self.status =
                    "Configure land, water, biomes, settlements, housing, and family rules"
                        .to_string();
            }
            break;
        }
        None
    }

    fn update_world_creator(&mut self) -> Option<WorldLaunchRequest> {
        match self.world_creator.update() {
            WorldCreationWizardAction::None => {}
            WorldCreationWizardAction::Cancel => {
                self.screen = FrontendScreen::Worlds;
                self.status = "World creation cancelled".to_string();
            }
            WorldCreationWizardAction::Invalid(error) => {
                self.status = format!("World settings are not valid: {error}");
            }
            WorldCreationWizardAction::Create(settings) => {
                let world_id = WorldSaveId::new_unique();
                let seed = settings.seed;
                match create_seeded_world_save_with_settings(&self.save_root, world_id, settings) {
                    Ok(_) => {
                        self.refresh_all();
                        self.screen = FrontendScreen::Worlds;
                        self.status = format!("Created world from seed {seed}");
                    }
                    Err(error) => self.status = format!("Could not create world: {error}"),
                }
            }
        }
        None
    }

    fn draw_main_menu(&self) {
        draw_title_menu_background(self.title_screen.as_ref());
        let can_continue = !self.profiles.is_empty() && !self.worlds.is_empty();

        if self.title_screen.is_some() {
            // Preferred path: the accepted project-owned title image already contains
            // the complete normal-state menu art. The hover texture supplies only
            // organic hover/pressed states over those authored button silhouettes.
            draw_title_menu_hover(
                self.title_button_hover.as_ref(),
                title_continue_visual_source(),
                main_continue_rect(),
                can_continue,
            );
            draw_title_menu_hover(
                self.title_button_hover.as_ref(),
                title_new_visual_source(),
                main_new_rect(),
                true,
            );
            draw_title_menu_hover(
                self.title_button_hover.as_ref(),
                title_load_visual_source(),
                main_load_rect(),
                true,
            );
            draw_title_menu_hover(
                self.title_button_hover.as_ref(),
                title_settings_visual_source(),
                main_settings_rect(),
                true,
            );
            draw_title_menu_hover(
                self.title_button_hover.as_ref(),
                title_multiplayer_visual_source(),
                main_multiplayer_rect(),
                true,
            );
            draw_title_menu_hover(
                self.title_button_hover.as_ref(),
                title_quit_visual_source(),
                main_quit_rect(),
                true,
            );
        } else {
            // Supported fail-safe path: if the accepted title artwork cannot be
            // loaded, keep the complete frontend usable with native drawn controls.
            // These deliberately reuse the exact same authoritative hit rectangles
            // consumed by update_main_menu(), so fallback behavior cannot drift from
            // the illustrated menu's navigation behavior.
            draw_button(main_continue_rect(), "CONTINUE", can_continue);
            draw_button(main_new_rect(), "NEW GAME", true);
            draw_button(main_load_rect(), "LOAD GAME", false);
            draw_button(main_settings_rect(), "SETTINGS", false);
            draw_button(main_multiplayer_rect(), "MULTIPLAYER", false);
            draw_button(main_quit_rect(), "QUIT", false);

            draw_text_centered(
                "Fallback menu active - title artwork unavailable",
                screen_width() * 0.5,
                screen_height() - 58.0,
                14.0,
                Color::from_rgba(190, 177, 148, 255),
            );
        }

        draw_button(credits_button_rect(), "Credits [C]", false);
        if self.status.starts_with("No existing") {
            draw_text_centered(
                &self.status,
                screen_width() * 0.5,
                screen_height() - 24.0,
                16.0,
                Color::from_rgba(255, 232, 184, 255),
            );
        }
    }

    fn draw_credits(&self) {
        draw_title("CREDITS & ATTRIBUTION");
        let panel = Rect::new(
            screen_width() * 0.5 - 360.0,
            120.0,
            720.0,
            (screen_height() - 230.0).max(430.0),
        );
        draw_panel(panel, true);
        let lines = [
            "Havenwild is an original project built on its own Rust runtime and authoring tools.",
            "Visual content includes attributed Liberated Pixel Cup-compatible source artwork.",
            "ElizaWy / LPC Revised content is pinned and audited by source revision.",
            "Universal LPC Character Generator content is pinned and audited by source revision.",
            "Additional credited OpenGameArt sources are tracked through Havenwild asset metadata.",
            "Complete license and attribution records ship with the project content manifests.",
        ];
        for (index, line) in lines.iter().enumerate() {
            draw_text(
                line,
                panel.x + 34.0,
                panel.y + 70.0 + index as f32 * 38.0,
                18.0,
                Color::from_rgba(235, 224, 199, 255),
            );
        }
        draw_text(
            "Press C or Back to return",
            panel.x + 34.0,
            panel.y + panel.h - 38.0,
            16.0,
            Color::from_rgba(166, 188, 184, 255),
        );
        draw_button(frontend_back_rect(), "BACK", false);
    }

    fn draw_settings(&self) {
        draw_title("SETTINGS");
        let panel = Rect::new(
            screen_width() * 0.5 - 310.0,
            130.0,
            620.0,
            (screen_height() - 240.0).max(390.0),
        );
        draw_panel(panel, true);
        draw_section_panel(
            Rect::new(panel.x + 18.0, panel.y + 18.0, panel.w - 36.0, 118.0),
            "DISPLAY & INTERFACE",
        );
        draw_text(
            "Window, scaling, tooltips, HUD visibility, and accessibility settings",
            panel.x + 36.0,
            panel.y + 88.0,
            17.0,
            Color::from_rgba(235, 224, 199, 255),
        );
        draw_section_panel(
            Rect::new(panel.x + 18.0, panel.y + 154.0, panel.w - 36.0, 118.0),
            "AUDIO",
        );
        draw_text(
            "Music, ambience, effects, dialogue, and multiplayer voice controls",
            panel.x + 36.0,
            panel.y + 224.0,
            17.0,
            Color::from_rgba(235, 224, 199, 255),
        );
        draw_section_panel(
            Rect::new(panel.x + 18.0, panel.y + 290.0, panel.w - 36.0, 118.0),
            "GAMEPLAY",
        );
        draw_text(
            "Input, camera, autosave, notifications, and host-world preferences",
            panel.x + 36.0,
            panel.y + 360.0,
            17.0,
            Color::from_rgba(235, 224, 199, 255),
        );
        draw_button(frontend_back_rect(), "BACK", false);
    }

    fn draw_multiplayer(&self) {
        draw_title("MULTIPLAYER");
        let panel = Rect::new(
            screen_width() * 0.5 - 330.0,
            150.0,
            660.0,
            (screen_height() - 300.0).max(340.0),
        );
        draw_panel(panel, true);
        draw_text_centered(
            "Havenwild worlds are host-controlled and server-authoritative",
            panel.x + panel.w * 0.5,
            panel.y + 72.0,
            20.0,
            Color::from_rgba(245, 228, 188, 255),
        );
        draw_text_centered(
            "Create or load a world, then enable multiplayer from its host settings.",
            panel.x + panel.w * 0.5,
            panel.y + 126.0,
            17.0,
            Color::from_rgba(225, 216, 195, 255),
        );
        draw_text_centered(
            "Joining, permissions, family play, and shared progression use the same persistent profiles.",
            panel.x + panel.w * 0.5,
            panel.y + 168.0,
            16.0,
            Color::from_rgba(190, 207, 194, 255),
        );
        draw_button(frontend_back_rect(), "BACK", false);
    }

    fn draw_character_list(&self) {
        draw_title("CHOOSE YOUR CHARACTER");
        draw_text_centered(
            "Up to 5 persistent characters • world saves are separate",
            screen_width() * 0.5,
            120.0,
            20.0,
            LIGHTGRAY,
        );
        for index in 0..MAX_PERSISTENT_CHARACTERS {
            let card = character_card_rect(index);
            draw_panel(card, index == 0);
            if let Some(profile) = self.profiles.get(index) {
                draw_character_preview(card, &profile.appearance, self.preview_layers.as_ref());
                draw_text(
                    &profile.display_name,
                    card.x + 14.0,
                    card.y + card.h - 58.0,
                    22.0,
                    WHITE,
                );
                draw_text(
                    "Persistent profile",
                    card.x + 14.0,
                    card.y + card.h - 35.0,
                    15.0,
                    LIGHTGRAY,
                );
                draw_button(character_edit_rect(card), "Edit", false);
                draw_button(character_delete_rect(card), "Delete", false);
            } else {
                draw_text_centered("+", card.x + card.w * 0.5, card.y + 105.0, 58.0, WHITE);
                draw_text_centered(
                    "Create Character",
                    card.x + card.w * 0.5,
                    card.y + 155.0,
                    19.0,
                    WHITE,
                );
            }
        }
    }

    fn draw_creator(&self) {
        draw_title(if self.creator.editing.is_some() {
            "EDIT CHARACTER"
        } else {
            "CREATE CHARACTER"
        });
        let layout = creator_layout();
        draw_panel(layout.preview_panel, true);
        draw_panel(layout.form_panel, false);
        draw_section_panel(layout.identity_panel, "IDENTITY");
        draw_section_panel(layout.appearance_panel, "APPEARANCE");
        draw_section_panel(layout.clothing_panel, "CLOTHING & ACCESSORIES");

        draw_character_preview(
            layout.preview_panel,
            &self.creator.appearance,
            self.preview_layers.as_ref(),
        );

        draw_text(
            "Name",
            layout.identity_panel.x + 14.0,
            layout.identity_panel.y + 66.0,
            16.0,
            Color::from_rgba(225, 216, 191, 255),
        );
        let name_rect = creator_name_rect();
        draw_rectangle(
            name_rect.x,
            name_rect.y,
            name_rect.w,
            name_rect.h,
            Color::from_rgba(18, 30, 31, 255),
        );
        draw_rectangle_lines(
            name_rect.x,
            name_rect.y,
            name_rect.w,
            name_rect.h,
            if self.creator.name_focused { 3.0 } else { 1.0 },
            if self.creator.name_focused {
                Color::from_rgba(221, 181, 106, 255)
            } else {
                Color::from_rgba(126, 88, 52, 255)
            },
        );
        draw_text(
            &self.creator.name,
            name_rect.x + 10.0,
            name_rect.y + 25.0,
            19.0,
            Color::from_rgba(250, 239, 211, 255),
        );
        if self.creator.name_focused && ((get_time() * 2.0) as i64 % 2 == 0) {
            let width = measure_text(&self.creator.name, None, 19, 1.0).width;
            draw_line(
                name_rect.x + 10.0 + width + 2.0,
                name_rect.y + 7.0,
                name_rect.x + 10.0 + width + 2.0,
                name_rect.y + 28.0,
                2.0,
                WHITE,
            );
        }

        let option_labels = [
            format!("Body: {}", self.creator.selection.body.label()),
            format!("Hair: {}", self.creator.selection.hair.label()),
            format!("Eyebrows: {}", self.creator.selection.eyebrows.label()),
            format!(
                "Facial hair: {}",
                self.creator.selection.facial_hair.label()
            ),
            format!("Torso: {}", self.creator.selection.torso.label()),
            format!("Legs: {}", self.creator.selection.legs.label()),
            format!("Feet: {}", self.creator.selection.footwear.label()),
            format!("Headwear: {}", self.creator.selection.headwear.label()),
        ];
        for (row, label) in option_labels.iter().enumerate() {
            draw_button(creator_option_rect(row), label, false);
        }

        draw_color_selector(0, "Skin", SKIN_PALETTES[self.creator.selection.skin_index]);
        draw_color_selector(1, "Eyes", EYE_PALETTES[self.creator.selection.eye_index]);
        draw_color_selector(
            5,
            "Hair color",
            HAIR_PALETTES[self.creator.selection.hair_index],
        );
        draw_color_selector(
            2,
            "Torso color",
            SHIRT_PALETTES[self.creator.selection.shirt_index],
        );
        draw_color_selector(
            3,
            "Leg color",
            BOTTOM_PALETTES[self.creator.selection.bottom_index],
        );
        draw_color_selector(
            4,
            "Foot color",
            FOOTWEAR_PALETTES[self.creator.selection.footwear_index],
        );

        draw_text_centered(
            "Starter outfit choices only. Clothing, armor, and accessories unlock through gameplay.",
            layout.form_panel.x + layout.form_panel.w * 0.5,
            layout.form_panel.y + layout.form_panel.h - 14.0,
            13.0,
            Color::from_rgba(175, 168, 151, 255),
        );
        draw_button(creator_cancel_rect(), "BACK", false);
        draw_button(creator_confirm_rect(), "SAVE CHARACTER", true);
    }

    fn draw_world_list(&self) {
        draw_title(match self.intent {
            FrontendIntent::NewGame => "CREATE OR CHOOSE A WORLD",
            FrontendIntent::LoadGame => "CHOOSE A WORLD",
        });
        let selected = self.selected_character.as_ref().and_then(|id| {
            self.profiles
                .iter()
                .find(|profile| &profile.character_id == id)
        });
        if let Some(profile) = selected {
            draw_text_centered(
                &format!("Playing as {}", profile.display_name),
                screen_width() * 0.5,
                118.0,
                21.0,
                WHITE,
            );
        }
        let start = self.world_page * 3;
        for local_index in 0..3 {
            let card = world_card_rect(local_index);
            draw_panel(card, false);
            if let Some(summary) = self.worlds.get(start + local_index) {
                let label = summary
                    .metadata
                    .as_ref()
                    .map(|value| value.display_name.as_str())
                    .unwrap_or(&summary.world_id.0);
                draw_text(label, card.x + 18.0, card.y + 34.0, 22.0, WHITE);
                if let Some(metadata) = &summary.metadata {
                    draw_text(
                        &format!("Seed {}", metadata.world_seed),
                        card.x + 18.0,
                        card.y + 66.0,
                        17.0,
                        LIGHTGRAY,
                    );
                    draw_button(world_play_rect(card), "Play", true);
                    draw_button(world_delete_rect(card), "Delete", false);
                } else {
                    draw_text(
                        "World metadata error",
                        card.x + 18.0,
                        card.y + 66.0,
                        17.0,
                        LIGHTGRAY,
                    );
                }
                draw_button(world_folder_rect(card), "Folder", false);
            } else if matches!(self.intent, FrontendIntent::NewGame) {
                draw_text(
                    "New unlimited world",
                    card.x + 18.0,
                    card.y + 66.0,
                    17.0,
                    LIGHTGRAY,
                );
                draw_button(world_create_rect(card), "Create World", true);
            } else {
                draw_text("No world", card.x + 18.0, card.y + 66.0, 17.0, LIGHTGRAY);
            }
        }
        draw_text_centered(
            &format!(
                "{} worlds • page {} • Page Up/Down to browse",
                self.worlds.len(),
                self.world_page + 1
            ),
            screen_width() * 0.5,
            screen_height() - 62.0,
            16.0,
            LIGHTGRAY,
        );
    }
}

fn default_appearance() -> CharacterAppearance {
    StarterCreatorSelection::default().appearance()
}

const FRONTEND_MUSIC_VOLUME: f32 = 0.40;

impl ClientFrontend {
    pub(crate) fn start_frontend_music(&mut self) {
        if self.frontend_music_playing {
            return;
        }
        let Some(sound) = self.frontend_music.as_ref() else {
            return;
        };
        play_sound(
            sound,
            PlaySoundParams {
                looped: true,
                volume: FRONTEND_MUSIC_VOLUME,
            },
        );
        self.frontend_music_playing = true;
    }

    pub(crate) fn stop_frontend_music(&mut self) {
        if !self.frontend_music_playing {
            return;
        }
        if let Some(sound) = self.frontend_music.as_ref() {
            stop_sound(sound);
        }
        self.frontend_music_playing = false;
    }
}
