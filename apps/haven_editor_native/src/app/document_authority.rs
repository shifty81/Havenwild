#![allow(dead_code)] // AUTH-01/02 migration contracts are consumed incrementally.
use super::*;

/// Stable resource identity. Presentation hosts must not be used as document identity.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub(crate) struct DocumentId(pub String);

#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub(crate) struct DocumentHostId(pub String);

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum DocumentKind { Scene, Ui, Pixel, Animation, Character, Logic, Sound, World }

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum DocumentSaveState { Clean, Dirty }

#[derive(Clone, Debug)]
pub(crate) struct DocumentRecord {
    pub id: DocumentId,
    pub host: DocumentHostId,
    pub kind: DocumentKind,
    pub display_name: String,
    pub writable: bool,
    pub save_state: DocumentSaveState,
}

#[derive(Clone, Debug, Default)]
pub(crate) struct DocumentRegistrySnapshot { pub documents: Vec<DocumentRecord> }

impl EditorApp {
    /// AUTH-02 adapter registry. Domain owners retain their documents; this is only
    /// a lifecycle/index snapshot and therefore cannot become a second source of truth.
    pub(crate) fn document_registry_snapshot(&self) -> DocumentRegistrySnapshot {
        let mut documents = Vec::new();
        if let Some(scene_id) = self.active_scene_id() {
            let dirty = self.scene_document_dirty_ids.contains(&scene_id)
                || (self.command_bus.undo_len() != self.saved_undo_depth);
            documents.push(DocumentRecord {
                id: DocumentId(format!("scene:{}", scene_id)), host: DocumentHostId("game-canvas".into()),
                kind: DocumentKind::Scene, display_name: scene_id.label(), writable: true,
                save_state: if dirty { DocumentSaveState::Dirty } else { DocumentSaveState::Clean },
            });
        }
        for info in self.pixel_studio.document_tab_info() {
            documents.push(DocumentRecord {
                id: DocumentId(format!("pixel:{}", info.index)), host: DocumentHostId(format!("pixel-tab:{}", info.index)),
                kind: DocumentKind::Pixel, display_name: info.label, writable: true,
                save_state: if info.dirty { DocumentSaveState::Dirty } else { DocumentSaveState::Clean },
            });
        }
        if let Some(document) = self.animation_studio.document.as_ref() {
            documents.push(DocumentRecord {
                id: DocumentId(format!("animation:{}", document.metadata.output_path)), host: DocumentHostId("animation-studio".into()),
                kind: DocumentKind::Animation, display_name: document.metadata.display_name.clone(), writable: true,
                save_state: if document.dirty { DocumentSaveState::Dirty } else { DocumentSaveState::Clean },
            });
        }
        documents.push(DocumentRecord {
            id: DocumentId("character:working-recipe".into()), host: DocumentHostId("character-studio".into()), kind: DocumentKind::Character,
            display_name: "Character Studio Recipe".into(), writable: true,
            save_state: if self.character_studio.dirty() { DocumentSaveState::Dirty } else { DocumentSaveState::Clean },
        });
        documents.push(DocumentRecord {
            id: DocumentId(format!("logic:{}", self.logic_studio.graph.id)), host: DocumentHostId("logic-studio".into()), kind: DocumentKind::Logic,
            display_name: self.logic_studio.graph.display_name.clone(), writable: true,
            save_state: if self.logic_studio.dirty { DocumentSaveState::Dirty } else { DocumentSaveState::Clean },
        });
        documents.push(DocumentRecord {
            id: DocumentId(format!("sound:{}", self.sound_studio.document.id)), host: DocumentHostId("sound-studio".into()), kind: DocumentKind::Sound,
            display_name: self.sound_studio.document.display_name.clone(), writable: true,
            save_state: if self.sound_studio.dirty { DocumentSaveState::Dirty } else { DocumentSaveState::Clean },
        });
        DocumentRegistrySnapshot { documents }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn document_and_host_identity_are_distinct() {
        assert_ne!(DocumentId("asset:a".into()).0, DocumentHostId("pixel-tab:0".into()).0);
    }
    #[test] fn lifecycle_kinds_cover_specialized_authoring_domains() {
        let kinds = [DocumentKind::Scene, DocumentKind::Ui, DocumentKind::Pixel, DocumentKind::Animation, DocumentKind::Character, DocumentKind::Logic, DocumentKind::Sound, DocumentKind::World];
        assert_eq!(kinds.len(), 8);
    }
}
