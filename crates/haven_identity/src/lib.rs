//! Havenwild-owned persistent/transient identity boundary.
//!
//! Public project data depends on these Havenwild IDs rather than paths or
//! third-party identifier types. UUID/slotmap adapters can be introduced behind
//! this boundary without changing serialized game/editor contracts.

use serde::{Deserialize, Serialize};
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

static NEXT_ID: AtomicU64 = AtomicU64::new(1);

#[derive(Clone, Debug, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(transparent)]
pub struct HavenId(String);

impl HavenId {
    pub fn new(prefix: &str) -> Self {
        let ticks = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|duration| duration.as_nanos())
            .unwrap_or_default();
        let sequence = NEXT_ID.fetch_add(1, Ordering::Relaxed);
        Self(format!("{}-{ticks:032x}-{sequence:016x}", sanitize_prefix(prefix)))
    }

    pub fn from_string(value: impl Into<String>) -> Result<Self, String> {
        let value = value.into();
        if value.trim().is_empty() {
            return Err("HavenId cannot be empty".to_string());
        }
        Ok(Self(value))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl std::fmt::Display for HavenId {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter.write_str(&self.0)
    }
}

fn sanitize_prefix(prefix: &str) -> String {
    let value: String = prefix
        .chars()
        .filter(|character| character.is_ascii_alphanumeric() || *character == '_' || *character == '-')
        .map(|character| character.to_ascii_lowercase())
        .collect();
    if value.is_empty() { "id".to_string() } else { value }
}

pub type AssetId = HavenId;
pub type DocumentId = HavenId;
pub type SceneInstanceId = HavenId;
pub type AuthoringSessionId = HavenId;
pub type RevisionId = HavenId;
pub type StampId = HavenId;
pub type TemplateId = HavenId;
pub type ExemplarId = HavenId;
pub type RigNodeId = HavenId;
pub type BehaviorGraphId = HavenId;
pub type SoundEventId = HavenId;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn generated_ids_are_unique_and_prefixed() {
        let left = HavenId::new("Document");
        let right = HavenId::new("Document");
        assert_ne!(left, right);
        assert!(left.as_str().starts_with("document-"));
    }

    #[test]
    fn empty_ids_are_rejected() {
        assert!(HavenId::from_string(" ").is_err());
    }
}
