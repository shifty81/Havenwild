# Havenwild source-only bootstrap

This archive contains the complete Rust workspace, content contracts, scripts, validators, and documentation, but intentionally contains no `assets/` payload.

From the repository root on Windows:

```bat
tools/build/Build.cmd lpc-sync
tools/build/Build.cmd tiles
tools/build/Build.cmd all
```

The first command acquires the pinned ElizaWy/LPC commit and mounts it under `assets/source/licensed/lpc_revised`. The tile and full-build commands regenerate approved runtime atlases and package the client/editor.

Editor diagnostics:

```bat
tools/build/Build.cmd editor-safe
tools/build/Build.cmd editor
```

Safe mode starts the editor without atlas textures. Runtime logs are written under `logs/`, including `haven_editor_native.log` and `haven_editor_native_crash.log`.

The complete source-only archive can be regenerated later with:

```bat
tools/build/Build.cmd source-only
```
