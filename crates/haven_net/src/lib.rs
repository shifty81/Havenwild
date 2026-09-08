use haven_authoring::EditorCommand;
use serde::{Deserialize, Serialize};

pub const ARCHITECTURE_STATUS: &str =
    "Active networking contract crate for authority and replication envelopes; future listen-server transport and replication systems will build on these contracts.";

pub use haven_world::{GameWorld, SceneId};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum AuthorityDomain {
    RuntimeWorld,
    EditorOverlay,
    ContentPipeline,
}

impl AuthorityDomain {
    pub fn label(self) -> &'static str {
        match self {
            AuthorityDomain::RuntimeWorld => "runtime_world",
            AuthorityDomain::EditorOverlay => "editor_overlay",
            AuthorityDomain::ContentPipeline => "content_pipeline",
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReplicationEnvelope {
    pub sequence: u64,
    pub authority: AuthorityDomain,
    pub command_id: String,
    pub command_type: String,
    pub source: String,
    pub project_id: String,
    pub scene_id: Option<String>,
    pub payload_summary: String,
}

impl ReplicationEnvelope {
    pub fn status_line(&self) -> String {
        format!(
            "Net seq {} [{}] {}",
            self.sequence,
            self.authority.label(),
            self.payload_summary
        )
    }
}

pub fn replicate_editor_command(sequence: u64, command: &EditorCommand) -> ReplicationEnvelope {
    ReplicationEnvelope {
        sequence,
        authority: AuthorityDomain::EditorOverlay,
        command_id: command.command_id.clone(),
        command_type: command.command_type.clone(),
        source: format!("{:?}", command.source),
        project_id: command.target.project_id.clone(),
        scene_id: command.target.scene_id.clone(),
        payload_summary: command.payload.description.clone(),
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct CharacterWorldStateSnapshot {
    pub sequence: u64,
    pub world_id: String,
    pub character_id: String,
    pub scene_id: String,
    pub tile_position: [i32; 2],
    pub global_reputation: i32,
    pub relationship_count: usize,
    pub quest_flag_count: usize,
    pub last_played_unix_seconds: u64,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum CharacterStateAuthority {
    Host,
    ClientReplica,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct CharacterWorldStateEnvelope {
    pub authority: CharacterStateAuthority,
    pub snapshot: CharacterWorldStateSnapshot,
    pub reason: String,
}

impl CharacterWorldStateEnvelope {
    pub fn host(snapshot: CharacterWorldStateSnapshot, reason: impl Into<String>) -> Self {
        Self {
            authority: CharacterStateAuthority::Host,
            snapshot,
            reason: reason.into(),
        }
    }

    pub fn validate_for_client(&self, last_applied_sequence: u64) -> Result<(), String> {
        if self.authority != CharacterStateAuthority::Host {
            return Err("character-world state mutation was not issued by the host".to_string());
        }
        if self.snapshot.sequence <= last_applied_sequence {
            return Err(format!(
                "stale character-world state sequence {} (last applied {})",
                self.snapshot.sequence, last_applied_sequence
            ));
        }
        if self.snapshot.world_id.trim().is_empty() || self.snapshot.character_id.trim().is_empty()
        {
            return Err("character-world state envelope has an empty identity".to_string());
        }
        Ok(())
    }
}
