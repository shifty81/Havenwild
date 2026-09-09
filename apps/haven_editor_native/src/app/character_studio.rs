use super::render_helpers::*;
use super::character_studio_layout::*;
use super::*;
use haven_assets::universal_lpc_animation::{
    animation_spec, custom_animation_spec, frame_for_progress, ULPC_DIRECTION_ORDER,
};
use haven_assets::universal_lpc_character_builder::UniversalLpcCharacterBuilderCatalog;
use haven_assets::universal_lpc_character_authority::{
    UniversalLpcCharacterAuthority, UniversalLpcCharacterRecord,
    DEFAULT_UNIVERSAL_LPC_AUTHORITY_PATH,
};
use haven_assets::universal_lpc_character_recipe::{
    universal_lpc_body_type_for_identity, universal_lpc_foundation_head_item_id,
    universal_lpc_foundation_head_kind, UniversalLpcCharacterRecipe, UniversalLpcSelection,
    UNIVERSAL_LPC_CHARACTER_BUILDER_CATEGORIES, UNIVERSAL_LPC_FOUNDATION_BODY_ITEM_ID,
    UNIVERSAL_LPC_REQUIRED_FOUNDATION_SLOTS,
};
use haven_assets::universal_lpc_resolver::UniversalLpcCharacterResolver;
use haven_assets::universal_lpc_character_presentation::CharacterPresentationIssue;
use haven_assets::universal_lpc_npc_generation::UniversalLpcNpcGenerationProfile;
use haven_assets::universal_lpc_sheet_definition::DEFAULT_ULPC_SOURCE_ROOT;
use serde::{Deserialize, Serialize};
use std::{collections::HashSet, fs};

#[path = "character_studio_runtime_ext.rs"]
mod runtime_ext;
pub(crate) use runtime_ext::RuntimeCharacterAnimationSource;

const CHARACTER_SOURCE_CELL: u32 = 64;
const CHARACTER_CATALOG_SEARCH_PLACEHOLDER: &str = "Search character options...";
const CHARACTER_PREVIEW_FPS: f64 = 8.0;
const CHARACTER_STUDIO_DRAFT_SCHEMA: &str = "havenwild.character_studio.draft.v1";
const CHARACTER_STUDIO_DRAFT_PATH: &str = "WORKSPACE/character_studio/draft_character_recipe_v1.json";
const CHARACTER_STUDIO_PRESET_SCHEMA: &str = "havenwild.character_authoring_preset.v1";
const CHARACTER_STUDIO_PRESET_DIR: &str = "content/characters/authoring_presets";
const CHARACTER_DIRECTIONS: [&str; 4] = ["South", "West", "North", "East"];
const CHARACTER_ACTIONS: [(&str, &str); 30] = [
    ("idle", "Idle"),
    ("walk", "Walk"),
    ("run", "Run"),
    ("jump", "Jump"),
    ("sit", "Sit"),
    ("emote", "Emote"),
    ("climb", "Climb"),
    ("hurt", "Hurt"),
    ("watering", "Watering"),
    ("spellcast", "Spellcast"),
    ("thrust", "Thrust"),
    ("slash", "Slash"),
    ("shoot", "Shoot"),
    ("combat", "Combat Idle"),
    ("1h_slash", "1H Slash"),
    ("1h_backslash", "1H Backslash"),
    ("1h_halfslash", "1H Halfslash"),
    ("tool_axe", "Tool: Axe/Pickaxe"),
    ("tool_hammer", "Tool: Hammer"),
    ("tool_rod", "Tool: Fishing Rod"),
    ("tool_whip", "Tool: Whip"),
    ("slash_128", "Oversize Slash 128"),
    ("backslash_128", "Oversize Backslash 128"),
    ("halfslash_128", "Oversize Halfslash 128"),
    ("walk_128", "Oversize Walk 128"),
    ("thrust_128", "Oversize Thrust 128"),
    ("thrust_oversize", "Oversize Thrust 192"),
    ("slash_oversize", "Oversize Slash 192"),
    ("slash_reverse_oversize", "Oversize Reverse Slash 192"),
    ("wheelchair", "Wheelchair"),
];
const SEX_FILTERS: [CharacterSexFilter; 2] = [CharacterSexFilter::Male, CharacterSexFilter::Female];
const AGE_FILTERS: [CharacterAgeFilter; 4] = [
    CharacterAgeFilter::Child,
    CharacterAgeFilter::Teen,
    CharacterAgeFilter::Adult,
    CharacterAgeFilter::Elder,
];


