//! Headless authoring contracts shared by native editor, in-game developer tools,
//! renderer diagnostics, networking envelopes, tests, and future automation.

pub mod animation_tracks;
pub mod capabilities;
pub mod canvas;
pub mod building_validation;
pub mod command_bus;
pub mod diagnostics;
mod edit_operation;
pub mod hit_testing;
pub mod palette;
pub mod resource_context;
pub mod selection;
pub mod session;
pub mod terrain_policy;
pub mod ui_document;
mod transaction_batch;
mod transaction_geometry;
mod transaction_stamp;
pub mod transactions;
pub mod transform;
pub mod world_inspection;
pub mod world_validation;

pub use animation_tracks::{AnimationLoopMode, GeneratedTransformPreset, Rig2D, TransformAnimationClip2D, TransformInterpolation, TransformKeyframe2D, TransformTrack2D};
pub use capabilities::{AuthoringCapability, AuthoringFrontendKind, AuthoringProfile};
pub use canvas::{
    AuthoringCanvasTransform, CanvasPoint, CanvasRect, AUTHORING_CANVAS_MAX_ZOOM,
    AUTHORING_CANVAS_MIN_ZOOM, visible_grid_bounds_in_world,
};
pub use command_bus::{
    CommandHistoryStep, CommandPayload, CommandTarget, CommandUndoStep, EditorCommand,
    EditorCommandBus, EditorCommandKind, EditorCommandSource, GridPos,
};
pub use diagnostics::InspectorReport;
pub use haven_core::{ObjectId, RegionNodeId, StampInstanceId, TransitionId, ZoneId};
pub use hit_testing::{hit_test_scene_cell, CanvasHit, SceneAuthoringLayer};
pub use palette::AuthoringPalette;
pub use resource_context::{
    read_resource_context, resource_context_path, write_resource_context,
    CharacterAnimationResourceContext, ResourceContext, ResourceContextKind, ResourceContextNode,
    UiResourceContext,
    RESOURCE_CONTEXT_RELATIVE_PATH, RESOURCE_CONTEXT_SCHEMA_V1,
};
pub use selection::{EditorSelection, GridRect, SelectionItem};
pub use session::{AuthoringSession, AuthoringSource, AuthoringSourceKind, PublishPreview, PublishTarget};
pub use terrain_policy::{apply_terrain_paint_mode_to_map, TerrainPaintModeReport};
pub use ui_document::{
    TransitionResource, UiAuthoringLane, UiBehaviorBinding, UiDataBinding, UiDocument,
    UiDocumentKind, UiRect, UiWidget, UiWidgetKind, TRANSITION_RESOURCE_SCHEMA_V1,
    UI_DOCUMENT_SCHEMA_V1,
};
pub use world_inspection::{inspect_cell, inspect_scene_cell};
pub use world_validation::{validate_scene_autotile_overrides, validate_world};

pub const ARCHITECTURE_STATUS: &str =
    "Canonical headless authoring kernel shared by native developer editor, player World Builder, developer overlay, automation, networking and tests; contains no windowing/rendering host code.";

pub use edit_operation::EditOperation;
pub use transaction_batch::EditTransactionBatch;
pub use transaction_geometry::transition_grid_rect;
pub use transactions::EditTransaction;
pub use transform::{AnchorKind, AuthoringAnchor, NamedSocket2D, Transform2D, TransformConstraints, TransformNode2D, TransformSpace};

pub use building_validation::{validate_building, BuildingValidationIssue};
