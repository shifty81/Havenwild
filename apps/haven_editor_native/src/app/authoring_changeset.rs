use haven_assets::asset_intake::repo_root_dir;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

const CHANGESET_SCHEMA: &str = "havenwild.authoring_changeset.v1";

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub(crate) struct AuthoringChangeEntry {
    pub id: String,
    pub kind: String,
    pub scope: String,
    pub target: String,
    pub revision: String,
    pub output_paths: Vec<String>,
    pub summary: String,
    pub timestamp_unix: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct AuthoringChangeManifest {
    schema: String,
    project: String,
    entries: Vec<AuthoringChangeEntry>,
}

fn current_manifest_path() -> PathBuf {
    repo_root_dir()
        .join("WORKSPACE")
        .join("authoring")
        .join("changesets")
        .join("current")
        .join("manifest.json")
}


pub(crate) fn next_revision(target: &str) -> String {
    let path = current_manifest_path();
    let next = if path.is_file() {
        fs::read_to_string(&path)
            .ok()
            .and_then(|text| serde_json::from_str::<AuthoringChangeManifest>(&text).ok())
            .map(|manifest| manifest.entries.into_iter().filter(|entry| entry.target == target).count() + 1)
            .unwrap_or(1)
    } else {
        1
    };
    format!("v{next:03}")
}

pub(crate) fn record_authoring_change(
    kind: impl Into<String>,
    scope: impl Into<String>,
    target: impl Into<String>,
    revision: impl Into<String>,
    output_paths: Vec<String>,
    summary: impl Into<String>,
) -> Result<String, String> {
    let path = current_manifest_path();
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .map_err(|error| format!("authoring changeset directory failed: {error}"))?;
    }
    let mut manifest = if path.is_file() {
        let text = fs::read_to_string(&path)
            .map_err(|error| format!("authoring changeset read failed: {error}"))?;
        serde_json::from_str::<AuthoringChangeManifest>(&text)
            .unwrap_or_else(|_| AuthoringChangeManifest {
                schema: CHANGESET_SCHEMA.to_string(),
                project: "Havenwild".to_string(),
                entries: Vec::new(),
            })
    } else {
        AuthoringChangeManifest {
            schema: CHANGESET_SCHEMA.to_string(),
            project: "Havenwild".to_string(),
            entries: Vec::new(),
        }
    };
    let timestamp_unix = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_secs())
        .unwrap_or_default();
    let id = format!("authoring-{timestamp_unix}-{:04}", manifest.entries.len() + 1);
    manifest.entries.push(AuthoringChangeEntry {
        id: id.clone(),
        kind: kind.into(),
        scope: scope.into(),
        target: target.into(),
        revision: revision.into(),
        output_paths,
        summary: summary.into(),
        timestamp_unix,
    });
    let text = serde_json::to_string_pretty(&manifest)
        .map_err(|error| format!("authoring changeset serialization failed: {error}"))?;
    fs::write(&path, text)
        .map_err(|error| format!("authoring changeset write failed: {error}"))?;
    Ok(id)
}
