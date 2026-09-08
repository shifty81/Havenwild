use std::env;
use std::path::{Path, PathBuf};
use std::sync::OnceLock;

use macroquad::prelude::Conf;

pub(crate) const PLAYER_SPEED: f32 = 190.0;
// Camera zooms are quantized so one 32 px terrain cell always occupies a
// whole number of output pixels. This prevents nearest-neighbor sampling from
// opening one-pixel cracks between independently submitted terrain quads.
pub(crate) const RUNTIME_CAMERA_DEFAULT_ZOOM: f32 = 43.0 / 32.0;
pub(crate) const RUNTIME_CAMERA_MIN_ZOOM: f32 = 27.0 / 32.0;
pub(crate) const RUNTIME_CAMERA_MAX_ZOOM: f32 = 70.0 / 32.0;
pub(crate) const RUNTIME_CAMERA_ZOOM_STEP: f32 = 1.12;
pub(crate) const CLIENT_SAVE_ROOT: &str = "WORKSPACE/saves";
pub(crate) const WORLDGEN_PACK_PATH: &str = "content/worldgen/packs/worldgen_open_world_v0_1.json";
pub(crate) const WORLDGEN_TEST_PACK_PATH: &str =
    "content/worldgen/packs/worldgen_open_world_test_v0_12.json";
pub(crate) const WORLDGEN_EXPORT_PACK_PATH: &str =
    "content/worldgen/packs/worldgen_home_island_runtime_export_v0_10.json";
pub(crate) const CLIENT_WORLDGEN_TEST_ENV: &str = "HAVENWILD_CLIENT_WORLDGEN_TEST";
pub(crate) const WORLD_PAINT_TEST_ATLAS_PATH: &str = "assets/generated/world_tiles/havenwild_world_environment_test_v0_1/havenwild_world_environment_test_v0_1.png";
pub(crate) const UNDO_LIMIT: usize = 40;
pub(crate) const UI_GRID: f32 = 16.0;

static RUNTIME_ROOT: OnceLock<PathBuf> = OnceLock::new();
static RUNTIME_SAVE_ROOT: OnceLock<PathBuf> = OnceLock::new();

pub(crate) fn runtime_root() -> &'static Path {
    RUNTIME_ROOT.get_or_init(discover_runtime_root).as_path()
}

pub(crate) fn runtime_path(relative_path: &str) -> String {
    let path = Path::new(relative_path);
    let resolved = if path.is_absolute() {
        path.to_path_buf()
    } else {
        runtime_root().join(path)
    };
    resolved.to_string_lossy().into_owned()
}

pub(crate) fn runtime_asset_path(relative_path: &str) -> String {
    runtime_path(relative_path)
}

pub(crate) fn runtime_save_root() -> String {
    RUNTIME_SAVE_ROOT
        .get_or_init(discover_runtime_save_root)
        .to_string_lossy()
        .into_owned()
}

pub(crate) fn runtime_layout_path() -> String {
    let save_root = runtime_save_root();
    Path::new(&save_root)
        .join("editor_layout.tlayout")
        .to_string_lossy()
        .into_owned()
}

/// The normal client boots the selected persistent PCG world. The focused
/// certification pack is available only through an explicit developer opt-in:
/// `HAVENWILD_CLIENT_WORLDGEN_TEST=1` (or true/on/yes).
pub(crate) fn client_worldgen_test_world_enabled() -> bool {
    match env::var(CLIENT_WORLDGEN_TEST_ENV) {
        Ok(value) => matches!(
            value.trim().to_ascii_lowercase().as_str(),
            "1" | "true" | "on" | "yes"
        ),
        Err(_) => false,
    }
}

pub(crate) fn runtime_worldgen_pack_path() -> String {
    let path = if client_worldgen_test_world_enabled() {
        WORLDGEN_TEST_PACK_PATH
    } else {
        WORLDGEN_PACK_PATH
    };
    runtime_path(path)
}

pub(crate) fn runtime_worldgen_export_path() -> String {
    runtime_path(WORLDGEN_EXPORT_PACK_PATH)
}

fn discover_runtime_save_root() -> PathBuf {
    if let Some(configured) = env::var_os("HAVENWILD_SAVE_ROOT") {
        return normalize_path(PathBuf::from(configured));
    }

    if let Ok(current_dir) = env::current_dir() {
        let legacy_root = current_dir.join(CLIENT_SAVE_ROOT);
        if contains_existing_save_data(&legacy_root) {
            return normalize_path(legacy_root);
        }
    }

    normalize_path(runtime_root().join(CLIENT_SAVE_ROOT))
}

fn contains_existing_save_data(root: &Path) -> bool {
    root.join("editor_layout.tlayout").is_file()
        || ["slot_1", "slot_2", "slot_3"]
            .iter()
            .any(|slot| root.join(slot).join("world.tworld").is_file())
}

fn discover_runtime_root() -> PathBuf {
    if let Some(configured) = env::var_os("HAVENWILD_ROOT") {
        let configured = PathBuf::from(configured);
        if let Some(root) = validated_root(configured) {
            return root;
        }
    }

    if let Ok(current_dir) = env::current_dir() {
        if let Some(root) = find_runtime_root(&current_dir) {
            return root;
        }
    }

    if let Ok(executable) = env::current_exe() {
        if let Some(parent) = executable.parent() {
            if let Some(root) = find_runtime_root(parent) {
                return root;
            }
        }
    }

    let compile_time_root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    normalize_path(compile_time_root)
}

fn find_runtime_root(start: &Path) -> Option<PathBuf> {
    start
        .ancestors()
        .find(|candidate| is_runtime_root(candidate))
        .map(|candidate| normalize_path(candidate.to_path_buf()))
}

fn validated_root(candidate: PathBuf) -> Option<PathBuf> {
    if is_runtime_root(&candidate) {
        Some(normalize_path(candidate))
    } else {
        None
    }
}

fn is_runtime_root(candidate: &Path) -> bool {
    candidate.join("assets").is_dir() && candidate.join("content").is_dir()
}

fn normalize_path(path: PathBuf) -> PathBuf {
    path.canonicalize().unwrap_or(path)
}

pub(crate) fn window_conf() -> Conf {
    Conf {
        window_title: "Havenwild".to_owned(),
        window_width: 1280,
        window_height: 720,
        high_dpi: true,
        sample_count: 1,
        ..Default::default()
    }
}