#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
struct CharacterRecipeDraftLayer {
    slot: String,
    source: String,
    #[serde(default)]
    item_id: Option<String>,
    #[serde(default)]
    variant: Option<String>,
    #[serde(default)]
    selection_group: Option<String>,
    #[serde(default)]
    selected_license: Option<String>,
    #[serde(default)]
    share_alike_required: bool,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
struct CharacterRecipeDraft {
    schema: String,
    mode: String,
    sex: String,
    age: String,
    #[serde(default = "default_character_template")]
    template: String,
    #[serde(default = "default_character_direction")]
    direction: String,
    #[serde(default = "default_character_action")]
    action: String,
    #[serde(default)]
    palette_variant: usize,
    #[serde(default)]
    layers: Vec<CharacterRecipeDraftLayer>,
}

fn default_character_template() -> String { "player".to_string() }
fn default_character_direction() -> String { CHARACTER_DIRECTIONS[0].to_string() }
fn default_character_action() -> String { CHARACTER_ACTIONS[0].0.to_string() }

impl Default for CharacterRecipeDraft {
    fn default() -> Self {
        Self {
            schema: CHARACTER_STUDIO_DRAFT_SCHEMA.to_string(),
            mode: CharacterStudioMode::Player.label().to_string(),
            sex: CharacterSexFilter::Male.label().to_string(),
            age: CharacterAgeFilter::Adult.label().to_string(),
            template: default_character_template(),
            direction: default_character_direction(),
            action: default_character_action(),
            palette_variant: 0,
            layers: Vec::new(),
        }
    }
}


#[cfg(test)]
fn standard_action_source_name(action: &str) -> &str {
    match action {
        "combat" => "combat_idle",
        "1h_slash" | "1h_backslash" => "backslash",
        "1h_halfslash" => "halfslash",
        "watering" => "thrust",
        value => value,
    }
}

#[cfg(test)]
fn standard_action_sibling_path(original: &std::path::Path, action: &str) -> std::path::PathBuf {
    let target_folder = standard_action_source_name(action);
    let known_animation_folders = [
        "spellcast", "thrust", "walk", "slash", "shoot", "hurt", "climb",
        "idle", "jump", "sit", "emote", "run", "combat_idle", "backslash", "halfslash",
    ];
    if let (Some(parent), Some(file_name)) = (original.parent(), original.file_name()) {
        let parent_name = parent.file_name().and_then(|value| value.to_str()).unwrap_or("");
        if known_animation_folders.iter().any(|candidate| *candidate == parent_name) {
            if let Some(base) = parent.parent() {
                return base.join(target_folder).join(file_name);
            }
        }
        // Compatibility with older flat category/item/animation.png layouts.
        return parent.join(format!("{target_folder}.png"));
    }
    original.to_path_buf()
}

fn character_direction_row(direction_index: usize, direction_rows: usize) -> usize {
    if direction_rows <= 1 {
        return 0;
    }
    let direction = CHARACTER_DIRECTIONS[direction_index % CHARACTER_DIRECTIONS.len()].to_ascii_lowercase();
    ULPC_DIRECTION_ORDER
        .iter()
        .position(|candidate| *candidate == direction)
        .unwrap_or(0)
        .min(direction_rows.saturating_sub(1))
}

#[cfg(test)]
fn character_animation_source_rect(
    width: u32,
    height: u32,
    action: &str,
    direction_index: usize,
    progress: f32,
) -> Rect {
    if width < CHARACTER_SOURCE_CELL || height < CHARACTER_SOURCE_CELL {
        return Rect::new(0.0, 0.0, width as f32, height as f32);
    }
    let columns = (width / CHARACTER_SOURCE_CELL).max(1) as usize;
    let rows = (height / CHARACTER_SOURCE_CELL).max(1) as usize;
    let spec = animation_spec(action);
    let frame = frame_for_progress(action, progress).min(columns.saturating_sub(1));
    let direction_rows = spec.map(|spec| spec.direction_rows).unwrap_or(rows).min(rows).max(1);
    let row = character_direction_row(direction_index, direction_rows).min(rows.saturating_sub(1));
    Rect::new(
        (frame as u32 * CHARACTER_SOURCE_CELL) as f32,
        (row as u32 * CHARACTER_SOURCE_CELL) as f32,
        CHARACTER_SOURCE_CELL as f32,
        CHARACTER_SOURCE_CELL as f32,
    )
}

fn preview_progress_at_time(action: &str, started_at: f64, now: f64) -> f32 {
    let cycle_len = animation_spec(action).map(|spec| spec.cycle.len())
        .or_else(|| custom_animation_spec(action).map(|_| 8))
        .unwrap_or(1).max(1) as f64;
    let elapsed_frames = ((now - started_at).max(0.0) * CHARACTER_PREVIEW_FPS) % cycle_len;
    (elapsed_frames / cycle_len) as f32
}

fn preview_started_at_for_progress(action: &str, progress: f32) -> f64 {
    let cycle_len = animation_spec(action).map(|spec| spec.cycle.len())
        .or_else(|| custom_animation_spec(action).map(|_| 8))
        .unwrap_or(1).max(1) as f64;
    get_time() - progress.clamp(0.0, 0.999_999) as f64 * cycle_len / CHARACTER_PREVIEW_FPS
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum CharacterStudioMode {
    Player,
    Npc,
}

impl CharacterStudioMode {
    fn label(self) -> &'static str {
        match self {
            Self::Player => "Player",
            Self::Npc => "NPC",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum CharacterSexFilter {
    Male,
    Female,
}

impl CharacterSexFilter {
    fn label(self) -> &'static str {
        match self {
            Self::Male => "Male",
            Self::Female => "Female",
        }
    }

    fn tag(self) -> &'static str {
        match self {
            Self::Male => "male",
            Self::Female => "female",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum CharacterAgeFilter {
    Child,
    Teen,
    Adult,
    Elder,
}

impl CharacterAgeFilter {
    fn label(self) -> &'static str {
        match self {
            Self::Child => "Child",
            Self::Teen => "Teen",
            Self::Adult => "Adult",
            Self::Elder => "Elder",
        }
    }

    fn tag(self) -> &'static str {
        match self {
            Self::Child => "child",
            Self::Teen => "teen",
            Self::Adult => "adult",
            Self::Elder => "elderly",
        }
    }
}

struct CharacterAssembledPreviewLayer {
    texture: Texture2D,
    slot: String,
    source_animation: String,
    frame_size: u32,
    z_pos: i32,
}

pub(crate) struct CharacterStudioState {
    authority: Option<UniversalLpcCharacterAuthority>,
    builder_catalog: Option<UniversalLpcCharacterBuilderCatalog>,
    load_error: Option<String>,
    pub mode: CharacterStudioMode,
    pub sex: CharacterSexFilter,
    pub age: CharacterAgeFilter,
    pub include_share_alike: bool,
    pub query: String,
    catalog_section: CharacterCatalogSection,
    slot_filter: usize,
    filtered_indices: Vec<usize>,
    selected: usize,
    list_offset: usize,
    selected_variant_index: usize,
    preview_texture: Option<Texture2D>,
    preview_source: Option<String>,
    preview_source_rect: Option<Rect>,
    preview_error: Option<String>,
    recipe: CharacterRecipeDraft,
    recipe_message: Option<String>,
    direction_index: usize,
    action_index: usize,
    palette_variant: usize,
    selected_recipe_layer: usize,
    layer_view_mode: runtime_ext::CharacterLayerViewMode,
    selected_equipment_slot: usize,
    assembled_preview_layers: Vec<CharacterAssembledPreviewLayer>,
    assembled_preview_error: Option<String>,
    presentation_issues: Vec<CharacterPresentationIssue>,
    preview_hidden_items: HashSet<String>,
    advanced_open: bool,
    category_menu_open: bool,
    preview_playing: bool,
    preview_animation_started_at: f64,
    preview_paused_progress: f32,
    locked_slots: HashSet<String>,
    random_seed: u64,
    npc_profile_index: usize,
    npc_generation_seed: u64,
    npc_profile_editor_open: bool,
    npc_profile_draft: Option<UniversalLpcNpcGenerationProfile>,
    saved_recipe_fingerprint: String,
}

impl CharacterStudioState {
    pub(crate) fn new() -> Self {
        let mut state = Self {
            authority: None,
            builder_catalog: None,
            load_error: None,
            mode: CharacterStudioMode::Player,
            sex: CharacterSexFilter::Male,
            age: CharacterAgeFilter::Adult,
            include_share_alike: false,
            query: String::new(),
            catalog_section: CharacterCatalogSection::Create,
            slot_filter: 0,
            filtered_indices: Vec::new(),
            selected: 0,
            list_offset: 0,
            selected_variant_index: 0,
            preview_texture: None,
            preview_source: None,
            preview_source_rect: None,
            preview_error: None,
            recipe: CharacterRecipeDraft::default(),
            recipe_message: None,
            direction_index: 0,
            action_index: 0,
            palette_variant: 0,
            selected_recipe_layer: 0,
            layer_view_mode: runtime_ext::CharacterLayerViewMode::Composition,
            selected_equipment_slot: 0,
            assembled_preview_layers: Vec::new(),
            assembled_preview_error: None,
            presentation_issues: Vec::new(),
            preview_hidden_items: HashSet::new(),
            advanced_open: false,
            category_menu_open: false,
            preview_playing: true,
            preview_animation_started_at: get_time(),
            preview_paused_progress: 0.0,
            locked_slots: HashSet::new(),
            random_seed: 0x4841_5645_4E57_494C,
            npc_profile_index: 0,
            npc_generation_seed: 0x4E50_435F_4841_5645,
            npc_profile_editor_open: false,
            npc_profile_draft: None,
            saved_recipe_fingerprint: String::new(),
        };
        state.reload();
        state.mark_recipe_saved();
        state
    }

    pub(crate) fn reload(&mut self) {
        match UniversalLpcCharacterAuthority::load_default() {
            Ok(authority) => {
                self.authority = Some(authority);
                self.load_error = None;
            }
            Err(error) => {
                self.authority = None;
                self.load_error = Some(error);
            }
        }
        let source_root = haven_assets::asset_intake::repo_root_dir().join(DEFAULT_ULPC_SOURCE_ROOT);
        match UniversalLpcCharacterBuilderCatalog::load_source_root(&source_root) {
            Ok(catalog) => self.builder_catalog = Some(catalog),
            Err(error) => {
                self.builder_catalog = None;
                if self.load_error.is_none() { self.load_error = Some(error); }
            }
        }
        self.preview_texture = None;
        self.preview_source = None;
        self.preview_source_rect = None;
        self.preview_error = None;
        self.assembled_preview_layers.clear();
        self.assembled_preview_error = None;
        self.presentation_issues.clear();
        self.rebuild_filter();
        self.ensure_required_foundation();
        self.sync_assembled_preview();
    }

    pub(crate) fn rebuild_filter(&mut self) {
        self.filtered_indices.clear();
        let Some(builder) = self.builder_catalog.as_ref() else {
            self.selected = 0;
            self.list_offset = 0;
            return;
        };
        let body = self.current_body_type();
        let query = self.query.trim().to_ascii_lowercase();
        let category = self.slot_label();
        for (index, option) in builder.options.iter().enumerate() {
            if !option.is_selectable(self.include_share_alike) { continue; }
            if category == "all" {
                if !self.catalog_section.contains(&option.category) { continue; }
            } else if option.category != category {
                continue;
            }
            if !option.supports_body(&builder.definitions, body) { continue; }
            if self.mode == CharacterStudioMode::Player
                && ["wings", "tail"].iter().any(|tag| option.tags.contains(*tag))
            {
                continue;
            }
            if !query.is_empty()
                && !option.display_name.to_ascii_lowercase().contains(&query)
                && !option.item_id.to_ascii_lowercase().contains(&query)
                && !option.tags.iter().any(|tag| tag.contains(&query))
            {
                continue;
            }
            self.filtered_indices.push(index);
        }
        self.selected = self.selected.min(self.filtered_indices.len().saturating_sub(1));
        self.selected_variant_index = self.selected_variant_index.min(
            self.selected_option().map(|option| option.variants.len().saturating_sub(1)).unwrap_or(0)
        );
        self.list_offset = self.list_offset
            .min(self.filtered_indices.len().saturating_sub(CHARACTER_MAX_ROWS));
    }

    pub(crate) fn selected_option(&self) -> Option<&haven_assets::universal_lpc_character_builder::UniversalLpcBuilderOption> {
        let builder = self.builder_catalog.as_ref()?;
        let option_index = *self.filtered_indices.get(self.selected)?;
        builder.options.get(option_index)
    }

    pub(crate) fn selected_record(&self) -> Option<&UniversalLpcCharacterRecord> {
        let option = self.selected_option()?;
        let builder = self.builder_catalog.as_ref()?;
        let definition = builder.definitions.find(&option.item_id)?;
        let body = self.current_body_type();
        let prefixes = definition.definition.layers().iter()
            .filter_map(|(_, layer)| layer.path_for_body(body))
            .map(|value| value.to_ascii_lowercase().replace('\\', "/"))
            .collect::<Vec<_>>();
        let authority = self.authority.as_ref()?;
        authority.records.iter().find(|record| {
            let source = record.source.to_ascii_lowercase().replace('\\', "/");
            prefixes.iter().any(|prefix| source.starts_with(prefix))
        })
    }

    pub(crate) fn authority(&self) -> Option<&UniversalLpcCharacterAuthority> { self.authority.as_ref() }

    pub(crate) fn load_error(&self) -> Option<&str> {
        self.load_error.as_deref()
    }

    pub(crate) fn filtered_count(&self) -> usize {
        self.filtered_indices.len()
    }

    pub(crate) fn selected_visible_index(&self) -> usize {
        self.selected
    }

    pub(crate) fn set_selected_with_rows(&mut self, index: usize, visible_rows: usize) {
        if self.filtered_indices.is_empty() {
            self.selected = 0;
            self.list_offset = 0;
            return;
        }
        let visible_rows = visible_rows.max(1);
        let next_selected = index.min(self.filtered_indices.len() - 1);
        if next_selected != self.selected { self.selected_variant_index = 0; }
        self.selected = next_selected;
        if self.selected < self.list_offset {
            self.list_offset = self.selected;
        } else if self.selected >= self.list_offset + visible_rows {
            self.list_offset = self.selected + 1 - visible_rows;
        }
        self.list_offset = self
            .list_offset
            .min(self.filtered_indices.len().saturating_sub(visible_rows));
    }

    pub(crate) fn cycle_selected_with_rows(&mut self, delta: i32, visible_rows: usize) {
        let next = cycle_index(self.selected, self.filtered_indices.len(), delta);
        self.set_selected_with_rows(next, visible_rows);
    }

    pub(crate) fn page_with_rows(&mut self, delta: i32, visible_rows: usize) {
        let visible_rows = visible_rows.max(1);
        if delta < 0 {
            self.list_offset = self.list_offset.saturating_sub(visible_rows);
        } else {
            self.list_offset = (self.list_offset + visible_rows)
                .min(self.filtered_indices.len().saturating_sub(visible_rows));
        }
        self.set_selected_with_rows(self.list_offset, visible_rows);
    }

    pub(crate) fn sync_selected_preview(&mut self) {
        let Some(builder) = self.builder_catalog.as_ref() else {
            self.preview_texture = None;
            self.preview_source = None;
            self.preview_source_rect = None;
            return;
        };
        let Some(option) = self.selected_option().cloned() else {
            self.preview_texture = None;
            self.preview_source = None;
            self.preview_source_rect = None;
            return;
        };
        let Some(authority) = self.authority.as_ref() else { return; };
        let mut recipe = UniversalLpcCharacterRecipe::new(authority.source_commit.clone(), self.current_body_type());
        recipe.apply_identity_foundations(self.sex.label(), self.age.label());
        if !matches!(option.category.as_str(), "body" | "head") {
            let _ = builder.select_option(&mut recipe, &option.item_id, self.selected_variant().map(str::to_string));
        } else if option.category == "body" {
            recipe.selections.insert("body".into(), UniversalLpcSelection {
                item_id: option.item_id.clone(), display_name: option.display_name.clone(), locked: true, ..Default::default()
            });
        } else {
            recipe.selections.insert("head".into(), UniversalLpcSelection {
                item_id: option.item_id.clone(), display_name: option.display_name.clone(), locked: true, ..Default::default()
            });
        }
        let source_root = haven_assets::asset_intake::repo_root_dir().join(DEFAULT_ULPC_SOURCE_ROOT);
        let resolver = UniversalLpcCharacterResolver::with_source_root(&source_root, &builder.definitions);
        let resolved = match resolver.resolve(&recipe, self.action_id()) {
            Ok(value) => value,
            Err(error) => { self.preview_error = Some(error); return; }
        };
        let Some(layer) = resolved.layers.iter().rev().find(|layer| layer.item_id == option.item_id) else {
            self.preview_texture = None;
            self.preview_source_rect = None;
            self.preview_error = Some(format!("{} has no compatible {} preview", option.display_name, self.action_label()));
            return;
        };
        let path = &layer.source_path;
        let source = path.to_string_lossy().to_string();
        if self.preview_source.as_deref() == Some(source.as_str()) { return; }
        self.preview_texture = None;
        self.preview_source_rect = None;
        self.preview_error = None;
        self.preview_source = Some(source);
        match image::open(path) {
            Ok(image) => {
                let image = image.to_rgba8();
                if image.width() > u16::MAX as u32 || image.height() > u16::MAX as u32 {
                    self.preview_error = Some(format!("{} exceeds the editor texture limit", path.display()));
                    return;
                }
                let texture = Texture2D::from_rgba8(image.width() as u16, image.height() as u16, image.as_raw());
                texture.set_filter(FilterMode::Nearest);
                let temp = CharacterAssembledPreviewLayer {
                    texture: texture.clone(), slot: layer.item_id.clone(), source_animation: layer.source_animation.clone(),
                    frame_size: layer.frame_size, z_pos: layer.z_pos,
                };
                self.preview_source_rect = Some(Self::assembled_preview_source_rect(&temp, self.direction_index, 0.0));
                self.preview_texture = Some(texture);
            }
            Err(error) => self.preview_error = Some(format!("Could not load {}: {error}", path.display())),
        }
    }

    fn identity_body_source_fragment(&self) -> String {
        let body = universal_lpc_body_type_for_identity(self.sex.label(), self.age.label());
        format!("body/bodies/{}/", body.as_str())
    }

    fn identity_head_source_fragment(&self) -> String {
        format!("head/heads/human/{}/", universal_lpc_foundation_head_kind(self.sex.label(), self.age.label()))
    }

    fn preferred_foundation_record(&self, slot: &str) -> Option<UniversalLpcCharacterRecord> {
        let authority = self.authority.as_ref()?;
        let fragment = if slot == "body" {
            self.identity_body_source_fragment()
        } else {
            self.identity_head_source_fragment()
        };
        authority.records.iter()
            .filter(|record| record.is_selectable(self.include_share_alike))
            .filter(|record| record.source.to_ascii_lowercase().starts_with(&fragment))
            .min_by_key(|record| if record.source.to_ascii_lowercase().ends_with("/idle.png") { 0 } else { 1 })
            .cloned()
    }

    fn current_body_type(&self) -> haven_assets::universal_lpc_animation::UniversalLpcBodyType {
        universal_lpc_body_type_for_identity(self.sex.label(), self.age.label())
    }



    pub(crate) fn load_runtime_typed_recipe(
        &mut self,
        typed: &UniversalLpcCharacterRecipe,
        action_id: &str,
        direction: &str,
    ) -> Result<String, String> {
        let builder = self
            .builder_catalog
            .as_ref()
            .ok_or_else(|| "Universal LPC sheet-definition catalog is unavailable".to_string())?;
        let head_id = typed
            .selections
            .get("head")
            .map(|selection| selection.item_id.to_ascii_lowercase())
            .unwrap_or_default();
        self.sex = if typed.body_type.as_str() == "female" || head_id.contains("female") {
            CharacterSexFilter::Female
        } else {
            CharacterSexFilter::Male
        };
        self.age = match typed.identity.age_group.to_ascii_lowercase().as_str() {
            "child" => CharacterAgeFilter::Child,
            "teen" => CharacterAgeFilter::Teen,
            "elder" | "elderly" => CharacterAgeFilter::Elder,
            _ if typed.body_type.as_str() == "child" => CharacterAgeFilter::Child,
            _ if typed.body_type.as_str() == "teen" => CharacterAgeFilter::Teen,
            _ => CharacterAgeFilter::Adult,
        };
        self.mode = if typed.identity.role.eq_ignore_ascii_case("npc") {
            CharacterStudioMode::Npc
        } else {
            CharacterStudioMode::Player
        };

        let layer_from_selection = |group: &str, selection: &UniversalLpcSelection| {
            let option = builder.option(&selection.item_id);
            CharacterRecipeDraftLayer {
                slot: option
                    .map(|value| value.category.clone())
                    .unwrap_or_else(|| group.to_string()),
                source: if !selection.definition_source.trim().is_empty() {
                    selection.definition_source.clone()
                } else {
                    option
                        .map(|value| value.definition_path.to_string_lossy().replace('\\', "/"))
                        .unwrap_or_else(|| selection.item_id.clone())
                },
                item_id: Some(selection.item_id.clone()),
                variant: selection.variant.clone(),
                selection_group: Some(
                    option
                        .map(|value| value.selection_group.clone())
                        .unwrap_or_else(|| group.to_string()),
                ),
                selected_license: selection.selected_license.clone(),
                share_alike_required: selection.share_alike_required,
            }
        };

        let mut layers = Vec::new();
        for (group, selection) in &typed.selections {
            if matches!(group.as_str(), "body" | "body/base" | "head") {
                continue;
            }
            layers.push(layer_from_selection(group, selection));
        }
        if let Some(selection) = typed.equipment.main_hand.as_ref() {
            layers.push(layer_from_selection("main_hand", selection));
        }
        if let Some(selection) = typed.equipment.off_hand.as_ref() {
            layers.push(layer_from_selection("off_hand", selection));
        }
        for (group, selection) in &typed.equipment.equipped {
            layers.push(layer_from_selection(group, selection));
        }

        self.recipe = CharacterRecipeDraft {
            schema: CHARACTER_STUDIO_DRAFT_SCHEMA.to_string(),
            mode: self.mode.label().to_string(),
            sex: self.sex.label().to_string(),
            age: self.age.label().to_string(),
            template: if self.mode == CharacterStudioMode::Npc { "npc" } else { "player" }.to_string(),
            direction: direction.to_string(),
            action: action_id.to_string(),
            palette_variant: self.palette_variant,
            layers,
        };
        self.ensure_required_foundation();
        self.direction_index = CHARACTER_DIRECTIONS
            .iter()
            .position(|value| value.eq_ignore_ascii_case(direction))
            .unwrap_or(0);
        self.action_index = CHARACTER_ACTIONS
            .iter()
            .position(|(id, label)| id.eq_ignore_ascii_case(action_id) || label.eq_ignore_ascii_case(action_id))
            .unwrap_or(0);
        self.selected_recipe_layer = self.recipe.layers.len().saturating_sub(1);
        self.restart_preview_animation();
        self.sync_recipe_identity();
        self.sync_assembled_preview();
        Ok(format!(
            "Loaded runtime character {} · {} · {}",
            typed.identity.character_id.as_deref().unwrap_or("character"),
            self.direction_label(),
            self.action_label()
        ))
    }

    pub(crate) fn apply_runtime_animation_context(
        &mut self,
        action_id: &str,
        direction: &str,
    ) {
        let before = (self.direction_index, self.action_index);
        if let Some(index) = CHARACTER_DIRECTIONS
            .iter()
            .position(|value| value.eq_ignore_ascii_case(direction))
        {
            self.direction_index = index;
        }
        if let Some(index) = CHARACTER_ACTIONS
            .iter()
            .position(|(id, label)| id.eq_ignore_ascii_case(action_id) || label.eq_ignore_ascii_case(action_id))
        {
            self.action_index = index;
        }
        if before != (self.direction_index, self.action_index) {
            self.sync_recipe_identity();
            self.restart_preview_animation();
            self.sync_assembled_preview();
        }
    }

    fn typed_recipe_from_draft(&self) -> Result<UniversalLpcCharacterRecipe, String> {
        let authority = self.authority.as_ref()
            .ok_or_else(|| "Universal LPC authority is unavailable".to_string())?;
        let builder = self.builder_catalog.as_ref()
            .ok_or_else(|| "Universal LPC sheet-definition catalog is unavailable".to_string())?;
        let mut recipe = UniversalLpcCharacterRecipe::new(authority.source_commit.clone(), self.current_body_type());
        recipe.apply_identity_foundations(self.sex.label(), self.age.label());
        recipe.identity.role = if self.mode == CharacterStudioMode::Player { "player" } else { "npc" }.to_string();
        for layer in &self.recipe.layers {
            if matches!(layer.slot.as_str(), "body" | "head") { continue; }
            let item_id = layer.item_id.clone().or_else(|| {
                builder.definition_for_source(&layer.source, recipe.body_type).map(|record| record.item_id.clone())
            });
            let Some(item_id) = item_id else { continue; };
            let option = builder.option(&item_id);
            let mut selection = if option.is_some() {
                builder.selection_for_option(&item_id, layer.variant.clone())?
            } else {
                UniversalLpcSelection {
                    item_id: item_id.clone(),
                    display_name: item_id.clone(),
                    variant: layer.variant.clone(),
                    ..Default::default()
                }
            };
            selection.locked = self.locked_slots.contains(&layer.slot);
            if let Some(option) = option {
                if !builder.compatible_option(&recipe, option) { continue; }
                if option.category == "weapon" {
                    recipe.equipment.main_hand = Some(selection);
                } else if option.category == "shield" {
                    recipe.equipment.off_hand = Some(selection);
                } else if matches!(option.category.as_str(), "tools" | "accessory") {
                    recipe.equipment.equipped.insert(option.selection_group.clone(), selection);
                } else {
                    recipe.selections.insert(option.selection_group.clone(), selection);
                }
            } else {
                recipe.selections.insert(layer.selection_group.clone().unwrap_or_else(|| layer.slot.clone()), selection);
            }
        }
        recipe.validate()?;
        Ok(recipe)
    }

    fn ensure_required_foundation(&mut self) {
        let mut replacements = Vec::new();
        for slot in UNIVERSAL_LPC_REQUIRED_FOUNDATION_SLOTS {
            if let Some(record) = self.preferred_foundation_record(slot) {
                replacements.push(CharacterRecipeDraftLayer {
                    slot: slot.to_string(),
                    source: record.source.clone(),
                    item_id: Some(if slot == "body" {
                        UNIVERSAL_LPC_FOUNDATION_BODY_ITEM_ID.to_string()
                    } else {
                        universal_lpc_foundation_head_item_id(self.sex.label(), self.age.label())
                    }),
                    variant: None,
                    selection_group: Some(slot.to_string()),
                    selected_license: record.selected_license.clone(),
                    share_alike_required: record.share_alike_required,
                });
            }
        }
        for replacement in replacements {
            if let Some(existing) = self.recipe.layers.iter_mut().find(|layer| layer.slot == replacement.slot) {
                *existing = replacement;
            } else {
                self.recipe.layers.push(replacement);
            }
        }
    }

    pub(crate) fn set_sex(&mut self, sex: CharacterSexFilter) -> String {
        self.sex = sex;
        self.rebuild_filter();
        self.ensure_required_foundation();
        self.sync_recipe_identity();
        self.sync_assembled_preview();
        format!("Character sex: {}", self.sex.label())
    }

    pub(crate) fn set_age(&mut self, age: CharacterAgeFilter) -> String {
        self.age = age;
        self.rebuild_filter();
        self.ensure_required_foundation();
        self.sync_recipe_identity();
        self.sync_assembled_preview();
        format!("Character age group: {}", self.age.label())
    }

    fn sync_recipe_identity(&mut self) {
        self.recipe.schema = CHARACTER_STUDIO_DRAFT_SCHEMA.to_string();
        self.recipe.mode = self.mode.label().to_string();
        self.recipe.sex = self.sex.label().to_string();
        self.recipe.age = self.age.label().to_string();
        self.recipe.direction = CHARACTER_DIRECTIONS[self.direction_index].to_string();
        self.recipe.action = CHARACTER_ACTIONS[self.action_index].0.to_string();
        self.recipe.palette_variant = self.palette_variant;
    }

    pub(crate) fn assign_selected_to_recipe(&mut self) -> Result<String, String> {
        let option = self.selected_option().cloned()
            .ok_or_else(|| "Select a compatible Universal LPC item first".to_string())?;
        if matches!(option.category.as_str(), "body" | "head") {
            return Err(format!("{} is controlled by Identity and cannot replace the required foundation directly", option.display_name));
        }
        let group = option.selection_group.clone();
        let source = self.selected_record()
            .map(|record| record.source.clone())
            .unwrap_or_else(|| option.definition_path.to_string_lossy().replace('\\', "/"));
        self.sync_recipe_identity();
        let layer = CharacterRecipeDraftLayer {
            slot: option.category.clone(),
            source,
            item_id: Some(option.item_id.clone()),
            variant: self.selected_variant().map(str::to_string),
            selection_group: Some(group.clone()),
            selected_license: option.preferred_license().map(str::to_string),
            share_alike_required: option.share_alike_required(),
        };
        if let Some(existing) = self.recipe.layers.iter_mut().find(|item| {
            item.selection_group.as_deref() == Some(group.as_str())
        }) {
            *existing = layer;
            let message = format!("Replaced {} with {}", option.category, option.display_name);
            self.recipe_message = Some(message.clone());
            self.sync_assembled_preview();
            Ok(message)
        } else {
            self.recipe.layers.push(layer);
            self.selected_recipe_layer = self.recipe.layers.len().saturating_sub(1);
            let message = format!("Added {} to {}", option.display_name, option.category);
            self.recipe_message = Some(message.clone());
            self.sync_assembled_preview();
            Ok(message)
        }
    }

    pub(crate) fn remove_active_recipe_slot(&mut self) -> Result<String, String> {
        let (slot, group) = if self.slot_label() == "all" {
            let option = self.selected_option()
                .ok_or_else(|| "Choose a category or selected item first".to_string())?;
            (option.category.clone(), option.selection_group.clone())
        } else {
            let slot = self.slot_label().to_string();
            let group = self.selected_option()
                .filter(|option| option.category == slot)
                .map(|option| option.selection_group.clone())
                .unwrap_or_else(|| slot.clone());
            (slot, group)
        };
        if UNIVERSAL_LPC_REQUIRED_FOUNDATION_SLOTS.contains(&slot.as_str()) {
            return Err(format!("{slot} is a required character foundation and cannot be removed"));
        }
        let before = self.recipe.layers.len();
        self.recipe.layers.retain(|layer| {
            layer.selection_group.as_deref() != Some(group.as_str()) && layer.slot != slot
        });
        if before == self.recipe.layers.len() {
            return Err(format!("Recipe has no {slot} layer"));
        }
        self.selected_recipe_layer = self.selected_recipe_layer.min(self.recipe.layers.len().saturating_sub(1));
        let message = format!("Removed {slot} recipe layer");
        self.recipe_message = Some(message.clone());
        self.sync_assembled_preview();
        Ok(message)
    }

    pub(crate) fn clear_recipe(&mut self) -> String {
        self.recipe.layers.clear();
        self.selected_recipe_layer = 0;
        self.assembled_preview_layers.clear();
        self.restart_preview_animation();
        self.ensure_required_foundation();
        self.sync_recipe_identity();
        let message = "Cleared Character Studio working recipe".to_string();
        self.recipe_message = Some(message.clone());
        message
    }

    fn recipe_fingerprint(&self) -> String {
        serde_json::to_string(&self.recipe).unwrap_or_else(|_| self.recipe.layers.len().to_string())
    }

    pub(crate) fn dirty(&self) -> bool {
        self.recipe_fingerprint() != self.saved_recipe_fingerprint
    }

    fn mark_recipe_saved(&mut self) {
        self.saved_recipe_fingerprint = self.recipe_fingerprint();
    }

    pub(crate) fn save_recipe_draft(&mut self) -> Result<String, String> {
        self.sync_recipe_identity();
        let root = haven_assets::asset_intake::repo_root_dir();
        let path = root.join(CHARACTER_STUDIO_DRAFT_PATH);
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)
                .map_err(|error| format!("failed to create {}: {error}", parent.display()))?;
        }
        let text = serde_json::to_string_pretty(&self.recipe)
            .map_err(|error| format!("failed to encode Character Studio draft: {error}"))?;
        fs::write(&path, text)
            .map_err(|error| format!("failed to write {}: {error}", path.display()))?;
        let message = format!(
            "Saved Character Studio draft with {} layers",
            self.recipe.layers.len()
        );
        self.recipe_message = Some(message.clone());
        self.mark_recipe_saved();
        Ok(message)
    }

    pub(crate) fn load_recipe_draft(&mut self) -> Result<String, String> {
        let root = haven_assets::asset_intake::repo_root_dir();
        let path = root.join(CHARACTER_STUDIO_DRAFT_PATH);
        let text = fs::read_to_string(&path)
            .map_err(|error| format!("failed to read {}: {error}", path.display()))?;
        let recipe: CharacterRecipeDraft = serde_json::from_str(&text)
            .map_err(|error| format!("failed to parse {}: {error}", path.display()))?;
        if recipe.schema != CHARACTER_STUDIO_DRAFT_SCHEMA {
            return Err(format!("unsupported Character Studio draft schema {}", recipe.schema));
        }
        self.recipe = recipe;
        self.sex = if self.recipe.sex.eq_ignore_ascii_case("female") { CharacterSexFilter::Female } else { CharacterSexFilter::Male };
        self.age = if self.recipe.age.eq_ignore_ascii_case("child") { CharacterAgeFilter::Child }
            else if self.recipe.age.eq_ignore_ascii_case("teen") { CharacterAgeFilter::Teen }
            else if self.recipe.age.eq_ignore_ascii_case("elder") || self.recipe.age.eq_ignore_ascii_case("elderly") { CharacterAgeFilter::Elder }
            else { CharacterAgeFilter::Adult };
        self.ensure_required_foundation();
        self.direction_index = CHARACTER_DIRECTIONS.iter().position(|value| *value == self.recipe.direction).unwrap_or(0);
        self.action_index = CHARACTER_ACTIONS
            .iter()
            .position(|(id, label)| *id == self.recipe.action || *label == self.recipe.action)
            .unwrap_or(0);
        self.palette_variant = self.recipe.palette_variant;
        self.selected_recipe_layer = self.recipe.layers.len().saturating_sub(1);
        self.restart_preview_animation();
        self.sync_assembled_preview();
        let message = format!(
            "Loaded Character Studio draft with {} layers",
            self.recipe.layers.len()
        );
        self.recipe_message = Some(message.clone());
        self.mark_recipe_saved();
        Ok(message)
    }

    pub(crate) fn reset_recipe_template(&mut self, mode: CharacterStudioMode) -> String {
        self.mode = mode;
        self.recipe = CharacterRecipeDraft::default();
        self.recipe.template = match mode {
            CharacterStudioMode::Npc => "npc",
            CharacterStudioMode::Player => "player",
        }.to_string();
        self.direction_index = 0;
        self.action_index = 0;
        self.palette_variant = 0;
        self.selected_recipe_layer = 0;
        self.assembled_preview_layers.clear();
        self.ensure_required_foundation();
        self.sync_recipe_identity();
        self.sync_assembled_preview();
        let message = format!("Started new {} character recipe", mode.label());
        self.recipe_message = Some(message.clone());
        message
    }

    pub(crate) fn cycle_direction(&mut self, delta: i32) -> String {
        self.direction_index = cycle_index(self.direction_index, CHARACTER_DIRECTIONS.len(), delta);
        self.sync_recipe_identity();
        // Direction is presentation state, not merely recipe metadata. The assembled
        // preview reads this row live; only the single-component fallback needs refresh.
        self.preview_source = None;
        self.sync_selected_preview();
        format!("Preview direction: {}", self.direction_label())
    }

    pub(crate) fn cycle_action(&mut self, delta: i32) -> String {
        self.action_index = cycle_index(self.action_index, CHARACTER_ACTIONS.len(), delta);
        self.sync_recipe_identity();
        self.restart_preview_animation();
        // Each standard ULPC action is a sibling source sheet. Switching animation must
        // reload those siblings rather than continuing to display the previous action.
        self.sync_assembled_preview();
        self.preview_source = None;
        self.sync_selected_preview();
        format!("Preview animation: {}", self.action_label())
    }

    pub(crate) fn preview_playing(&self) -> bool { self.preview_playing }

    pub(crate) fn toggle_preview_playback(&mut self) -> String {
        if self.preview_playing {
            self.preview_paused_progress = self.preview_progress();
            self.preview_playing = false;
            format!("Paused {} preview", self.action_label())
        } else {
            self.preview_animation_started_at = preview_started_at_for_progress(
                self.action_id(),
                self.preview_paused_progress,
            );
            self.preview_playing = true;
            format!("Playing {} preview", self.action_label())
        }
    }

    pub(crate) fn restart_preview_animation(&mut self) {
        self.preview_paused_progress = 0.0;
        self.preview_animation_started_at = get_time();
    }

    fn action_id(&self) -> &'static str { CHARACTER_ACTIONS[self.action_index].0 }

    fn preview_progress(&self) -> f32 {
        if !self.preview_playing {
            return self.preview_paused_progress;
        }
        preview_progress_at_time(self.action_id(), self.preview_animation_started_at, get_time())
    }

    pub(crate) fn resolved_runtime_animation_source(
        &self,
        item_id: Option<&str>,
        action_id: &str,
    ) -> Result<(std::path::PathBuf, String), String> {
        let builder = self
            .builder_catalog
            .as_ref()
            .ok_or_else(|| "Universal LPC sheet-definition catalog is unavailable".to_string())?;
        let recipe = self.typed_recipe_from_draft()?;
        let source_root = haven_assets::asset_intake::repo_root_dir().join(DEFAULT_ULPC_SOURCE_ROOT);
        let resolver = UniversalLpcCharacterResolver::with_source_root(
            &source_root,
            &builder.definitions,
        );
        let resolved = resolver.resolve(&recipe, action_id)?;
        let body_item_id = recipe
            .selections
            .get("body")
            .or_else(|| recipe.selections.get("body/base"))
            .map(|selection| selection.item_id.as_str());
        let layer = item_id
            .and_then(|item_id| resolved.layers.iter().find(|layer| layer.item_id == item_id))
            .or_else(|| {
                body_item_id.and_then(|body_item_id| {
                    resolved
                        .layers
                        .iter()
                        .find(|layer| layer.item_id == body_item_id)
                })
            })
            .or_else(|| resolved.layers.first())
            .ok_or_else(|| format!("{action_id} resolved no character animation layers"))?;
        if !layer.source_path.is_file() {
            return Err(format!(
                "resolved animation source is missing: {}",
                layer.source_path.display()
            ));
        }
        Ok((layer.source_path.clone(), layer.source_animation.clone()))
    }

    pub(crate) fn selected_variant(&self) -> Option<&str> {
        let option = self.selected_option()?;
        if option.variants.is_empty() { return None; }
        option.variants.get(self.selected_variant_index % option.variants.len()).map(String::as_str)
    }

    pub(crate) fn selected_variant_label(&self) -> String {
        self.selected_variant().unwrap_or("Default").to_string()
    }

    pub(crate) fn cycle_selected_variant(&mut self, delta: i32) -> String {
        let count = self.selected_option().map(|option| option.variants.len()).unwrap_or(0);
        if count == 0 {
            self.selected_variant_index = 0;
            return "Selected item uses its default variant".to_string();
        }
        self.selected_variant_index = cycle_index(self.selected_variant_index, count, delta);
        self.preview_source = None;
        self.sync_selected_preview();
        format!("Variant: {}", self.selected_variant_label())
    }

    pub(crate) fn cycle_palette_variant(&mut self, delta: i32) -> String {
        self.palette_variant = cycle_index(self.palette_variant, 8, delta);
        self.sync_recipe_identity();
        format!("Character palette variant: {}", self.palette_variant + 1)
    }

    pub(crate) fn direction_label(&self) -> &'static str { CHARACTER_DIRECTIONS[self.direction_index] }
    pub(crate) fn action_label(&self) -> &'static str { CHARACTER_ACTIONS[self.action_index].1 }
    pub(crate) fn preview_playback_label(&self) -> &'static str { if self.preview_playing { "Pause" } else { "Play" } }
    pub(crate) fn palette_variant_label(&self) -> String { format!("Variant {}", self.palette_variant + 1) }
    pub(crate) fn selected_recipe_layer(&self) -> usize { self.selected_recipe_layer }

    pub(crate) fn move_selected_recipe_layer(&mut self, delta: i32) -> Result<String, String> {
        if self.recipe.layers.len() < 2 { return Err("Recipe needs at least two layers to reorder".to_string()); }
        self.selected_recipe_layer = self.selected_recipe_layer.min(self.recipe.layers.len() - 1);
        let next = if delta < 0 { self.selected_recipe_layer.saturating_sub(1) } else { (self.selected_recipe_layer + 1).min(self.recipe.layers.len() - 1) };
        if next == self.selected_recipe_layer { return Err("Selected recipe layer is already at that edge".to_string()); }
        self.recipe.layers.swap(self.selected_recipe_layer, next);
        self.selected_recipe_layer = next;
        self.sync_assembled_preview();
        let message = format!("Moved recipe layer to draw position {}", next + 1);
        self.recipe_message = Some(message.clone());
        Ok(message)
    }

    pub(crate) fn cycle_selected_recipe_layer(&mut self, delta: i32) -> String {
        if self.recipe.layers.is_empty() { return "Recipe has no layers".to_string(); }
        self.selected_recipe_layer = cycle_index(self.selected_recipe_layer, self.recipe.layers.len(), delta);
        let layer = &self.recipe.layers[self.selected_recipe_layer];
        format!("Selected recipe layer {}: {}", self.selected_recipe_layer + 1, layer.slot)
    }

    pub(crate) fn publish_recipe_preset(&mut self) -> Result<String, String> {
        if self.recipe.layers.is_empty() { return Err("Add at least one character layer before publishing".to_string()); }
        self.sync_recipe_identity();
        let root = haven_assets::asset_intake::repo_root_dir();
        let directory = root.join(CHARACTER_STUDIO_PRESET_DIR);
        fs::create_dir_all(&directory).map_err(|error| format!("failed to create {}: {error}", directory.display()))?;
        let stem = match self.mode {
            CharacterStudioMode::Player => "player_character_preset",
            CharacterStudioMode::Npc => "npc_character_preset",
        };
        let path = directory.join(format!("{stem}.json"));
        #[derive(Serialize)]
        struct CharacterPreset<'a> { schema: &'static str, recipe: &'a CharacterRecipeDraft }
        let payload = CharacterPreset { schema: CHARACTER_STUDIO_PRESET_SCHEMA, recipe: &self.recipe };
        let text = serde_json::to_string_pretty(&payload).map_err(|error| format!("failed to encode character preset: {error}"))?;
        fs::write(&path, text).map_err(|error| format!("failed to write {}: {error}", path.display()))?;
        let message = format!("Published project-owned character preset: {}", path.display());
        self.recipe_message = Some(message.clone());
        Ok(message)
    }

    pub(crate) fn advanced_open(&self) -> bool { self.advanced_open }

    pub(crate) fn toggle_advanced(&mut self) -> String {
        self.advanced_open = !self.advanced_open;
        if self.advanced_open { "Character Advanced controls visible".to_string() }
        else { "Character wardrobe view restored".to_string() }
    }

    pub(crate) fn current_slot_locked(&self) -> bool {
        let slot = self.slot_label();
        slot != "all" && self.locked_slots.contains(slot)
    }

    pub(crate) fn toggle_current_slot_lock(&mut self) -> String {
        let slot = self.slot_label().to_string();
        if slot == "all" { return "Choose a wardrobe/equipment slot before locking it".to_string(); }
        if !self.locked_slots.insert(slot.clone()) {
            self.locked_slots.remove(&slot);
            format!("Unlocked {slot} for randomization")
        } else {
            format!("Locked {slot} during randomization")
        }
    }

    pub(crate) fn randomize_recipe_scope(&mut self, scope: &str) -> String {
        let slots: &[&str] = match scope {
            "appearance" => &["hair", "eyebrows", "eyes", "nose", "ears", "beards", "expression"],
            "outfit" => &["torso", "arms", "hands", "legs", "feet", "hat", "neck", "back", "accessory"],
            "equipment" => &["weapon", "shield", "tools"],
            _ => &["hair", "eyebrows", "eyes", "nose", "ears", "beards", "expression", "torso", "arms", "hands", "legs", "feet", "hat", "neck", "back", "accessory", "weapon", "shield", "tools", "wings", "tail", "mobility", "effects"],
        };
        let Some(builder) = self.builder_catalog.as_ref() else {
            return "Universal LPC definition catalog is unavailable".to_string();
        };
        let mut typed = match self.typed_recipe_from_draft() {
            Ok(recipe) => recipe,
            Err(error) => return error,
        };
        let body = typed.body_type;
        let mut seed = self.random_seed.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut replacements = Vec::new();
        for slot in slots.iter().copied() {
            if self.locked_slots.contains(slot) { continue; }
            let candidates = builder.options_for(slot, body)
                .filter(|option| option.is_selectable(self.include_share_alike))
                .filter(|option| builder.compatible_option(&typed, option))
                .filter(|option| self.mode != CharacterStudioMode::Player || !option.tags.contains("zombie"))
                .collect::<Vec<_>>();
            if candidates.is_empty() { continue; }
            seed ^= seed >> 12; seed ^= seed << 25; seed ^= seed >> 27;
            let index = (seed.wrapping_mul(0x2545_F491_4F6C_DD1D) as usize) % candidates.len();
            let option = candidates[index];
            let variant = if option.variants.is_empty() { None } else {
                Some(option.variants[(seed as usize) % option.variants.len()].clone())
            };
            if builder.select_option(&mut typed, &option.item_id, variant.clone()).is_err() { continue; }
            replacements.push(CharacterRecipeDraftLayer {
                slot: option.category.clone(),
                source: option.definition_path.to_string_lossy().replace('\\', "/"),
                item_id: Some(option.item_id.clone()),
                variant,
                selection_group: Some(option.selection_group.clone()),
                selected_license: option.preferred_license().map(str::to_string),
                share_alike_required: option.share_alike_required(),
            });
        }
        self.random_seed = seed;
        for replacement in replacements {
            let group = replacement.selection_group.clone().unwrap_or_else(|| replacement.slot.clone());
            if let Some(existing) = self.recipe.layers.iter_mut().find(|layer| {
                layer.selection_group.as_deref() == Some(group.as_str())
            }) {
                *existing = replacement;
            } else {
                self.recipe.layers.push(replacement);
            }
        }
        self.ensure_required_foundation();
        self.sync_recipe_identity();
        self.selected_recipe_layer = self.selected_recipe_layer.min(self.recipe.layers.len().saturating_sub(1));
        self.sync_assembled_preview();
        let message = format!("Randomized {scope} from definition-level Universal LPC items; foundations and locks preserved");
        self.recipe_message = Some(message.clone());
        message
    }

    pub(crate) fn sync_assembled_preview(&mut self) {
        self.assembled_preview_layers.clear();
        self.assembled_preview_error = None;
        self.presentation_issues.clear();
        let Some(builder) = self.builder_catalog.as_ref() else {
            self.assembled_preview_error = Some("Universal LPC sheet-definition catalog is unavailable".to_string());
            return;
        };
        let recipe = match self.typed_recipe_from_draft() {
            Ok(recipe) => recipe,
            Err(error) => {
                self.assembled_preview_error = Some(error);
                return;
            }
        };
        let source_root = haven_assets::asset_intake::repo_root_dir().join(DEFAULT_ULPC_SOURCE_ROOT);
        let resolver = UniversalLpcCharacterResolver::with_source_root(&source_root, &builder.definitions);
        let resolved = match resolver.resolve(&recipe, self.action_id()) {
            Ok(value) => value,
            Err(error) => {
                self.assembled_preview_error = Some(error);
                return;
            }
        };
        self.presentation_issues = resolved.presentation_issues.clone();
        if !self.presentation_issues.is_empty() {
            let summary = self
                .presentation_issues
                .iter()
                .map(|issue| issue.reason.as_str())
                .take(2)
                .collect::<Vec<_>>()
                .join(" | ");
            self.recipe_message = Some(format!(
                "Character presentation resolved {} occlusion/conflict rule(s): {summary}",
                self.presentation_issues.len()
            ));
        }
        if !resolved.dependency_rejections.is_empty() {
            self.recipe_message = Some(format!(
                "Skipped {} dependency-incompatible ULPC item(s)",
                resolved.dependency_rejections.len()
            ));
        }
        for layer in resolved.layers {
            let path = layer.source_path.clone();
            if !path.is_file() {
                // Exact resolver is fail-closed. Never fall back to a different action sheet.
                if layer.item_id == UNIVERSAL_LPC_FOUNDATION_BODY_ITEM_ID {
                    self.assembled_preview_error = Some(format!("Required body sheet is missing: {}", path.display()));
                }
                continue;
            }
            match image::open(&path) {
                Ok(image) => {
                    let image = image.to_rgba8();
                    if image.width() > u16::MAX as u32 || image.height() > u16::MAX as u32 {
                        self.assembled_preview_error = Some(format!("{} exceeds editor texture limit", path.display()));
                        continue;
                    }
                    let texture = Texture2D::from_rgba8(image.width() as u16, image.height() as u16, image.as_raw());
                    texture.set_filter(FilterMode::Nearest);
                    self.assembled_preview_layers.push(CharacterAssembledPreviewLayer {
                        texture,
                        slot: layer.item_id,
                        source_animation: layer.source_animation,
                        frame_size: layer.frame_size,
                        z_pos: layer.z_pos,
                    });
                }
                Err(error) => self.assembled_preview_error = Some(format!("Could not assemble {}: {error}", path.display())),
            }
        }
        self.assembled_preview_layers.sort_by(|left, right| {
            left.z_pos.cmp(&right.z_pos).then_with(|| left.slot.cmp(&right.slot))
        });
    }

    fn assembled_preview_source_rect(layer: &CharacterAssembledPreviewLayer, direction_index: usize, progress: f32) -> Rect {
        let frame_size = layer.frame_size.max(1);
        let width = layer.texture.width() as u32;
        let height = layer.texture.height() as u32;
        if width < frame_size || height < frame_size {
            return Rect::new(0.0, 0.0, width as f32, height as f32);
        }
        let columns = (width / frame_size).max(1) as usize;
        let rows = (height / frame_size).max(1) as usize;
        let frame = if animation_spec(&layer.source_animation).is_some() {
            frame_for_progress(&layer.source_animation, progress).min(columns.saturating_sub(1))
        } else {
            ((progress.clamp(0.0, 0.999_999) * columns as f32).floor() as usize)
                .min(columns.saturating_sub(1))
        };
        let direction_rows = rows.min(4).max(1);
        let row = character_direction_row(direction_index, direction_rows).min(rows.saturating_sub(1));
        Rect::new(
            (frame as u32 * frame_size) as f32,
            (row as u32 * frame_size) as f32,
            frame_size as f32,
            frame_size as f32,
        )
    }

    pub(crate) fn assembled_preview_layers(&self) -> impl Iterator<Item = (&Texture2D, Rect, &str, u32)> + '_ {
        let direction = self.direction_index;
        let progress = self.preview_progress();
        self.assembled_preview_layers
            .iter()
            .filter(move |layer| !self.preview_hidden_items.contains(&layer.slot))
            .map(move |layer| {
                let source = Self::assembled_preview_source_rect(layer, direction, progress);
                (&layer.texture, source, layer.slot.as_str(), layer.frame_size)
            })
    }

