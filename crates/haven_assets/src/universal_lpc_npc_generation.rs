use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::fs::create_dir_all;
use std::path::{Path, PathBuf};

use crate::universal_lpc_character_builder::UniversalLpcCharacterBuilderCatalog;
use crate::universal_lpc_character_recipe::{
    universal_lpc_body_type_for_identity, UniversalLpcCharacterRecipe,
};

pub const DEFAULT_ULPC_NPC_PROFILE_PATH: &str =
    "content/characters/universal_lpc_npc_generation_profiles_v0_1.json";
pub const DEFAULT_ULPC_NPC_PROFILE_VARIANTS_DIR: &str =
    "content/characters/npc_profiles";
pub const ULPC_NPC_PROFILE_VARIANT_SCHEMA: &str =
    "havenwild.universal_lpc_npc_generation_profile_variant.v1";

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UniversalLpcNpcGenerationCatalog {
    pub schema: String,
    pub policy: String,
    pub profiles: Vec<UniversalLpcNpcGenerationProfile>,
    pub authored_npc_rule: String,
}

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UniversalLpcNpcPopulationConstraints {
    #[serde(default)]
    pub minimum: u32,
    #[serde(default)]
    pub maximum: Option<u32>,
    #[serde(default = "default_population_weight")]
    pub weight: u32,
    #[serde(default)]
    pub unique_per_settlement: bool,
    #[serde(default)]
    pub requires_home: bool,
    #[serde(default)]
    pub requires_workplace: bool,
}

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UniversalLpcNpcLifeHooks {
    #[serde(default)]
    pub home_tags: Vec<String>,
    #[serde(default)]
    pub workplace_tags: Vec<String>,
    #[serde(default)]
    pub schedule_tags: Vec<String>,
    #[serde(default)]
    pub relationship_tags: Vec<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UniversalLpcNpcGenerationProfile {
    pub id: String,
    #[serde(default)]
    pub profile_version: u32,
    #[serde(default)]
    pub extends: Option<String>,
    #[serde(default)]
    pub region: String,
    #[serde(default)]
    pub species: Vec<String>,
    #[serde(default)]
    pub pools: Vec<String>,
    #[serde(default)]
    pub age_weights: BTreeMap<String, f32>,
    #[serde(default)]
    pub sex_weights: BTreeMap<String, f32>,
    #[serde(default)]
    pub roles: Vec<String>,
    #[serde(default)]
    pub outfits: Vec<String>,
    #[serde(default)]
    pub factions: Vec<String>,
    #[serde(default)]
    pub wealth_tiers: Vec<String>,
    #[serde(default)]
    pub seasons: Vec<String>,
    #[serde(default)]
    pub wardrobe_categories: Vec<String>,
    #[serde(default)]
    pub equipment_categories: Vec<String>,
    #[serde(default)]
    pub required_animations: Vec<String>,
    #[serde(default)]
    pub forbidden_option_tags: Vec<String>,
    #[serde(default)]
    pub preferred_option_tags: Vec<String>,
    #[serde(default)]
    pub required_option_tags: Vec<String>,
    #[serde(default)]
    pub population: UniversalLpcNpcPopulationConstraints,
    #[serde(default)]
    pub life_hooks: UniversalLpcNpcLifeHooks,
}


#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UniversalLpcNpcProfileVariantFile {
    pub schema: String,
    pub profile: UniversalLpcNpcGenerationProfile,
}

