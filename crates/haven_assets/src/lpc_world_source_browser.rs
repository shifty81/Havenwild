use crate::asset_intake::repo_root_dir;
use serde::Deserialize;
use std::fs::read_to_string;

pub const LPC_WORLD_SOURCE_BROWSER_PATH: &str =
    "content/editor/assets/lpc_world_source_browser_v1.json";

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LpcWorldSourceBrowserCatalog {
    schema: String,
    pub entries: Vec<LpcWorldSourceBrowserEntry>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LpcWorldSourceBrowserEntry {
    pub stable_id: String,
    pub display_name: String,
    pub semantic_path: String,
    pub category: String,
    pub source_path: String,
    #[serde(default)]
    pub production_state: String,
    #[serde(default)]
    pub keywords: Vec<String>,
}

impl LpcWorldSourceBrowserCatalog {
    pub fn load_default() -> Result<Self, String> {
        let path = repo_root_dir().join(LPC_WORLD_SOURCE_BROWSER_PATH);
        let raw = read_to_string(&path)
            .map_err(|error| format!("failed to read {}: {error}", path.display()))?;
        let catalog: Self = serde_json::from_str(&raw)
            .map_err(|error| format!("failed to parse {}: {error}", path.display()))?;
        if catalog.schema != "havenwild.editor.lpc_world_source_browser.v1" {
            return Err(format!(
                "unsupported LPC world source browser schema {}",
                catalog.schema
            ));
        }
        Ok(catalog)
    }
}