    pub(crate) fn assembled_preview_canvas_frame_size(&self) -> u32 {
        self.assembled_preview_layers.iter().map(|layer| layer.frame_size).max().unwrap_or(64)
    }

    pub(crate) fn assembled_preview_error(&self) -> Option<&str> { self.assembled_preview_error.as_deref() }

    pub(crate) fn recipe_layer_count(&self) -> usize {
        self.recipe.layers.len()
    }

    pub(crate) fn recipe_layers(&self) -> impl Iterator<Item = (&str, &str, bool)> {
        self.recipe.layers.iter().map(|layer| {
            (
                layer.slot.as_str(),
                layer.source.as_str(),
                layer.share_alike_required,
            )
        })
    }

    pub(crate) fn recipe_message(&self) -> Option<&str> {
        self.recipe_message.as_deref()
    }

    pub(crate) fn cycle_slot(&mut self, delta: i32) {
        let ids = self.catalog_section.category_ids();
        let current = if self.slot_filter == 0 {
            0
        } else {
            let current_id = UNIVERSAL_LPC_CHARACTER_BUILDER_CATEGORIES[self.slot_filter - 1].id;
            ids.iter().position(|id| *id == current_id).map(|index| index + 1).unwrap_or(0)
        };
        let next = cycle_index(current, ids.len() + 1, delta);
        self.slot_filter = if next == 0 {
            0
        } else {
            UNIVERSAL_LPC_CHARACTER_BUILDER_CATEGORIES
                .iter()
                .position(|category| category.id == ids[next - 1])
                .map(|index| index + 1)
                .unwrap_or(0)
        };
        self.category_menu_open = false;
        self.rebuild_filter();
    }

