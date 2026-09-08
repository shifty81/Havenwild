use super::*;
use haven_assets::user_asset_registry::user_asset_manifest_modified;

/// W76Q — the retired Asset Intake panel no longer owns runtime hot reload.
/// Import is a canonical command workflow; this service only watches promoted outputs.
impl EditorApp {
    pub(crate) fn poll_asset_hot_reload(&mut self) {
        if get_time() < self.asset_hot_reload_next_check {
            return;
        }
        self.asset_hot_reload_next_check = get_time() + 0.75;
        let modified = user_asset_manifest_modified();
        if modified.is_some() && modified != self.asset_manifest_modified {
            self.asset_manifest_modified = modified;
            self.asset_hot_reload_requested = true;
        }
    }

    pub(crate) async fn reload_asset_outputs_if_requested(&mut self) {
        if !self.asset_hot_reload_requested {
            return;
        }
        self.asset_hot_reload_requested = false;
        match self.editor_textures.reload_user_assets().await {
            Ok(summary) => {
                self.asset_catalog = AssetPaletteCatalog::load_default().unwrap_or_default();
                self.asset_intake_catalog = AssetIntakeCatalog::load_default().unwrap_or_default();
                self.asset_manifest_modified = user_asset_manifest_modified();
                self.status_message = format!("Hot reloaded promoted assets | {summary}");
            }
            Err(error) => self.status_message = format!("Asset hot reload failed: {error}"),
        }
    }
}
