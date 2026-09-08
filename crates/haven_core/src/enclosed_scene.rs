use crate::{
    ProjectSceneId, SceneBiome, SceneDimensions, SceneKind, SceneMap, TileKind, ZoneKind,
};

/// Shared semantic shell for houses, shops, caves and dungeons. Enclosed scenes
/// keep their unused backing cells as void material and author only a compact
/// floor area plus its one-cell structural wall boundary.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum EnclosedSceneSkin {
    House,
    StoneInterior,
    Cave,
    Dungeon,
}

impl EnclosedSceneSkin {
    pub const fn scene_kind(self) -> SceneKind {
        match self {
            Self::House | Self::StoneInterior => SceneKind::Interior,
            Self::Cave | Self::Dungeon => SceneKind::Cave,
        }
    }

    pub const fn floor_tile(self) -> TileKind {
        match self {
            Self::House => TileKind::WoodFloor,
            Self::StoneInterior | Self::Dungeon => TileKind::StoneFloor,
            Self::Cave => TileKind::CaveFloor,
        }
    }

    pub const fn wall_tile(self) -> TileKind {
        match self.scene_kind() {
            SceneKind::Interior => TileKind::Wall,
            SceneKind::Cave => TileKind::CaveWall,
            SceneKind::Exterior => TileKind::Wall,
        }
    }

    pub const fn zone(self) -> ZoneKind {
        match self.scene_kind() {
            SceneKind::Interior => ZoneKind::None,
            SceneKind::Cave => ZoneKind::Cave,
            SceneKind::Exterior => ZoneKind::None,
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct EnclosedSceneSpec {
    pub id: ProjectSceneId,
    pub name: String,
    pub skin: EnclosedSceneSkin,
    /// Complete logical scene dimensions, including the structural perimeter.
    pub dimensions: SceneDimensions,
    /// x, y, width, height for the authored walkable floor region.
    pub floor_rect: [i32; 4],
    /// Spawn tile inside the authored floor region.
    pub spawn: [i32; 2],
    /// Walkable opening cut through the south structural wall.
    pub entry_threshold: [i32; 2],
    pub biome: SceneBiome,
}

impl EnclosedSceneSpec {
    pub fn rectangular(
        id: impl Into<ProjectSceneId>,
        name: impl Into<String>,
        skin: EnclosedSceneSkin,
        interior_width: usize,
        interior_height: usize,
        entry_x: usize,
    ) -> Result<Self, String> {
        if interior_width < 3 || interior_height < 3 {
            return Err("enclosed scene interior must be at least 3x3 tiles".to_string());
        }
        let dimensions = SceneDimensions::new(interior_width + 2, interior_height + 2).validate()?;
        let entry_x = entry_x.clamp(1, interior_width);
        let floor_rect = [1, 1, interior_width as i32, interior_height as i32];
        let spawn = [entry_x as i32, interior_height as i32];
        let entry_threshold = [entry_x as i32, interior_height as i32 + 1];
        Ok(Self {
            id: id.into(),
            name: name.into(),
            skin,
            dimensions,
            floor_rect,
            spawn,
            entry_threshold,
            biome: if matches!(skin.scene_kind(), SceneKind::Cave) {
                SceneBiome::Cave
            } else {
                SceneBiome::Temperate
            },
        })
    }

    pub fn build(&self) -> Result<SceneMap, String> {
        let mut scene = SceneMap::blank_sized(
            self.id.clone(),
            self.name.clone(),
            self.skin.scene_kind(),
            self.biome,
            self.dimensions,
        )?;
        let [x, y, w, h] = self.floor_rect;
        if w <= 0 || h <= 0 {
            return Err("enclosed scene floor rectangle must be positive".to_string());
        }
        if !self.dimensions.contains(x, y)
            || !self.dimensions.contains(x + w - 1, y + h - 1)
        {
            return Err("enclosed scene floor rectangle exceeds logical dimensions".to_string());
        }
        for yy in y..y + h {
            for xx in x..x + w {
                scene.map.set(xx, yy, self.skin.floor_tile());
                scene.set_zone(xx, yy, self.skin.zone());
            }
        }
        if !self.dimensions.contains(self.spawn[0], self.spawn[1])
            || scene.map.get(self.spawn[0], self.spawn[1]) == self.skin.wall_tile()
        {
            return Err("enclosed scene spawn must be inside authored floor".to_string());
        }
        if !self.dimensions.contains(self.entry_threshold[0], self.entry_threshold[1]) {
            return Err("enclosed scene entry threshold must be inside logical dimensions".to_string());
        }
        scene
            .map
            .set(self.entry_threshold[0], self.entry_threshold[1], self.skin.floor_tile());
        scene.set_zone(
            self.entry_threshold[0],
            self.entry_threshold[1],
            self.skin.zone(),
        );
        scene.spawn_x = self.spawn[0];
        scene.spawn_y = self.spawn[1];
        Ok(scene)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn house_scene_keeps_one_wall_border_and_void_beyond_it() {
        let scene = EnclosedSceneSpec::rectangular(
            ProjectSceneId::new("test.house"),
            "House",
            EnclosedSceneSkin::House,
            8,
            6,
            4,
        )
        .unwrap()
        .build()
        .unwrap();
        assert_eq!(scene.kind, SceneKind::Interior);
        assert_eq!(scene.map.get(1, 1), TileKind::WoodFloor);
        assert_eq!(scene.map.get(0, 1), TileKind::Wall);
        assert!(scene.is_renderable_cell(0, 1));
        assert!(!scene.is_renderable_cell(12, 12));
        assert_eq!(scene.renderable_bounds(), Some((0, 0, 9, 7)));
    }

    #[test]
    fn cave_uses_same_enclosed_contract_with_cave_skin() {
        let scene = EnclosedSceneSpec::rectangular(
            ProjectSceneId::new("test.cave"),
            "Cave",
            EnclosedSceneSkin::Cave,
            7,
            5,
            3,
        )
        .unwrap()
        .build()
        .unwrap();
        assert_eq!(scene.kind, SceneKind::Cave);
        assert_eq!(scene.map.get(1, 1), TileKind::CaveFloor);
        assert_eq!(scene.map.get(0, 1), TileKind::CaveWall);
        assert!(scene.is_renderable_cell(0, 1));
    }
}
