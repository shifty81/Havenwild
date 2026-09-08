// Havenwild V009 Editor Command Bus Pseudocode

#[derive(Clone, Debug)]
pub enum EditorCommandSource {
    MainEditor,
    InGameOverlay,
    WebEditor,
    RuntimeScript,
    Importer,
    ValidatorAutoFix,
}

#[derive(Clone, Debug)]
pub enum EditorCommandKind {
    PaintTerrain,
    SetHeight,
    SetMoisture,
    PlaceObject,
    MoveObject,
    RotateObject,
    DeleteObject,
    AssignRoom,
    BuyParcel,
    ExpandSceneBoundary,
    AddWaterTile,
    PushWallOut,
    CreateTransition,
    EditCollisionMask,
    EditInteractionSocket,
    ImportAsset,
    EditPixelAsset,
    ValidateScene,
    SaveScene,
}

#[derive(Clone, Debug)]
pub enum ValidationStatus {
    Valid,
    ValidWithWarning,
    Invalid,
    RequiresConfirmation,
    RequiresRebuild,
}

#[derive(Clone, Debug)]
pub struct EditorCommand {
    pub id: String,
    pub source: EditorCommandSource,
    pub kind: EditorCommandKind,
    pub target: CommandTarget,
    pub payload: CommandPayload,
    pub preview_only: bool,
}

#[derive(Clone, Debug)]
pub struct CommandTarget {
    pub project_id: String,
    pub scene_id: Option<String>,
    pub asset_id: Option<String>,
    pub grid_cells: Vec<GridPos>,
}

#[derive(Clone, Debug)]
pub struct CommandPayload {
    pub data: serde_json::Value,
}

#[derive(Clone, Debug)]
pub struct CommandResult {
    pub status: ValidationStatus,
    pub warnings: Vec<String>,
    pub errors: Vec<String>,
    pub undo_patch: Option<UndoPatch>,
    pub dirty_regions: Vec<DirtyRegion>,
}

pub trait CommandHandler {
    fn validate(&self, command: &EditorCommand, ctx: &EditorContext) -> CommandResult;
    fn apply(&self, command: &EditorCommand, ctx: &mut EditorContext) -> CommandResult;
    fn undo(&self, patch: &UndoPatch, ctx: &mut EditorContext) -> CommandResult;
}

pub struct EditorCommandBus {
    handlers: std::collections::HashMap<String, Box<dyn CommandHandler>>,
    undo_stack: Vec<UndoPatch>,
    redo_stack: Vec<UndoPatch>,
}

impl EditorCommandBus {
    pub fn execute(&mut self, command: EditorCommand, ctx: &mut EditorContext) -> CommandResult {
        let key = format!("{:?}", command.kind);
        let Some(handler) = self.handlers.get(&key) else {
            return CommandResult::error(format!("No handler for command {key}"));
        };

        let validation = handler.validate(&command, ctx);
        if matches!(validation.status, ValidationStatus::Invalid) {
            return validation;
        }

        if command.preview_only {
            return validation;
        }

        let result = handler.apply(&command, ctx);
        if let Some(patch) = &result.undo_patch {
            self.undo_stack.push(patch.clone());
            self.redo_stack.clear();
        }
        result
    }
}

// Placeholder types.
#[derive(Clone, Debug)] pub struct GridPos { pub x: i32, pub y: i32 }
#[derive(Clone, Debug)] pub struct DirtyRegion;
#[derive(Clone, Debug)] pub struct UndoPatch;
pub struct EditorContext;

impl CommandResult {
    pub fn error(message: String) -> Self {
        Self {
            status: ValidationStatus::Invalid,
            warnings: vec![],
            errors: vec![message],
            undo_patch: None,
            dirty_regions: vec![],
        }
    }
}
