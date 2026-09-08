use crate::{Transform2D, TransformConstraints, TransformNode2D};
use haven_identity::HavenId;
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AnimationLoopMode {
    Once,
    Loop,
    PingPong,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum TransformInterpolation {
    Step,
    Linear,
    Smooth,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct TransformKeyframe2D {
    pub time_seconds: f32,
    pub transform: Transform2D,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct TransformTrack2D {
    pub target_node: String,
    pub interpolation: TransformInterpolation,
    pub constraints: TransformConstraints,
    pub keys: Vec<TransformKeyframe2D>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Rig2D {
    pub schema: String,
    pub id: HavenId,
    pub display_name: String,
    pub nodes: Vec<TransformNode2D>,
}

impl Rig2D {
    pub fn new(display_name: impl Into<String>, nodes: Vec<TransformNode2D>) -> Self {
        Self {
            schema: "havenwild.rig2d.v1".to_string(),
            id: HavenId::new("rig"),
            display_name: display_name.into(),
            nodes,
        }
    }
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct TransformAnimationClip2D {
    pub schema: String,
    pub id: HavenId,
    pub display_name: String,
    pub duration_seconds: f32,
    pub loop_mode: AnimationLoopMode,
    pub tracks: Vec<TransformTrack2D>,
}

#[derive(Clone, Copy, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum GeneratedTransformPreset {
    Hinge { open_degrees: f32 },
    Sway { amplitude_degrees: f32 },
    Bob { distance_pixels: f32 },
    Pulse { scale_amount: f32 },
    Recoil { distance_pixels: f32 },
}

impl TransformAnimationClip2D {
    pub fn from_preset(
        display_name: impl Into<String>,
        target_node: impl Into<String>,
        base: Transform2D,
        preset: GeneratedTransformPreset,
    ) -> Self {
        let target_node = target_node.into();
        let (duration_seconds, loop_mode, interpolation, constraints, keys) = match preset {
            GeneratedTransformPreset::Hinge { open_degrees } => {
                let open = open_degrees.clamp(-180.0, 180.0);
                let mut end = base;
                end.rotation_degrees = base.rotation_degrees + open;
                (
                    0.6,
                    AnimationLoopMode::Once,
                    TransformInterpolation::Smooth,
                    TransformConstraints {
                        rotation_min_degrees: Some(base.rotation_degrees.min(end.rotation_degrees)),
                        rotation_max_degrees: Some(base.rotation_degrees.max(end.rotation_degrees)),
                        ..TransformConstraints::default()
                    },
                    vec![
                        TransformKeyframe2D { time_seconds: 0.0, transform: base },
                        TransformKeyframe2D { time_seconds: 0.6, transform: end },
                    ],
                )
            }
            GeneratedTransformPreset::Sway { amplitude_degrees } => {
                let amplitude = amplitude_degrees.abs().clamp(0.25, 25.0);
                let mut left = base;
                left.rotation_degrees = base.rotation_degrees - amplitude;
                let mut right = base;
                right.rotation_degrees = base.rotation_degrees + amplitude;
                (
                    1.8,
                    AnimationLoopMode::PingPong,
                    TransformInterpolation::Smooth,
                    TransformConstraints::tree_sway(amplitude),
                    vec![
                        TransformKeyframe2D { time_seconds: 0.0, transform: left },
                        TransformKeyframe2D { time_seconds: 0.9, transform: right },
                        TransformKeyframe2D { time_seconds: 1.8, transform: left },
                    ],
                )
            }
            GeneratedTransformPreset::Bob { distance_pixels } => {
                let distance = distance_pixels.abs().clamp(1.0, 64.0);
                let mut up = base;
                up.position[1] -= distance;
                (
                    1.0,
                    AnimationLoopMode::PingPong,
                    TransformInterpolation::Smooth,
                    TransformConstraints::default(),
                    vec![
                        TransformKeyframe2D { time_seconds: 0.0, transform: base },
                        TransformKeyframe2D { time_seconds: 0.5, transform: up },
                        TransformKeyframe2D { time_seconds: 1.0, transform: base },
                    ],
                )
            }
            GeneratedTransformPreset::Pulse { scale_amount } => {
                let amount = scale_amount.abs().clamp(0.01, 1.0);
                let mut expanded = base;
                expanded.scale = [base.scale[0] + amount, base.scale[1] + amount];
                (
                    0.8,
                    AnimationLoopMode::PingPong,
                    TransformInterpolation::Smooth,
                    TransformConstraints::default(),
                    vec![
                        TransformKeyframe2D { time_seconds: 0.0, transform: base },
                        TransformKeyframe2D { time_seconds: 0.4, transform: expanded },
                        TransformKeyframe2D { time_seconds: 0.8, transform: base },
                    ],
                )
            }
            GeneratedTransformPreset::Recoil { distance_pixels } => {
                let distance = distance_pixels.abs().clamp(1.0, 64.0);
                let mut recoiled = base;
                recoiled.position[0] -= distance;
                (
                    0.2,
                    AnimationLoopMode::Once,
                    TransformInterpolation::Linear,
                    TransformConstraints::default(),
                    vec![
                        TransformKeyframe2D { time_seconds: 0.0, transform: base },
                        TransformKeyframe2D { time_seconds: 0.07, transform: recoiled },
                        TransformKeyframe2D { time_seconds: 0.2, transform: base },
                    ],
                )
            }
        };
        Self {
            schema: "havenwild.transform_animation_clip2d.v1".to_string(),
            id: HavenId::new("transform_clip"),
            display_name: display_name.into(),
            duration_seconds,
            loop_mode,
            tracks: vec![TransformTrack2D {
                target_node,
                interpolation,
                constraints,
                keys,
            }],
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn hinge_preset_generates_two_registered_keys() {
        let base = Transform2D::default();
        let clip = TransformAnimationClip2D::from_preset(
            "Door Open",
            "door.leaf",
            base,
            GeneratedTransformPreset::Hinge { open_degrees: 90.0 },
        );
        assert_eq!(clip.tracks[0].keys.len(), 2);
        assert_eq!(clip.tracks[0].keys[1].transform.rotation_degrees, 90.0);
    }
}
