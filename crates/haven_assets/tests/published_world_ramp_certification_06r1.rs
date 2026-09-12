use haven_assets::published_world_topology::{
    published_world_topology_registry_v1, PublishedWorldAssetKind, PublishedWorldDomain,
    PublishedWorldUsageLane,
};

const CLIFF_RAMP_SOURCE: &str =
    "content/assets/oga_lpc/source/terrain/cliffs_grass_top/LPC_cliffs_grass.png";

#[test]
fn published_directional_ramps_keep_current_certified_anchor() {
    let registry = published_world_topology_registry_v1()
        .expect("published topology registry should load for ramp certification");

    for (id, rect) in [
        ("cliff.ramp.rise_right.grass", [3, 5, 3, 4]),
        ("cliff.ramp.rise_left.grass", [6, 5, 3, 4]),
    ] {
        let entry = registry
            .entry(id)
            .expect("directional ramp entry should be published");
        assert_eq!(entry.domain, PublishedWorldDomain::Cliff);
        assert_eq!(entry.kind, PublishedWorldAssetKind::SourceStamp);
        assert_eq!(entry.usage_lane, PublishedWorldUsageLane::StructuralRuntime);
        assert_eq!(entry.source_path, CLIFF_RAMP_SOURCE);
        assert_eq!(entry.source_rect_cells, rect);
        assert_eq!(entry.anchor_offset_cells, Some([-1, 0]));
        assert!(entry.tags.iter().any(|tag| tag == "ramp"));
        assert_eq!(entry.certification, "runtime_certified");
    }
}

#[test]
fn historical_minus_one_minus_one_ramp_anchor_is_not_the_runtime_contract() {
    let registry = published_world_topology_registry_v1()
        .expect("published topology registry should load for ramp certification");

    for id in [
        "cliff.ramp.rise_right.grass",
        "cliff.ramp.rise_left.grass",
    ] {
        let entry = registry
            .entry(id)
            .expect("directional ramp entry should be published");
        assert_ne!(entry.anchor_offset_cells, Some([-1, -1]));
    }
}
