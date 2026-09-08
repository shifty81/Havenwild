use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Path, PathBuf};

use crate::universal_lpc_animation::UniversalLpcBodyType;

pub const DEFAULT_ULPC_SOURCE_ROOT: &str = "assets/source/licensed/universal_lpc_generator";
pub const ULPC_DEFINITION_ROOT: &str = "sheet_definitions";

#[derive(Clone, Debug, Default, PartialEq, Serialize, Deserialize)]
pub struct UniversalLpcLayerDefinition {
    #[serde(default, rename = "zPos")]
    pub z_pos: Option<i32>,
    #[serde(default)]
    pub custom_animation: Option<String>,
    #[serde(flatten)]
    pub body_paths: BTreeMap<String, Value>,
}

impl UniversalLpcLayerDefinition {
    pub fn path_for_body(&self, body: UniversalLpcBodyType) -> Option<&str> {
        self.body_paths.get(body.as_str())?.as_str()
    }
}

#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct UniversalLpcCredit {
    #[serde(default)]
    pub file: String,
    #[serde(default)]
    pub notes: String,
    #[serde(default)]
    pub authors: Vec<String>,
    #[serde(default)]
    pub licenses: Vec<String>,
    #[serde(default)]
    pub urls: Vec<String>,
}

#[derive(Clone, Debug, Default, PartialEq, Serialize, Deserialize)]
pub struct UniversalLpcSheetDefinition {
    #[serde(default)]
    pub ignore: bool,
    #[serde(default)]
    pub name: Option<String>,
    #[serde(default)]
    pub priority: Option<i32>,
    #[serde(default)]
    pub type_name: Option<String>,
    #[serde(default)]
    pub path: Option<Vec<String>>,
    #[serde(default)]
    pub animations: Vec<String>,
    #[serde(default)]
    pub tags: Vec<String>,
    #[serde(default)]
    pub required_tags: Vec<String>,
    #[serde(default)]
    pub excluded_tags: Vec<String>,
    #[serde(default)]
    pub replace_in_path: BTreeMap<String, BTreeMap<String, String>>,
    #[serde(default)]
    pub variants: Vec<String>,
    #[serde(default)]
    pub credits: Vec<UniversalLpcCredit>,
    #[serde(default)]
    pub preview_row: Option<i32>,
    #[serde(default)]
    pub preview_column: Option<i32>,
    #[serde(default)]
    pub preview_x_offset: Option<i32>,
    #[serde(default)]
    pub preview_y_offset: Option<i32>,
    #[serde(default)]
    pub match_body_color: bool,
    #[serde(default)]
    pub aliases: BTreeMap<String, String>,
    #[serde(default)]
    pub recolors: Value,
    #[serde(default)]
    pub layer_1: Option<UniversalLpcLayerDefinition>,
    #[serde(default)]
    pub layer_2: Option<UniversalLpcLayerDefinition>,
    #[serde(default)]
    pub layer_3: Option<UniversalLpcLayerDefinition>,
    #[serde(default)]
    pub layer_4: Option<UniversalLpcLayerDefinition>,
    #[serde(default)]
    pub layer_5: Option<UniversalLpcLayerDefinition>,
    #[serde(default)]
    pub layer_6: Option<UniversalLpcLayerDefinition>,
    #[serde(default)]
    pub layer_7: Option<UniversalLpcLayerDefinition>,
    #[serde(default)]
    pub layer_8: Option<UniversalLpcLayerDefinition>,
    #[serde(default)]
    pub layer_9: Option<UniversalLpcLayerDefinition>,
    #[serde(flatten)]
    pub additional: BTreeMap<String, Value>,
}

impl UniversalLpcSheetDefinition {
    pub fn layers(&self) -> Vec<(usize, &UniversalLpcLayerDefinition)> {
        [
            self.layer_1.as_ref(), self.layer_2.as_ref(), self.layer_3.as_ref(),
            self.layer_4.as_ref(), self.layer_5.as_ref(), self.layer_6.as_ref(),
            self.layer_7.as_ref(), self.layer_8.as_ref(), self.layer_9.as_ref(),
        ]
        .into_iter()
        .enumerate()
        .filter_map(|(index, layer)| layer.map(|layer| (index + 1, layer)))
        .collect()
    }

