# Havenwild Development Layout — Pass167Z106N5

## Root contract
The root contains only project metadata and `HavenwildTools.cmd`.

## Active product
- `apps/` executable application crates
- `crates/` Rust libraries and runtime systems
- `content/` authored schema-backed game/editor data
- `assets/` source and generated media

## Development infrastructure
- `tools/build/` internal build/check/test/run implementation
- `tools/control/` project control center and registered actions
- `tools/automation/<domain>/` deterministic generators and maintenance
- `tools/automation/common/` shared import-safe Python helpers used by relocated automation
- `tools/automation/validation/` active validation framework
- `tools/automation/validation/checks/<domain>/` current registered checks plus historical pass checks; registry membership determines current authority
- `tools/archive/` retired tooling
- `docs/` current documentation and archived handoffs
- `manifests/` lineage, packaging, provenance, and normalization metadata
- `WORKSPACE/` project-local profiles/workspaces plus machine-local generated state, saves, recovery, and test output; generated/test/save/recovery roots are excluded from source packages
- `logs/` all transient logs and reports

## Archived source
Unrelated Open2D/C++ authoring-shell source is not part of Havenwild. Pass167Z106N5 removes that foreign-project archive from Havenwild packaging and source authority.

## Rules
1. Add control-center actions instead of new root scripts.
2. Put automation in the narrowest owning domain.
3. Write transient output only under `logs/`, `WORKSPACE/`, `target/`, or `artifacts/`.
4. Treat archive trees as reference-only; archived browser/Open2D tooling is never build/runtime authority.
5. Automation scripts that use shared Python helpers must add `tools/automation/` to `sys.path` and import from `common.*`; the retired `generation.*` namespace is forbidden.


## External dependency intake
- `IMPORTS/` is the normalized landing zone for large locked archives that are not included in source rollups.
- Successful dependency bootstrap may move a recognized root archive into `IMPORTS/`.
- `.local/dependencies/` owns extracted caches; source rollups and patches exclude those caches.


## Upgrade preflight
Every build runs `tools/automation/project/Normalize-WorkspaceLayout.py` first. It repairs Windows case-only `TOOLS`/`DOCS` names, migrates the retired root `SCRIPTS` framework and validators into canonical `tools/automation/validation` or `tools/archive` locations, merges legacy `.logs/` output into `logs/`, and removes only explicitly listed transient rollup/test leftovers without deleting product source. Normal development then uses the fast build profile; source validation/certification is explicit.

## Validation ownership boundary
- Havenwild-owned JSON is validated across active project source and metadata.
- `.local/`, `IMPORTS/`, `assets/source/licensed/`, dependency test fixtures, caches, logs, build outputs, and archived source are excluded from generic JSON parsing.
- Dedicated dependency and LPC validators remain authoritative for external repository identity and production bindings.


## Development/checkpoint/release build profiles

- **Build development (fast)**: repair/verify dependency mounts and required runtime sentinels, `cargo check --workspace --all-targets`, then debug-profile `haven_game` + `haven_editor_native`. Formatting is intentionally not a blocking normal-development gate; use **Check Rust workspace**, validation, or explicit `fmt` when a formatting check is desired.
- **Validate current source / Run tests**: explicit checkpoint gates. They are not hidden inside normal Build All.
- **Strict Rust checkpoint** (`tools/build/Build.cmd rust` or `cargo-only`): fmt/check/Clippy/tests/debug workspace build when a compile-risk milestone needs it.
- **Release builds** (`release-client` / `release-apps` advanced commands): explicit only. Normal development never invokes `cargo build --release` or stages release application content.
- Terrain acceptance/certification remains under the dedicated terrain commands and is never part of unrelated normal development builds.
