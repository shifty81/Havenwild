//! Compatibility import surface for the W40 shared structural-cliff visual authority.
//!
//! The implementation now lives in `haven_render::structural_cliff_visual` so the
//! native editor and game runtime resolve identical LPC cliff recipes. Keep this
//! module only while older runtime modules are migrated to direct shared imports.

pub(super) use haven_render::structural_cliff_visual::*;
