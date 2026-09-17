# Havenwild B02: Canonical Base World — implementation and acceptance

Date: 2026-09-17. Target: experimental. Build status: not run in Linux audit container; validate through existing Windows PCC.

## Implemented in this cumulative patch

1. Retain the previous E02 scene-library repair (visible Open/Edit; card/list click open scene; inspector no longer owns navigation).
2. Declare source-owned `content/worldgen/dev_worlds/core_dev_001/development_world.json` with a valid `world_`-prefixed save identifier.
3. Initialize `world.tworld` once from the project scene-rectangle manifest and existing island generator; do not reroll authored island rectangles or import historical starter scenes as the new world.
4. On editor reopen, load only `content/worldgen/dev_worlds/core_dev_001/world.tworld`; if it exists and cannot be loaded/validated, show error and block Save/Play instead of overwriting it with a starter fixture.
5. Route native editor save/scene-close/direct-authoring publication through one `save_base_world()` gateway that validates, saves project source, reloads and validates, then publishes a disposable client replica.
6. Persist generation settings and semantic bake sidecars beside source and replica. External development launch requires the authored source rather than creating an independent random development world. Live reload uses the same shared source-path constant.
7. Client New World and editor first generation share `materialize_base_world()` for terrain scene materialization; client world instances still have their own save IDs and generation options.

## Windows acceptance steps

- Drop cumulative patch ZIP unextracted into Havenwild repo root. Run the EXISTING Project Control Center Full Quality Gate. Do not run a second patch-applier.
- With `world.tworld` absent, launch native editor. Confirm first run creates the canonical world and generation sidecars, not nine starter fixtures. Check visible Base World READY status. This initial build may take time in the generator; measure it on Windows.
- Open Scene Library and select a generated scene using its direct Open/Edit action. Paint/place an object in Game Canvas. Save All, then reload; verify the authored edit persists.
- Check source `content/worldgen/dev_worlds/core_dev_001/world.tworld` and disposable `WORKSPACE/saves/world_core_dev_001/world.tworld` contain identical scene data after Save All.
- Use Play From Here. Verify the development game launches the authored scene with the expected object and loaded creation settings. Save & Push should update the running client from the project source. Stop retains editor context.
- Close editor and relaunch. Confirm it opens the same authored Base World, without rerolling the layout.
- Temporarily corrupt a copy of the canonical file in a disposable test checkout. Confirm startup visibly refuses it and Save/Play cannot overwrite it. Restore the valid source file after test.
- Create a separate player world through client New World. Confirm it creates an independent save. This does **not** yet verify authored-source override application because that stage is deferred.
- Once the Base World is approved and visually authored, include `world.tworld` and its source sidecars in a project source-control commit or explicit authored-world handoff. The source rollups did not contain this file, so the patch cannot fabricate authored terrain that does not exist yet.

## Explicitly not implemented or claimed

- True embedded in-canvas PIE. Current Play is an external process; runtime extraction and input/render ownership are a later gate.
- Story/Sandbox gameplay-mode selector, authored overrides layered into client New World, save migration, or finished world content.
- Windows compilation, visual screenshot parity, test verification, or newly authored Willowmere artwork.
