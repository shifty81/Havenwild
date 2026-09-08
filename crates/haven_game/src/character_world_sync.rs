use super::*;
use haven_net::{CharacterWorldStateEnvelope, CharacterWorldStateSnapshot};

const CHARACTER_AUTOSAVE_INTERVAL_SECONDS: f64 = 120.0;

impl Game {
    pub(super) fn update_character_world_autosave(&mut self, now: f64) {
        if now < self.character_autosave_next_at {
            return;
        }
        self.character_autosave_next_at = now + CHARACTER_AUTOSAVE_INTERVAL_SECONDS;
        if let Err(error) = self.persist_character_world_state("autosave") {
            self.log
                .event(&format!("Character-world autosave failed: {error}"));
            return;
        }
        let envelope = self.host_character_world_state_envelope("autosave");
        self.last_replication_status = format!(
            "Character state seq {} prepared for host replication",
            envelope.snapshot.sequence
        );
    }

    pub(super) fn host_character_world_state_envelope(
        &mut self,
        reason: &str,
    ) -> CharacterWorldStateEnvelope {
        self.character_state_sequence = self.character_state_sequence.saturating_add(1);
        CharacterWorldStateEnvelope::host(
            CharacterWorldStateSnapshot {
                sequence: self.character_state_sequence,
                world_id: self.world_id.0.clone(),
                character_id: self.character_id.0.clone(),
                scene_id: self.world.active_scene.code().to_string(),
                tile_position: if self.world.active().kind == SceneKind::Exterior {
                    {
                        let tile = self.surface_global_tile();
                        [tile.x, tile.y]
                    }
                } else {
                    [
                        (self.player.x / TILE_SIZE).floor() as i32,
                        (self.player.y / TILE_SIZE).floor() as i32,
                    ]
                },
                global_reputation: self.reputation,
                relationship_count: self.character_world_link.world_relationships.len(),
                quest_flag_count: self.character_world_link.world_quest_flags.len(),
                last_played_unix_seconds: self.character_world_link.last_played_unix_seconds,
            },
            reason,
        )
    }

    #[expect(
        dead_code,
        reason = "listen-server transport adapter is not connected yet"
    )]
    pub(super) fn apply_replicated_character_world_state(
        &mut self,
        envelope: &CharacterWorldStateEnvelope,
    ) -> Result<(), String> {
        envelope.validate_for_client(self.last_applied_character_state_sequence)?;
        if envelope.snapshot.world_id != self.world_id.0
            || envelope.snapshot.character_id != self.character_id.0
        {
            return Err(
                "character-world state envelope targets another runtime identity".to_string(),
            );
        }
        let scene = SceneReference::new(envelope.snapshot.scene_id.clone());
        if self.world.scene_by_reference(&scene).is_none() {
            return Err(format!(
                "replicated character scene {} is unavailable",
                envelope.snapshot.scene_id
            ));
        }
        self.world.set_active_scene(scene)?;
        let replicated_link = CharacterWorldLink {
            world_position: envelope.snapshot.tile_position,
            world_scene: envelope.snapshot.scene_id.clone(),
            ..self.character_world_link.clone()
        };
        let spawn = self.world.active();
        self.player =
            Self::character_world_position_or_spawn(&replicated_link, spawn.spawn_x, spawn.spawn_y);
        self.camera_target = self.local_world_to_runtime_world(self.player);
        self.reputation = envelope.snapshot.global_reputation;
        self.character_world_link.world_scene = envelope.snapshot.scene_id.clone();
        self.character_world_link.world_position = envelope.snapshot.tile_position;
        self.character_world_link
            .world_reputation
            .insert("global".to_string(), envelope.snapshot.global_reputation);
        self.character_world_link.last_played_unix_seconds =
            envelope.snapshot.last_played_unix_seconds;
        self.last_applied_character_state_sequence = envelope.snapshot.sequence;
        self.last_replication_status = format!(
            "Applied host character state seq {} ({})",
            envelope.snapshot.sequence, envelope.reason
        );
        Ok(())
    }

    pub(super) fn persist_scene_transition_state(&mut self, reason: &str) {
        if let Err(error) = self.persist_character_world_state(reason) {
            self.log.event(&format!(
                "Character-world scene-transition save failed: {error}"
            ));
            return;
        }
        let envelope = self.host_character_world_state_envelope(reason);
        self.last_replication_status = format!(
            "Character state seq {} prepared after scene transition",
            envelope.snapshot.sequence
        );
    }

    pub(super) fn persist_disconnect_state(&mut self, reason: &str) {
        if let Err(error) = self.persist_character_world_state(reason) {
            self.log
                .event(&format!("Character-world disconnect save failed: {error}"));
        }
    }

    pub(super) fn persist_runtime_exit_state(&mut self, reason: &str) {
        self.persist_disconnect_state(reason);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use haven_net::CharacterStateAuthority;

    #[test]
    fn rejects_client_authored_or_stale_snapshots() {
        let snapshot = CharacterWorldStateSnapshot {
            sequence: 2,
            world_id: "world_test".to_string(),
            character_id: "character_test".to_string(),
            scene_id: "overworld".to_string(),
            tile_position: [1, 2],
            global_reputation: 1,
            relationship_count: 0,
            quest_flag_count: 0,
            last_played_unix_seconds: 1,
        };
        let client = CharacterWorldStateEnvelope {
            authority: CharacterStateAuthority::ClientReplica,
            snapshot: snapshot.clone(),
            reason: "client mutation".to_string(),
        };
        assert!(client.validate_for_client(0).is_err());
        let host = CharacterWorldStateEnvelope::host(snapshot, "host update");
        assert!(host.validate_for_client(2).is_err());
        assert!(host.validate_for_client(1).is_ok());
    }
}
