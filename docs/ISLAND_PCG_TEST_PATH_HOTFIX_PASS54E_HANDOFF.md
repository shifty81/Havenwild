# Havenwild Island PCG Test-Path Hotfix — Pass 54E

## Failure addressed

`cargo test --workspace` reached the `haven_world` test suite but the island PCG test attempted to open:

```text
content/worldgen/scene_rectangle_manifest_v0_8.json
```

as a process-working-directory-relative path. Cargo may run a package test with `crates/haven_world` as its working directory, so the manifest was incorrectly searched for beneath that crate rather than beneath the repository root.

## Correction

The test now:

1. Starts from compile-time `CARGO_MANIFEST_DIR` for `crates/haven_world`.
2. Walks up to the repository root.
3. Joins the shared `SCENE_RECTANGLE_MANIFEST_PATH` constant.
4. Loads the real repository manifest independently of the shell, IDE, package, or workspace working directory.

No island-generation behavior, content, camera behavior, editor behavior, or runtime code changed.

## Regression guard

Added:

```text
tools/automation/validation/checks/worldgen/Validate-IslandPcgTestPathV70.py
```

and registered it in `tools/automation/validation/validate.py`.

The validator requires the island-PCG test to use `CARGO_MANIFEST_DIR` and the shared manifest constant, and rejects the old working-directory-relative fixture literal.

## Local verification completed

Passed in the packaging environment:

- Island PCG fixture-path regression validator V70
- Havenwild world preset validation
- Architecture validation across 134 Rust files
- Content validation across 183 JSON files
- Scene Bank/runtime framing V68
- Bash build entrypoint V69
- Python syntax compilation for project scripts

Cargo and Rustc are not installed in the packaging environment, so final Rust compilation and test execution must run on the Windows Rust workstation.

## Recommended Git Bash verification

From the repository root:

```bash
./tools/build/Build.sh test
```

To verify only the previously failing test first:

```bash
cargo test -p haven_world --lib \
  island_pcg::tests::main_island_generation_spans_many_editable_scenes_with_mountain_and_harbor \
  -- --exact --nocapture
```

Then resume the complete build:

```bash
./tools/build/Build.sh all
```

## Expected result

The island PCG test should find:

```text
<repository-root>/content/worldgen/scene_rectangle_manifest_v0_8.json
```

regardless of Cargo's test working directory, allowing the workspace test stage to continue.
