use crate::EditorSelection;
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EditorDocumentKind {
    World,
    Scene,
    Pixel,
    Animation,
    Character,
    Logic,
    Sound,
    Ui,
    Asset,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct EditorDocumentRef {
    pub id: String,
    pub kind: EditorDocumentKind,
    pub label: String,
    #[serde(default)]
    pub dirty: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum InspectorContextKind {
    Project,
    Document,
    Selection,
    Runtime,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct EditorContextSnapshot {
    pub active_document: Option<EditorDocumentRef>,
    #[serde(default)]
    pub open_documents: Vec<EditorDocumentRef>,
    pub selection: EditorSelection,
    pub inspector: InspectorContextKind,
}

impl Default for EditorContextSnapshot {
    fn default() -> Self {
        Self {
            active_document: None,
            open_documents: Vec::new(),
            selection: EditorSelection::default(),
            inspector: InspectorContextKind::Project,
        }
    }
}

impl EditorContextSnapshot {
    pub fn activate(&mut self, document: EditorDocumentRef) {
        if let Some(existing) = self.open_documents.iter_mut().find(|d| d.id == document.id) {
            *existing = document.clone();
        } else {
            self.open_documents.push(document.clone());
        }
        self.active_document = Some(document);
        self.inspector = if self.selection.is_empty() {
            InspectorContextKind::Document
        } else {
            InspectorContextKind::Selection
        };
    }

    pub fn clear_selection(&mut self) {
        self.selection.clear();
        self.inspector = if self.active_document.is_some() {
            InspectorContextKind::Document
        } else {
            InspectorContextKind::Project
        };
    }

    pub fn mark_active_dirty(&mut self, dirty: bool) {
        let Some(active) = self.active_document.as_mut() else { return; };
        active.dirty = dirty;
        if let Some(open) = self.open_documents.iter_mut().find(|d| d.id == active.id) {
            open.dirty = dirty;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn document_and_inspector_context_move_together() {
        let mut context = EditorContextSnapshot::default();
        context.activate(EditorDocumentRef {
            id: "scene:willowmere".into(),
            kind: EditorDocumentKind::Scene,
            label: "Willowmere".into(),
            dirty: false,
        });
        context.mark_active_dirty(true);
        assert!(context.active_document.as_ref().is_some_and(|d| d.dirty));
        assert_eq!(context.inspector, InspectorContextKind::Document);
    }
}
