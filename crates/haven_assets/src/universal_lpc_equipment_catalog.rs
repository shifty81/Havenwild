use serde::Deserialize;
use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

pub const DEFAULT_UNIVERSAL_LPC_EQUIPMENT_CATALOG_PATH: &str =
    "content/assets/lpc/universal_lpc_equipment_action_catalog_v0_1.json";
pub const DEFAULT_UNIVERSAL_LPC_EQUIPMENT_ITEM_SEED_CATALOG_PATH: &str =
    "content/gameplay/universal_lpc_equipment_item_seed_catalog_v0_1.json";

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UniversalLpcEquipmentCatalog {
    pub schema: String,
    pub source_commit: String,
    #[serde(default)]
    pub records: Vec<UniversalLpcEquipmentRecord>,
    #[serde(default)]
    pub tool_bindings: BTreeMap<String, Vec<String>>,
    #[serde(default)]
    pub runtime_policy: String,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UniversalLpcEquipmentRecord {
    pub stable_id: String,
    pub source_path: String,
    #[serde(default)]
    pub roles: Vec<String>,
    #[serde(default)]
    pub body_families: Vec<String>,
    #[serde(default)]
    pub animations: Vec<String>,
    #[serde(default)]
    pub tool_id: Option<String>,
    #[serde(default)]
    pub credit_record_indices: Vec<usize>,
    #[serde(default)]
    pub production_state: String,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UniversalLpcEquipmentItemSeedCatalog {
    pub schema: String,
    pub source_catalog: String,
    pub item_count: usize,
    #[serde(default)]
    pub items: Vec<UniversalLpcEquipmentItemSeed>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UniversalLpcEquipmentItemSeed {
    pub item_id: String,
    pub display_name: String,
    pub equipment_source_id: String,
    pub category: String,
    pub subcategory: String,
    pub gameplay_action: String,
    pub stack_limit: usize,
    pub starter_granted: bool,
    #[serde(default)]
    pub acquisition: Vec<String>,
}

impl UniversalLpcEquipmentCatalog {
    pub fn load_default() -> Result<Self, String> {
        Self::load_from_path(resolve_default_catalog_path(
            DEFAULT_UNIVERSAL_LPC_EQUIPMENT_CATALOG_PATH,
        ))
    }

    pub fn load_from_path(path: impl AsRef<Path>) -> Result<Self, String> {
        let path = path.as_ref();
        let text = fs::read_to_string(path)
            .map_err(|error| format!("failed to read {}: {error}", path.display()))?;
        let catalog: Self = serde_json::from_str(&text)
            .map_err(|error| format!("failed to parse {}: {error}", path.display()))?;
        catalog.validate()?;
        Ok(catalog)
    }

    pub fn validate(&self) -> Result<(), String> {
        if self.schema != "havenwild.universal_lpc.equipment_action_catalog.v0_1" {
            return Err(format!("unsupported Universal LPC equipment schema: {}", self.schema));
        }
        if self.source_commit.trim().is_empty() {
            return Err("Universal LPC equipment catalog must retain a source commit".into());
        }
        if self.records.is_empty() {
            return Err("Universal LPC equipment action catalog has no compatibility records".into());
        }
        for record in &self.records {
            if record.stable_id.trim().is_empty() || !record.source_path.starts_with("spritesheets/") {
                return Err(format!("invalid Universal LPC equipment record: {}", record.stable_id));
            }
        }
        Ok(())
    }

    pub fn find_record(&self, stable_id: &str) -> Option<&UniversalLpcEquipmentRecord> {
        self.records.iter().find(|record| record.stable_id == stable_id)
    }

    pub fn compatible_records<'a>(
        &'a self,
        body_family: &'a str,
        animation: &'a str,
    ) -> impl Iterator<Item = &'a UniversalLpcEquipmentRecord> + 'a {
        self.records.iter().filter(move |record| {
            record.body_families.iter().any(|value| value == body_family)
                && record.animations.iter().any(|value| value == animation)
        })
    }

    pub fn tool_records<'a>(&'a self, tool_id: &'a str) -> impl Iterator<Item = &'a UniversalLpcEquipmentRecord> + 'a {
        self.tool_bindings
            .get(tool_id)
            .into_iter()
            .flatten()
            .filter_map(move |stable_id| self.find_record(stable_id))
    }
}

impl UniversalLpcEquipmentItemSeedCatalog {
    pub fn load_default() -> Result<Self, String> {
        Self::load_from_path(resolve_default_catalog_path(
            DEFAULT_UNIVERSAL_LPC_EQUIPMENT_ITEM_SEED_CATALOG_PATH,
        ))
    }

    pub fn load_from_path(path: impl AsRef<Path>) -> Result<Self, String> {
        let path = path.as_ref();
        let text = fs::read_to_string(path)
            .map_err(|error| format!("failed to read {}: {error}", path.display()))?;
        let catalog: Self = serde_json::from_str(&text)
            .map_err(|error| format!("failed to parse {}: {error}", path.display()))?;
        catalog.validate()?;
        Ok(catalog)
    }

    pub fn validate(&self) -> Result<(), String> {
        if self.schema != "havenwild.universal_lpc_equipment_item_seed_catalog.v0_1" {
            return Err(format!("unsupported Universal LPC item seed schema: {}", self.schema));
        }
        if self.item_count != self.items.len() {
            return Err(format!(
                "Universal LPC item seed count mismatch: declared {}, loaded {}",
                self.item_count,
                self.items.len()
            ));
        }
        if self.item_count != 105 {
            return Err(format!("Universal LPC equipment seed authority must currently contain 105 definitions, got {}", self.item_count));
        }
        Ok(())
    }

    pub fn find(&self, item_id: &str) -> Option<&UniversalLpcEquipmentItemSeed> {
        self.items.iter().find(|item| item.item_id == item_id)
    }

    pub fn by_gameplay_action<'a>(&'a self, action: &'a str) -> impl Iterator<Item = &'a UniversalLpcEquipmentItemSeed> + 'a {
        self.items.iter().filter(move |item| item.gameplay_action.eq_ignore_ascii_case(action))
    }
}