    pub(crate) fn select_slot_filter(&mut self, slot_filter: usize) {
        self.slot_filter = slot_filter.min(UNIVERSAL_LPC_CHARACTER_BUILDER_CATEGORIES.len());
        if self.slot_filter > 0 {
            let id = UNIVERSAL_LPC_CHARACTER_BUILDER_CATEGORIES[self.slot_filter - 1].id;
            self.catalog_section = if CharacterCatalogSection::WardrobeGear.contains(id) {
                CharacterCatalogSection::WardrobeGear
            } else {
                CharacterCatalogSection::Create
            };
        }
        self.category_menu_open = false;
        self.rebuild_filter();
    }

    pub(crate) fn set_catalog_section(&mut self, section: CharacterCatalogSection) {
        if self.catalog_section == section { return; }
        self.catalog_section = section;
        self.slot_filter = 0;
        self.selected = 0;
        self.list_offset = 0;
        self.category_menu_open = false;
        self.rebuild_filter();
    }

    pub(crate) fn catalog_section(&self) -> CharacterCatalogSection { self.catalog_section }

    pub(crate) fn toggle_category_menu(&mut self) { self.category_menu_open = !self.category_menu_open; }
    pub(crate) fn category_menu_open(&self) -> bool { self.category_menu_open }

    pub(crate) fn slot_label(&self) -> &'static str {
        if self.slot_filter == 0 { "all" } else { UNIVERSAL_LPC_CHARACTER_BUILDER_CATEGORIES[self.slot_filter - 1].id }
    }

    pub(crate) fn slot_display_label(&self) -> &'static str {
        if self.slot_filter == 0 {
            match self.catalog_section {
                CharacterCatalogSection::Create => "All Create",
                CharacterCatalogSection::WardrobeGear => "All Wardrobe & Gear",
            }
        } else {
            UNIVERSAL_LPC_CHARACTER_BUILDER_CATEGORIES[self.slot_filter - 1].label
        }
    }

}