#[derive(Clone, Debug)]
pub struct UniversalLpcNpcGenerationResult {
    pub recipe: UniversalLpcCharacterRecipe,
    pub warnings: Vec<String>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct UniversalLpcNpcPopulationPlanEntry {
    pub profile_id: String,
    pub target_count: u32,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct UniversalLpcNpcPopulationContext {
    /// Empty means any region. Matching is case-insensitive and also accepts
    /// profiles whose region begins with the requested settlement region.
    pub region: Option<String>,
    pub available_site_tags: BTreeSet<String>,
    pub allowed_factions: BTreeSet<String>,
    pub include_hostile_profiles: bool,
}

impl Default for UniversalLpcNpcPopulationContext {
    fn default() -> Self {
        Self {
            region: None,
            available_site_tags: BTreeSet::new(),
            allowed_factions: BTreeSet::new(),
            include_hostile_profiles: true,
        }
    }
}

impl UniversalLpcNpcPopulationContext {
    pub fn willowmere() -> Self {
        Self {
            region: Some("Willowmere".to_string()),
            available_site_tags: [
                "housing", "farm", "ranch", "apiary", "shop", "market", "tavern",
                "workshop", "forge", "tailor", "kitchen", "guard_post", "barracks",
            ]
            .into_iter()
            .map(str::to_string)
            .collect(),
            allowed_factions: ["civilian", "willowmere_civilian", "merchant_guild", "craft_guild", "willowmere_guard"]
                .into_iter()
                .map(str::to_string)
                .collect(),
            include_hostile_profiles: false,
        }
    }
}

impl UniversalLpcNpcGenerationCatalog {
    pub fn load_default() -> Result<Self, String> {
        let root = repo_root_dir();
        let mut catalog = Self::load_from_path(root.join(DEFAULT_ULPC_NPC_PROFILE_PATH))?;
        catalog.merge_profile_variants_from_dir(root.join(DEFAULT_ULPC_NPC_PROFILE_VARIANTS_DIR))?;
        catalog.validate()?;
        Ok(catalog)
    }

    pub fn load_from_path(path: impl AsRef<Path>) -> Result<Self, String> {
        let path = path.as_ref();
        let raw = fs::read_to_string(path)
            .map_err(|error| format!("failed to read {}: {error}", path.display()))?;
        let catalog: Self = serde_json::from_str(&raw)
            .map_err(|error| format!("failed to parse {}: {error}", path.display()))?;
        if catalog.schema != "havenwild.universal_lpc_npc_generation_profiles.v0_1" {
            return Err(format!("unsupported NPC generation schema {}", catalog.schema));
        }
        catalog.validate()?;
        Ok(catalog)
    }

    pub fn merge_profile_variants_from_dir(&mut self, path: impl AsRef<Path>) -> Result<usize, String> {
        let path = path.as_ref();
        if !path.exists() {
            return Ok(0);
        }
        let mut files = fs::read_dir(path)
            .map_err(|error| format!("failed to enumerate {}: {error}", path.display()))?
            .filter_map(Result::ok)
            .map(|entry| entry.path())
            .filter(|entry| entry.extension().and_then(|value| value.to_str()) == Some("json"))
            .collect::<Vec<_>>();
        files.sort();
        let mut merged = 0usize;
        for file in files {
            let raw = fs::read_to_string(&file)
                .map_err(|error| format!("failed to read {}: {error}", file.display()))?;
            let variant: UniversalLpcNpcProfileVariantFile = serde_json::from_str(&raw)
                .map_err(|error| format!("failed to parse {}: {error}", file.display()))?;
            if variant.schema != ULPC_NPC_PROFILE_VARIANT_SCHEMA {
                return Err(format!("unsupported NPC profile variant schema {} in {}", variant.schema, file.display()));
            }
            if let Some(index) = self.profiles.iter().position(|profile| profile.id == variant.profile.id) {
                self.profiles[index] = variant.profile;
            } else {
                self.profiles.push(variant.profile);
            }
            merged += 1;
        }
        Ok(merged)
    }

    pub fn save_profile_variant_default(
        &self,
        profile: &UniversalLpcNpcGenerationProfile,
    ) -> Result<String, String> {
        self.save_profile_variant(DEFAULT_ULPC_NPC_PROFILE_VARIANTS_DIR, profile)
    }

    pub fn save_profile_variant(
        &self,
        directory: impl AsRef<Path>,
        profile: &UniversalLpcNpcGenerationProfile,
    ) -> Result<String, String> {
        let directory = directory.as_ref();
        create_dir_all(directory)
            .map_err(|error| format!("failed to create {}: {error}", directory.display()))?;
        let safe_id = sanitize_profile_filename(&profile.id);
        let path = directory.join(format!("{safe_id}.json"));
        let file = UniversalLpcNpcProfileVariantFile {
            schema: ULPC_NPC_PROFILE_VARIANT_SCHEMA.to_string(),
            profile: profile.clone(),
        };
        let data = serde_json::to_string_pretty(&file)
            .map_err(|error| format!("failed to serialize NPC profile variant {}: {error}", profile.id))?;
        fs::write(&path, format!("{data}\n"))
            .map_err(|error| format!("failed to write {}: {error}", path.display()))?;
        Ok(path.to_string_lossy().to_string())
    }

    pub fn validate(&self) -> Result<(), String> {
        let mut ids = BTreeSet::new();
        for profile in &self.profiles {
            if profile.id.trim().is_empty() {
                return Err("NPC generation profile id must not be empty".to_string());
            }
            if !ids.insert(profile.id.as_str()) {
                return Err(format!("duplicate NPC generation profile {}", profile.id));
            }
            if let Some(maximum) = profile.population.maximum {
                if maximum < profile.population.minimum {
                    return Err(format!(
                        "NPC profile {} population maximum is below minimum",
                        profile.id
                    ));
                }
            }
        }
        for profile in &self.profiles {
            let _ = self.resolved_profile(&profile.id)?;
        }
        Ok(())
    }

    pub fn find(&self, id: &str) -> Option<&UniversalLpcNpcGenerationProfile> {
        self.profiles.iter().find(|profile| profile.id == id)
    }

    /// Resolve data-driven profile inheritance. Empty child collections inherit
    /// their parent; non-empty child collections intentionally replace it. Tag
    /// constraints merge so specialization can add restrictions/preferences.
    pub fn resolved_profile(&self, id: &str) -> Result<UniversalLpcNpcGenerationProfile, String> {
        let mut visiting = BTreeSet::new();
        self.resolve_profile_inner(id, &mut visiting)
    }

    fn resolve_profile_inner(
        &self,
        id: &str,
        visiting: &mut BTreeSet<String>,
    ) -> Result<UniversalLpcNpcGenerationProfile, String> {
        if !visiting.insert(id.to_string()) {
            return Err(format!("NPC profile inheritance cycle detected at {id}"));
        }
        let raw = self
            .find(id)
            .cloned()
            .ok_or_else(|| format!("unknown NPC generation profile {id}"))?;
        let resolved = if let Some(parent_id) = raw.extends.as_deref() {
            let parent = self.resolve_profile_inner(parent_id, visiting)?;
            merge_profiles(parent, raw)
        } else {
            raw
        };
        visiting.remove(id);
        Ok(resolved)
    }

    pub fn generate_recipe(
        &self,
        profile_id: &str,
        seed: u64,
        source_commit: &str,
    ) -> Result<UniversalLpcCharacterRecipe, String> {
        let profile = self.resolved_profile(profile_id)?;
        let age = weighted_choice(&profile.age_weights, mix(seed, 0xA93D_14C7)).unwrap_or("Adult");
        let sex = weighted_choice(&profile.sex_weights, mix(seed, 0x61D2_B933)).unwrap_or("Male");
        let body_type = universal_lpc_body_type_for_identity(sex, age);
        let mut recipe = UniversalLpcCharacterRecipe::new(source_commit, body_type);
        recipe.apply_identity_foundations(sex, age);
        recipe.identity.species = choose_slice(&profile.species, mix(seed, 0x2215_D00D))
            .map(String::as_str)
            .unwrap_or("Human")
            .to_string();
        recipe.identity.age_group = age.to_string();
        recipe.identity.role = choose_slice(&profile.roles, mix(seed, 0x78E4_6A1B))
            .map(String::as_str)
            .unwrap_or("resident")
            .to_string();
        if let Some(outfit) = choose_slice(&profile.outfits, mix(seed, 0xC12C_50A7)) {
            recipe.identity.authored_traits.insert(format!("outfit_profile:{outfit}"));
        }
        if let Some(pool) = choose_slice(&profile.pools, mix(seed, 0x4C50_0A11)) {
            recipe.identity.authored_traits.insert(format!("appearance_pool:{pool}"));
        }
        recipe.identity.authored_traits.insert(format!("npc_profile:{profile_id}"));
        recipe.identity.authored_traits.insert(format!("npc_profile_version:{}", profile.profile_version.max(1)));
        recipe.identity.authored_traits.insert(format!("sex:{sex}"));
        recipe.identity.character_id = Some(format!("npc:{profile_id}:{seed:016x}"));
        recipe.identity.authored_traits.insert(format!("generation_seed:{seed}"));
        if let Some(faction) = choose_slice(&profile.factions, mix(seed, 0xFA47_10A1)) {
            recipe.identity.authored_traits.insert(format!("faction:{faction}"));
        }
        if let Some(wealth) = choose_slice(&profile.wealth_tiers, mix(seed, 0x0EA1_7001)) {
            recipe.identity.authored_traits.insert(format!("wealth:{wealth}"));
        }
        if let Some(season) = choose_slice(&profile.seasons, mix(seed, 0x5EA5_0A11)) {
            recipe.identity.authored_traits.insert(format!("season:{season}"));
        }
        for tag in &profile.life_hooks.home_tags {
            recipe.identity.authored_traits.insert(format!("home:{tag}"));
        }
        for tag in &profile.life_hooks.workplace_tags {
            recipe.identity.authored_traits.insert(format!("workplace:{tag}"));
        }
        for tag in &profile.life_hooks.schedule_tags {
            recipe.identity.authored_traits.insert(format!("schedule:{tag}"));
        }
        recipe.validate()?;
        Ok(recipe)
    }

    pub fn generate_recipe_with_builder(
        &self,
        profile_id: &str,
        seed: u64,
        source_commit: &str,
        builder: &UniversalLpcCharacterBuilderCatalog,
    ) -> Result<UniversalLpcCharacterRecipe, String> {
        Ok(self
            .generate_recipe_with_builder_report(profile_id, seed, source_commit, builder)?
            .recipe)
    }

    pub fn generate_recipe_with_builder_report(
        &self,
        profile_id: &str,
        seed: u64,
        source_commit: &str,
        builder: &UniversalLpcCharacterBuilderCatalog,
    ) -> Result<UniversalLpcNpcGenerationResult, String> {
        let profile = self.resolved_profile(profile_id)?;
        let mut recipe = self.generate_recipe(profile_id, seed, source_commit)?;
        let mut warnings = Vec::new();

        // NPCs and players draw from the same definition-level wardrobe catalog.
        // Foundation is already locked; optional categories are deterministic and
        // profile-constrained. Missing required category coverage is reported.
        let default_wardrobe = ["hair", "eyebrows", "eyes", "torso", "legs", "feet", "hat", "back"];
        let mut categories = if profile.wardrobe_categories.is_empty() {
            default_wardrobe.iter().map(|value| (*value).to_string()).collect::<Vec<_>>()
        } else {
            profile.wardrobe_categories.clone()
        };
        for category in &profile.equipment_categories {
            if !categories.iter().any(|value| value == category) {
                categories.push(category.clone());
            }
        }
        for (index, category) in categories.iter().enumerate() {
            let mut candidates = builder.options_for(category, recipe.body_type)
                .filter(|option| option.is_selectable(false))
                .filter(|option| builder.compatible_option(&recipe, option))
                .filter(|option| profile_allows_option(&profile, option))
                .collect::<Vec<_>>();
            if candidates.is_empty() {
                warnings.push(format!(
                    "profile {profile_id} found no compatible {category} option satisfying {:?}",
                    profile.required_animations
                ));
                continue;
            }
            if !profile.preferred_option_tags.is_empty() {
                let preferred = candidates
                    .iter()
                    .copied()
                    .filter(|option| option_matches_any_tag(option, &profile.preferred_option_tags))
                    .collect::<Vec<_>>();
                if !preferred.is_empty() {
                    candidates = preferred;
                }
            }
            let pick = (mix(seed, 0x1000_0000u64 + index as u64) as usize) % candidates.len();
            let option = candidates[pick];
            let variant = if option.variants.is_empty() {
                None
            } else {
                let variant_index =
                    (mix(seed, 0x2000_0000u64 + index as u64) as usize) % option.variants.len();
                Some(option.variants[variant_index].clone())
            };
            if let Err(error) = builder.select_option(&mut recipe, &option.item_id, variant) {
                warnings.push(format!("{category}: {error}"));
            }
        }
        recipe.validate()?;
        Ok(UniversalLpcNpcGenerationResult { recipe, warnings })
    }

    /// Produce a deterministic settlement-level population target. Profile
    /// minimums are honored first; remaining population is distributed by
    /// profile weight without exceeding per-profile maximums.
    pub fn plan_population(
        &self,
        seed: u64,
        target_population: u32,
    ) -> Result<Vec<UniversalLpcNpcPopulationPlanEntry>, String> {
        self.plan_population_for_context(seed, target_population, &UniversalLpcNpcPopulationContext::default())
    }

    pub fn plan_population_for_context(
        &self,
        seed: u64,
        target_population: u32,
        context: &UniversalLpcNpcPopulationContext,
    ) -> Result<Vec<UniversalLpcNpcPopulationPlanEntry>, String> {
        let mut profiles = self
            .profiles
            .iter()
            .map(|profile| self.resolved_profile(&profile.id))
            .collect::<Result<Vec<_>, _>>()?
            .into_iter()
            .filter(|profile| population_profile_matches_context(profile, context))
            .collect::<Vec<_>>();
        profiles.sort_by(|left, right| left.id.cmp(&right.id));
        if profiles.is_empty() {
            return Err("no NPC generation profiles satisfy the settlement population context".to_string());
        }

        let minimum_total: u32 = profiles.iter().map(|p| p.population.minimum).sum();
        if minimum_total > target_population {
            return Err(format!(
                "population minimums require {minimum_total} NPCs but settlement target is {target_population}"
            ));
        }
        let mut counts = profiles
            .iter()
            .map(|profile| (profile.id.clone(), profile.population.minimum))
            .collect::<BTreeMap<_, _>>();
        let mut remaining = target_population - minimum_total;
        let mut cursor = (mix(seed, 0x50F0_1A71) as usize) % profiles.len().max(1);
        while remaining > 0 && !profiles.is_empty() {
            let mut assigned = false;
            for offset in 0..profiles.len() {
                let index = (cursor + offset) % profiles.len();
                let profile = &profiles[index];
                let current = counts.get(&profile.id).copied().unwrap_or(0);
                let maximum = profile.population.maximum.unwrap_or(u32::MAX);
                if current >= maximum || profile.population.weight == 0 {
                    continue;
                }
                let tickets = profile.population.weight.max(1).min(16);
                let grant = tickets.min(remaining).min(maximum - current);
                *counts.entry(profile.id.clone()).or_default() += grant;
                remaining -= grant;
                cursor = (index + 1) % profiles.len();
                assigned = true;
                if remaining == 0 {
                    break;
                }
            }
            if !assigned {
                break;
            }
        }
        if remaining > 0 {
            return Err(format!(
                "NPC profile population maxima leave {remaining} settlement positions unfilled"
            ));
        }
        Ok(counts
            .into_iter()
            .filter(|(_, target_count)| *target_count > 0)
            .map(|(profile_id, target_count)| UniversalLpcNpcPopulationPlanEntry {
                profile_id,
                target_count,
            })
            .collect())
    }
}

fn merge_profiles(
    parent: UniversalLpcNpcGenerationProfile,
    mut child: UniversalLpcNpcGenerationProfile,
) -> UniversalLpcNpcGenerationProfile {
    if child.profile_version == 0 { child.profile_version = parent.profile_version.max(1); }
    if child.region.is_empty() { child.region = parent.region; }
    inherit_vec(&mut child.species, parent.species);
    inherit_vec(&mut child.pools, parent.pools);
    inherit_map(&mut child.age_weights, parent.age_weights);
    inherit_map(&mut child.sex_weights, parent.sex_weights);
    inherit_vec(&mut child.roles, parent.roles);
    inherit_vec(&mut child.outfits, parent.outfits);
    inherit_vec(&mut child.factions, parent.factions);
    inherit_vec(&mut child.wealth_tiers, parent.wealth_tiers);
    inherit_vec(&mut child.seasons, parent.seasons);
    inherit_vec(&mut child.wardrobe_categories, parent.wardrobe_categories);
    inherit_vec(&mut child.equipment_categories, parent.equipment_categories);
    inherit_vec(&mut child.required_animations, parent.required_animations);
    merge_unique(&mut child.forbidden_option_tags, parent.forbidden_option_tags);
    merge_unique(&mut child.preferred_option_tags, parent.preferred_option_tags);
    merge_unique(&mut child.required_option_tags, parent.required_option_tags);
    if child.population.weight == default_population_weight()
        && child.population.minimum == 0
        && child.population.maximum.is_none()
        && !child.population.unique_per_settlement
        && !child.population.requires_home
        && !child.population.requires_workplace
    {
        child.population = parent.population;
    }
    if child.life_hooks.home_tags.is_empty() { child.life_hooks.home_tags = parent.life_hooks.home_tags; }
    if child.life_hooks.workplace_tags.is_empty() { child.life_hooks.workplace_tags = parent.life_hooks.workplace_tags; }
    if child.life_hooks.schedule_tags.is_empty() { child.life_hooks.schedule_tags = parent.life_hooks.schedule_tags; }
    if child.life_hooks.relationship_tags.is_empty() { child.life_hooks.relationship_tags = parent.life_hooks.relationship_tags; }
    child
}

fn inherit_vec<T>(child: &mut Vec<T>, parent: Vec<T>) {
    if child.is_empty() { *child = parent; }
}

fn inherit_map<K: Ord, V>(child: &mut BTreeMap<K, V>, parent: BTreeMap<K, V>) {
    if child.is_empty() { *child = parent; }
}

fn merge_unique(child: &mut Vec<String>, parent: Vec<String>) {
    for value in parent {
        if !child.iter().any(|existing| existing.eq_ignore_ascii_case(&value)) {
            child.push(value);
        }
    }
}

fn population_profile_matches_context(
    profile: &UniversalLpcNpcGenerationProfile,
    context: &UniversalLpcNpcPopulationContext,
) -> bool {
    if let Some(region) = context.region.as_deref() {
        let requested = region.to_ascii_lowercase();
        let profile_region = profile.region.to_ascii_lowercase();
        if !profile_region.is_empty()
            && profile_region != requested
            && !profile_region.starts_with(&requested)
            && !requested.starts_with(&profile_region)
        {
            return false;
        }
    }
    let hostile = profile.factions.iter().any(|faction| {
        let faction = faction.to_ascii_lowercase();
        faction.contains("hostile") || faction.contains("bandit") || faction.contains("raider")
    });
    if hostile && !context.include_hostile_profiles {
        return false;
    }
    if !context.allowed_factions.is_empty()
        && !profile.factions.is_empty()
        && !profile.factions.iter().any(|faction| {
            context
                .allowed_factions
                .iter()
                .any(|allowed| allowed.eq_ignore_ascii_case(faction))
        })
    {
        return false;
    }
    if !context.available_site_tags.is_empty()
        && profile.population.requires_home
        && !profile.life_hooks.home_tags.is_empty()
        && !profile.life_hooks.home_tags.iter().any(|tag| {
            context
                .available_site_tags
                .iter()
                .any(|available| available.eq_ignore_ascii_case(tag))
        })
    {
        return false;
    }
    if !context.available_site_tags.is_empty()
        && profile.population.requires_workplace
        && !profile.life_hooks.workplace_tags.is_empty()
        && !profile.life_hooks.workplace_tags.iter().any(|tag| {
            context
                .available_site_tags
                .iter()
                .any(|available| available.eq_ignore_ascii_case(tag))
        })
    {
        return false;
    }
    true
}

fn option_matches_any_tag(
    option: &crate::universal_lpc_character_builder::UniversalLpcBuilderOption,
    tags: &[String],
) -> bool {
    tags.iter().any(|tag| {
        let needle = tag.to_ascii_lowercase();
        option.tags.iter().any(|value| value.eq_ignore_ascii_case(&needle))
            || option.item_id.to_ascii_lowercase().contains(&needle)
            || option.display_name.to_ascii_lowercase().contains(&needle)
    })
}

fn profile_allows_option(
    profile: &UniversalLpcNpcGenerationProfile,
    option: &crate::universal_lpc_character_builder::UniversalLpcBuilderOption,
) -> bool {
    if option_matches_any_tag(option, &profile.forbidden_option_tags) {
        return false;
    }
    if !profile.required_option_tags.is_empty()
        && !profile.required_option_tags.iter().all(|tag| option_matches_any_tag(option, std::slice::from_ref(tag)))
    {
        return false;
    }
    profile
        .required_animations
        .iter()
        .all(|required| option.supports_animation(required))
}

fn sanitize_profile_filename(value: &str) -> String {
    let mut out = String::with_capacity(value.len());
    for ch in value.chars() {
        if ch.is_ascii_alphanumeric() || matches!(ch, '_' | '-') {
            out.push(ch.to_ascii_lowercase());
        } else if !out.ends_with('_') {
            out.push('_');
        }
    }
    let trimmed = out.trim_matches('_');
    if trimmed.is_empty() { "npc_profile".to_string() } else { trimmed.to_string() }
}

fn weighted_choice<'a>(weights: &'a BTreeMap<String, f32>, seed: u64) -> Option<&'a str> {
    let total: f64 = weights
        .values()
        .filter(|value| **value > 0.0)
        .map(|value| *value as f64)
        .sum();
    if total <= f64::EPSILON {
        return None;
    }
    let mut cursor = unit(seed) * total;
    for (name, weight) in weights {
        if *weight <= 0.0 {
            continue;
        }
        cursor -= *weight as f64;
        if cursor <= 0.0 {
            return Some(name.as_str());
        }
    }
    weights.keys().next_back().map(String::as_str)
}

