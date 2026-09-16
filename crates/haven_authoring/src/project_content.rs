use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ProjectContentKind {
    Folder,
    Scene,
    Asset,
    Document,
    SourceSheet,
    Script,
    Data,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ProjectContentRef {
    pub id: String,
    pub kind: ProjectContentKind,
    pub relative_path: String,
    #[serde(default)]
    pub asset_id: Option<String>,
    #[serde(default)]
    pub read_only: bool,
    #[serde(default)]
    pub external_source: bool,
}

#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ProjectContentQuery {
    #[serde(default)]
    pub search: String,
    #[serde(default)]
    pub include_external_sources: bool,
    #[serde(default)]
    pub kinds: Vec<ProjectContentKind>,
}

impl ProjectContentQuery {
    pub fn matches(&self, item: &ProjectContentRef) -> bool {
        if item.external_source && !self.include_external_sources {
            return false;
        }
        if !self.kinds.is_empty() && !self.kinds.contains(&item.kind) {
            return false;
        }
        let needle = self.search.trim().to_ascii_lowercase();
        needle.is_empty()
            || item.id.to_ascii_lowercase().contains(&needle)
            || item.relative_path.to_ascii_lowercase().contains(&needle)
            || item
                .asset_id
                .as_deref()
                .is_some_and(|id| id.to_ascii_lowercase().contains(&needle))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn project_files_and_asset_browser_share_one_query_contract() {
        let item = ProjectContentRef {
            id: "terrain.grass.summer".into(),
            kind: ProjectContentKind::Asset,
            relative_path: "content/assets/grass.json".into(),
            asset_id: Some("terrain.grass.summer".into()),
            read_only: false,
            external_source: false,
        };
        let query = ProjectContentQuery { search: "grass".into(), ..Default::default() };
        assert!(query.matches(&item));
    }
}
