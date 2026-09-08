use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum TransformSpace {
    #[default]
    AssetLocal,
    ParentLocal,
    RigLocal,
    SceneLocal,
    World,
    Canvas,
    Camera,
}

#[derive(Clone, Copy, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Transform2D {
    #[serde(default)]
    pub position: [f32; 2],
    #[serde(default)]
    pub rotation_degrees: f32,
    #[serde(default = "unit_scale")]
    pub scale: [f32; 2],
    #[serde(default)]
    pub flip_x: bool,
    #[serde(default)]
    pub flip_y: bool,
    #[serde(default)]
    pub pivot: [f32; 2],
    #[serde(default)]
    pub space: TransformSpace,
}

impl Default for Transform2D {
    fn default() -> Self {
        Self {
            position: [0.0, 0.0],
            rotation_degrees: 0.0,
            scale: unit_scale(),
            flip_x: false,
            flip_y: false,
            pivot: [0.0, 0.0],
            space: TransformSpace::AssetLocal,
        }
    }
}

fn unit_scale() -> [f32; 2] {
    [1.0, 1.0]
}

#[derive(Clone, Copy, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct TransformConstraints {
    #[serde(default)]
    pub position_min: Option<[f32; 2]>,
    #[serde(default)]
    pub position_max: Option<[f32; 2]>,
    #[serde(default)]
    pub rotation_min_degrees: Option<f32>,
    #[serde(default)]
    pub rotation_max_degrees: Option<f32>,
    #[serde(default)]
    pub scale_min: Option<[f32; 2]>,
    #[serde(default)]
    pub scale_max: Option<[f32; 2]>,
    #[serde(default)]
    pub lock_x: bool,
    #[serde(default)]
    pub lock_y: bool,
    #[serde(default)]
    pub lock_rotation: bool,
    #[serde(default)]
    pub preserve_aspect: bool,
    #[serde(default = "default_position_snap")]
    pub position_snap: f32,
    #[serde(default = "default_rotation_snap")]
    pub rotation_snap_degrees: f32,
    #[serde(default = "default_scale_snap")]
    pub scale_snap: f32,
    #[serde(default)]
    pub soft_limits: bool,
}

impl Default for TransformConstraints {
    fn default() -> Self {
        Self {
            position_min: None,
            position_max: None,
            rotation_min_degrees: None,
            rotation_max_degrees: None,
            scale_min: Some([0.01, 0.01]),
            scale_max: None,
            lock_x: false,
            lock_y: false,
            lock_rotation: false,
            preserve_aspect: false,
            position_snap: default_position_snap(),
            rotation_snap_degrees: default_rotation_snap(),
            scale_snap: default_scale_snap(),
            soft_limits: false,
        }
    }
}

fn default_position_snap() -> f32 {
    1.0
}

fn default_rotation_snap() -> f32 {
    1.0
}

fn default_scale_snap() -> f32 {
    0.01
}

impl TransformConstraints {
    pub fn apply(self, original: Transform2D, requested: Transform2D) -> Transform2D {
        let mut result = requested;
        if self.lock_x {
            result.position[0] = original.position[0];
        }
        if self.lock_y {
            result.position[1] = original.position[1];
        }
        if self.lock_rotation {
            result.rotation_degrees = original.rotation_degrees;
        }
        result.position[0] = clamp_optional(
            result.position[0],
            self.position_min.map(|value| value[0]),
            self.position_max.map(|value| value[0]),
        );
        result.position[1] = clamp_optional(
            result.position[1],
            self.position_min.map(|value| value[1]),
            self.position_max.map(|value| value[1]),
        );
        result.rotation_degrees = clamp_optional(
            result.rotation_degrees,
            self.rotation_min_degrees,
            self.rotation_max_degrees,
        );
        result.scale[0] = clamp_optional(
            result.scale[0],
            self.scale_min.map(|value| value[0]),
            self.scale_max.map(|value| value[0]),
        );
        result.scale[1] = clamp_optional(
            result.scale[1],
            self.scale_min.map(|value| value[1]),
            self.scale_max.map(|value| value[1]),
        );
        if self.preserve_aspect {
            let original_ratio = if original.scale[1].abs() > f32::EPSILON {
                original.scale[0] / original.scale[1]
            } else {
                1.0
            };
            result.scale[1] = if original_ratio.abs() > f32::EPSILON {
                result.scale[0] / original_ratio
            } else {
                result.scale[0]
            };
        }
        if self.position_snap > 0.0 {
            result.position[0] = snap(result.position[0], self.position_snap);
            result.position[1] = snap(result.position[1], self.position_snap);
        }
        if self.rotation_snap_degrees > 0.0 {
            result.rotation_degrees = snap(result.rotation_degrees, self.rotation_snap_degrees);
        }
        if self.scale_snap > 0.0 {
            result.scale[0] = snap(result.scale[0], self.scale_snap);
            result.scale[1] = snap(result.scale[1], self.scale_snap);
        }
        result
    }

