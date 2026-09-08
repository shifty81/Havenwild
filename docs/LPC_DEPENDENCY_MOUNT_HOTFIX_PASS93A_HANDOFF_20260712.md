# LPC Dependency Mount Hotfix — Pass 93A

## Problem

The compact Pass 93 source intentionally omitted the 64,000+ file raw LPC tree. `tools/build/Build.cmd all` correctly detected the missing dependency, but the previous repair path physically copied every LPC file into the project without progress output. On Windows this appeared stalled and was interrupted, producing exit code 130 and Bash `pop_var_context` cleanup noise.

A misconfigured `HAVENWILD_LPC_REPO` could also point at the Havenwild root and cause a recursive self-copy.

## Correction

`tools/automation/dependencies/Ensure-LpcDependency.py` now:

- validates a cached checkout against the exact pinned commit;
- rejects project-root and overlapping source/destination paths;
- mounts the cached checkout at `assets/source/licensed/lpc_revised` with a directory junction on Windows or directory symlink elsewhere;
- falls back to a progress-reporting physical copy only when linking is unavailable;
- preserves repository symlinks instead of following them recursively;
- skips same-file copies when the project source path is linked to the cache;
- reports cancellation cleanly.

## Usage

```bat
tools/build/Build.cmd lpc-sync
tools/build/Build.cmd all
```

Default mode is link/junction and should complete quickly when the cache already exists.

Force a physical copy:

```bat
set HAVENWILD_LPC_SOURCE_MODE=copy
tools/build/Build.cmd lpc-sync
```

Use an existing LPC checkout:

```bat
set HAVENWILD_LPC_REPO=C:\Assets\LPC
tools/build/Build.cmd lpc-sync
```

`HAVENWILD_LPC_REPO` must point to the ElizaWy/LPC checkout, never the Havenwild project directory.
