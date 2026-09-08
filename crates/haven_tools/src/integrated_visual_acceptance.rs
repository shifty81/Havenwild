#[cfg(test)]
mod tests {
    use crate::analyze_scene_visual_truth;
    use haven_core::load_worldgen_pack_from_path;
    use std::collections::BTreeSet;
    use std::path::PathBuf;

    fn project_root() -> PathBuf {
        PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
    }

    #[test]
    fn w56_integrated_visual_pack_loads_through_the_real_worldgen_loader() {
        let pack = project_root().join(
            "content/worldgen/packs/worldgen_w56_integrated_visual_acceptance_v0_1.json",
        );
        let (world, report) = load_worldgen_pack_from_path(&pack)
            .expect("load W56 integrated visual acceptance pack");
        assert_eq!(report.scene_count, 1);
        assert_eq!(world.active_scene.code(), "w56_integrated_visual_acceptance");
        let scene = world.active();
        assert_eq!([scene.dimensions.width, scene.dimensions.height], [96, 64]);

        let mut levels = BTreeSet::new();
        for y in 0..scene.dimensions.height as i32 {
            for x in 0..scene.dimensions.width as i32 {
                levels.insert(scene.map.get_structural_level(x, y).unwrap_or(0));
            }
        }
        assert_eq!(levels.into_iter().collect::<Vec<_>>(), vec![0, 1, 2, 3, 4]);

        let truth = analyze_scene_visual_truth(scene);
        assert_eq!(truth.natural_object_count, 18);
        assert!(truth.semantic_asset_counts.len() >= 20);
        for shrub in [
            "shrub_berry_01",
            "shrub_berry_02",
            "shrub_berry_03",
            "shrub_berry_04",
        ] {
            assert_eq!(truth.semantic_asset_counts.get(shrub), Some(&1));
        }
        assert_eq!(truth.semantic_asset_counts.get("cave_entrance_default"), Some(&1));
        assert_eq!(truth.semantic_asset_counts.get("container_crate_wood_01"), Some(&1));
    }
}
