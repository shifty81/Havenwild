use haven_core::TileKind;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum TerrainSetV2 {
    NaturalGround,
    Path,
    Water,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum TerrainIdV2 {
    Grass,
    Sand,
    Road,
    StonePath,
    ShallowWater,
    DeepWater,
}

impl TerrainIdV2 {
    pub fn from_tile(tile: TileKind) -> Option<Self> {
        match tile {
            TileKind::Grass | TileKind::TallGrass => Some(Self::Grass),
            TileKind::Sand | TileKind::WetSand => Some(Self::Sand),
            TileKind::Road => Some(Self::Road),
            TileKind::StonePath | TileKind::PebbleShore => Some(Self::StonePath),
            TileKind::ShallowWater | TileKind::OceanShallow | TileKind::ShoreFoam => {
                Some(Self::ShallowWater)
            }
            TileKind::DeepWater | TileKind::OceanDeep => Some(Self::DeepWater),
            _ => None,
        }
    }

    pub fn terrain_set(self) -> TerrainSetV2 {
        match self {
            Self::Grass | Self::Sand => TerrainSetV2::NaturalGround,
            Self::Road | Self::StonePath => TerrainSetV2::Path,
            Self::ShallowWater | Self::DeepWater => TerrainSetV2::Water,
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum TerrainPeerV2 {
    Empty,
    Terrain(TerrainIdV2),
    Any,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct TerrainPatternV2 {
    pub center: TerrainIdV2,
    pub north: TerrainPeerV2,
    pub north_east: TerrainPeerV2,
    pub east: TerrainPeerV2,
    pub south_east: TerrainPeerV2,
    pub south: TerrainPeerV2,
    pub south_west: TerrainPeerV2,
    pub west: TerrainPeerV2,
    pub north_west: TerrainPeerV2,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct TerrainPatternCandidateV2 {
    pub id: String,
    pub pattern: TerrainPatternV2,
    pub verified: bool,
    pub weight: u16,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct TerrainPatternRequestV2 {
    pub pattern: TerrainPatternV2,
    pub world_seed: u64,
    pub x: i32,
    pub y: i32,
}

pub fn resolve_pattern_v2<'a>(
    request: &TerrainPatternRequestV2,
    candidates: &'a [TerrainPatternCandidateV2],
) -> Option<&'a TerrainPatternCandidateV2> {
    // Resolve topology first, then choose among equally-good visual variants by
    // deterministic weight. Weight 0 intentionally means manual-only: the
    // candidate remains valid terrain metadata but is never auto-selected.
    let mut eligible = Vec::<(&TerrainPatternCandidateV2, u16)>::new();
    let mut best_score = None::<u16>;
    for candidate in candidates {
        if candidate.weight == 0
            || candidate.pattern.center != request.pattern.center
            || candidate.pattern.center.terrain_set() != request.pattern.center.terrain_set()
        {
            continue;
        }
        let Some(score) = pattern_score(&request.pattern, &candidate.pattern) else {
            continue;
        };
        let total = score + u16::from(candidate.verified) * 100;
        match best_score {
            None => {
                best_score = Some(total);
                eligible.push((candidate, total));
            }
            Some(best) if total > best => {
                best_score = Some(total);
                eligible.clear();
                eligible.push((candidate, total));
            }
            Some(best) if total == best => eligible.push((candidate, total)),
            _ => {}
        }
    }
    if eligible.is_empty() {
        return None;
    }
    eligible.sort_by(|(left, _), (right, _)| left.id.cmp(&right.id));
    let total_weight = eligible
        .iter()
        .fold(0u64, |sum, (candidate, _)| sum.saturating_add(u64::from(candidate.weight)));
    if total_weight == 0 {
        return None;
    }
    let mut pick = stable_request_hash(request) % total_weight;
    for (candidate, _) in eligible {
        let weight = u64::from(candidate.weight);
        if pick < weight {
            return Some(candidate);
        }
        pick -= weight;
    }
    None
}

fn pattern_score(request: &TerrainPatternV2, candidate: &TerrainPatternV2) -> Option<u16> {
    let requested = [
        request.north,
        request.north_east,
        request.east,
        request.south_east,
        request.south,
        request.south_west,
        request.west,
        request.north_west,
    ];
    let authored = [
        candidate.north,
        candidate.north_east,
        candidate.east,
        candidate.south_east,
        candidate.south,
        candidate.south_west,
        candidate.west,
        candidate.north_west,
    ];
    let mut score = 0u16;
    for (actual, expected) in requested.into_iter().zip(authored) {
        match expected {
            TerrainPeerV2::Any => score += 1,
            _ if expected == actual => score += 10,
            _ => return None,
        }
    }
    Some(score)
}

fn stable_request_hash(request: &TerrainPatternRequestV2) -> u64 {
    let mut value = request.world_seed
        ^ (request.x as u64).wrapping_mul(0x9e37_79b9_7f4a_7c15)
        ^ (request.y as u64).rotate_left(31);
    value = mix_hash(value, terrain_code(request.pattern.center));
    for peer in [
        request.pattern.north,
        request.pattern.north_east,
        request.pattern.east,
        request.pattern.south_east,
        request.pattern.south,
        request.pattern.south_west,
        request.pattern.west,
        request.pattern.north_west,
    ] {
        value = mix_hash(value, peer_code(peer));
    }
    value
}

fn mix_hash(mut value: u64, byte: u8) -> u64 {
    value ^= u64::from(byte);
    value.wrapping_mul(0x100_0000_01b3)
}

fn terrain_code(terrain: TerrainIdV2) -> u8 {
    match terrain {
        TerrainIdV2::Grass => 1,
        TerrainIdV2::Sand => 2,
        TerrainIdV2::Road => 3,
        TerrainIdV2::StonePath => 4,
        TerrainIdV2::ShallowWater => 5,
        TerrainIdV2::DeepWater => 6,
    }
}

fn peer_code(peer: TerrainPeerV2) -> u8 {
    match peer {
        TerrainPeerV2::Empty => 0,
        TerrainPeerV2::Any => 255,
        TerrainPeerV2::Terrain(terrain) => terrain_code(terrain),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn all(center: TerrainIdV2, peer: TerrainPeerV2) -> TerrainPatternV2 {
        TerrainPatternV2 {
            center,
            north: peer,
            north_east: peer,
            east: peer,
            south_east: peer,
            south: peer,
            south_west: peer,
            west: peer,
            north_west: peer,
        }
    }

    #[test]
    fn road_and_stone_path_keep_distinct_identity() {
        assert_ne!(TerrainIdV2::Road, TerrainIdV2::StonePath);
        assert_eq!(TerrainIdV2::Road.terrain_set(), TerrainSetV2::Path);
        assert_eq!(TerrainIdV2::StonePath.terrain_set(), TerrainSetV2::Path);
    }

    #[test]
    fn exact_pattern_beats_wildcard_pattern() {
        let request = TerrainPatternRequestV2 {
            pattern: all(TerrainIdV2::Road, TerrainPeerV2::Terrain(TerrainIdV2::Road)),
            world_seed: 7,
            x: 3,
            y: 9,
        };
        let candidates = vec![
            TerrainPatternCandidateV2 {
                id: "wildcard".into(),
                pattern: all(TerrainIdV2::Road, TerrainPeerV2::Any),
                verified: true,
                weight: 1,
            },
            TerrainPatternCandidateV2 {
                id: "exact".into(),
                pattern: request.pattern,
                verified: true,
                weight: 1,
            },
        ];
        assert_eq!(
            resolve_pattern_v2(&request, &candidates).unwrap().id,
            "exact"
        );
    }

    #[test]
    fn road_candidate_cannot_satisfy_stone_path_request() {
        let request = TerrainPatternRequestV2 {
            pattern: all(TerrainIdV2::StonePath, TerrainPeerV2::Any),
            world_seed: 1,
            x: 0,
            y: 0,
        };
        let candidates = vec![TerrainPatternCandidateV2 {
            id: "road".into(),
            pattern: all(TerrainIdV2::Road, TerrainPeerV2::Any),
            verified: true,
            weight: 1,
        }];
        assert!(resolve_pattern_v2(&request, &candidates).is_none());
    }

    #[test]
    fn zero_weight_candidate_is_manual_only() {
        let request = TerrainPatternRequestV2 {
            pattern: all(TerrainIdV2::Grass, TerrainPeerV2::Any),
            world_seed: 44,
            x: 7,
            y: 8,
        };
        let candidates = vec![TerrainPatternCandidateV2 {
            id: "manual_detail".into(),
            pattern: request.pattern,
            verified: true,
            weight: 0,
        }];
        assert!(resolve_pattern_v2(&request, &candidates).is_none());
    }

    #[test]
    fn weighted_variant_choice_is_deterministic_and_order_independent() {
        let request = TerrainPatternRequestV2 {
            pattern: all(TerrainIdV2::Grass, TerrainPeerV2::Terrain(TerrainIdV2::Grass)),
            world_seed: 991,
            x: 123,
            y: -45,
        };
        let a = TerrainPatternCandidateV2 {
            id: "grass_clean".into(),
            pattern: request.pattern,
            verified: true,
            weight: 8,
        };
        let b = TerrainPatternCandidateV2 {
            id: "grass_flowers".into(),
            pattern: request.pattern,
            verified: true,
            weight: 2,
        };
        let first = vec![a.clone(), b.clone()];
        let reversed = vec![b, a];
        assert_eq!(
            resolve_pattern_v2(&request, &first).map(|candidate| candidate.id.as_str()),
            resolve_pattern_v2(&request, &reversed).map(|candidate| candidate.id.as_str()),
        );
    }

}
