use haven_identity::{AuthoringSessionId, RevisionId};
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PublishTarget {
    ApplyHere,
    Variation,
    Asset,
    StampMotif,
    Template,
    PresentationSet,
    PcgExemplar,
    PcgMotifs,
}

impl PublishTarget {
    pub const ALL: [Self; 8] = [
        Self::ApplyHere,
        Self::Variation,
        Self::Asset,
        Self::StampMotif,
        Self::Template,
        Self::PresentationSet,
        Self::PcgExemplar,
        Self::PcgMotifs,
    ];

    pub fn label(self) -> &'static str {
        match self {
            Self::ApplyHere => "Apply Here",
            Self::Variation => "Save Variation",
            Self::Asset => "Promote Asset",
            Self::StampMotif => "Create Stamp / Motif",
            Self::Template => "Create Template",
            Self::PresentationSet => "Presentation Set",
            Self::PcgExemplar => "Create PCG Exemplar",
            Self::PcgMotifs => "Extract PCG Motifs",
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AuthoringSourceKind {
    Asset,
    SceneSelection,
    WorldSelection,
    BuildingComposite,
    Animation,
    Character,
    Foreground,
    Sound,
    Logic,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AuthoringSource {
    pub kind: AuthoringSourceKind,
    pub label: String,
    #[serde(default)]
    pub scene_id: Option<String>,
    #[serde(default)]
    pub world_rect: Option<[i32; 4]>,
    #[serde(default)]
    pub asset_ids: Vec<String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AuthoringSession {
    pub schema: String,
    pub id: AuthoringSessionId,
    pub revision: RevisionId,
    pub source: AuthoringSource,
    pub publish_targets: BTreeSet<PublishTarget>,
    #[serde(default)]
    pub validation_messages: Vec<String>,
}

impl AuthoringSession {
    pub fn new(source: AuthoringSource) -> Self {
        let mut publish_targets = BTreeSet::new();
        publish_targets.insert(PublishTarget::ApplyHere);
        Self {
            schema: "havenwild.authoring_session.v1".to_string(),
            id: AuthoringSessionId::new("authoring_session"),
            revision: RevisionId::new("authoring_revision"),
            source,
            publish_targets,
            validation_messages: Vec::new(),
        }
    }

    pub fn enable_publish_everywhere(&mut self) {
        self.publish_targets.extend(PublishTarget::ALL);
    }

    pub fn toggle_target(&mut self, target: PublishTarget) {
        if !self.publish_targets.remove(&target) {
            self.publish_targets.insert(target);
        }
    }

    pub fn can_publish(&self) -> bool {
        self.validation_messages.is_empty() && !self.publish_targets.is_empty()
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PublishPreview {
    pub session_id: String,
    pub revision_id: String,
    pub targets: Vec<PublishTarget>,
    pub summary: Vec<String>,
}

impl From<&AuthoringSession> for PublishPreview {
    fn from(session: &AuthoringSession) -> Self {
        Self {
            session_id: session.id.to_string(),
            revision_id: session.revision.to_string(),
            targets: session.publish_targets.iter().copied().collect(),
            summary: session
                .publish_targets
                .iter()
                .map(|target| target.label().to_string())
                .collect(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn publish_everywhere_enables_all_targets() {
        let mut session = AuthoringSession::new(AuthoringSource {
            kind: AuthoringSourceKind::WorldSelection,
            label: "test".to_string(),
            scene_id: None,
            world_rect: Some([0, 0, 4, 4]),
            asset_ids: Vec::new(),
        });
        session.enable_publish_everywhere();
        assert_eq!(session.publish_targets.len(), PublishTarget::ALL.len());
    }
}