    pub fn swing_door_left() -> Self {
        Self {
            rotation_min_degrees: Some(0.0),
            rotation_max_degrees: Some(90.0),
            position_snap: 1.0,
            rotation_snap_degrees: 1.0,
            ..Self::default()
        }
    }

    pub fn tree_sway(max_degrees: f32) -> Self {
        let max = max_degrees.abs();
        Self {
            rotation_min_degrees: Some(-max),
            rotation_max_degrees: Some(max),
            position_snap: 1.0,
            rotation_snap_degrees: 0.25,
            ..Self::default()
        }
    }
}

fn clamp_optional(value: f32, min: Option<f32>, max: Option<f32>) -> f32 {
    let value = min.map_or(value, |minimum| value.max(minimum));
    max.map_or(value, |maximum| value.min(maximum))
}

fn snap(value: f32, step: f32) -> f32 {
    if step <= 0.0 {
        value
    } else {
        (value / step).round() * step
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AnchorKind {
    Placement,
    TransformPivot,
    HingePivot,
    Ground,
    FootLeft,
    FootRight,
    Shadow,
    Interaction,
    Effect,
    Camera,
    Socket,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AuthoringAnchor {
    pub id: String,
    pub name: String,
    pub kind: AnchorKind,
    pub position: [f32; 2],
    #[serde(default)]
    pub rotation_degrees: f32,
    #[serde(default)]
    pub space: TransformSpace,
}

impl AuthoringAnchor {
    pub fn hinge(position: [f32; 2]) -> Self {
        Self {
            id: "hinge".to_string(),
            name: "Door Hinge".to_string(),
            kind: AnchorKind::HingePivot,
            position,
            rotation_degrees: 0.0,
            space: TransformSpace::AssetLocal,
        }
    }
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct NamedSocket2D {
    pub name: String,
    pub anchor_id: String,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct TransformNode2D {
    pub id: String,
    #[serde(default)]
    pub parent_id: Option<String>,
    #[serde(default)]
    pub transform: Transform2D,
    #[serde(default)]
    pub constraints: TransformConstraints,
    #[serde(default)]
    pub anchors: Vec<AuthoringAnchor>,
    #[serde(default)]
    pub sockets: Vec<NamedSocket2D>,
}

impl TransformNode2D {
    pub fn new(id: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            parent_id: None,
            transform: Transform2D::default(),
            constraints: TransformConstraints::default(),
            anchors: Vec::new(),
            sockets: Vec::new(),
        }
    }

    pub fn anchor(&self, kind: AnchorKind) -> Option<&AuthoringAnchor> {
        self.anchors.iter().find(|anchor| anchor.kind == kind)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn door_constraint_clamps_rotation_without_moving_position() {
        let original = Transform2D {
            position: [8.0, 12.0],
            ..Transform2D::default()
        };
        let requested = Transform2D {
            position: [8.2, 12.4],
            rotation_degrees: 142.0,
            ..original
        };
        let result = TransformConstraints::swing_door_left().apply(original, requested);
        assert_eq!(result.position, [8.0, 12.0]);
        assert_eq!(result.rotation_degrees, 90.0);
    }

    #[test]
    fn tree_sway_profile_is_symmetric() {
        let constraints = TransformConstraints::tree_sway(4.0);
        assert_eq!(constraints.rotation_min_degrees, Some(-4.0));
        assert_eq!(constraints.rotation_max_degrees, Some(4.0));
    }

    #[test]
    fn hinge_anchor_uses_asset_local_space() {
        let anchor = AuthoringAnchor::hinge([2.0, 30.0]);
        assert_eq!(anchor.kind, AnchorKind::HingePivot);
        assert_eq!(anchor.space, TransformSpace::AssetLocal);
    }
}
