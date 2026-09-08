# Apply This Havenwild Source Rollup

This archive is a complete source rollup intended to overwrite the matching
files in the existing Havenwild repository. It is not a patch workflow.

## Windows workflow

1. Close the Havenwild client and editor.
2. Extract this archive into the Havenwild repository root.
3. Allow the archive to overwrite existing files and directories.
4. If a `target` directory exists, delete it. If it does not exist, continue.
5. Run:

```bat
tools/build/Build.cmd all
```

Do not run `tools/build/dev.sh` for this handoff.

The raw LPC dependency and large asset library remain external/cached and are
not duplicated in this source rollup. `tools/build/Build.cmd all` validates the pinned LPC
dependency, restores the Pass 95 runtime metadata from the canonical summer
contract, rebuilds the terrain atlases, performs V107/V108 validation, runs the
Rust checks/tests, and packages the client and editor.

Expected terrain output includes:

```text
Baked 176 ordered-pair LPC transition variants
```
