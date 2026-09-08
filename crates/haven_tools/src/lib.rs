pub mod natural_anchor_audit;
pub use natural_anchor_audit::*;
pub mod world_visual_truth;
pub use world_visual_truth::*;
pub mod building_certification;
pub use building_certification::*;
pub use haven_authoring as authoring;
pub const ARCHITECTURE_STATUS: &str =
    "Scaffolded tools crate; validators, packagers, asset processors, and CLI tasks will consolidate here.";

// Keep crate access namespaced so haven_assets::autotile and haven_world::autotile
// do not collide as ambiguous glob re-exports.
pub use haven_assets as assets;
pub use haven_editor as editor;
pub use haven_world as world;

mod integrated_visual_acceptance;
