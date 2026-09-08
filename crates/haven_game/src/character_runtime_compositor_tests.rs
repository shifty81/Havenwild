    use super::*;

    #[test]
    fn frame_selection_preserves_eight_walk_frames() {
        let frame = RuntimeCharacterAppearance::frame(vec2(1.0, 0.0), CharacterAnimationKind::Walk, 3.4, None, 0.0);
        assert_eq!(frame.facing, CharacterFacing::East);
        assert!(frame.frame < 8);
    }

    #[test]
    fn sprint_selects_authored_run_clip_instead_of_speeding_walk() {
        let frame = RuntimeCharacterAppearance::frame(
            vec2(1.0, 0.0),
            CharacterAnimationKind::Run,
            3.4,
            None,
            0.0,
        );
        assert_eq!(frame.animation, CharacterAnimationKind::Run);
        assert!(frame.frame < 8);
    }


    #[test]
    fn climb_is_valid_looping_locomotion_in_debug_builds() {
        let first = RuntimeCharacterAppearance::frame(
            vec2(0.0, -1.0),
            CharacterAnimationKind::Climb,
            0.0,
            None,
            0.0,
        );
        let later = RuntimeCharacterAppearance::frame(
            vec2(0.0, -1.0),
            CharacterAnimationKind::Climb,
            2.0,
            None,
            0.0,
        );
        assert_eq!(first.animation, CharacterAnimationKind::Climb);
        assert_eq!(later.animation, CharacterAnimationKind::Climb);
        assert!(first.moving && later.moving);
        assert_ne!(first.frame, later.frame);
        assert!(first.frame < 6 && later.frame < 6);
    }

    #[test]
    fn base_body_draws_before_clothing_and_equipment() {
        assert!(layer_order("body/base") < layer_order("clothing/torso"));
        assert!(layer_order("clothing/torso") < layer_order("weapon"));
    }

    #[test]
    fn portable_character_reference_converts_to_runtime_reference() {
        let portable = PortableAssetRef {
            pack_id: "havenwild.core".to_string(),
            category: "clothing".to_string(),
            asset_id: "starter_shirt".to_string(),
            source_id: "starter_character_sheet".to_string(),
            variant_id: Some("green".to_string()),
        };
        let stable = portable_to_stable_ref(&portable).expect("valid category");
        assert_eq!(stable.pack_id.0, portable.pack_id);
        assert_eq!(stable.category, AssetCategory::Clothing);
        assert_eq!(stable.variant_id, portable.variant_id);
    }

    #[test]
    fn generated_component_paths_follow_saved_variants() {
        assert!(generated_component_paths(
            "body/base",
            Some("female_neutral"),
            "female",
            CharacterAnimationKind::Walk
        )
        .first()
        .cloned()
        .expect("female body")
        .contains("body_female"));
        assert!(generated_component_paths(
            "clothing/legs",
            Some("starter_skirt"),
            "female",
            CharacterAnimationKind::Walk
        )
        .first()
        .cloned()
        .expect("skirt")
        .contains("legs_skirt"));
        assert!(generated_component_paths(
            "hair",
            Some("hair_medium_07_bob_side_part"),
            "female",
            CharacterAnimationKind::Walk
        )
        .first()
        .cloned()
        .expect("bob hair")
        .contains("hair_medium_07_bob_side_part"));
    }

    #[test]
    fn face_details_render_between_body_and_clothing() {
        assert!(layer_order("body/base") < layer_order("face/eyes"));
        assert!(layer_order("face/eyes") < layer_order("clothing/legs"));
    }

    #[test]
    fn profile_path_matches_frontend_profile_store() {
        let path = profile_path(
            Path::new("WORKSPACE/saves"),
            &CharacterId("hero".to_string()),
        );
        assert_eq!(
            path,
            Path::new("WORKSPACE/profiles/characters/hero/profile.json")
        );
    }

    #[test]
    fn hood_occludes_hair_without_deleting_saved_hair() {
        let mut appearance =
            crate::character_creator_model::StarterCreatorSelection::default().appearance();
        appearance
            .layers
            .push(haven_save::CharacterAppearanceLayer {
                slot: "headwear".to_string(),
                asset: PortableAssetRef {
                    pack_id: "havenwild_starter_character".to_string(),
                    category: "clothing".to_string(),
                    asset_id: "starter_headwear".to_string(),
                    source_id: "havenwild_authored".to_string(),
                    variant_id: Some("headwear_hood".to_string()),
                },
                palette_id: None,
                tint_rgba: None,
                enabled: true,
            });
        assert!(appearance_occludes_slot(&appearance, "hair"));
        assert!(appearance.layers.iter().any(|layer| layer.slot == "hair"));
    }

    #[test]
    fn unknown_portable_category_is_rejected() {
        assert_eq!(parse_asset_category("not_a_category"), None);
    }
    #[test]
    fn generated_idle_paths_are_distinct_from_walk_paths() {
        let idle = generated_component_paths(
            "body/base",
            Some("female_neutral"),
            "female",
            CharacterAnimationKind::Idle,
        )
        .first()
        .cloned()
        .expect("idle body path");
        let walk = generated_component_paths(
            "body/base",
            Some("female_neutral"),
            "female",
            CharacterAnimationKind::Walk,
        )
        .first()
        .cloned()
        .expect("walk body path");
        assert!(idle.contains("_idle_64.png"));
        assert!(walk.contains("_walk_64.png"));
        assert_ne!(idle, walk);
    }

    #[test]
    fn gameplay_action_fallbacks_are_explicit_and_sprint_never_falls_back_to_walk() {
        assert_eq!(
            explicit_animation_fallback(CharacterAnimationKind::Punch),
            None
        );
        assert_eq!(
            explicit_animation_fallback(CharacterAnimationKind::Watering),
            None
        );
        assert_eq!(
            explicit_animation_fallback(CharacterAnimationKind::OneHandBackslash),
            Some(CharacterAnimationKind::Slash)
        );
        assert_eq!(explicit_animation_fallback(CharacterAnimationKind::Run), None);
    }

    #[test]
    fn hand_action_has_dedicated_punch_clip_name() {
        let path = generated_component_paths(
            "body/base",
            Some("female_neutral"),
            "female",
            CharacterAnimationKind::Punch,
        )
        .first()
        .cloned()
        .expect("punch body path");
        assert!(path.contains("_punch_64.png"));
    }

    #[test]
    fn tool_action_frames_select_authored_action_columns() {
        let frame = RuntimeCharacterAppearance::frame(
            vec2(0.0, 1.0),
            CharacterAnimationKind::Idle,
            0.0,
            Some(CharacterAnimationKind::Watering),
            0.42,
        );
        assert_eq!(frame.animation, CharacterAnimationKind::Watering);
        assert!(frame.frame > 0);
    }

    #[test]
    fn diagonal_movement_prefers_horizontal_cardinal_row() {
        assert_eq!(resolve_character_facing(vec2(1.0, 1.0)), CharacterFacing::East);
        assert_eq!(resolve_character_facing(vec2(-1.0, -1.0)), CharacterFacing::West);
        assert_eq!(resolve_character_facing(vec2(0.4, -1.0)), CharacterFacing::North);
    }

    #[test]
    fn character_layer_alignment_reports_off_grid_sheets() {
        assert!(validate_character_layer_alignment("body/base", 576, 384).is_empty());
        let issues = validate_character_layer_alignment("hair", 577, 383);
        assert_eq!(issues.len(), 2);
    }
    #[test]
    fn sprint_presentation_has_whole_character_walk_fallback() {
        assert_eq!(
            presentation_animation_candidates(CharacterAnimationKind::Run),
            &[
                CharacterAnimationKind::Run,
                CharacterAnimationKind::Walk,
                CharacterAnimationKind::Idle,
            ]
        );
        let original = CharacterAnimationFrame {
            facing: CharacterFacing::South,
            animation: CharacterAnimationKind::Run,
            frame: 3,
            moving: true,
        };
        let fallback = remap_frame_for_presentation(original, CharacterAnimationKind::Walk);
        assert_eq!(fallback.animation, CharacterAnimationKind::Walk);
        assert_eq!(fallback.frame, 4);
        assert!(fallback.moving);
    }

    #[test]
    fn equipment_seed_source_id_normalizes_to_exact_builder_definition_id() {
        assert_eq!(
            normalized_universal_lpc_equipment_definition_id("ulpc.tools_tool_axe"),
            "tools_tool_axe"
        );
        assert_eq!(
            normalized_universal_lpc_equipment_definition_id("tools_tool_axe"),
            "tools_tool_axe"
        );
    }

    #[test]
    fn legacy_development_body_can_synthesize_equipment_identity_without_recipe_rewrite() {
        let appearance = crate::character_creator_model::StarterCreatorSelection::default().appearance();
        let (sex, age) = fallback_universal_lpc_identity(&appearance);
        assert!(!sex.is_empty());
        assert!(!age.is_empty());
    }