fn choose_slice<T>(values: &[T], seed: u64) -> Option<&T> {
    if values.is_empty() {
        return None;
    }
    Some(&values[(seed as usize) % values.len()])
}

fn unit(seed: u64) -> f64 {
    ((mix(seed, 0x9E37_79B9_7F4A_7C15) >> 11) as f64) / ((1u64 << 53) as f64)
}

fn mix(mut value: u64, salt: u64) -> u64 {
    value ^= salt
        .wrapping_add(0x9E37_79B9_7F4A_7C15)
        .wrapping_add(value << 6)
        .wrapping_add(value >> 2);
    value ^= value >> 30;
    value = value.wrapping_mul(0xBF58_476D_1CE4_E5B9);
    value ^= value >> 27;
    value = value.wrapping_mul(0x94D0_49BB_1331_11EB);
    value ^ (value >> 31)
}

const fn default_population_weight() -> u32 { 1 }


fn repo_root_dir() -> PathBuf {
    let current = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
    if current.join("assets").is_dir() && current.join("content").is_dir() {
        return current;
    }
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("..")
        .canonicalize()
        .expect("workspace root should be reachable from haven_assets")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn willowmere_population_context_rejects_hostile_and_off_region_profiles() {
        let catalog = UniversalLpcNpcGenerationCatalog::load_default().expect("profiles");
        let context = UniversalLpcNpcPopulationContext::willowmere();
        let plan = catalog
            .plan_population_for_context(99, 24, &context)
            .expect("Willowmere plan");
        assert!(plan.iter().all(|entry| !entry.profile_id.contains("bandit")));
        assert!(plan.iter().all(|entry| !entry.profile_id.contains("ruins")));
    }

    #[test]
    fn deterministic_choice_is_stable() {
        let values = vec!["a", "b", "c"];
        assert_eq!(choose_slice(&values, 7), choose_slice(&values, 7));
    }
}
