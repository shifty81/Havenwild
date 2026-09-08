use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::{fs, path::Path};

pub const NATURAL_ANCHOR_AUDIT_SCHEMA: &str = "havenwild.natural_anchor_audit.v1";

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct NaturalAnchorAssetResult {
    pub id: String,
    pub foot_anchor: [i64; 2],
    pub visual_footprint_tiles: [i64; 2],
    pub collision_footprint_tiles: [i64; 2],
    pub expected_bottom_center: [i64; 2],
    pub passed: bool,
    #[serde(default)]
    pub issues: Vec<String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct NaturalAnchorAuditReport {
    pub schema: String,
    pub cache_id: String,
    pub cell_size: [i64; 2],
    pub results: Vec<NaturalAnchorAssetResult>,
}

impl NaturalAnchorAuditReport {
    pub fn passed(&self) -> bool {
        self.results.len() == NATURAL_RUNTIME_IDS.len()
            && self.results.iter().all(|result| result.passed)
    }
}

const NATURAL_RUNTIME_IDS: [&str; 5] = [
    "oak_tree",
    "berry_bush",
    "boulder",
    "forage_mushroom",
    "wild_herb",
];

/// Audits the generated runtime cache that both editor and client are expected to consume.
/// It verifies that natural sprites use one bottom-center placement anchor rather than a
/// top-left atlas-cell origin, while preserving separate visual and collision footprints.
pub fn audit_natural_placeable_cache(path: impl AsRef<Path>) -> Result<NaturalAnchorAuditReport, String> {
    let path = path.as_ref();
    let text = fs::read_to_string(path)
        .map_err(|error| format!("{}: {error}", path.display()))?;
    let root: Value = serde_json::from_str(&text)
        .map_err(|error| format!("{}: {error}", path.display()))?;
    let cell_width = int_field(&root, "cellWidth")?;
    let cell_height = int_field(&root, "cellHeight")?;
    let cache_id = root
        .get("id")
        .and_then(Value::as_str)
        .unwrap_or("unknown")
        .to_string();
    let objects = root
        .get("objects")
        .and_then(Value::as_array)
        .ok_or_else(|| format!("{} has no objects array", path.display()))?;

    let mut results = Vec::new();
    for id in NATURAL_RUNTIME_IDS {
        let Some(object) = objects.iter().find(|entry| entry.get("id").and_then(Value::as_str) == Some(id)) else {
            results.push(NaturalAnchorAssetResult {
                id: id.to_string(),
                foot_anchor: [0, 0],
                visual_footprint_tiles: [0, 0],
                collision_footprint_tiles: [0, 0],
                expected_bottom_center: [cell_width / 2, cell_height],
                passed: false,
                issues: vec!["runtime cache entry is missing".to_string()],
            });
            continue;
        };
        let foot_anchor = pair_field(object, "footAnchor")?;
        let visual_footprint_tiles = pair_field(object, "visualFootprintTiles")?;
        let collision_footprint_tiles = pair_field(object, "collisionFootprintTiles")?;
        let expected_bottom_center = [cell_width / 2, cell_height];
        let mut issues = Vec::new();
        if foot_anchor != expected_bottom_center {
            issues.push(format!(
                "foot anchor {:?} is not generated-cell bottom center {:?}",
                foot_anchor, expected_bottom_center
            ));
        }
        if id == "oak_tree" {
            if visual_footprint_tiles != [3, 4] {
                issues.push(format!(
                    "oak tree visual footprint {:?} must remain 3x4",
                    visual_footprint_tiles
                ));
            }
            if collision_footprint_tiles != [1, 1] {
                issues.push(format!(
                    "oak tree collision footprint {:?} must remain 1x1 trunk-only",
                    collision_footprint_tiles
                ));
            }
        }
        if matches!(id, "forage_mushroom" | "wild_herb")
            && collision_footprint_tiles != [0, 0]
        {
            issues.push(format!(
                "forage collision footprint {:?} must remain non-blocking",
                collision_footprint_tiles
            ));
        }
        results.push(NaturalAnchorAssetResult {
            id: id.to_string(),
            foot_anchor,
            visual_footprint_tiles,
            collision_footprint_tiles,
            expected_bottom_center,
            passed: issues.is_empty(),
            issues,
        });
    }

    Ok(NaturalAnchorAuditReport {
        schema: NATURAL_ANCHOR_AUDIT_SCHEMA.to_string(),
        cache_id,
        cell_size: [cell_width, cell_height],
        results,
    })
}

fn int_field(value: &Value, field: &str) -> Result<i64, String> {
    value
        .get(field)
        .and_then(Value::as_i64)
        .ok_or_else(|| format!("missing integer field {field}"))
}

fn pair_field(value: &Value, field: &str) -> Result<[i64; 2], String> {
    let values = value
        .get(field)
        .and_then(Value::as_array)
        .ok_or_else(|| format!("missing pair field {field}"))?;
    if values.len() != 2 {
        return Err(format!("field {field} must have exactly two values"));
    }
    Ok([
        values[0]
            .as_i64()
            .ok_or_else(|| format!("field {field}[0] must be an integer"))?,
        values[1]
            .as_i64()
            .ok_or_else(|| format!("field {field}[1] must be an integer"))?,
    ])
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    #[test]
    fn current_generated_natural_cache_uses_bottom_center_anchor_contract() {
        let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../assets/generated/havenwild_lpc_objects_160x192_v2.json");
        let report = audit_natural_placeable_cache(path).unwrap();
        assert!(report.passed(), "{:#?}", report.results);
        let tree = report.results.iter().find(|entry| entry.id == "oak_tree").unwrap();
        assert_eq!(tree.foot_anchor, [80, 192]);
        assert_eq!(tree.visual_footprint_tiles, [3, 4]);
        assert_eq!(tree.collision_footprint_tiles, [1, 1]);
    }
}