fn representative_character_cell(image: &image::RgbaImage) -> Rect {
    let width = image.width();
    let height = image.height();
    if width < CHARACTER_SOURCE_CELL || height < CHARACTER_SOURCE_CELL {
        return Rect::new(0.0, 0.0, width as f32, height as f32);
    }
    let columns = width / CHARACTER_SOURCE_CELL;
    let rows = height / CHARACTER_SOURCE_CELL;
    for row in 0..rows {
        for column in 0..columns {
            let x0 = column * CHARACTER_SOURCE_CELL;
            let y0 = row * CHARACTER_SOURCE_CELL;
            let mut occupied = false;
            'cell: for y in y0..(y0 + CHARACTER_SOURCE_CELL).min(height) {
                for x in x0..(x0 + CHARACTER_SOURCE_CELL).min(width) {
                    if image.get_pixel(x, y).0[3] != 0 {
                        occupied = true;
                        break 'cell;
                    }
                }
            }
            if occupied {
                return Rect::new(
                    x0 as f32,
                    y0 as f32,
                    CHARACTER_SOURCE_CELL as f32,
                    CHARACTER_SOURCE_CELL as f32,
                );
            }
        }
    }
    Rect::new(
        0.0,
        0.0,
        CHARACTER_SOURCE_CELL as f32,
        CHARACTER_SOURCE_CELL as f32,
    )
}

