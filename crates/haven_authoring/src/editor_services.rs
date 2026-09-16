use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EditorServiceKind {
    Commands,
    Documents,
    Selection,
    Transactions,
    ProjectContent,
    Assets,
    Jobs,
    Problems,
    RuntimeBridge,
    Persistence,
    StudioRegistry,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct EditorServiceDescriptor {
    pub kind: EditorServiceKind,
    pub authority: String,
    pub shared: bool,
}

pub fn canonical_editor_services() -> Vec<EditorServiceDescriptor> {
    use EditorServiceKind::*;
    [
        Commands,
        Documents,
        Selection,
        Transactions,
        ProjectContent,
        Assets,
        Jobs,
        Problems,
        RuntimeBridge,
        Persistence,
        StudioRegistry,
    ]
    .into_iter()
    .map(|kind| EditorServiceDescriptor {
        kind,
        authority: match kind {
            Commands => "haven_authoring::editor_actions",
            Documents => "haven_authoring::editor_context",
            Selection => "haven_authoring::selection",
            Transactions => "haven_authoring::transactions",
            ProjectContent => "haven_authoring::project_content",
            Assets => "haven_assets",
            Jobs | Problems => "haven_authoring::editor_operations",
            RuntimeBridge => "haven_authoring::play_bridge",
            Persistence => "haven_save",
            StudioRegistry => "haven_authoring::studio_registry",
        }
        .to_string(),
        shared: true,
    })
    .collect()
}

pub fn validate_editor_service_registry(services: &[EditorServiceDescriptor]) -> Result<(), String> {
    let mut seen = BTreeSet::new();
    for service in services {
        if !seen.insert(service.kind) {
            return Err(format!("duplicate editor service authority: {:?}", service.kind));
        }
        if service.authority.trim().is_empty() {
            return Err(format!("editor service {:?} has empty authority", service.kind));
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn canonical_service_registry_has_one_owner_per_service() {
        let services = canonical_editor_services();
        assert_eq!(services.len(), 11);
        assert!(validate_editor_service_registry(&services).is_ok());
    }
}
