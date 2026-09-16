use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PlayRequestKind {
    Play,
    PlayFromHere,
    Restart,
    Stop,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PlayRequest {
    pub kind: PlayRequestKind,
    #[serde(default)]
    pub scene_id: Option<String>,
    #[serde(default)]
    pub world_position: Option<[f32; 2]>,
    #[serde(default)]
    pub preserve_editor_selection: bool,
}

impl PlayRequest {
    pub fn validate(&self) -> Result<(), String> {
        if self.kind == PlayRequestKind::PlayFromHere
            && (self.scene_id.is_none() || self.world_position.is_none())
        {
            return Err("play_from_here requires both scene_id and world_position".to_string());
        }
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PlaySessionPhase {
    Stopped,
    Launching,
    Running,
    Stopping,
    Failed,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PlaySessionStatus {
    pub phase: PlaySessionPhase,
    #[serde(default)]
    pub connected: bool,
    #[serde(default)]
    pub active_scene_id: Option<String>,
    #[serde(default)]
    pub last_sequence: u64,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn play_from_here_never_silently_degrades_to_plain_play() {
        let request = PlayRequest {
            kind: PlayRequestKind::PlayFromHere,
            scene_id: None,
            world_position: None,
            preserve_editor_selection: true,
        };
        assert!(request.validate().is_err());
    }
}