#[cfg(test)]
mod character_studio_layout_tests {
    use super::*;

    #[test]
    fn catalog_rows_shrink_before_footer_overlap() {
        let tall = Rect::new(0.0, 0.0, 260.0, 700.0);
        let short = Rect::new(0.0, 0.0, 260.0, 280.0);
        assert_eq!(character_visible_rows(tall), CHARACTER_MAX_ROWS);
        assert!(character_visible_rows(short) < CHARACTER_MAX_ROWS);
        let last = character_row_rect(short, character_visible_rows(short) - 1);
        assert!(last.y + last.h <= short.y + short.h - CHARACTER_LIST_FOOTER + 0.01);
    }

    #[test]
    fn create_and_wardrobe_sections_cover_every_builder_category_once() {
        let mut seen = std::collections::BTreeSet::new();
        for section in [CharacterCatalogSection::Create, CharacterCatalogSection::WardrobeGear] {
            for category in section.category_ids() {
                assert!(seen.insert(*category), "duplicate Character Studio category {category}");
            }
        }
        let expected = UNIVERSAL_LPC_CHARACTER_BUILDER_CATEGORIES
            .iter()
            .map(|category| category.id)
            .collect::<std::collections::BTreeSet<_>>();
        assert_eq!(seen, expected);
    }

    #[test]
    fn preview_direction_controls_map_to_ulpc_cardinal_rows() {
        assert_eq!(character_direction_row(0, 4), 2); // South
        assert_eq!(character_direction_row(1, 4), 1); // West
        assert_eq!(character_direction_row(2, 4), 0); // North
        assert_eq!(character_direction_row(3, 4), 3); // East
        assert_eq!(character_direction_row(3, 1), 0); // Hurt/climb single-row actions
    }

    #[test]
    fn assembled_preview_uses_declared_animation_frame_and_direction() {
        let source = character_animation_source_rect(9 * 64, 4 * 64, "walk", 0, 0.0);
        assert_eq!(source.x, 64.0); // walk cycle begins on authored column 1
        assert_eq!(source.y, 2.0 * 64.0); // South is ULPC row 2
        assert_eq!(source.w, 64.0);
        assert_eq!(source.h, 64.0);
    }

    #[test]
    fn preview_switches_animation_folder_without_losing_variant() {
        let original = std::path::Path::new("body/bodies/male/backslash/light.png");
        assert_eq!(
            standard_action_sibling_path(original, "idle"),
            std::path::Path::new("body/bodies/male/idle/light.png")
        );
    }

    #[test]
    fn preview_action_aliases_match_normalized_ulpc_sources() {
        assert_eq!(standard_action_source_name("combat"), "combat_idle");
        assert_eq!(standard_action_source_name("watering"), "thrust");
        assert_eq!(standard_action_source_name("1h_backslash"), "backslash");
        assert_eq!(standard_action_source_name("1h_halfslash"), "halfslash");
    }

    #[test]
    fn representative_preview_uses_first_nontransparent_grid_cell() {
        let mut image = image::RgbaImage::new(
            CHARACTER_SOURCE_CELL * 2,
            CHARACTER_SOURCE_CELL * 2,
        );
        image.put_pixel(
            CHARACTER_SOURCE_CELL + 3,
            CHARACTER_SOURCE_CELL + 4,
            image::Rgba([255, 255, 255, 255]),
        );
        let cell = representative_character_cell(&image);
        assert_eq!(cell.x, CHARACTER_SOURCE_CELL as f32);
        assert_eq!(cell.y, CHARACTER_SOURCE_CELL as f32);
        assert_eq!(cell.w, CHARACTER_SOURCE_CELL as f32);
        assert_eq!(cell.h, CHARACTER_SOURCE_CELL as f32);
    }

    #[test]
    fn draft_recipe_round_trips() {
        let draft = CharacterRecipeDraft {
            schema: CHARACTER_STUDIO_DRAFT_SCHEMA.to_string(),
            mode: "NPC".to_string(),
            sex: "Female".to_string(),
            age: "Adult".to_string(),
            template: "npc".to_string(),
            direction: "South".to_string(),
            action: "idle".to_string(),
            palette_variant: 0,
            layers: vec![CharacterRecipeDraftLayer {
                slot: "hair".to_string(),
                source: "hair/example.png".to_string(),
                item_id: Some("hair_example".to_string()),
                variant: None,
                selection_group: Some("hair".to_string()),
                selected_license: Some("CC-BY 4.0".to_string()),
                share_alike_required: false,
            }],
        };
        let json = serde_json::to_string(&draft).expect("serialize draft");
        let decoded: CharacterRecipeDraft =
            serde_json::from_str(&json).expect("deserialize draft");
        assert_eq!(decoded, draft);
    }
}

