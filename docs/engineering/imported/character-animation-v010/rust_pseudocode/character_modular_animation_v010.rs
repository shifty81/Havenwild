// Havenwild V010 Modular Character Animation Pseudocode

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Direction8 {
    N, NE, E, SE, S, SW, W, NW,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum AnimationKind {
    Idle,
    Walk,
    Run,
    Sit,
    Sleep,
    Carry,
    Serve,
    UseTool,
    Fish,
    Mine,
    Chop,
    Hoe,
    Water,
    Cook,
    WashDishes,
    Interact,
    Emote,
}

#[derive(Clone, Copy, Debug)]
pub struct Point {
    pub x: f32,
    pub y: f32,
}

#[derive(Clone, Debug)]
pub struct FrameRig {
    pub root_anchor: Point,
    pub head_anchor: Point,
    pub torso_anchor: Point,
    pub shoulder_left: Point,
    pub shoulder_right: Point,
    pub hand_left: Point,
    pub hand_right: Point,
    pub hip_left: Point,
    pub hip_right: Point,
    pub knee_left: Point,
    pub knee_right: Point,
    pub foot_left: Point,
    pub foot_right: Point,
    pub held_item_anchor: Point,
    pub shadow_anchor: Point,
    pub depth_flags: Vec<DepthFlag>,
    pub events: Vec<AnimationEvent>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DepthFlag {
    LeftArmFront,
    RightArmFront,
    HeldItemFront,
    HeldItemBehind,
    HairFront,
    CapeBack,
}

#[derive(Clone, Debug)]
pub enum AnimationEvent {
    FootstepLeft,
    FootstepRight,
    ToolSwingStart,
    ToolContact,
    ServePlaceItem,
    PickupItem,
    CastFishingLine,
    MineHit,
    ChopHit,
    WaterPour,
}

#[derive(Clone, Debug)]
pub struct AnimationSheetSpec {
    pub asset_id: String,
    pub cell_width: u32,
    pub cell_height: u32,
    pub directions: Vec<Direction8>,
    pub frames_per_direction: u8,
    pub frame_rigs: Vec<FrameRig>,
    pub grid_alignment: GridAlignment,
}

#[derive(Clone, Copy, Debug)]
pub struct GridAlignment {
    pub origin_x: i32,
    pub origin_y: i32,
    pub cell_width: u32,
    pub cell_height: u32,
    pub padding_x: u32,
    pub padding_y: u32,
    pub spacing_x: u32,
    pub spacing_y: u32,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum CharacterLayerKind {
    BaseBody,
    Hair,
    Face,
    Beard,
    Shirt,
    Pants,
    Boots,
    Gloves,
    ChestArmor,
    ArmArmor,
    LegArmor,
    Helmet,
    HeldItem,
    BackAccessory,
}

#[derive(Clone, Debug)]
pub struct CharacterLayer {
    pub asset_id: String,
    pub kind: CharacterLayerKind,
    pub animation_sheet: AnimationSheetSpec,
    pub binds_to_sockets: Vec<String>,
    pub validation_state: ValidationState,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ValidationState {
    Draft,
    GridValidated,
    SocketValidated,
    MotionValidated,
    CompositeValidated,
    ProductionReady,
    Rejected,
}

#[derive(Clone, Debug)]
pub struct LayerConformanceReport {
    pub asset_id: String,
    pub animation: AnimationKind,
    pub direction: Direction8,
    pub frame: u8,
    pub root_match: bool,
    pub socket_match: bool,
    pub drift_pixels: f32,
    pub warnings: Vec<String>,
    pub errors: Vec<String>,
}

pub fn validate_layer_against_template(
    layer: &CharacterLayer,
    template: &AnimationSheetSpec,
) -> Vec<LayerConformanceReport> {
    let mut reports = Vec::new();

    for (idx, rig) in layer.animation_sheet.frame_rigs.iter().enumerate() {
        let template_rig = &template.frame_rigs[idx];

        let root_drift = distance(rig.root_anchor, template_rig.root_anchor);
        let mut warnings = Vec::new();
        let mut errors = Vec::new();

        if root_drift > 0.0 {
            errors.push(format!("Root anchor drift: {root_drift}px"));
        }

        let hand_drift = distance(rig.hand_right, template_rig.hand_right);
        if hand_drift > 1.0 {
            warnings.push(format!("Right hand socket drift: {hand_drift}px"));
        }
        if hand_drift > 2.0 {
            errors.push(format!("Right hand socket drift exceeds tolerance: {hand_drift}px"));
        }

        reports.push(LayerConformanceReport {
            asset_id: layer.asset_id.clone(),
            animation: AnimationKind::Walk,
            direction: Direction8::S,
            frame: idx as u8,
            root_match: root_drift == 0.0,
            socket_match: errors.is_empty(),
            drift_pixels: root_drift.max(hand_drift),
            warnings,
            errors,
        });
    }

    reports
}

fn distance(a: Point, b: Point) -> f32 {
    let dx = a.x - b.x;
    let dy = a.y - b.y;
    (dx * dx + dy * dy).sqrt()
}