    pub fn required_body_types(&self) -> BTreeSet<String> {
        let mut out = BTreeSet::new();
        let Some(layer) = self.layer_1.as_ref() else { return out; };
        for body in UniversalLpcBodyType::ALL {
            if layer.path_for_body(body).is_some() {
                out.insert(body.as_str().to_string());
            }
        }
        out
    }

    pub fn validate(&self, source_path: &Path) -> Result<(), String> {
        if self.ignore { return Ok(()); }
        if self.layer_1.is_none() {
            return Err(format!("{} has no layer_1", source_path.display()));
        }
        let mut seen_gap = false;
        for (index, layer) in [
            self.layer_1.as_ref(), self.layer_2.as_ref(), self.layer_3.as_ref(),
            self.layer_4.as_ref(), self.layer_5.as_ref(), self.layer_6.as_ref(),
            self.layer_7.as_ref(), self.layer_8.as_ref(), self.layer_9.as_ref(),
        ].into_iter().enumerate() {
            match layer {
                None => seen_gap = true,
                Some(_) if seen_gap => return Err(format!(
                    "{} has non-contiguous layer_{} after a missing layer",
                    source_path.display(), index + 1
                )),
                Some(_) => {}
            }
        }
        Ok(())
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct UniversalLpcDefinitionRecord {
    pub item_id: String,
    pub definition_path: PathBuf,
    pub definition: UniversalLpcSheetDefinition,
}

#[derive(Clone, Debug, Default, PartialEq)]
pub struct UniversalLpcDefinitionCatalog {
    pub records: Vec<UniversalLpcDefinitionRecord>,
}

impl UniversalLpcDefinitionCatalog {
    pub fn load_default_source() -> Result<Self, String> {
        Self::load_source_root(Path::new(DEFAULT_ULPC_SOURCE_ROOT))
    }

    pub fn load_source_root(source_root: &Path) -> Result<Self, String> {
        let root = source_root.join(ULPC_DEFINITION_ROOT);
        if !root.is_dir() {
            return Err(format!("ULPC definition root is unavailable: {}", root.display()));
        }
        let mut paths = Vec::new();
        collect_json_files(&root, &mut paths)?;
        paths.sort();
        let mut records = Vec::with_capacity(paths.len());
        for path in paths {
            let raw = fs::read_to_string(&path)
                .map_err(|error| format!("failed to read {}: {error}", path.display()))?;
            let definition: UniversalLpcSheetDefinition = serde_json::from_str(&raw)
                .map_err(|error| format!("failed to parse {}: {error}", path.display()))?;
            definition.validate(&path)?;
            if definition.ignore { continue; }
            let relative = path.strip_prefix(source_root).unwrap_or(&path).to_path_buf();
            let item_relative = path.strip_prefix(&root).unwrap_or(&path);
            let item_id = item_relative.with_extension("").to_string_lossy()
                .replace('\\', "/")
                .replace('/', "_");
            if item_id.trim().is_empty() {
                return Err(format!("invalid ULPC definition file name: {}", path.display()));
            }
            records.push(UniversalLpcDefinitionRecord { item_id, definition_path: relative, definition });
        }
        let mut seen = BTreeSet::new();
        for record in &records {
            if !seen.insert(record.item_id.clone()) {
                return Err(format!("duplicate stable ULPC definition item id {}", record.item_id));
            }
        }
        Ok(Self { records })
    }

    pub fn find(&self, item_id: &str) -> Option<&UniversalLpcDefinitionRecord> {
        self.records.iter().find(|record| record.item_id == item_id)
    }

    pub fn by_type_name<'a>(&'a self, type_name: &'a str) -> impl Iterator<Item = &'a UniversalLpcDefinitionRecord> + 'a {
        self.records.iter().filter(move |record| record.definition.type_name.as_deref() == Some(type_name))
    }
}

fn collect_json_files(root: &Path, out: &mut Vec<PathBuf>) -> Result<(), String> {
    for entry in fs::read_dir(root).map_err(|error| format!("failed to scan {}: {error}", root.display()))? {
        let entry = entry.map_err(|error| error.to_string())?;
        let path = entry.path();
        if path.is_dir() {
            collect_json_files(&path, out)?;
        } else if path.extension().and_then(|value| value.to_str()).is_some_and(|ext| ext.eq_ignore_ascii_case("json"))
            && !path.file_name().and_then(|value| value.to_str()).is_some_and(|name| name.starts_with("meta_"))
        {
            out.push(path);
        }
    }
    Ok(())
}