impl EditorApp {
    pub(crate) fn draw_character_studio_workspace(&self, _rect: Rect) {
        // Character Wardrobe workflow: the default surface is a production character
        // creator. Raw source, layer ordering, palette and license diagnostics stay
        // behind Advanced instead of competing with identity/wardrobe/preview tasks.
        let host = self.canvas_workspace_layout().workspace_body;
        let (controls, preview, c) = character_wardrobe_layout(host);

        draw_rectangle(controls.x, controls.y, controls.w, controls.h, editor_theme::colors::PANEL_BG);
        draw_rectangle_lines(controls.x, controls.y, controls.w, controls.h, 1.0, PANEL_EDGE);
        draw_editor_text("Character Creator", controls.x + 10.0, controls.y + 22.0, 18.0, TEXT);
        draw_scissored_text(
            "Build a player or NPC, dress them, then preview every direction and animation.",
            controls.x + 10.0,
            controls.y + 42.0,
            controls.w - 20.0,
            11.0,
            MUTED,
        );

        draw_scissored_text("IDENTITY", c.x, c.y - 4.0, c.w, 10.5, MUTED);
        for (index, mode) in [CharacterStudioMode::Player, CharacterStudioMode::Npc].into_iter().enumerate() {
            super::gui_controls::draw_control(
                center_button_rect(c, 0, index, 2),
                if mode == CharacterStudioMode::Player { "Player Character" } else { "NPC" },
                super::gui_controls::GuiControlClass::Segmented,
                self.character_studio.mode == mode, true,
            );
        }
        for (index, sex) in SEX_FILTERS.into_iter().enumerate() {
            super::gui_controls::draw_control(
                center_button_rect(c, 1, index, 2), sex.label(),
                super::gui_controls::GuiControlClass::Segmented,
                self.character_studio.sex == sex, true,
            );
        }
        for (index, age) in AGE_FILTERS.into_iter().enumerate() {
            super::gui_controls::draw_control(
                center_button_rect(c, 2, index, AGE_FILTERS.len()), age.label(),
                super::gui_controls::GuiControlClass::Segmented,
                self.character_studio.age == age, true,
            );
        }
        self.draw_npc_profile_controls(c);
        draw_editor_widget(center_button_rect(c, 4, 0, 3), "‹ Category", false);
        draw_editor_widget(center_button_rect(c, 4, 1, 3), self.character_studio.slot_display_label(), true);
        draw_editor_widget(center_button_rect(c, 4, 2, 3), "Category ›", false);
        super::gui_controls::draw_control(
            center_button_rect(c, 5, 0, 3),
            if self.character_studio.current_slot_locked() { "Locked" } else { "Lock" },
            super::gui_controls::GuiControlClass::Toggle,
            self.character_studio.current_slot_locked(), true,
        );
        draw_editor_widget(center_button_rect(c, 5, 1, 3), "Add Selected", false);
        draw_editor_widget(center_button_rect(c, 5, 2, 3), "Remove", false);
        // Historical W76 label: Randomize Unlocked. The production creator now exposes the same scope as All Unlocked.
        draw_editor_widget(center_button_rect(c, 6, 0, 3), "Appearance", false);
        draw_editor_widget(center_button_rect(c, 6, 1, 3), "Outfit", false);
        super::gui_controls::draw_control(
            center_button_rect(c, 6, 2, 3), "All Unlocked",
            super::gui_controls::GuiControlClass::Primary, false, true,
        );

        draw_scissored_text("PREVIEW", c.x, c.y + 7.0 * 32.0 + 13.0, c.w, 10.5, MUTED);
        draw_editor_widget(center_button_rect(c, 8, 0, 3), "Turn Left", false);
        draw_editor_widget(center_button_rect(c, 8, 1, 3), self.character_studio.direction_label(), true);
        draw_editor_widget(center_button_rect(c, 8, 2, 3), "Turn Right", false);
        draw_editor_widget(center_button_rect(c, 9, 0, 3), "‹ Animation", false);
        draw_editor_widget(center_button_rect(c, 9, 1, 3), self.character_studio.action_label(), true);
        draw_editor_widget(center_button_rect(c, 9, 2, 3), "Animation ›", false);
        super::gui_controls::draw_control(
            center_button_rect(c, 10, 0, 2), self.character_studio.preview_playback_label(),
            super::gui_controls::GuiControlClass::Toggle,
            self.character_studio.preview_playing(), true,
        );
        draw_editor_widget(center_button_rect(c, 10, 1, 2), "Restart Animation", false);

        draw_scissored_text("PRESET", c.x, c.y + 11.0 * 32.0 + 13.0, c.w, 10.5, MUTED);
        draw_editor_widget(center_button_rect(c, 12, 0, 4), "Save", false);
        draw_editor_widget(center_button_rect(c, 12, 1, 4), "Load", false);
        draw_editor_widget(center_button_rect(c, 12, 2, 4), "Clear", false);
        super::gui_controls::draw_control(
            center_button_rect(c, 12, 3, 4), "Publish",
            super::gui_controls::GuiControlClass::Primary, false, true,
        );
        super::gui_controls::draw_control(
            center_button_rect(c, 13, 0, 2),
            &format!("Layers: {}", self.character_studio.layer_view_label()),
            super::gui_controls::GuiControlClass::Toggle,
            self.character_studio.layer_view_label() == "Equipment Slots", true,
        );
        super::gui_controls::draw_control(
            center_button_rect(c, 13, 1, 2),
            if self.character_studio.advanced_open() { "Advanced ▴" } else { "Advanced ▾" },
            super::gui_controls::GuiControlClass::Toggle,
            self.character_studio.advanced_open(), true,
        );
        if self.character_studio.advanced_open() {
            draw_editor_widget(
                center_button_rect(c, 14, 0, 2),
                "Preferred Licenses",
                !self.character_studio.include_share_alike,
            );
            draw_editor_widget(
                center_button_rect(c, 14, 1, 2),
                "Include CC-BY-SA",
                self.character_studio.include_share_alike,
            );
            draw_editor_widget(center_button_rect(c, 15, 0, 3), "‹ Palette", false);
            draw_editor_widget(center_button_rect(c, 15, 1, 3), &self.character_studio.palette_variant_label(), true);
            draw_editor_widget(center_button_rect(c, 15, 2, 3), "Palette ›", false);
        }
        self.draw_npc_profile_rule_editor(c);

        if self.character_studio.category_menu_open() {
            let menu = character_category_menu_rect(c);
            draw_rectangle(menu.x, menu.y, menu.w, menu.h, editor_theme::colors::PANEL_BG);
            draw_rectangle_lines(menu.x, menu.y, menu.w, menu.h, 1.0, PANEL_EDGE);
            super::gui_controls::draw_control(
                character_category_all_rect(c),
                "All Categories",
                super::gui_controls::GuiControlClass::Segmented,
                self.character_studio.slot_label() == "all",
                true,
            );
            for (index, category) in UNIVERSAL_LPC_CHARACTER_BUILDER_CATEGORIES.into_iter().enumerate() {
                super::gui_controls::draw_control(
                    character_category_option_rect(c, index),
                    category.label,
                    super::gui_controls::GuiControlClass::Segmented,
                    self.character_studio.slot_label() == category.id,
                    true,
                );
            }
        }

        draw_rectangle(preview.x, preview.y, preview.w, preview.h, editor_theme::colors::CANVAS_SURROUND);
        draw_rectangle_lines(preview.x, preview.y, preview.w, preview.h, 1.0, PANEL_EDGE);
        draw_editor_text("Assembled Character Preview", preview.x + 12.0, preview.y + 22.0, 18.0, TEXT);
        draw_scissored_text(
            &format!(
                "{} · {} · {} · {} · {} layers",
                self.character_studio.mode.label(),
                self.character_studio.direction_label(),
                self.character_studio.action_label(),
                if self.character_studio.preview_playing() { "Playing" } else { "Paused" },
                self.character_studio.recipe_layer_count(),
            ),
            preview.x + 12.0,
            preview.y + 43.0,
            preview.w - 24.0,
            11.5,
            MUTED,
        );
        if let Some(message) = self.character_studio.recipe_message() {
            draw_scissored_text(message, preview.x + 12.0, preview.y + 62.0, preview.w - 24.0, 11.0, MUTED);
        }

        let assembled_area = Rect::new(
            preview.x + 18.0,
            preview.y + 80.0,
            (preview.w - 36.0).max(1.0),
            (preview.h - 118.0).max(1.0),
        );
        let assembled_size = assembled_area.w.min(assembled_area.h).min(420.0);
        let assembled_dest = Rect::new(
            assembled_area.x + (assembled_area.w - assembled_size) * 0.5,
            assembled_area.y + (assembled_area.h - assembled_size) * 0.5,
            assembled_size,
            assembled_size,
        );
        let mut assembled_count = 0usize;
        let canvas_frame = self.character_studio.assembled_preview_canvas_frame_size().max(1) as f32;
        for (texture, source, _slot, frame_size) in self.character_studio.assembled_preview_layers() {
            assembled_count += 1;
            let ratio = frame_size.max(1) as f32 / canvas_frame;
            let draw_w = assembled_dest.w * ratio;
            let draw_h = assembled_dest.h * ratio;
            let draw_x = assembled_dest.x + (assembled_dest.w - draw_w) * 0.5;
            let draw_y = assembled_dest.y + (assembled_dest.h - draw_h) * 0.5;
            draw_texture_ex(
                texture,
                draw_x,
                draw_y,
                WHITE,
                DrawTextureParams {
                    dest_size: Some(vec2(draw_w, draw_h)),
                    source: Some(source),
                    ..Default::default()
                },
            );
        }
        if assembled_count == 0 {
            if let (Some(texture), Some(source)) = (
                self.character_studio.preview_texture.as_ref(),
                self.character_studio.preview_source_rect,
            ) {
                let scale = (assembled_area.w / source.w).min(assembled_area.h / source.h).max(0.01);
                let draw_w = source.w * scale;
                let draw_h = source.h * scale;
                draw_texture_ex(
                    texture,
                    assembled_area.x + (assembled_area.w - draw_w) * 0.5,
                    assembled_area.y + (assembled_area.h - draw_h) * 0.5,
                    WHITE,
                    DrawTextureParams { dest_size: Some(vec2(draw_w, draw_h)), source: Some(source), ..Default::default() },
                );
            } else if let Some(error) = self.character_studio.assembled_preview_error() {
                draw_wrapped(error, assembled_area.x, assembled_area.y + 24.0, assembled_area.w, 14.0, WARN);
            } else {
                draw_wrapped(
                    "Choose a wardrobe category from Assets, assign compatible components, or use Randomize Unlocked.",
                    assembled_area.x + 12.0,
                    assembled_area.y + 40.0,
                    assembled_area.w - 24.0,
                    15.0,
                    MUTED,
                );
            }
        }
        draw_scissored_text(
            if self.character_studio.advanced_open() {
                "Advanced source/layer/provenance diagnostics are available in the Properties dock."
            } else {
                "Use Turn Left/Right and Animation controls to inspect the same assembled character in motion."
            },
            preview.x + 12.0,
            preview.y + preview.h - 14.0,
            preview.w - 24.0,
            11.0,
            MUTED,
        );
    }

    pub(crate) fn draw_character_studio_inspector(&self, rect: Rect) {
        let footer = character_reload_rect(rect);
        let runtime_context_button = character_runtime_context_rect(rect);
        let content_bottom = runtime_context_button.y - 8.0;
        let mut y = rect.y;
        draw_editor_text("Character Recipe Source", rect.x, y, 22.0, TEXT);
        y += 30.0;
        for line in [
            format!("Mode: {}", self.character_studio.mode.label()),
            format!("Sex: {}", self.character_studio.sex.label()),
            format!("Age: {}", self.character_studio.age.label()),
            format!("Direction intent: {}", self.character_studio.direction_label()),
            format!("Action intent: {}", self.character_studio.action_label()),
            format!("Palette: {}", self.character_studio.palette_variant_label()),
            format!(
                "Pool: {}",
                if self.character_studio.include_share_alike {
                    "Preferred + ShareAlike"
                } else {
                    "Preferred only"
                }
            ),
            format!(
                "Compatible records: {}",
                self.character_studio.filtered_count()
            ),
        ] {
            if y + 20.0 > content_bottom {
                break;
            }
            draw_scissored_text(&line, rect.x, y, rect.w, 16.0, TEXT);
            y += 23.0;
        }
        if self.character_studio.mode == CharacterStudioMode::Npc {
            y += 6.0;
            if y + 24.0 <= content_bottom {
                draw_editor_text("Effective NPC Profile Rules", rect.x, y, 17.0, TEXT);
                y += 22.0;
            }
            for line in self.character_studio.npc_profile_detail_lines() {
                if y + 20.0 > content_bottom { break; }
                draw_scissored_text(&line, rect.x, y, rect.w, 12.5, MUTED);
                y += 19.0;
            }
        }
        y += 8.0;
        if !self.character_studio.advanced_open() {
            if y + 26.0 <= content_bottom {
                draw_editor_text("Wardrobe Summary", rect.x, y, 18.0, TEXT);
                y += 24.0;
            }
            for line in [
                format!("Recipe layers: {}", self.character_studio.recipe_layer_count()),
                format!("Active slot: {}", self.character_studio.slot_label()),
                format!("Slot lock: {}", if self.character_studio.current_slot_locked() { "Locked" } else { "Unlocked" }),
                "Raw ULPC paths, z-order, aliases, provenance and license diagnostics are hidden in normal wardrobe mode.".to_string(),
            ] {
                if y + 22.0 > content_bottom { break; }
                draw_wrapped(&line, rect.x, y, rect.w, 14.0, MUTED);
                y += if line.len() > 56 { 42.0 } else { 22.0 };
            }
            if y + 42.0 <= content_bottom {
                draw_wrapped(
                    "Open Advanced in Character Studio only when diagnosing compatibility or source metadata.",
                    rect.x, y + 4.0, rect.w, 14.0, editor_theme::colors::ACCENT,
                );
            }
            if let Some(breadcrumb) = self.resource_context_breadcrumb() {
                draw_scissored_text(
                    &format!("Runtime: {breadcrumb}"),
                    rect.x,
                    runtime_context_button.y - 14.0,
                    rect.w,
                    10.5,
                    MUTED,
                );
                draw_editor_widget_tone(
                    runtime_context_button,
                    "Open Runtime Animation",
                    false,
                    WidgetTone::Primary,
                );
            } else {
                draw_editor_widget_tone(
                    runtime_context_button,
                    "Runtime Context unavailable",
                    false,
                    WidgetTone::Quiet,
                );
            }
            if let Some(breadcrumb) = self.resource_context_breadcrumb() {
            draw_scissored_text(
                &format!("Runtime: {breadcrumb}"),
                rect.x,
                runtime_context_button.y - 14.0,
                rect.w,
                10.5,
                MUTED,
            );
            draw_editor_widget_tone(
                runtime_context_button,
                "Open Runtime Animation",
                false,
                WidgetTone::Primary,
            );
        } else {
            draw_editor_widget_tone(
                runtime_context_button,
                "Runtime Context unavailable",
                false,
                WidgetTone::Quiet,
            );
        }
        draw_editor_widget(character_variant_rect(rect, 0), "‹ Variant", false);
            draw_editor_widget(character_variant_rect(rect, 1), &self.character_studio.selected_variant_label(), true);
            draw_editor_widget(character_variant_rect(rect, 2), "Variant ›", false);
            draw_scissored_text(
                DEFAULT_UNIVERSAL_LPC_AUTHORITY_PATH,
                rect.x,
                footer.y - 10.0,
                rect.w,
                11.0,
                MUTED,
            );
            draw_editor_widget(footer, "Reload Universal LPC Authority", false);
            return;
        }
        if y + 24.0 <= content_bottom {
            draw_editor_text(
                &format!(
                    "Working Recipe ({})",
                    self.character_studio.recipe_layer_count()
                ),
                rect.x,
                y,
                18.0,
                TEXT,
            );
            y += 24.0;
        }
        for (recipe_index, (slot, source, share_alike)) in self.character_studio.recipe_layers().take(8).enumerate() {
            if y + 19.0 > content_bottom {
                break;
            }
            let file = source.rsplit('/').next().unwrap_or(source);
            draw_scissored_text(
                &format!("{slot}: {file}"),
                rect.x,
                y,
                rect.w,
                13.0,
                if recipe_index == self.character_studio.selected_recipe_layer() { TEXT } else if share_alike { WARN } else { MUTED },
            );
            y += 18.0;
        }
        if self.character_studio.recipe_layer_count() > 8 && y + 19.0 <= content_bottom {
            draw_editor_text("...more recipe layers", rect.x, y, 12.0, MUTED);
            y += 18.0;
        }
        y += 6.0;
        if let Some(record) = self.character_studio.selected_record() {
            if y + 26.0 <= content_bottom {
                draw_editor_text("Selected Layer", rect.x, y, 20.0, TEXT);
                y += 26.0;
            }
            if y + 38.0 <= content_bottom {
                draw_wrapped(&record.source, rect.x, y, rect.w, 15.0, TEXT);
                y += 44.0;
            }
            for line in [
                format!("Category: {}", record.category),
                format!("License tier: {}", record.license_tier),
                format!(
                    "Selected license: {}",
                    record.selected_license.as_deref().unwrap_or("blocked")
                ),
                format!("Authors: {}", record.authors.len()),
                format!("Source links: {}", record.urls.len()),
                format!(
                    "Mounted: {}",
                    self.character_studio
                        .authority()
                        .map(|authority| authority.source_path(record).is_file())
                        .unwrap_or(false)
                ),
            ] {
                if y + 20.0 > content_bottom {
                    break;
                }
                draw_scissored_text(
                    &line,
                    rect.x,
                    y,
                    rect.w,
                    15.0,
                    if record.share_alike_required { WARN } else { MUTED },
                );
                y += 22.0;
            }
            if y + 48.0 <= content_bottom {
                y += 6.0;
                draw_editor_text("Tags", rect.x, y, 18.0, TEXT);
                y += 22.0;
                draw_scissored_text(&record.tags.join(", "), rect.x, y, rect.w, 13.0, MUTED);
                y += 20.0;
            }
            if let Some(authority) = self.character_studio.authority() {
                if y + 20.0 <= content_bottom {
                    draw_scissored_text(
                        &format!("Source commit: {}", authority.source_commit),
                        rect.x,
                        y,
                        rect.w,
                        12.0,
                        MUTED,
                    );
                }
            }
        } else if let Some(error) = self.character_studio.load_error() {
            if y + 52.0 <= content_bottom {
                draw_wrapped(error, rect.x, y, rect.w, 15.0, WARN);
                y += 58.0;
            }
            if y + 44.0 <= content_bottom {
                draw_editor_text("Generate authority with:", rect.x, y, 17.0, TEXT);
                y += 22.0;
                draw_scissored_text(
                    "tools/automation/characters/Bootstrap-UniversalLpcGenerator.cmd",
                    rect.x,
                    y,
                    rect.w,
                    12.0,
                    MUTED,
                );
            }
        }
        draw_editor_widget(character_variant_rect(rect, 0), "‹ Variant", false);
        draw_editor_widget(character_variant_rect(rect, 1), &self.character_studio.selected_variant_label(), true);
        draw_editor_widget(character_variant_rect(rect, 2), "Variant ›", false);
        draw_scissored_text(
            DEFAULT_UNIVERSAL_LPC_AUTHORITY_PATH,
            rect.x,
            footer.y - 10.0,
            rect.w,
            11.0,
            MUTED,
        );
        draw_editor_widget(footer, "Reload Universal LPC Authority", false);
    }