fn resolve_default_catalog_path(relative: &str) -> PathBuf {
    let relative = Path::new(relative);
    if relative.is_absolute() {
        return relative.to_path_buf();
    }

    if let Ok(current_dir) = std::env::current_dir() {
        if let Some(path) = find_project_relative_file(&current_dir, relative) {
            return path;
        }
    }

    if let Ok(executable) = std::env::current_exe() {
        if let Some(parent) = executable.parent() {
            if let Some(path) = find_project_relative_file(parent, relative) {
                return path;
            }
        }
    }

    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join(relative)
}

fn find_project_relative_file(start: &Path, relative: &Path) -> Option<PathBuf> {
    start
        .ancestors()
        .map(|candidate| candidate.join(relative))
        .find(|candidate| candidate.is_file())
}

#[cfg(test)]
mod tests {
    use std::path::Path;

    #[test]
    fn generated_action_catalog_path_matches_the_file_it_loads() {
        assert_eq!(
            super::DEFAULT_UNIVERSAL_LPC_EQUIPMENT_CATALOG_PATH,
            "content/assets/lpc/universal_lpc_equipment_action_catalog_v0_1.json"
        );
    }

    #[test]
    fn default_catalog_resolution_walks_from_nested_runtime_directories() {
        let nested_runtime = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../target/debug/deps");
        let resolved = super::find_project_relative_file(
            &nested_runtime,
            Path::new(super::DEFAULT_UNIVERSAL_LPC_EQUIPMENT_ITEM_SEED_CATALOG_PATH),
        )
        .expect("runtime-style nested path should resolve the project catalog");
        assert!(resolved.is_file());
        assert!(resolved.ends_with(super::DEFAULT_UNIVERSAL_LPC_EQUIPMENT_ITEM_SEED_CATALOG_PATH));
    }

    #[test]
    fn default_item_seed_catalog_loads_through_runtime_root_resolution() {
        let catalog = super::UniversalLpcEquipmentItemSeedCatalog::load_default()
            .expect("default Universal LPC item seed catalog should load");
        assert_eq!(catalog.item_count, 105);
        assert_eq!(catalog.items.len(), 105);
    }
}
