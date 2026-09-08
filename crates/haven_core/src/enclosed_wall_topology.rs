use crate::{SceneKind, SceneMap, TileKind};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum EnclosedWallSkin {
    HouseCreamSiding,
    HouseInteriorTimber,
    CaveRock,
    DungeonStone,
}

impl EnclosedWallSkin {
    pub const fn default_for_scene(kind: SceneKind) -> Self {
        match kind {
            SceneKind::Interior => Self::HouseInteriorTimber,
            SceneKind::Cave => Self::CaveRock,
            SceneKind::Exterior => Self::HouseCreamSiding,
        }
    }

    pub const fn code(self) -> &'static str {
        match self {
            Self::HouseCreamSiding => "house_cream_siding",
            Self::HouseInteriorTimber => "house_interior_timber",
            Self::CaveRock => "cave_rock",
            Self::DungeonStone => "dungeon_stone",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum WallTopologyRole {
    Isolated,
    EndNorth,
    EndEast,
    EndSouth,
    EndWest,
    StraightVertical,
    StraightHorizontal,
    CornerNorthEast,
    CornerSouthEast,
    CornerSouthWest,
    CornerNorthWest,
    TeeNorth,
    TeeEast,
    TeeSouth,
    TeeWest,
    Cross,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct WallTopologyResolution {
    pub role: WallTopologyRole,
    /// N/E/S/W bit mask. This remains stable across visual skins.
    pub neighbor_mask: u8,
    pub skin: EnclosedWallSkin,
}


#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum HouseInteriorWallPresentation {
    /// A real south-facing wall body. The exact 32x96 drywall strip is anchored
    /// to this tile and rises northward over the room, matching the LPC wall
    /// source contract.
    SouthFacingBody,
    /// A camera-facing/side shell edge that remains collision authority but is
    /// visually suppressed in the fixed 2.5D house view. Repeating 32x32
    /// CutawayOverlay cells around every perimeter tile produces rail-like bands;
    /// those assets are trim candidates, not a complete wall-body solution.
    CutawayEdge,
}

/// Resolves the visual presentation role for a semantic interior Wall cell.
///
/// House interiors use tall wall faces only when walkable wood floor is directly
/// south of the wall. This covers rear walls and interior dividers. Side/front
/// shell cells remain visually suppressed cut edges so the room stays readable
/// in the fixed top-down 2.5D camera. Collision continues to come from
/// TileKind::Wall; a future certified edge/trim grammar may decorate them.
pub fn resolve_house_interior_wall_presentation(
    scene: &SceneMap,
    x: i32,
    y: i32,
) -> Option<HouseInteriorWallPresentation> {
    if scene.kind != SceneKind::Interior
        || !scene.contains_cell(x, y)
        || scene.map.get(x, y) != TileKind::Wall
    {
        return None;
    }
    let south_is_walkable_floor = scene.contains_cell(x, y + 1)
        && scene.map.get(x, y + 1) == TileKind::WoodFloor;
    Some(if south_is_walkable_floor {
        HouseInteriorWallPresentation::SouthFacingBody
    } else {
        HouseInteriorWallPresentation::CutawayEdge
    })
}

pub const fn is_enclosed_wall(tile: TileKind) -> bool {
    matches!(tile, TileKind::Wall | TileKind::CaveWall)
}

pub fn resolve_enclosed_wall_topology(
    scene: &SceneMap,
    x: i32,
    y: i32,
    skin: EnclosedWallSkin,
) -> Option<WallTopologyResolution> {
    if !scene.contains_cell(x, y) || !is_enclosed_wall(scene.map.get(x, y)) {
        return None;
    }
    let same = |nx: i32, ny: i32| {
        scene.contains_cell(nx, ny) && is_enclosed_wall(scene.map.get(nx, ny))
    };
    let north = same(x, y - 1);
    let east = same(x + 1, y);
    let south = same(x, y + 1);
    let west = same(x - 1, y);
    let mask = (north as u8)
        | ((east as u8) << 1)
        | ((south as u8) << 2)
        | ((west as u8) << 3);
    let role = match mask {
        0b0000 => WallTopologyRole::Isolated,
        0b0001 => WallTopologyRole::EndNorth,
        0b0010 => WallTopologyRole::EndEast,
        0b0100 => WallTopologyRole::EndSouth,
        0b1000 => WallTopologyRole::EndWest,
        0b0101 => WallTopologyRole::StraightVertical,
        0b1010 => WallTopologyRole::StraightHorizontal,
        0b0011 => WallTopologyRole::CornerNorthEast,
        0b0110 => WallTopologyRole::CornerSouthEast,
        0b1100 => WallTopologyRole::CornerSouthWest,
        0b1001 => WallTopologyRole::CornerNorthWest,
        0b1011 => WallTopologyRole::TeeNorth,
        0b0111 => WallTopologyRole::TeeEast,
        0b1110 => WallTopologyRole::TeeSouth,
        0b1101 => WallTopologyRole::TeeWest,
        0b1111 => WallTopologyRole::Cross,
        _ => WallTopologyRole::Isolated,
    };
    Some(WallTopologyResolution {
        role,
        neighbor_mask: mask,
        skin,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{EnclosedSceneSkin, EnclosedSceneSpec, ProjectSceneId};

    #[test]
    fn house_and_cave_use_identical_topology_for_identical_shells() {
        let house = EnclosedSceneSpec::rectangular(
            ProjectSceneId::new("test.wall.house"),
            "House",
            EnclosedSceneSkin::House,
            6,
            4,
            3,
        )
        .unwrap()
        .build()
        .unwrap();
        let cave = EnclosedSceneSpec::rectangular(
            ProjectSceneId::new("test.wall.cave"),
            "Cave",
            EnclosedSceneSkin::Cave,
            6,
            4,
            3,
        )
        .unwrap()
        .build()
        .unwrap();
        let house_role = resolve_enclosed_wall_topology(
            &house,
            0,
            0,
            EnclosedWallSkin::HouseInteriorTimber,
        )
        .unwrap();
        let cave_role = resolve_enclosed_wall_topology(
            &cave,
            0,
            0,
            EnclosedWallSkin::CaveRock,
        )
        .unwrap();
        assert_eq!(house_role.neighbor_mask, cave_role.neighbor_mask);
        assert_eq!(house_role.role, cave_role.role);
        assert_ne!(house_role.skin, cave_role.skin);
    }

    #[test]
    fn doorway_breaks_south_wall_connectivity_without_special_cave_logic() {
        let scene = EnclosedSceneSpec::rectangular(
            ProjectSceneId::new("test.wall.door"),
            "Interior",
            EnclosedSceneSkin::House,
            6,
            4,
            3,
        )
        .unwrap()
        .build()
        .unwrap();
        let threshold = [3, 5];
        assert!(!is_enclosed_wall(scene.map.get(threshold[0], threshold[1])));
        let left = resolve_enclosed_wall_topology(
            &scene,
            threshold[0] - 1,
            threshold[1],
            EnclosedWallSkin::HouseInteriorTimber,
        )
        .unwrap();
        let right = resolve_enclosed_wall_topology(
            &scene,
            threshold[0] + 1,
            threshold[1],
            EnclosedWallSkin::HouseInteriorTimber,
        )
        .unwrap();
        assert_ne!(left.role, WallTopologyRole::StraightHorizontal);
        assert_ne!(right.role, WallTopologyRole::StraightHorizontal);
    }

    #[test]
    fn house_wall_presentation_keeps_real_bodies_and_cut_edges_separate() {
        let mut scene = EnclosedSceneSpec::rectangular(
            ProjectSceneId::new("test.wall.presentation"),
            "Interior",
            EnclosedSceneSkin::House,
            6,
            4,
            3,
        )
        .unwrap()
        .build()
        .unwrap();

        // Rear wall has walkable floor immediately south and therefore owns a
        // real tall wall face. West/front shell cells are camera cut edges.
        assert_eq!(
            resolve_house_interior_wall_presentation(&scene, 2, 0),
            Some(HouseInteriorWallPresentation::SouthFacingBody)
        );
        assert_eq!(
            resolve_house_interior_wall_presentation(&scene, 0, 2),
            Some(HouseInteriorWallPresentation::CutawayEdge)
        );

        // A blocking divider inside the room also becomes a real wall body.
        scene.map.set(2, 2, TileKind::Wall);
        assert_eq!(
            resolve_house_interior_wall_presentation(&scene, 2, 2),
            Some(HouseInteriorWallPresentation::SouthFacingBody)
        );
    }

}
