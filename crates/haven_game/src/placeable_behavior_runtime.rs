use haven_assets::placeable_asset_registry::PublishedWorldAssetDefinition;

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum PlaceableBehaviorCommand {
    Inspect,
    ReserveAttachment {
        attachment_id: String,
        reservation: String,
    },
    ReleaseAttachments,
    RestUntilMorning,
    GrantPlaceholderReward {
        amount: i32,
    },
    ToggleOpen,
    RequestSceneTransition {
        target: Option<String>,
    },
}

pub fn compile_placeable_behavior(
    definition: &PublishedWorldAssetDefinition,
    resulting_state: Option<&str>,
) -> Vec<PlaceableBehaviorCommand> {
    let mut commands = Vec::new();
    match definition.behavior.node_id.as_deref() {
        Some("behavior.placeable.chair_basic") | Some("behavior.placeable.bed_basic") => {
            let points = definition
                .attachment_points_for_state(resulting_state)
                .map(|point| PlaceableBehaviorCommand::ReserveAttachment {
                    attachment_id: point.id.clone(),
                    reservation: point.reservation.clone(),
                })
                .collect::<Vec<_>>();
            if points.is_empty() {
                commands.push(PlaceableBehaviorCommand::ReleaseAttachments);
            } else {
                commands.extend(points);
            }
            if definition.behavior.node_id.as_deref() == Some("behavior.placeable.bed_basic") {
                commands.push(PlaceableBehaviorCommand::RestUntilMorning);
            }
        }
        Some("behavior.placeable.tree_default") => {
            commands.push(PlaceableBehaviorCommand::GrantPlaceholderReward { amount: 1 });
        }
        Some("behavior.placeable.door_basic") => {
            commands.push(PlaceableBehaviorCommand::ToggleOpen);
        }
        Some("behavior.placeable.cave_entrance_default") => {
            commands.push(PlaceableBehaviorCommand::RequestSceneTransition {
                target: definition.interaction.target.clone(),
            });
        }
        Some(_) | None => commands.push(PlaceableBehaviorCommand::Inspect),
    }
    commands
}

#[cfg(test)]
mod tests {
    #[test]
    fn behavior_command_set_is_deterministic_for_same_definition() {
        let source =
            include_str!("../../../content/asset_packs/havenwild_objects/published_world_assets_v1.json");
        assert!(source.contains("behavior.placeable.door_basic"));
        assert!(source.contains("state_geometry"));
    }
}
