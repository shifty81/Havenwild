use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EditorStudioId {
    World,
    Scene,
    Terrain,
    AtlasMapper,
    Pixel,
    Animation,
    Character,
    Building,
    Prefab,
    Pcg,
    Logic,
    Dialogue,
    Sound,
    Project,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct EditorStudioDescriptor {
    pub id: EditorStudioId,
    pub label: String,
    pub integrated: bool,
    #[serde(default)]
    pub legacy_launcher_command: Option<String>,
}

pub fn havenwild_studio_registry() -> Vec<EditorStudioDescriptor> {
    use EditorStudioId::*;
    [
        (World, "World Studio", None),
        (Scene, "Scene Studio", None),
        (Terrain, "Terrain Studio", None),
        (AtlasMapper, "TileSet / Atlas Mapper Studio", Some("assets.atlas-mapper-lite")),
        (Pixel, "Pixel Studio", None),
        (Animation, "Animation Studio", None),
        (Character, "Character Studio", None),
        (Building, "Building Studio", None),
        (Prefab, "Prefab Studio", None),
        (Pcg, "PCG Studio", None),
        (Logic, "Logic Studio", None),
        (Dialogue, "Dialogue Studio", None),
        (Sound, "Sound Studio", None),
        (Project, "Project / Build / Validation", None),
    ]
    .into_iter()
    .map(|(id, label, legacy)| EditorStudioDescriptor {
        id,
        label: label.to_string(),
        integrated: true,
        legacy_launcher_command: legacy.map(str::to_string),
    })
    .collect()
}

pub fn validate_studio_registry(studios: &[EditorStudioDescriptor]) -> Result<(), String> {
    let mut seen = BTreeSet::new();
    for studio in studios {
        if !seen.insert(studio.id) {
            return Err(format!("duplicate studio id: {:?}", studio.id));
        }
        if studio.label.trim().is_empty() {
            return Err(format!("studio {:?} has empty label", studio.id));
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn atlas_mapper_is_an_integrated_studio_with_legacy_launcher_only_as_adapter() {
        let studios = havenwild_studio_registry();
        assert!(validate_studio_registry(&studios).is_ok());
        let mapper = studios.iter().find(|studio| studio.id == EditorStudioId::AtlasMapper).unwrap();
        assert!(mapper.integrated);
        assert_eq!(mapper.legacy_launcher_command.as_deref(), Some("assets.atlas-mapper-lite"));
    }
}
