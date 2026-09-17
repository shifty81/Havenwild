use std::env;

use haven_save::{world_save_paths, CharacterId, WorldSaveId};

use crate::client_frontend::WorldLaunchRequest;
use crate::runtime_config::runtime_save_root;

const DEV_WORLD_ARG: &str = "--dev-world";
const DEV_CHARACTER_ARG: &str = "--dev-character";
const DEV_SCENE_ARG: &str = "--dev-scene";
const DEV_X_ARG: &str = "--dev-x";
const DEV_Y_ARG: &str = "--dev-y";

#[derive(Clone, Debug)]
pub(crate) struct DevelopmentLaunchRequest {
    pub(crate) world: WorldLaunchRequest,
    pub(crate) scene_id: Option<String>,
    pub(crate) spawn: Option<[i32; 2]>,
}

pub(crate) fn request_from_process_args() -> Result<Option<DevelopmentLaunchRequest>, String> {
    request_from_args(env::args().skip(1))
}

fn request_from_args<I>(args: I) -> Result<Option<DevelopmentLaunchRequest>, String>
where
    I: IntoIterator<Item = String>,
{
    let args = args.into_iter().collect::<Vec<_>>();
    let has_dev_launch_arg = args.iter().any(|arg| {
        matches!(
            arg.as_str(),
            DEV_WORLD_ARG | DEV_CHARACTER_ARG | DEV_SCENE_ARG | DEV_X_ARG | DEV_Y_ARG
        )
    });
    if !has_dev_launch_arg {
        return Ok(None);
    }

    let world = argument_value(&args, DEV_WORLD_ARG)?;
    let character = argument_value(&args, DEV_CHARACTER_ARG)?;
    let world_id = WorldSaveId(world);
    world_id
        .validate()
        .map_err(|error| format!("invalid {DEV_WORLD_ARG}: {error}"))?;

    let scene_id = optional_argument_value(&args, DEV_SCENE_ARG)?;
    let x = optional_i32_argument(&args, DEV_X_ARG)?;
    let y = optional_i32_argument(&args, DEV_Y_ARG)?;
    let spawn = match (x, y) {
        (Some(x), Some(y)) => Some([x, y]),
        (None, None) => None,
        _ => return Err(format!("{DEV_X_ARG} and {DEV_Y_ARG} must be supplied together")),
    };

    let save_root = runtime_save_root();
    let save_paths = world_save_paths(&save_root, &world_id)
        .map_err(|error| format!("invalid development world: {error}"))?;
    provision_development_world(&save_paths)?;
    if !std::path::Path::new(&save_paths.world).is_file() {
        return Err(format!(
            "development world '{}' provisioning completed without producing {}",
            world_id.0, save_paths.world
        ));
    }

    Ok(Some(DevelopmentLaunchRequest {
        world: WorldLaunchRequest {
            world_id,
            character_id: CharacterId(character),
        },
        scene_id,
        spawn,
    }))
}


fn provision_development_world(paths: &haven_save::ClientSavePaths) -> Result<(), String> {
    // The project Base World is the only development authority. Its local
    // runtime save is a disposable copy, not an independently seeded world.
    let source = crate::runtime_config::runtime_root()
        .join(haven_world::CANONICAL_BASE_WORLD_RELATIVE_PATH);
    if !source.is_file() {
        return Err(format!("Base World missing: {}. Open the native editor to initialize it", source.display()));
    }
    let world = haven_save::load_world_from_path(&source.to_string_lossy())
        .map_err(|error| format!("Base World unreadable (not replaced): {error}"))?;
    if !world.scenes.iter().any(|scene| scene.id.as_str().starts_with("pcg_havenwild_mainland_")) {
        return Err("Base World has no generated Alderreach mainland; refusing legacy fixture".to_string());
    }
    haven_save::save_world_to_path(&paths.world, &world)?;
    let source_root = source.parent().ok_or("Base World source directory is missing")?;
    let replica_root = std::path::Path::new(&paths.root);
    for relative in [
        haven_world::WORLD_CREATION_SETTINGS_FILENAME,
        haven_world::SEMANTIC_WORLD_BAKE_RELATIVE_PATH,
    ] {
        let from = source_root.join(relative);
        if !from.is_file() {
            return Err(format!("Base World sidecar missing: {}", from.display()));
        }
        let to = replica_root.join(relative);
        if let Some(parent) = to.parent() {
            std::fs::create_dir_all(parent).map_err(|error| error.to_string())?;
        }
        std::fs::copy(&from, &to).map_err(|error| format!("{}: {error}", to.display()))?;
    }
    Ok(())
}

fn argument_value(args: &[String], name: &str) -> Result<String, String> {
    optional_argument_value(args, name)?
        .ok_or_else(|| format!("development launch requires {name} <value>"))
}

fn optional_argument_value(args: &[String], name: &str) -> Result<Option<String>, String> {
    let Some(index) = args.iter().position(|arg| arg == name) else {
        return Ok(None);
    };
    let Some(value) = args.get(index + 1) else {
        return Err(format!("development launch requires a value after {name}"));
    };
    if value.starts_with("--") || value.trim().is_empty() {
        return Err(format!("development launch requires a value after {name}"));
    }
    Ok(Some(value.clone()))
}

fn optional_i32_argument(args: &[String], name: &str) -> Result<Option<i32>, String> {
    optional_argument_value(args, name)?
        .map(|value| {
            value
                .parse::<i32>()
                .map_err(|_| format!("{name} requires an integer tile coordinate"))
        })
        .transpose()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn normal_arguments_do_not_request_development_launch() {
        assert!(request_from_args(Vec::<String>::new()).unwrap().is_none());
    }

    #[test]
    fn partial_development_arguments_fail_instead_of_falling_back() {
        let error = request_from_args(vec![
            DEV_WORLD_ARG.to_string(),
            "world_test".to_string(),
        ])
        .unwrap_err();
        assert!(error.contains(DEV_CHARACTER_ARG));
    }

    #[test]
    fn play_here_coordinates_must_be_paired() {
        let error = request_from_args(vec![
            DEV_WORLD_ARG.to_string(),
            "world_test".to_string(),
            DEV_CHARACTER_ARG.to_string(),
            "character_test".to_string(),
            DEV_X_ARG.to_string(),
            "12".to_string(),
        ])
        .unwrap_err();
        assert!(error.contains(DEV_Y_ARG));
    }
}
