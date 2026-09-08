//! Havenwild-owned 2D spatial-query seam.
//!
//! The initial vector-backed index keeps project types independent of an OSS
//! implementation. rstar/geo/parry2d can replace the backend without changing
//! authored world, selection or save schemas.

use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Aabb2 {
    pub min: [f32; 2],
    pub max: [f32; 2],
}

impl Aabb2 {
    pub fn intersects(self, other: Self) -> bool {
        self.min[0] <= other.max[0]
            && self.max[0] >= other.min[0]
            && self.min[1] <= other.max[1]
            && self.max[1] >= other.min[1]
    }
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SpatialEntry {
    pub id: String,
    pub bounds: Aabb2,
}

#[derive(Clone, Debug, Default)]
pub struct SpatialIndex {
    entries: Vec<SpatialEntry>,
}

impl SpatialIndex {
    pub fn rebuild(entries: Vec<SpatialEntry>) -> Self {
        Self { entries }
    }

    pub fn query(&self, bounds: Aabb2) -> Vec<&SpatialEntry> {
        self.entries
            .iter()
            .filter(|entry| entry.bounds.intersects(bounds))
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn query_returns_intersecting_entries() {
        let index = SpatialIndex::rebuild(vec![SpatialEntry {
            id: "tree".to_string(),
            bounds: Aabb2 { min: [0.0, 0.0], max: [2.0, 2.0] },
        }]);
        assert_eq!(index.query(Aabb2 { min: [1.0, 1.0], max: [3.0, 3.0] }).len(), 1);
    }
}