    pub(crate) fn update_character_studio_input(&mut self) {
        let list = self
            .active_asset_browser_body_rect()
            .unwrap_or_else(|| self.shell_layout().list_content);
        let visible_rows = character_visible_cards(list);
        self.load_visible_character_catalog_thumbnail(list);
        if is_key_pressed(KeyCode::Down) {
            let columns = character_grid_columns(list) as i32;
            self.character_studio
                .cycle_selected_with_rows(columns, visible_rows);
        }
        if is_key_pressed(KeyCode::Up) {
            let columns = character_grid_columns(list) as i32;
            self.character_studio
                .cycle_selected_with_rows(-columns, visible_rows);
        }
        if is_key_pressed(KeyCode::Right) {
            self.character_studio.cycle_selected_with_rows(1, visible_rows);
        }
        if is_key_pressed(KeyCode::Left) {
            self.character_studio.cycle_selected_with_rows(-1, visible_rows);
        }
        if is_key_pressed(KeyCode::PageDown) {
            self.character_studio.page_with_rows(1, visible_rows);
        }
        if is_key_pressed(KeyCode::PageUp) {
            self.character_studio.page_with_rows(-1, visible_rows);
        }
        let pointer = vec2(mouse_position().0, mouse_position().1);
        if list.contains(pointer) {
            let (_, wheel_y) = mouse_wheel();
            if wheel_y.abs() > 0.01 {
                self.character_studio.cycle_selected_with_rows(
                    if wheel_y < 0.0 { 1 } else { -1 },
                    visible_rows,
                );
            }
        }
        if is_key_pressed(KeyCode::R) {
            self.character_studio.reload();
            self.status_message = "Reloaded Universal LPC character authority".to_string();
        }
        self.character_studio.sync_selected_preview();
    }

    pub(crate) fn handle_character_catalog_click_in_rect(&mut self, mouse: Vec2, list: Rect) -> bool {
        for (index, section) in [CharacterCatalogSection::Create, CharacterCatalogSection::WardrobeGear]
            .into_iter()
            .enumerate()
        {
            if character_catalog_section_rect(list, index).contains(mouse) {
                self.character_studio.set_catalog_section(section);
                self.status_message = format!("Character catalog: {}", section.label());
                return true;
            }
        }
        if character_search_rect(list).contains(mouse) {
            self.text_focus = EditorTextFocus::CharacterAssetFilter;
            return true;
        }
        let visible_rows = character_visible_cards(list);
        for row in 0..visible_rows {
            if character_card_rect(list, row).contains(mouse) {
                let index = self.character_studio.list_offset + row;
                self.character_studio.set_selected_with_rows(index, visible_rows);
                self.character_studio.sync_selected_preview();
                return true;
            }
        }
        true
    }

    pub(crate) fn handle_character_studio_click(&mut self, mx: f32, my: f32) -> bool {
        let mouse = vec2(mx, my);
        let list = self.contextual_asset_browser_rect();
        if list.contains(mouse) {
            return self.handle_character_catalog_click_in_rect(mouse, list);
        }

        let host = self.canvas_workspace_layout().workspace_body;
        let (_controls, _preview, c) = character_wardrobe_layout(host);

        if self.character_studio.category_menu_open() {
            if character_category_all_rect(c).contains(mouse) {
                self.character_studio.select_slot_filter(0);
                self.focus_right_dock(super::workspace_shell::RightDockTab::Assets);
                return true;
            }
            for (index, _category) in UNIVERSAL_LPC_CHARACTER_BUILDER_CATEGORIES.into_iter().enumerate() {
                if character_category_option_rect(c, index).contains(mouse) {
                    self.character_studio.select_slot_filter(index + 1);
                    self.focus_right_dock(super::workspace_shell::RightDockTab::Assets);
                    return true;
                }
            }
            if !character_category_menu_rect(c).contains(mouse)
                && !center_button_rect(c, 4, 1, 3).contains(mouse)
            {
                self.character_studio.toggle_category_menu();
            }
        }

        // Character Creator rows exactly mirror draw_character_studio_workspace.
        for (index, mode) in [CharacterStudioMode::Player, CharacterStudioMode::Npc]
            .into_iter()
            .enumerate()
        {
            if center_button_rect(c, 0, index, 2).contains(mouse) {
                self.character_studio.mode = mode;
                self.status_message = self.character_studio.reset_recipe_template(mode);
                self.character_studio.rebuild_filter();
                return true;
            }
        }
        for (index, sex) in SEX_FILTERS.into_iter().enumerate() {
            if center_button_rect(c, 1, index, 2).contains(mouse) {
                self.status_message = self.character_studio.set_sex(sex);
                return true;
            }
        }
        for (index, age) in AGE_FILTERS.into_iter().enumerate() {
            if center_button_rect(c, 2, index, AGE_FILTERS.len()).contains(mouse) {
                self.status_message = self.character_studio.set_age(age);
                return true;
            }
        }
        if self.handle_npc_profile_controls(mouse, c) { return true; }

        if center_button_rect(c, 4, 0, 3).contains(mouse) {
            self.character_studio.cycle_slot(-1);
            return true;
        }
        if center_button_rect(c, 4, 1, 3).contains(mouse) {
            self.character_studio.toggle_category_menu();
            return true;
        }
        if center_button_rect(c, 4, 2, 3).contains(mouse) {
            self.character_studio.cycle_slot(1);
            return true;
        }
        if center_button_rect(c, 5, 0, 3).contains(mouse) {
            self.status_message = self.character_studio.toggle_current_slot_lock();
            return true;
        }
        if center_button_rect(c, 5, 1, 3).contains(mouse) {
            self.status_message = self.character_studio.assign_selected_to_recipe().unwrap_or_else(|error| error);
            return true;
        }
        if center_button_rect(c, 5, 2, 3).contains(mouse) {
            self.status_message = self.character_studio.remove_active_recipe_slot().unwrap_or_else(|error| error);
            return true;
        }
        if center_button_rect(c, 6, 0, 3).contains(mouse) {
            self.status_message = self.character_studio.randomize_recipe_scope("appearance");
            return true;
        }
        if center_button_rect(c, 6, 1, 3).contains(mouse) {
            self.status_message = self.character_studio.randomize_recipe_scope("outfit");
            return true;
        }
        if center_button_rect(c, 6, 2, 3).contains(mouse) {
            self.status_message = self.character_studio.randomize_recipe_scope("unlocked");
            return true;
        }

        if center_button_rect(c, 8, 0, 3).contains(mouse) {
            self.status_message = self.character_studio.cycle_direction(-1);
            return true;
        }
        if center_button_rect(c, 8, 2, 3).contains(mouse) {
            self.status_message = self.character_studio.cycle_direction(1);
            return true;
        }
        if center_button_rect(c, 9, 0, 3).contains(mouse) {
            self.status_message = self.character_studio.cycle_action(-1);
            return true;
        }
        if center_button_rect(c, 9, 2, 3).contains(mouse) {
            self.status_message = self.character_studio.cycle_action(1);
            return true;
        }
        if center_button_rect(c, 10, 0, 2).contains(mouse) {
            self.status_message = self.character_studio.toggle_preview_playback();
            return true;
        }
        if center_button_rect(c, 10, 1, 2).contains(mouse) {
            self.character_studio.restart_preview_animation();
            self.status_message = format!("Restarted {} preview", self.character_studio.action_label());
            return true;
        }

        if center_button_rect(c, 12, 0, 4).contains(mouse) {
            self.status_message = self.character_studio.save_recipe_draft().unwrap_or_else(|error| error);
            return true;
        }
        if center_button_rect(c, 12, 1, 4).contains(mouse) {
            self.status_message = self.character_studio.load_recipe_draft().unwrap_or_else(|error| error);
            return true;
        }
        if center_button_rect(c, 12, 2, 4).contains(mouse) {
            self.status_message = self.character_studio.clear_recipe();
            return true;
        }
        if center_button_rect(c, 12, 3, 4).contains(mouse) {
            self.status_message = self.character_studio.publish_recipe_preset().unwrap_or_else(|error| error);
            return true;
        }
        if center_button_rect(c, 13, 0, 2).contains(mouse) {
            self.status_message = self.character_studio.toggle_layer_view_mode();
            return true;
        }
        if center_button_rect(c, 13, 1, 2).contains(mouse) {
            self.status_message = self.character_studio.toggle_advanced();
            return true;
        }

        if self.character_studio.advanced_open() {
            if center_button_rect(c, 14, 0, 2).contains(mouse) {
                self.character_studio.include_share_alike = false;
                self.character_studio.rebuild_filter();
                return true;
            }
            if center_button_rect(c, 14, 1, 2).contains(mouse) {
                self.character_studio.include_share_alike = true;
                self.character_studio.rebuild_filter();
                return true;
            }
            if center_button_rect(c, 15, 0, 3).contains(mouse) {
                self.status_message = self.character_studio.cycle_palette_variant(-1);
                return true;
            }
            if center_button_rect(c, 15, 2, 3).contains(mouse) {
                self.status_message = self.character_studio.cycle_palette_variant(1);
                return true;
            }
        }

        let inspector = self.inspector_content_rect();
        if character_runtime_context_rect(inspector).contains(mouse) {
            self.open_runtime_context_animation_in_studio();
            return true;
        }
        if character_variant_rect(inspector, 0).contains(mouse) {
            self.status_message = self.character_studio.cycle_selected_variant(-1);
            return true;
        }
        if character_variant_rect(inspector, 2).contains(mouse) {
            self.status_message = self.character_studio.cycle_selected_variant(1);
            return true;
        }
        if character_reload_rect(inspector).contains(mouse) {
            self.character_studio.reload();
            self.status_message = "Reloaded Universal LPC character authority".to_string();
            return true;
        }
        false
    }
}
