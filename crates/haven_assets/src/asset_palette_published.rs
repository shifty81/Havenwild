use super::*;
use crate::placeable_asset_registry::{
    PublishedWorldAssetCertification, PublishedWorldAssetRegistry,
};

impl AssetPaletteCatalog {
    /// Adds every runtime-ready published world asset as its own browser card.
    ///
    /// Published assets retain their stable registry identity even when they
    /// expose a legacy `ObjectKind` compatibility adapter. The editor can
    /// therefore select/place the exact promoted tree, prop, door, furnishing,
    /// or structure component instead of collapsing the choice back to a
    /// generic object brush.
    pub fn extend_published_placeables(&mut self, registry: &PublishedWorldAssetRegistry) {
        let root = repo_root_dir();
        let existing = self
            .entries
            .iter()
            .map(|entry| entry.stable_id.clone())
            .collect::<BTreeSet<_>>();
        let mut appended = Vec::new();
        for definition in registry.entries() {
            if existing.contains(&definition.stable_id)
                || matches!(
                    definition.certification,
                    PublishedWorldAssetCertification::Missing
                        | PublishedWorldAssetCertification::Rejected
                )
            {
                continue;
            }
            let Some(source_path) = definition.source_path.as_ref() else {
                continue;
            };
            let Some(frame) = definition
                .visual
                .as_ref()
                .and_then(|visual| visual.frame_for_state(definition.initial_state()))
            else {
                continue;
            };
            let sheet = source_path.to_string_lossy().replace('\\', "/");
            let [x, y, w, h] = frame.source_rect;
            let mut keywords = vec![
                "published asset".to_string(),
                "runtime ready".to_string(),
                definition.semantic_id.replace('.', " ").replace('_', " "),
            ];
            keywords.extend(definition.placement_tags.iter().cloned());
            appended.push(AssetPaletteEntry {
                stable_id: definition.stable_id.clone(),
                label: definition.label.clone(),
                category: category_for_object(definition.compatibility_kind()),
                kind: AssetPaletteKind::Object(definition.compatibility_kind()),
                sheet: Some(sheet.clone()),
                rect: Some(AtlasRect { x, y, w, h }),
                provenance: AssetProvenance::ProjectOwnedImport,
                warning: (!root.join(&sheet).is_file())
                    .then(|| format!("missing published source {sheet}")),
                keywords,
            });
        }
        self.entries.extend(appended);
        self.entries.sort_by(|left, right| {
            left.category
                .label()
                .cmp(right.category.label())
                .then_with(|| left.label.cmp(&right.label))
                .then_with(|| left.stable_id.cmp(&right.stable_id))
        });
    }
}
