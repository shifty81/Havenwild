#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMMAND="${1:-all}"
if [[ $# -gt 0 ]]; then shift; fi
cd "$ROOT"
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

LOG_ROOT="$ROOT/logs/builds"
mkdir -p "$LOG_ROOT"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
LOG_PATH="$LOG_ROOT/havenwild-${COMMAND}-${TIMESTAMP}.log"
START_SECONDS="$(date +%s)"

exec > >(tee -a "$LOG_PATH") 2>&1

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

finish() {
  local result=$?
  local end_seconds elapsed
  end_seconds="$(date +%s)"
  elapsed=$((end_seconds - START_SECONDS))
  if [[ $result -eq 0 ]]; then
    log "Havenwild bash build completed successfully (${COMMAND}, ${elapsed}s)"
  else
    log "Havenwild bash build failed (${COMMAND}) with exit code ${result} after ${elapsed}s"
  fi
  log "Build log: $LOG_PATH"
  trap - EXIT
  exit "$result"
}
trap finish EXIT

require() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log "ERROR: $1 is required but was not found in PATH"
    return 1
  fi
}

python_cmd() {
  if command -v python3 >/dev/null 2>&1; then printf '%s\n' python3; return; fi
  if command -v python >/dev/null 2>&1; then printf '%s\n' python; return; fi
  log "ERROR: python or python3 is required"
  return 1
}

run_step() {
  local name="$1"
  shift
  log "START $name"
  "$@"
  log "OK $name"
}

normalize_workspace_layout() {
  local python
  python="$(python_cmd)"
  run_step "normalize machine-local workspace layout" \
    "$python" tools/automation/project/Normalize-WorkspaceLayout.py
}

ensure_frontend_music() {
  local python
  python="$(python_cmd)"
  run_step "restore/verify attributed frontend music" \
    "$python" tools/automation/audio/Ensure-FrontendMusicV167Z56.py
}






ensure_lpc_dependency_fast() {
  local python
  python="$(python_cmd)"
  run_step "verify/repair pinned LPC mount" "$python" tools/automation/dependencies/Ensure-LpcDependency.py
}

ensure_lpc_dependency() {
  local python
  python="$(python_cmd)"
  ensure_lpc_dependency_fast
  run_step "audit and route complete ElizaWy/LPC repository" \
    "$python" tools/automation/assets/Build-ElizaWyProjectAssetAuditV167Z38.py --strict
}

ensure_universal_lpc_mount() {
  local python
  python="$(python_cmd)"
  run_step "verify/repair Universal LPC mount" \
    env HAVENWILD_ULPC_STRICT=1 "$python" tools/automation/characters/Ensure-UniversalLpcGenerator.py
}

ensure_universal_lpc_character_authority() {
  local python
  python="$(python_cmd)"
  local authority="WORKSPACE/generated/universal_lpc_character_authority_v167w.json"
  if [[ ! -f "$authority" ]]; then
    run_step "build Universal LPC Character Studio authority" \
      "$python" tools/automation/characters/Build-UniversalLpcCharacterAuthorityV167W.py
  else
    log "Universal LPC Character Studio authority ready"
  fi
}

ensure_universal_lpc_character_repository_fast() {
  local python
  python="$(python_cmd)"
  ensure_universal_lpc_mount
  ensure_universal_lpc_character_authority
  local required=(
    content/assets/lpc/universal_lpc_complete_repository_index_v0_1.json.gz
    content/assets/lpc/universal_lpc_equipment_action_catalog_v0_1.json
    content/assets/lpc/universal_lpc_gameplay_item_seed_catalog_v0_1.json
    content/assets/lpc/universal_lpc_complete_repository_summary_v0_1.json
  )
  local item
  local missing=0
  for item in "${required[@]}"; do
    if [[ ! -f "$item" ]]; then
      missing=1
      break
    fi
  done
  if [[ "$missing" == "1" ]]; then
    run_step "restore missing Universal LPC repository index" \
      "$python" tools/automation/characters/Build-UniversalLpcCompleteRepositoryIndexV167Z7.py
  else
    log "Universal LPC generated indexes present; deep repository summary validation deferred"
  fi
  if [[ ! -f content/assets/lpc/universal_lpc_normalized_character_catalog_v1.json.gz \
        || ! -f content/assets/lpc/universal_lpc_normalized_character_catalog_summary_v1.json ]]; then
    run_step "build normalized Universal LPC character metadata catalog" \
      "$python" tools/automation/characters/Build-UniversalLpcNormalizedCharacterCatalogV1.py
  fi
  local icon_validator="tools/automation/characters/Validate-UniversalLpcItemIconAtlasV1.py"
  if [[ ! -f assets/generated/lpc/item_icons/universal_lpc_item_icons_v1.png \
        || ! -f assets/generated/lpc/item_icons/universal_lpc_item_icons_v1.json ]] \
      || ! "$python" "$icon_validator" --quiet; then
    run_step "build Universal LPC player item icon atlas" \
      "$python" tools/automation/characters/Build-UniversalLpcItemIconAtlasV1.py
    run_step "validate Universal LPC player item icon atlas" \
      "$python" "$icon_validator"
  else
    log "Universal LPC player item icon atlas ready and current"
  fi
}

ensure_universal_lpc_character_repository() {
  local python
  python="$(python_cmd)"
  ensure_universal_lpc_mount
  ensure_universal_lpc_character_authority
  local revision_file="WORKSPACE/generated/.universal_lpc_complete_repository_revision"
  local required_revision="0f898bb675a1abe16ce430e82e3bf9daed278690"
  local summary_validator="tools/automation/characters/Validate-UniversalLpcCompleteRepositorySummaryV167Z41.py"
  local installed_revision=""
  local summary_valid="0"
  if [[ -f "$revision_file" ]]; then
    installed_revision="$(tr -d '\r\n' < "$revision_file")"
  fi
  if [[ "$installed_revision" == "$required_revision" ]] \
      && "$python" "$summary_validator" --quiet; then
    summary_valid="1"
  fi
  if [[ "${HAVENWILD_REBUILD_ULPC_INDEX:-0}" == "1" \
        || ! -f content/assets/lpc/universal_lpc_complete_repository_index_v0_1.json.gz \
        || ! -f content/assets/lpc/universal_lpc_equipment_action_catalog_v0_1.json \
        || ! -f content/assets/lpc/universal_lpc_gameplay_item_seed_catalog_v0_1.json \
        || ! -f content/assets/lpc/universal_lpc_complete_repository_summary_v0_1.json \
        || "$installed_revision" != "$required_revision" \
        || "$summary_valid" != "1" ]]; then
    run_step "index complete Universal LPC character/equipment repository" \
      "$python" tools/automation/characters/Build-UniversalLpcCompleteRepositoryIndexV167Z7.py
    run_step "validate complete Universal LPC repository summary" \
      "$python" "$summary_validator"
    run_step "build normalized Universal LPC character metadata catalog" \
      "$python" tools/automation/characters/Build-UniversalLpcNormalizedCharacterCatalogV1.py
  else
    log "Complete Universal LPC character/equipment index and summary match $required_revision"
  fi
  if [[ ! -f content/assets/lpc/universal_lpc_normalized_character_catalog_v1.json.gz \
        || ! -f content/assets/lpc/universal_lpc_normalized_character_catalog_summary_v1.json ]]; then
    run_step "build normalized Universal LPC character metadata catalog" \
      "$python" tools/automation/characters/Build-UniversalLpcNormalizedCharacterCatalogV1.py
  fi
  local icon_validator="tools/automation/characters/Validate-UniversalLpcItemIconAtlasV1.py"
  if [[ ! -f assets/generated/lpc/item_icons/universal_lpc_item_icons_v1.png \
        || ! -f assets/generated/lpc/item_icons/universal_lpc_item_icons_v1.json ]] \
      || ! "$python" "$icon_validator" --quiet; then
    run_step "build Universal LPC player item icon atlas" \
      "$python" tools/automation/characters/Build-UniversalLpcItemIconAtlasV1.py
    run_step "validate Universal LPC player item icon atlas" \
      "$python" "$icon_validator"
  fi
}


build_lpc_project_foundation() {
  local python
  python="$(python_cmd)"
  run_step "build combined ElizaWy and Universal LPC project foundation" \
    "$python" tools/automation/assets/Build-LpcProjectFoundationV167Z40.py --strict
}


sync_oga_lpc_prototypes() {
  local python
  python="$(python_cmd)"
  run_step "sync curated OpenGameArt LPC prototype sources" \
    "$python" tools/automation/assets/Acquire-OgaLpcGameplayBatchV167S.py --all --best-effort
}

build_asset_promotion_closeout() {
  local python
  python="$(python_cmd)"
  if [[ "${1:-}" == "--strict" ]]; then
    run_step "build strict Havenwild asset promotion closeout matrix" \
      "$python" tools/automation/assets/Build-HavenwildAssetPromotionCloseoutV167Z84.py --strict
  else
    run_step "build Havenwild asset promotion closeout matrix" \
      "$python" tools/automation/assets/Build-HavenwildAssetPromotionCloseoutV167Z84.py
  fi
}


generate_lpc_summer_map() {
  local python
  python="$(python_cmd)"
  run_step "restore/verify Pass 95 summer runtime metadata"     "$python" tools/automation/terrain/Sync-LpcSummerRuntimeMetadataV108.py
  run_step "build complete LPC summer terrain source map" \
    "$python" tools/automation/terrain/Build-LpcTerrainSummerCompleteMapV103.py
}

generate_lpc_seasonal_topology() {
  local python
  python="$(python_cmd)"
  run_step "build shared LPC seasonal terrain topology"     "$python" tools/automation/terrain/Build-LpcSeasonalTerrainTopologyV106.py
}

generate_lpc_summer_runtime() {
  local python
  python="$(python_cmd)"
  run_step "ensure deterministic base terrain bootstrap" \
    "$python" tools/automation/terrain/Ensure-BaseTerrainBootstrapV145D.py
  run_step "promote active LPC summer runtime terrain families"     "$python" tools/automation/terrain/Promote-LpcTerrainFamiliesV90.py
  run_step "rebuild same-family autotile atlas from promoted LPC bases" \
    "$python" tools/automation/terrain/Generate-LiveAutotileAtlas.py
  run_step "build LPC summer runtime conformance board"     "$python" tools/automation/terrain/Build-LpcSummerRuntimeConformanceV107.py
  run_step "build mapped LPC terrain replacement atlas" \
    "$python" tools/automation/terrain/Build-LpcMappedTerrainV7.py
}

ensure_direct_lpc_compatibility_assets() {
  local required=(
    assets/generated/worldgen_v0_1/terrain/lpc_terrain_summer_complete_map_32.json
    assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.json
    assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.png
    assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.json
    assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.png
    assets/generated/worldgen_v0_1/terrain/lpc_expandable_ponds_32.json
    assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json
    assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.png
  )
  local missing=()
  local item
  for item in "${required[@]}"; do
    [[ -f "$item" ]] || missing+=("$item")
  done
  if [[ ${#missing[@]} -eq 0 ]]; then
    log "Direct-LPC editor/test compatibility assets are present"
    return 0
  fi

  log "Restoring ${#missing[@]} direct-LPC editor/test compatibility asset(s)"
  local python
  python="$(python_cmd)"
  run_step "restore/verify LPC summer runtime metadata" \
    "$python" tools/automation/terrain/Sync-LpcSummerRuntimeMetadataV108.py
  run_step "build complete LPC summer source map" \
    "$python" tools/automation/terrain/Build-LpcTerrainSummerCompleteMapV103.py
  run_step "ensure deterministic terrain compatibility bootstrap" \
    "$python" tools/automation/terrain/Ensure-BaseTerrainBootstrapV145D.py
  run_step "promote reviewed LPC terrain compatibility families" \
    "$python" tools/automation/terrain/Promote-LpcTerrainFamiliesV90.py
  run_step "rebuild live autotile compatibility atlas" \
    "$python" tools/automation/terrain/Generate-LiveAutotileAtlas.py
  run_step "promote expandable LPC pond compatibility contracts" \
    "$python" tools/automation/terrain/Promote-LpcExpandablePondsV87.py
  run_step "rebuild authored LPC terrain-map-v7 tuple atlas" \
    "$python" tools/automation/terrain/Build-LpcMappedTerrainV7.py
  log "Compatibility outputs restored; authored LPC sheets and exact tuple atlas are runtime authority"
}


prepare_direct_lpc_runtime_assets() {
  local python
  python="$(python_cmd)"
  ensure_universal_lpc_character_repository
  build_lpc_project_foundation
  local player_atlas="assets/generated/lpc/characters/havenwild_player_walk_64.png"
  local player_atlas_revision="assets/generated/lpc/characters/.generator_revision"
  local required_player_atlas_revision="167Z109V1-authored-action-alias-and-directional-coverage-v1"
  local installed_player_atlas_revision=""
  if [[ -f "$player_atlas_revision" ]]; then
    installed_player_atlas_revision="$(tr -d '\r\n' < "$player_atlas_revision")"
  fi
  if [[ "${HAVENWILD_REBUILD_PLAYER_ATLAS:-0}" == "1" \
        || ! -f "$player_atlas" \
        || "$installed_player_atlas_revision" != "$required_player_atlas_revision" ]]; then
    run_step "build Universal LPC character runtime caches" "$python" tools/automation/characters/Build-UniversalLpcPlayerRuntimeCachesV167Z7.py
  else
    log "LPC player atlases match generator revision $required_player_atlas_revision"
  fi

  local object_atlas_revision="assets/generated/.lpc_terrain_object_revision"
  local required_object_atlas_revision="AC3R4F-tree-visible-natural-object-rebuild-v1"
  local installed_object_atlas_revision=""
  if [[ -f "$object_atlas_revision" ]]; then
    installed_object_atlas_revision="$(tr -d '\r\n' < "$object_atlas_revision")"
  fi
  if [[ ! -f assets/generated/havenwild_lpc_objects_160x192_v2.png \
        || ! -f assets/generated/havenwild_lpc_objects_160x192_v2.json \
        || "$installed_object_atlas_revision" != "$required_object_atlas_revision" ]]; then
    run_step "build natural-scale ElizaWy tree and object atlas" \
      "$python" tools/automation/assets/Promote-LpcRuntimeAssets.py --objects-only
  else
    log "ElizaWy tree/object atlas matches revision $required_object_atlas_revision"
  fi

  ensure_direct_lpc_compatibility_assets
  log "Authored LPC sheets and exact terrain-map-v7 tuple atlas are runtime authority; heavy terrain certification is skipped during normal builds"
}

ensure_rebuildable_lpc_metadata_fast() {
  local python
  python="$(python_cmd)"
  if [[ ! -f content/assets/intake/external_pack_indexes/elizawy_lpc_main.json ]]; then
    run_step "restore rebuildable ElizaWy external-pack index" \
      "$python" tools/automation/assets/Build-ElizaWyExternalPackIndexV1.py
  fi
  local legacy_required=(
    content/assets/lpc/lpc_character_sheet_catalog_v0_1.json
    content/assets/lpc/lpc_character_animation_catalog_v0_1.json
    content/assets/lpc/lpc_character_repository_inventory_v0_1.json
    content/assets/lpc/lpc_character_production_catalog_v0_1.json
  )
  local missing_legacy=0
  local item
  for item in "${legacy_required[@]}"; do
    if [[ ! -f "$item" ]]; then
      missing_legacy=1
      break
    fi
  done
  if [[ "$missing_legacy" == "1" ]]; then
    run_step "restore rebuildable ElizaWy character metadata catalogs" \
      "$python" tools/automation/characters/Build-LpcLegacyCharacterCatalogsV1.py
  fi

  if [[ ! -f content/assets/lpc/lpc_slice_catalog_v0_1.json \
        || ! -f content/assets/lpc/lpc_slice_catalog_v0_1.json.gz \
        || ! -f content/assets/lpc/lpc_asset_library_bundle_v0_1.json.gz ]]; then
    run_step "restore rebuildable ElizaWy slice/library catalogs" \
      "$python" tools/automation/assets/Promote-LpcRuntimeAssets.py
  fi
}

prepare_direct_lpc_runtime_assets_fast() {
  local python
  python="$(python_cmd)"
  ensure_universal_lpc_character_repository_fast
  ensure_rebuildable_lpc_metadata_fast

  local player_atlas="assets/generated/lpc/characters/havenwild_player_walk_64.png"
  local player_atlas_revision="assets/generated/lpc/characters/.generator_revision"
  local required_player_atlas_revision="167Z109V1-authored-action-alias-and-directional-coverage-v1"
  local installed_player_atlas_revision=""
  if [[ -f "$player_atlas_revision" ]]; then
    installed_player_atlas_revision="$(tr -d '\r\n' < "$player_atlas_revision")"
  fi
  if [[ ! -f "$player_atlas" || "$installed_player_atlas_revision" != "$required_player_atlas_revision" ]]; then
    run_step "restore stale/missing Universal LPC runtime cache" \
      "$python" tools/automation/characters/Build-UniversalLpcPlayerRuntimeCachesV167Z7.py
  else
    log "LPC player runtime cache ready ($required_player_atlas_revision)"
  fi

  local object_atlas_revision="assets/generated/.lpc_terrain_object_revision"
  local required_object_atlas_revision="AC3R4F-tree-visible-natural-object-rebuild-v1"
  local installed_object_atlas_revision=""
  if [[ -f "$object_atlas_revision" ]]; then
    installed_object_atlas_revision="$(tr -d '\r\n' < "$object_atlas_revision")"
  fi
  if [[ ! -f assets/generated/havenwild_lpc_objects_160x192_v2.png \
        || ! -f assets/generated/havenwild_lpc_objects_160x192_v2.json \
        || "$installed_object_atlas_revision" != "$required_object_atlas_revision" ]]; then
    run_step "restore stale/missing ElizaWy object runtime cache" \
      "$python" tools/automation/assets/Promote-LpcRuntimeAssets.py --objects-only
  else
    log "ElizaWy object runtime cache ready ($required_object_atlas_revision)"
  fi

  ensure_direct_lpc_compatibility_assets
  log "Fast development dependency/runtime sentinel checks complete"
}

generate_lpc_runtime_assets() {
  local python
  python="$(python_cmd)"
  ensure_universal_lpc_character_repository
  build_lpc_project_foundation
  generate_lpc_summer_map
  generate_lpc_seasonal_topology
  generate_lpc_summer_runtime
  run_step "promote expandable LPC pond families" \
    "$python" tools/automation/terrain/Promote-LpcExpandablePondsV87.py
  local player_atlas="assets/generated/lpc/characters/havenwild_player_walk_64.png"
  local player_atlas_revision="assets/generated/lpc/characters/.generator_revision"
  local required_player_atlas_revision="167Z109V1-authored-action-alias-and-directional-coverage-v1"
  local installed_player_atlas_revision=""
  if [[ -f "$player_atlas_revision" ]]; then
    installed_player_atlas_revision="$(tr -d '\r\n' < "$player_atlas_revision")"
  fi
  if [[ "${HAVENWILD_REBUILD_PLAYER_ATLAS:-0}" == "1" \
        || ! -f "$player_atlas" \
        || "$installed_player_atlas_revision" != "$required_player_atlas_revision" ]]; then
    run_step "build Universal LPC character runtime caches" "$python" tools/automation/characters/Build-UniversalLpcPlayerRuntimeCachesV167Z7.py
  else
    log "LPC player atlases match generator revision $required_player_atlas_revision"
  fi

  local object_atlas_revision="assets/generated/.lpc_terrain_object_revision"
  local required_object_atlas_revision="AC3R4F-tree-visible-natural-object-rebuild-v1"
  local installed_object_atlas_revision=""
  if [[ -f "$object_atlas_revision" ]]; then
    installed_object_atlas_revision="$(tr -d '\r\n' < "$object_atlas_revision")"
  fi
  if [[ ! -f assets/generated/havenwild_lpc_objects_160x192_v2.png \
        || ! -f assets/generated/havenwild_lpc_objects_160x192_v2.json \
        || "$installed_object_atlas_revision" != "$required_object_atlas_revision" ]]; then
    run_step "build natural-scale ElizaWy tree and object atlas" \
      "$python" tools/automation/assets/Promote-LpcRuntimeAssets.py --objects-only
  else
    log "ElizaWy tree/object atlas matches revision $required_object_atlas_revision"
  fi

  if [[ -f assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.json \
        && -f assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.json ]]; then
    run_step "build LPC world-paint compatibility atlas" \
      "$python" tools/automation/worldgen/Build-LpcWorldPaintEnvironmentTest.py
  else
    log "LPC terrain outputs are not present yet; world-paint compatibility bake deferred to tiles"
  fi

  run_step "materialize topology-validated open-world biome test scene" \
    "$python" tools/automation/worldgen/Build-ClientWorldgenTestSceneV167Z.py
  run_step "generate terrain acceptance topology scenes" \
    "$python" tools/automation/terrain/Generate-TerrainAcceptanceScenes.py
  run_step "regenerate W77 transition authoring workbench" \
    "$python" tools/automation/terrain/Build-TerrainTransitionWorkbenchW77.py
  run_step "validate W77 exact terrain presentation + transition workbench" \
    "$python" tools/automation/validation/checks/terrain/Validate-TerrainPresentationAuthorityAndWorkbenchW77.py
  run_step "render production LPC terrain certification evidence" \
    "$python" tools/automation/terrain/Render-TerrainLpcCertification.py
  run_step "validate terrain topology, LPC evidence, and retained frame plan" \
    "$python" tools/automation/validation/validate_terrain_topology_v167z5.py
}


validate_character_pipeline() {
  local python
  python="$(python_cmd)"
  run_step "validate active character runtime integration"     "$python" tools/automation/validation/checks/characters/Validate-CharacterRuntimeIntegrationV150H.py
}

validate_current_capabilities() {
  local suite="${1:-all}"
  local python
  python="$(python_cmd)"
  local profile="source"
  [[ "$suite" == "build" || "$suite" == "quick" || "$suite" == "full" || "$suite" == "source" || "$suite" == "framework" ]] && profile="$suite"
  run_step "current validation profile: $profile" "$python" tools/automation/validation/validation_runner.py "$profile"
}

validate() {
  local domain="${1:-all}"
  local python
  python="$(python_cmd)"
  run_step "Havenwild validation: $domain" "$python" tools/automation/validation/validate.py "$domain"
}

normalize_rust_source() {
  require cargo
  run_step "normalize Rust formatting before architecture validation" cargo fmt --all
}

normalize_rust_source_after_validation() {
  require cargo
  run_step "re-normalize Rust formatting after read-only validation" cargo fmt --all
}

rust_check_fast() {
  require cargo
  run_step "cargo fmt --all -- --check" cargo fmt --all -- --check
  run_step "cargo check --workspace --all-targets" cargo check --workspace --all-targets
}

rust_check_strict() {
  require cargo
  rust_check_fast
  run_step "cargo clippy --workspace --all-targets -- -D warnings" cargo clippy --workspace --all-targets -- -D warnings
}

rust_checkpoint() {
  require cargo
  rust_check_strict
  run_step "cargo test --workspace" cargo test --workspace
  run_step "cargo build --workspace" cargo build --workspace
}

cargo_only() {
  require cargo
  rust_checkpoint
}

copy_application_content() {
  local destination="$1"
  local python
  python="$(python_cmd)"
  "$python" tools/automation/release/Stage-ApplicationContent.py "$destination"
}

build_release_client() {
  require cargo
  mkdir -p Build/HavenwildClient
  run_step "cargo build --release -p haven_game" cargo build --release -p haven_game
  if [[ ! -f target/release/haven_game.exe ]]; then
    log "ERROR: client executable was not produced: $ROOT/target/release/haven_game.exe"
    return 1
  fi
  cp -f target/release/haven_game.exe Build/HavenwildClient/HavenwildClient.exe
  copy_application_content Build/HavenwildClient
  log "Client: $ROOT/Build/HavenwildClient/HavenwildClient.exe"
}

build_release_apps() {
  require cargo
  mkdir -p Build/HavenwildClient Build/HavenwildEditor
  run_step "cargo build --release -p haven_game -p haven_editor_native" \
    cargo build --release -p haven_game -p haven_editor_native

  if [[ ! -f target/release/haven_game.exe ]]; then
    log "ERROR: client executable was not produced: $ROOT/target/release/haven_game.exe"
    return 1
  fi
  if [[ ! -f target/release/haven_editor_native.exe ]]; then
    log "ERROR: editor executable was not produced: $ROOT/target/release/haven_editor_native.exe"
    return 1
  fi

  cp -f target/release/haven_game.exe Build/HavenwildClient/HavenwildClient.exe
  cp -f target/release/haven_editor_native.exe Build/HavenwildEditor/HavenwildEditor.exe
  copy_application_content Build/HavenwildClient
  copy_application_content Build/HavenwildEditor
  log "Client: $ROOT/Build/HavenwildClient/HavenwildClient.exe"
  log "Editor: $ROOT/Build/HavenwildEditor/HavenwildEditor.exe"
}


build_dev_client() {
  require cargo
  run_step "cargo build -p haven_game (dev profile)" cargo build -p haven_game
  log "Development client: $ROOT/target/debug/haven_game.exe"
}


run_development_world() {
  require python
  require cargo
  local descriptor="$ROOT/WORKSPACE/development/active_world.json"
  local client="$ROOT/target/debug/haven_game.exe"
  if [[ ! -f "$descriptor" ]]; then
    log "ERROR: development-world descriptor is missing: $descriptor"
    return 1
  fi
  local values world_id character_id default_scene spawn_x spawn_y
  values="$(python - "$descriptor" <<'PY'
import json,sys
p=sys.argv[1]
d=json.load(open(p,encoding='utf-8'))
if d.get('schema')!='havenwild.development_world.v1':
    raise SystemExit('unsupported development-world descriptor schema')
for key in ('world_id','character_id'):
    if not str(d.get(key,'')).strip(): raise SystemExit(f'missing {key}')
sp=d.get('spawn') or {}
print(d['world_id'])
print(d['character_id'])
print(d.get('default_scene',''))
x=sp.get('x',None); y=sp.get('y',None)
if x is not None and (isinstance(x,bool) or not isinstance(x,int)):
    raise SystemExit('spawn.x must be an integer tile coordinate')
if y is not None and (isinstance(y,bool) or not isinstance(y,int)):
    raise SystemExit('spawn.y must be an integer tile coordinate')
print('' if x is None else int(x))
print('' if y is None else int(y))
PY
)" || return 1
  mapfile -t fields <<< "$values"
  world_id="${fields[0]:-}"; character_id="${fields[1]:-}"; default_scene="${fields[2]:-}"; spawn_x="${fields[3]:-}"; spawn_y="${fields[4]:-}"

  # Git Bash/MSYS can preserve CR/LF characters in command-substitution fields.
  # Normalize descriptor-derived scalar values before validating or forwarding
  # them as client command-line arguments.
  world_id="${world_id//$'\r'/}"; world_id="${world_id//$'\n'/}"
  character_id="${character_id//$'\r'/}"; character_id="${character_id//$'\n'/}"
  default_scene="${default_scene//$'\r'/}"; default_scene="${default_scene//$'\n'/}"
  spawn_x="${spawn_x//$'\r'/}"; spawn_x="${spawn_x//$'\n'/}"
  spawn_y="${spawn_y//$'\r'/}"; spawn_y="${spawn_y//$'\n'/}"
  if [[ ! -f "$client" ]]; then
    run_step "build missing development client" cargo build -p haven_game
  fi
  local launch_args=(--dev-world "$world_id" --dev-character "$character_id")
  if [[ -n "$default_scene" ]]; then launch_args+=(--dev-scene "$default_scene"); fi
  if [[ -n "$spawn_x" ]]; then
    [[ "$spawn_x" =~ ^-?[0-9]+$ ]] || { log "ERROR: invalid development spawn.x: '$spawn_x'"; return 1; }
    launch_args+=(--dev-x="$spawn_x")
  fi
  if [[ -n "$spawn_y" ]]; then
    [[ "$spawn_y" =~ ^-?[0-9]+$ ]] || { log "ERROR: invalid development spawn.y: '$spawn_y'"; return 1; }
    launch_args+=(--dev-y="$spawn_y")
  fi
  log "Launching development world: $world_id"
  log "Development character: $character_id"
  log "Requested development scene: ${default_scene:-<world default>} (stale generated ids fall back to the loaded world scene)"
  local world_file="$ROOT/WORKSPACE/saves/$world_id/world.tworld"
  if [[ ! -f "$world_file" ]]; then
    log "Development world save is missing; haven_game will provision the canonical deterministic development world on launch"
  fi
  log "Development client: $client"
  local client_log_dir="$ROOT/logs/development"
  mkdir -p "$client_log_dir"
  local client_log="$client_log_dir/dev-client-$(date +%Y%m%d-%H%M%S).log"
  log "Development client log: $client_log"
  (cd "$ROOT" && "$client" "${launch_args[@]}") >"$client_log" 2>&1 &
  local pid=$!
  local startup_ok=1
  for _ in 1 2 3; do
    sleep 1
    if ! kill -0 "$pid" 2>/dev/null; then startup_ok=0; break; fi
    if grep -q "Havenwild development launch failed:" "$client_log" 2>/dev/null; then startup_ok=0; break; fi
  done
  if [[ "$startup_ok" -ne 1 ]]; then
    local exit_code=0
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
      exit_code=1
    else
      wait "$pid" || exit_code=$?
    fi
    log "ERROR: development client failed startup verification (PID $pid, exit $exit_code)"
    if [[ -s "$client_log" ]]; then
      log "----- development client output -----"
      while IFS= read -r line; do log "CLIENT: $line"; done < "$client_log"
      log "----- end development client output -----"
    fi
    return 1
  fi
  log "Development world launched successfully (PID $pid); startup verified for 3s; frontend bypassed"
}

build_dev_apps() {
  require cargo
  run_step "cargo build -p haven_game -p haven_editor_native (dev profile)" \
    cargo build -p haven_game -p haven_editor_native
  log "Development client: $ROOT/target/debug/haven_game.exe"
  log "Development editor: $ROOT/target/debug/haven_editor_native.exe"
}

web_check() {
  log "The legacy browser editor is archived under archive/source/legacy_web_editor."
  log "Use the native Havenwild editor or the in-game Player World Builder."
}

doctor() {
  log "Repository root: $ROOT"
  log "Bash: ${BASH_VERSION:-unknown}"
  log "Bash executable: $(command -v bash || printf 'not found')"
  log "Cargo: $(command -v cargo || printf 'not found')"
  log "Rustc: $(command -v rustc || printf 'not found')"
  log "Python: $(command -v python3 || command -v python || printf 'not found')"
  log "Node: $(command -v node || printf 'not found')"
  if command -v cargo >/dev/null 2>&1; then cargo --version; fi
  if command -v rustc >/dev/null 2>&1; then rustc --version; fi
  if command -v python3 >/dev/null 2>&1; then python3 --version; elif command -v python >/dev/null 2>&1; then python --version; fi
  if command -v node >/dev/null 2>&1; then node --version; fi
}

log "Havenwild bash build started ($COMMAND)"
log "Repository root: $ROOT"
normalize_workspace_layout
log "Active Rust sources are authoritative; legacy build-time source rewriters are disabled"

case "$COMMAND" in
  devgame) run_development_world ;;
  dev|all)
    ensure_frontend_music
    ensure_lpc_dependency_fast
    prepare_direct_lpc_runtime_assets_fast
    require cargo
    run_step "cargo check --workspace --all-targets" cargo check --workspace --all-targets
    build_dev_apps
    ;;
  cargo-only) cargo_only ;;
  rust) ensure_lpc_dependency; ensure_direct_lpc_compatibility_assets; rust_checkpoint ;;
  check) rust_check_fast ;;
  test)
    ensure_lpc_dependency
    ensure_direct_lpc_compatibility_assets
    require cargo
    run_step "cargo test --workspace" cargo test --workspace
    run_step "validate W57K10A-W60 unified authoring authority" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-UnifiedCanvasAuthoringW60.py
    run_step "validate W60B editor UI authority" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-EditorUiAuthorityW60B.py
    run_step "validate W60C canvas UX and asset-browser authority" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-CanvasUxAssetBrowserW60C.py
    run_step "validate W60D ruler-safe canvas corner layer dock" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-CanvasCornerLayerDockW60D.py
    run_step "validate W60E1 shared canvas composition" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-SharedCanvasCompositionW60E1.py
    run_step "validate W60E2 collision truth" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-CollisionAuthoringW60E2.py
    run_step "validate W60E3 CanvasWorkspace authority" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-CanvasWorkspaceAuthorityW60E3.py
    run_step "validate W60E3I Building Composite authoring handoff" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-BuildingCompositeAuthoringHandoffW60E3I.py
    run_step "validate W60E4 Building Composite runtime publish" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-BuildingCompositeRuntimePublishW60E4.py
    run_step "validate W60E5 contextual CanvasWorkspace workflow" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-ContextualCanvasWorkflowW60E5.py
    run_step "validate W60E6 Pixel interaction and symmetry workflow" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-PixelInteractionSymmetryW60E6.py
    run_step "validate W60E7 structural selected-region round trip" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-StructuralCanvasRoundTripW60E7.py
    run_step "validate W60E7 Canvas tool capability truth" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-CanvasToolCapabilityTruthW60E7.py
    run_step "validate W60E8 tool adapter completion" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-ToolAdapterCompletionW60E8.py
    run_step "validate W60E9 gameplay layer adapters" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-GameplayLayerAdaptersW60E9.py
    run_step "validate W60E10 pixel selection transforms" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-PixelSelectionTransformsW60E10.py
    run_step "validate W60E11 animation metadata" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-AnimationMetadataW60E11.py
    run_step "validate W60E12 shared inspector/canvas normalization" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-SharedInspectorCanvasW60E12.py
    run_step "validate W60E13 canvas chrome/widget normalization" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-CanvasChromeWidgetNormalizationW60E13.py
    run_step "validate W60E14 tool taxonomy/options" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-ToolTaxonomyOptionsW60E14.py
    run_step "validate W60E15 pixel viewport alignment" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-PixelViewportAlignmentW60E15.py
    run_step "validate W60E16 project-wide panel mapping" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-ProjectPanelMappingW60E16.py
    run_step "validate W60E17 Character Studio foundation" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-CharacterStudioFoundationW60E17.py
    run_step "validate W60E18 Logic Node Editor architecture lock" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-LogicNodeEditorContractW60E18.py
    run_step "validate W60E19 Pixel multi-document clipboard/promotion" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-PixelMultiDocumentClipboardW60E19.py
    run_step "validate W60E20 integrated canvas rails" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-IntegratedCanvasRailsW60E20.py
    run_step "validate W60E21 canvas view chrome" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-CanvasViewChromeW60E21.py
    run_step "validate W60E22 editor command routing" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-EditorCommandRoutingW60E22.py
    run_step "validate W60E23 inspector/bottom dock normalization" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-InspectorBottomDockW60E23.py
    run_step "validate W60E24 native widget/palette normalization" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-NativeWidgetPaletteW60E24.py
    run_step "validate W61A Transform2D authority" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-Transform2DAuthorityW61A.py
    run_step "validate W61B anchor/socket authority" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-AnchorSocketAuthorityW61B.py
    run_step "validate W61C selection transform gizmo/clipboard" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-SelectionTransformGizmoW61C.py
    run_step "validate W61D animation hinge metadata" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-AnimationHingeMetadataW61D.py
    run_step "validate W76A-T native editor GUI closure" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-NativeEditorGuiClosureW76.py
    run_step "validate W76U-V GameMaker workspace document lifecycle" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-GameMakerWorkspaceDocumentLifecycleW76UV.py
    run_step "validate W77 exact terrain presentation + transition workbench" "$(python_cmd)" tools/automation/validation/checks/terrain/Validate-TerrainPresentationAuthorityAndWorkbenchW77.py
    run_step "validate W78 native editor GUI authority cleanup" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-NativeEditorGuiAuthorityCleanupW78.py
    run_step "validate W79 native editor interaction/document closure" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-NativeEditorInteractionDocumentClosureW79.py
    run_step "validate HW-AUTHORITY-05 document lifecycle authority" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-DocumentAuthorityAuth05.py
    run_step "validate HW-AUTHORITY-05 document lifecycle authority" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-AuthoringAuthorityAuth10.py
    run_step "validate W80 Tool Rail + Layer Rail production completion" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-ToolLayerRailProductionW80.py
    run_step "validate A14Z palette preview + icon button polish" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-PalettePreviewIconButtonsA14Z.py
    run_step "validate A14AA semantic layer visibility + multi-selection" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-SemanticLayerVisibilitySelectionA14AA.py
    run_step "validate A14AB terrain tile + variant authoring" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-TerrainTileVariantAuthoringA14AB.py
    run_step "validate A14AB3 development runtime startup responsiveness" "$(python_cmd)" tools/automation/validation/checks/runtime/Validate-DevelopmentRuntimeStartupResponsivenessA14AB3.py
    run_step "validate A14AB4 streaming cadence + ramp presentation" "$(python_cmd)" tools/automation/validation/checks/runtime/Validate-StreamingCadenceRampPresentationA14AB4.py
    run_step "validate A14AB8 Home Estate runtime isolation" "$(python_cmd)" tools/automation/validation/checks/runtime/Validate-HomeEstateRuntimeIsolationA14AB8.py
    run_step "validate A14AB9-AB18 LPC content + gameplay integration" "$(python_cmd)" tools/automation/validation/checks/gameplay/Validate-LpcGameplayExpansionA14AB18.py
    run_step "validate A14AB19-AB28 player-facing GUI production closure" "$(python_cmd)" tools/automation/validation/checks/ui/Validate-PlayerFacingGuiProductionA14AB28.py
    run_step "validate A14AB29 lean reproducible source-rollup authority" "$(python_cmd)" tools/automation/validation/checks/project/Validate-LeanSourceRollupPolicyA14AB29.py
    run_step "validate A14AB30-AB39 terrain/cliff + Pixel Studio closeout" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-TerrainCliffPixelCloseoutA14AB39.py
    run_step "validate A14AB40-AB49 player interaction + GUI production closure" "$(python_cmd)" tools/automation/validation/checks/ui/Validate-PlayerInteractionGuiA14AB49.py
    run_step "validate W81 World Terrain Authoring + Global Tooltip Authority" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-WorldTerrainAuthoringW81.py
    run_step "validate W81R30-R44H6 editor UX + real world view closure" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-EditorUxRealWorldViewW81R30R44H6.py
    run_step "validate W81R30-R44H8 production archipelago scale + main-island authority" "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-ProductionArchipelagoScaleW81R30R44H8.py
    run_step "validate W81R6 Character Builder foundation + shared authority" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-CharacterBuilderSharedAuthorityW81R6.py
    run_step "validate W81R7-R16 Character Builder production closure" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-CharacterBuilderProductionClosureW81R7R16.py
    ;;
  validate) validate "${1:-all}" ;;
  certify) validate_current_capabilities full ;;
  framework-audit) validate_current_capabilities framework ;;
  character-audit)
    require cargo
    run_step "cargo test character pipeline" cargo test --workspace character
    run_step "build Universal LPC Character Conformance Lab" "$(python_cmd)" tools/automation/characters/Build-UniversalLpcCharacterConformanceLabV1.py
    run_step "validate C1-C20 Universal LPC character/gameplay conformance" "$(python_cmd)" tools/automation/validation/checks/characters/Validate-UniversalLpcCharacterConformanceC1C20.py
    ;;
  catalog) run_step "generate asset catalog" "$(python_cmd)" tools/automation/assets/Generate-AssetCatalog.py ;;
  asset-pack-prepare)
    if [[ $# -lt 1 ]]; then
      log "ERROR: asset-pack-prepare requires the path to a ZIP archive"
      log 'Example: ./tools/build/Build.sh asset-pack-prepare "C:/Assets/Asset Pack.zip" --license-status cc0'
      exit 2
    fi
    run_step "prepare external asset pack"       "$(python_cmd)" tools/automation/assets/Prepare-ExternalAssetPack.py "$@"
    run_step "catalog external sprite library"       "$(python_cmd)" tools/automation/assets/Catalog-ExternalSpriteLibrary.py
    ;;
  asset-pack-catalog)
    run_step "catalog external sprite library"       "$(python_cmd)" tools/automation/assets/Catalog-ExternalSpriteLibrary.py
    ;;
  asset-pack-audit)
    run_step "validate external asset pack intake"       "$(python_cmd)" tools/automation/validation/checks/assets/Validate-ExternalAssetPackIntakeV83.py
    ;;
  asset-utilization-audit)
    run_step "build Havenwild asset utilization audit" \
      "$(python_cmd)" tools/automation/assets/Build-HavenwildAssetUtilizationAuditV115.py "$@"
    run_step "validate Havenwild asset utilization audit workflow" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-HavenwildAssetUtilizationAuditV115.py
    ;;
  source-rollup)
    run_step "create compact ChatGPT/Codex source rollup"       "$(python_cmd)" tools/automation/packaging/Create-ChatGPTSourceRollup.py "$@"
    ;;
  source-only)
    run_step "create source-only rollup without assets"       "$(python_cmd)" tools/automation/packaging/Create-SourceOnlyRollup.py "$@"
    ;;
  lpc-sync)
    ensure_lpc_dependency
    ensure_universal_lpc_character_repository
    sync_oga_lpc_prototypes
    build_lpc_project_foundation
    build_asset_promotion_closeout --strict
    ;;
  lpc-audit)
    ensure_lpc_dependency
    run_step "force complete ElizaWy/LPC project asset audit"       "$(python_cmd)" tools/automation/assets/Build-ElizaWyProjectAssetAuditV167Z38.py --force --strict
    ensure_universal_lpc_character_repository
    build_lpc_project_foundation
    build_asset_promotion_closeout --strict
    ;;
  lpc-foundation)
    ensure_lpc_dependency
    ensure_universal_lpc_character_repository
    build_lpc_project_foundation
    build_asset_promotion_closeout --strict
    ;;
  asset-sources)
    ensure_lpc_dependency
    ensure_universal_lpc_character_repository
    sync_oga_lpc_prototypes
    build_lpc_project_foundation
    build_asset_promotion_closeout --strict
    ;;
  oga-prototypes)
    sync_oga_lpc_prototypes
    ;;
  asset-promotion-audit)
    build_asset_promotion_closeout
    ;;
  asset-truth)
    run_step "build W41A world asset truth inventory" \
      "$(python_cmd)" tools/automation/assets/Build-PublishedWorldAssetInventoryV1.py --root "$ROOT"
    run_step "validate W41A world asset truth inventory" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-PublishedWorldAssetInventoryV1.py
    ;;
  published-assets)
    run_step "build W41A world asset truth inventory" \
      "$(python_cmd)" tools/automation/assets/Build-PublishedWorldAssetInventoryV1.py --root "$ROOT"
    run_step "validate W41A world asset truth inventory" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-PublishedWorldAssetInventoryV1.py
    run_step "validate W42 published world asset authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-PublishedWorldAssetAuthorityV1.py
    ;;
  asset-acceptance)
    run_step "build W41A world asset truth inventory" \
      "$(python_cmd)" tools/automation/assets/Build-PublishedWorldAssetInventoryV1.py --root "$ROOT"
    run_step "validate W42 published world asset authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-PublishedWorldAssetAuthorityV1.py
    run_step "build W43A world asset acceptance scene" \
      "$(python_cmd)" tools/automation/assets/Build-WorldAssetAcceptanceSceneV1.py --root "$ROOT"
    run_step "validate W43A world asset acceptance scene" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-WorldAssetAcceptanceSceneV1.py
    run_step "validate W43B complete placeable visual sweep" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-PlaceableVisualSweepV1.py
    run_step "validate W43C Estate visual authority closure" \
      "$(python_cmd)" tools/automation/validation/checks/editor/Validate-EstateVisualAuthorityClosureV1.py
    run_step "build W43D complete placeable acceptance scene" \
      "$(python_cmd)" tools/automation/assets/Build-PlaceableVisualAcceptanceSceneV1.py --root "$ROOT"
    run_step "validate W43D complete placeable acceptance scene" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-PlaceableVisualAcceptanceSceneV1.py
    ;;
  exact-source)
    run_step "validate W44A exact-source Pixel Studio authority" \
      "$(python_cmd)" tools/automation/validation/checks/editor/Validate-ExactSourcePixelStudioAuthorityV1.py
    ;;
  structure-sources)
    run_step "build W45A LPC structure source inventory" \
      "$(python_cmd)" tools/automation/assets/Build-StructureSourceInventoryV1.py --root "$ROOT"
    run_step "validate W45A LPC structure source inventory" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-StructureSourceInventoryV1.py
    ;;
  structure-components)
    run_step "build W45A/W45B LPC structure source inventory" \
      "$(python_cmd)" tools/automation/assets/Build-StructureSourceInventoryV1.py --root "$ROOT"
    run_step "validate W45A/W45B LPC structure source inventory" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-StructureSourceInventoryV1.py
    run_step "build W45B exact structure component runtime cache" \
      "$(python_cmd)" tools/automation/assets/Build-StructureComponentCertificationV1.py --root "$ROOT"
    run_step "validate W45B exact structure component authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-StructureComponentCertificationV1.py
    ;;
  structure-surfaces)
    run_step "build W45A-W45C LPC structure source inventory" \
      "$(python_cmd)" tools/automation/assets/Build-StructureSourceInventoryV1.py --root "$ROOT"
    run_step "validate W45A-W45C LPC structure source inventory" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-StructureSourceInventoryV1.py
    run_step "build W45B exact structure component runtime cache" \
      "$(python_cmd)" tools/automation/assets/Build-StructureComponentCertificationV1.py --root "$ROOT"
    run_step "validate W45B exact structure component authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-StructureComponentCertificationV1.py
    run_step "build W45C structure surface runtime cache" \
      "$(python_cmd)" tools/automation/assets/Build-StructureSurfaceCertificationV1.py --root "$ROOT"
    run_step "build W45C structure surface acceptance scene" \
      "$(python_cmd)" tools/automation/assets/Build-StructureSurfaceAcceptanceSceneV1.py --root "$ROOT"
    run_step "build W45C machine-local roof/wall-trim review boards when LPC source is mounted" \
      "$(python_cmd)" tools/automation/assets/Build-StructureRoofTrimReviewV1.py --root "$ROOT"
    run_step "validate W45C structure surface + building visibility authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-StructureSurfaceCertificationV1.py
    ;;
  structure-roof-trim)
    run_step "build W45A-W45C2 LPC structure source inventory" \
      "$(python_cmd)" tools/automation/assets/Build-StructureSourceInventoryV1.py --root "$ROOT"
    run_step "build W45C structure surface runtime cache" \
      "$(python_cmd)" tools/automation/assets/Build-StructureSurfaceCertificationV1.py --root "$ROOT"
    run_step "build W45C2 exact wall-border runtime cache" \
      "$(python_cmd)" tools/automation/assets/Build-StructureRoofTrimCertificationV1.py --root "$ROOT"
    run_step "build W45C2 roof/trim acceptance scene" \
      "$(python_cmd)" tools/automation/assets/Build-StructureRoofTrimAcceptanceSceneV1.py --root "$ROOT"
    run_step "build machine-local roof review boards when LPC source is mounted" \
      "$(python_cmd)" tools/automation/assets/Build-StructureRoofTrimReviewV1.py --root "$ROOT"
    run_step "validate W45C2 roof topology + wall-border authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-StructureRoofTrimCertificationV1.py
    ;;
  structure-roof-review)
    ensure_lpc_dependency
    run_step "build W45C3A exact roof evidence bundle" \
      "$(python_cmd)" tools/automation/assets/Build-ExactRoofReviewEvidenceV1.py --root "$ROOT" --require-all
    run_step "validate W45C3A exact roof review authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-ExactRoofReviewEvidenceV1.py
    ;;
  structure-support-review)
    ensure_lpc_dependency
    run_step "build W45D1 exact bridge/platform/pillar evidence bundle" \
      "$(python_cmd)" tools/automation/assets/Build-StructureSupportReviewEvidenceV1.py --root "$ROOT" --require-all
    run_step "validate W45D1 structure support topology + exact review authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-StructureSupportReviewEvidenceV1.py
    ;;
  structure-exact-modules)
    ensure_lpc_dependency
    run_step "rebuild W45D2 structure source inventory" \
      "$(python_cmd)" tools/automation/assets/Build-StructureSourceInventoryV1.py --root "$ROOT"
    run_step "build W45D2 exact roof/support acceptance scene" \
      "$(python_cmd)" tools/automation/assets/Build-ExactStructureModuleAcceptanceSceneV1.py --root "$ROOT"
    run_step "validate W45C3B/W45D2 exact roof/support publication" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-ExactStructureModulePublicationV1.py
    ;;
  building-recipes)
    run_step "build W46A BuildingRecipe acceptance scene" \
      "$(python_cmd)" tools/automation/assets/Build-BuildingRecipeAcceptanceSceneV1.py --root "$ROOT"
    run_step "validate W46A BuildingRecipe authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-BuildingRecipeAuthorityV1.py
    ;;
  building-instances)
    run_step "rebuild W46A BuildingRecipe acceptance baseline" \
      "$(python_cmd)" tools/automation/assets/Build-BuildingRecipeAcceptanceSceneV1.py --root "$ROOT"
    run_step "validate W46A BuildingRecipe authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-BuildingRecipeAuthorityV1.py
    run_step "build W46B native BuildingInstance acceptance scene" \
      "$(python_cmd)" tools/automation/assets/Build-BuildingInstanceAcceptanceSceneV1.py --root "$ROOT"
    run_step "validate W46B BuildingInstance runtime/editor authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-BuildingInstanceAuthorityV1.py
    ;;
  building-persistence)
    run_step "rebuild W46B native BuildingInstance acceptance baseline" \
      "$(python_cmd)" tools/automation/assets/Build-BuildingInstanceAcceptanceSceneV1.py --root "$ROOT"
    run_step "validate W46B BuildingInstance runtime/editor authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-BuildingInstanceAuthorityV1.py
    run_step "build W46C placement/persistence/PCG acceptance scene" \
      "$(python_cmd)" tools/automation/assets/Build-BuildingPersistenceAcceptanceSceneV1.py --root "$ROOT"
    run_step "validate W46C BuildingInstance placement/persistence authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-BuildingInstancePersistenceAuthorityV1.py
    ;;
  building-interiors)
    run_step "rebuild W46C placement/persistence acceptance baseline" \
      "$(python_cmd)" tools/automation/assets/Build-BuildingPersistenceAcceptanceSceneV1.py --root "$ROOT"
    run_step "validate W46C BuildingInstance placement/persistence authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-BuildingInstancePersistenceAuthorityV1.py
    run_step "validate W47 same-world interior grammar authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-BuildingInteriorGrammarV1.py
    ;;
  production-tavern)
    run_step "validate W47 same-world interior grammar authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-BuildingInteriorGrammarV1.py
    run_step "build W48 production tavern acceptance scene" \
      "$(python_cmd)" tools/automation/assets/Build-TavernBuildingAcceptanceSceneV1.py --root "$ROOT"
    run_step "validate W48 production tavern BuildingInstance authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-ProductionTavernAuthorityV1.py
    ;;
  cave-assets)
    run_step "validate W49 cave asset authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-CaveAssetAuthorityV1.py
    ;;
  cave-resolver)
    run_step "validate W49 cave asset authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-CaveAssetAuthorityV1.py
    run_step "build W50 cave resolver/PCG acceptance scene" \
      "$(python_cmd)" tools/automation/assets/Build-CaveResolverAcceptanceSceneV1.py --root "$ROOT"
    run_step "validate W50 cave resolver/PCG/editor authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-CaveResolverAuthorityV1.py
    ;;
  structural-connectors)
    run_step "build W51 structural connector acceptance scene" \
      "$(python_cmd)" tools/automation/assets/Build-StructuralConnectorAcceptanceSceneV1.py --root "$ROOT"
    run_step "validate W51 structural connector authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-StructuralConnectorAuthorityV1.py
    ;;
  world-visual-certification)
    run_step "validate W49 cave asset authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-CaveAssetAuthorityV1.py
    run_step "validate W50 cave resolver/PCG/editor authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-CaveResolverAuthorityV1.py
    run_step "validate W51 structural connector authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-StructuralConnectorAuthorityV1.py
    run_step "build W52 production tavern visual closure" \
      "$(python_cmd)" tools/automation/assets/Build-TavernBuildingAcceptanceSceneV1.py --root "$ROOT"
    run_step "build W52 world visual certification acceptance scene" \
      "$(python_cmd)" tools/automation/assets/Build-WorldVisualCertificationAcceptanceV1.py --root "$ROOT"
    run_step "validate W52 world visual certification" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-WorldVisualCertificationV1.py
    run_step "validate W56 scene population + narrow cave-mouth authority" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-W56ScenePopulationAuthority.py
    run_step "build W56F cliff-height/editor-runtime parity fixture" \
      "$(python_cmd)" tools/automation/worldgen/Build-CliffHeightAcceptanceW53D.py
    run_step "validate W56F cliff-height/editor-runtime parity" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-CliffHeightRuntimeGrammarW53D.py
    run_step "validate W56G editor/runtime object identity + anchor parity" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-W56EditorRuntimeObjectParity.py
    run_step "validate W56 cave-mouth geometry contract" \
      "$(python_cmd)" tools/validation/Validate-W56-CaveMouthContract.py
    run_step "validate W56 cave round-trip transition safety" \
      "$(python_cmd)" tools/validation/Validate-W56-CaveRoundTrip.py
    run_step "build W56I/J integrated visual acceptance scene" \
      "$(python_cmd)" tools/automation/worldgen/Build-W56IntegratedVisualAcceptance.py
    run_step "validate W56I/J integrated editor/client visual acceptance" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-W56IntegratedVisualAcceptance.py
    ;;
  cliff-height-grammar)
    run_step "build W53D cliff-height acceptance fixture" \
      "$(python_cmd)" tools/automation/worldgen/Build-CliffHeightAcceptanceW53D.py
    run_step "validate W53D cliff-height runtime grammar" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-CliffHeightRuntimeGrammarW53D.py
    ;;
  estate-composition)
    run_step "regenerate W53E Home Estate composition" \
      "$(python_cmd)" tools/automation/worldgen/Build-HomeEstateSceneW53.py
    run_step "validate W53E Estate composition authority" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-EstateCompositionW53E.py
    ;;
  building-exterior)
    run_step "validate W54A building exterior grammar" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-BuildingExteriorGrammarW54A.py
    ;;
  building-exterior-evidence)
    run_step "build W54C exact exterior review evidence" \
      "$(python_cmd)" tools/automation/assets/Build-ExteriorExactReviewEvidenceW54C.py
    run_step "validate W54C exact exterior review evidence authority" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-ExteriorExactReviewEvidenceW54C.py
    ;;
  building-exterior-selections)
    run_step "validate W54D1 exact exterior source selections" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-ExteriorExactSelectionsW54D1.py
    ;;
  starter-cottage)
    run_step "validate W54E starter cottage production layout" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-StarterCottageW54E.py
    ;;
  cottage-visual-repair)
    run_step "regenerate current Estate visual repair" \
      "$(python_cmd)" tools/automation/worldgen/Build-HomeEstateSceneW53.py
    run_step "validate W54F cottage/Estate geometry baseline" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-CottageEstateVisualRepairW54F.py
    run_step "validate W54G cottage visibility/cutaway repair" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-CottageVisibilityCutawayW54G.py
    ;;
  visual-checkpoint)
    run_step "validate W53D cliff-height runtime grammar" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-CliffHeightRuntimeGrammarW53D.py
    run_step "validate W53E Estate composition authority" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-EstateCompositionW53E.py
    run_step "validate W54A building exterior grammar" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-BuildingExteriorGrammarW54A.py
    run_step "validate W54B integrated visual checkpoint" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-IntegratedVisualCheckpointW54B.py
    run_step "validate W54D2 isolated Estate visual launch" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-EstateVisualLaunchW54D2.py
    run_step "validate W54E starter cottage production layout" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-StarterCottageW54E.py
    run_step "validate W54F cottage/Estate geometry baseline" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-CottageEstateVisualRepairW54F.py
    run_step "validate W54G cottage visibility/cutaway repair" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-CottageVisibilityCutawayW54G.py
    run_step "validate W56 scene population + narrow cave-mouth authority" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-W56ScenePopulationAuthority.py
    run_step "validate W56G editor/runtime object identity + anchor parity" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-W56EditorRuntimeObjectParity.py
    run_step "validate W56 cave-mouth geometry contract" \
      "$(python_cmd)" tools/validation/Validate-W56-CaveMouthContract.py
    run_step "validate W56 cave round-trip transition safety" \
      "$(python_cmd)" tools/validation/Validate-W56-CaveRoundTrip.py
    run_step "build W56I/J integrated visual acceptance scene" \
      "$(python_cmd)" tools/automation/worldgen/Build-W56IntegratedVisualAcceptance.py
    run_step "validate W56I/J integrated editor/client visual acceptance" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-W56IntegratedVisualAcceptance.py
    ;;
  estate-regeneration)
    run_step "validate W52 world visual certification baseline" \
      "$(python_cmd)" tools/automation/validation/checks/assets/Validate-WorldVisualCertificationV1.py
    run_step "regenerate W53 Home Estate" \
      "$(python_cmd)" tools/automation/worldgen/Build-HomeEstateSceneW53.py
    run_step "validate W53 Home Estate regeneration authority" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-HomeEstateRegenerationW53.py
    run_step "validate W53B runtime scene/content convergence" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-RuntimeContentConvergenceW53B.py
    run_step "validate W53C Estate structural/runtime visual repair" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-EstateStructuralRuntimeRepairW53C.py
    run_step "build W53D cliff-height acceptance fixture" \
      "$(python_cmd)" tools/automation/worldgen/Build-CliffHeightAcceptanceW53D.py
    run_step "validate W53D cliff-height runtime grammar" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-CliffHeightRuntimeGrammarW53D.py
    run_step "validate W53E Estate composition authority" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-EstateCompositionW53E.py
    run_step "validate W54A building exterior grammar" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-BuildingExteriorGrammarW54A.py
    run_step "validate W54B integrated visual checkpoint" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-IntegratedVisualCheckpointW54B.py
    ;;
  estate-visual-test)
    run_step "validate W53B runtime scene/content convergence" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-RuntimeContentConvergenceW53B.py
    run_step "validate W53C Estate structural/runtime visual repair" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-EstateStructuralRuntimeRepairW53C.py
    run_step "validate W54B integrated visual checkpoint" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-IntegratedVisualCheckpointW54B.py
    run_step "validate W54D2 isolated Estate visual launch" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-EstateVisualLaunchW54D2.py
    run_step "regenerate W54F Estate visual repair" \
      "$(python_cmd)" tools/automation/worldgen/Build-HomeEstateSceneW53.py
    run_step "validate W54F cottage/Estate geometry baseline" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-CottageEstateVisualRepairW54F.py
    run_step "validate W54G cottage visibility/cutaway repair" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-CottageVisibilityCutawayW54G.py
    run_step "validate W56 scene population + narrow cave-mouth authority" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-W56ScenePopulationAuthority.py
    run_step "validate W56G editor/runtime object identity + anchor parity" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-W56EditorRuntimeObjectParity.py
    run_step "validate W56 cave-mouth geometry contract" \
      "$(python_cmd)" tools/validation/Validate-W56-CaveMouthContract.py
    run_step "validate W56 cave round-trip transition safety" \
      "$(python_cmd)" tools/validation/Validate-W56-CaveRoundTrip.py
    require cargo
    run_step "build W54D2 Estate visual-test client" cargo build -p haven_game
    log "Launching isolated W54G Estate visual test; normal gameplay saves are not used"
    (cd "$ROOT" && "$ROOT/target/debug/haven_game.exe" --estate-visual-test)
    ;;
  visual-acceptance)
    run_step "build W56I/J integrated visual acceptance scene" \
      "$(python_cmd)" tools/automation/worldgen/Build-W56IntegratedVisualAcceptance.py
    run_step "validate W56I/J integrated editor/client visual acceptance" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-W56IntegratedVisualAcceptance.py
    run_step "validate integrated visual checkpoint" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-IntegratedVisualCheckpointW54B.py
    require cargo
    run_step "build W56 integrated visual-acceptance client" cargo build -p haven_game
    log "Launching isolated W56 integrated visual acceptance; normal gameplay saves are not used"
    (cd "$ROOT" && "$ROOT/target/debug/haven_game.exe" --w56-visual-acceptance)
    ;;
  visual-acceptance-editor)
    run_step "build W56I/J integrated visual acceptance scene" \
      "$(python_cmd)" tools/automation/worldgen/Build-W56IntegratedVisualAcceptance.py
    run_step "validate W56I/J integrated editor/client visual acceptance" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-W56IntegratedVisualAcceptance.py
    run_step "validate integrated visual checkpoint" \
      "$(python_cmd)" tools/automation/validation/checks/worldgen/Validate-IntegratedVisualCheckpointW54B.py
    require cargo
    run_step "build W56 integrated visual-acceptance editor" cargo build -p haven_editor_native
    log "Launching native editor directly into the isolated W56 integrated visual acceptance scene"
    (cd "$ROOT" && "$ROOT/target/debug/haven_editor_native.exe" --w56-visual-acceptance)
    ;;
  lpc-runtime)
    ensure_lpc_dependency
    generate_lpc_runtime_assets
    ;;
  lpc-summer-map)
    ensure_lpc_dependency
    generate_lpc_summer_map
    ;;
  lpc-seasonal-topology)
    ensure_lpc_dependency
    generate_lpc_summer_map
    generate_lpc_seasonal_topology
    ;;
  lpc-summer-runtime)
    ensure_lpc_dependency
    generate_lpc_summer_map
    generate_lpc_seasonal_topology
    generate_lpc_summer_runtime
    ;;
  lpc-seams)
    ensure_lpc_dependency
    generate_lpc_summer_map
    generate_lpc_seasonal_topology
    generate_lpc_summer_runtime
    ;;
  asset-bake) run_step "bake asset intake atlas" "$(python_cmd)" tools/automation/assets/Bake-AssetIntakeAtlasV66.py ;;
  tiles)
    ensure_lpc_dependency
    run_step "promote normalized LPC water and ground transition families" \
      "$(python_cmd)" tools/automation/terrain/Promote-LpcTerrainFamiliesV90.py
    run_step "promote expandable LPC pond families" \
      "$(python_cmd)" tools/automation/terrain/Promote-LpcExpandablePondsV87.py
    generate_lpc_runtime_assets
    ;;
  stamps)
    ensure_lpc_dependency
    run_step "promote expandable LPC pond families" \
      "$(python_cmd)" tools/automation/terrain/Promote-LpcExpandablePondsV87.py
    ;;
  island-previews)
    preview_args=(--write-manifest)
    if [[ $# -gt 0 ]]; then preview_args+=(--seed "$1"); fi
    run_step "generate structural archipelago previews" \
      "$(python_cmd)" tools/automation/worldgen/Generate-StructuralArchipelagoPreviews.py "${preview_args[@]}"
    ;;
  island-reroll)
    run_step "reroll structural archipelago seed" \
      "$(python_cmd)" tools/automation/worldgen/Generate-StructuralArchipelagoPreviews.py --reroll --write-manifest
    ;;
  web) web_check ;;
  terrain-cert)
    run_step "rebuild production LPC mapped terrain atlas" \
      "$(python_cmd)" tools/automation/terrain/Build-LpcMappedTerrainV7.py
    run_step "materialize topology-validated open-world biome test scene" \
      "$(python_cmd)" tools/automation/worldgen/Build-ClientWorldgenTestSceneV167Z.py
    run_step "generate terrain acceptance topology scenes" \
      "$(python_cmd)" tools/automation/terrain/Generate-TerrainAcceptanceScenes.py
    run_step "regenerate W77 transition authoring workbench" \
      "$(python_cmd)" tools/automation/terrain/Build-TerrainTransitionWorkbenchW77.py
    run_step "validate W77 exact terrain presentation + transition workbench" \
      "$(python_cmd)" tools/automation/validation/checks/terrain/Validate-TerrainPresentationAuthorityAndWorkbenchW77.py
    run_step "render production LPC terrain certification evidence" \
      "$(python_cmd)" tools/automation/terrain/Render-TerrainLpcCertification.py
    run_step "validate terrain topology, LPC evidence, and retained frame plan" \
      "$(python_cmd)" tools/automation/validation/validate_terrain_topology_v167z5.py
    ;;
  worldgen) validate world ;;
  editor) require cargo; run_step "cargo run -p haven_editor_native" cargo run -p haven_editor_native -- "$@" ;;
  editor-safe) require cargo; run_step "cargo run native editor safe mode" cargo run -p haven_editor_native -- --safe-mode "$@" ;;
  pixel-studio) require cargo; run_step "cargo run Pixel Studio" cargo run -p haven_editor_native -- --pixel-studio ;;
  pixel-audit) run_step "validate native Pixel Studio" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-NativePixelStudioV79.py ;;
  pixel-doc-audit) run_step "validate layered Pixel Studio documents" "$(python_cmd)" tools/automation/validation/checks/editor/Validate-PixelDocumentLayerSystemV81.py ;;
  pixel-animation-audit) run_step "validate Pixel Studio and Animation Studio round trip" "$(python_cmd)" tools/automation/validation/checks/characters/Validate-PixelAnimationRoundtripBridgeV82.py ;;
  animation-studio) require cargo; run_step "cargo run Animation Studio" cargo run -p haven_editor_native -- --animation-studio ;;
  animation-audit) run_step "validate native Animation Studio" "$(python_cmd)" tools/automation/validation/checks/characters/Validate-NativeAnimationStudioV80.py ;;
  game) require cargo; run_step "cargo run -p haven_game" cargo run -p haven_game -- "$@" ;;
  client) ensure_frontend_music; build_dev_client ;;
  apps) ensure_frontend_music; build_dev_apps ;;
  release-client) ensure_frontend_music; build_release_client ;;
  release-apps) ensure_frontend_music; build_release_apps ;;
  fmt) require cargo; run_step "cargo fmt --all" cargo fmt --all ;;
  doctor) doctor ;;
  clean) require cargo; run_step "cargo clean" cargo clean; rm -rf Build ;;
  help|-h|--help)
    cat <<'HELP'
Usage: ./tools/build/Build.sh COMMAND [arguments]

Commands:
  devgame             Launch the configured development world directly, bypassing the frontend
  dev / all           Fast development build: repair dependency mounts if needed, cargo check, debug apps
                      Does NOT run source certification, Clippy, tests, catalog rebuild, or release builds
  cargo-only          Explicit strict Rust checkpoint: fmt/check/Clippy/tests/debug workspace build
  asset-sources        Acquire/audit ElizaWy + Universal LPC + curated OGA/LPC prototypes and rebuild the promotion matrix
  oga-prototypes       Sync curated OpenGameArt/LPC prototype authoring dependencies only
  asset-promotion-audit Rebuild the promotion matrix from committed indexes without requiring source mounts
  asset-truth          Build the W41A world asset truth inventory and validate its normalization contract
  published-assets     Rebuild Asset Truth and validate W42 PublishedWorldAsset authority
  asset-acceptance     Build/validate W43A-W43D world/placeable visual acceptance fixtures
  exact-source         Validate W44A exact-source Pixel Studio world-asset authoring authority
  structure-sources    Build/validate W45A/W45B LPC Structure source inventory and promotion queue
  structure-components Build/validate W45B exact door/stairs/fence/sign component authority
  structure-surfaces   Build/validate W45C floor/wall/cutaway/window + multi-level building visibility authority
  structure-roof-trim Build/validate W45C2 roof topology + exact wall-border authority
  structure-roof-review Build W45C3A exact roof review evidence bundle from pinned LPC source
  structure-support-review Build W45D1 exact bridge/platform/pillar review evidence bundle from pinned LPC source
  structure-exact-modules Build W45C3B/W45D2 exact roof/bridge/platform/pillar published candidates and acceptance scene
  building-recipes   Build/validate W46A same-world multi-level BuildingRecipe authority and acceptance scene
  building-instances Build/validate W46B native same-scene BuildingInstance materialization, floor traversal, collision and cutaway
  building-persistence Build/validate W46C authored/PCG placement, save deltas, persistent door state and camera-local replication split
  building-interiors  Validate W47 same-world room/furnishing/navigation/persistent-state grammar
  production-tavern  Build/validate W48/W52 production three-level Tavern acceptance
  cave-assets        Validate W49 exact cave material/mouth/ore asset authority
  cave-resolver      Build/validate W50 solid-first cave PCG/resolver/editor acceptance
  structural-connectors Build/validate W51 stairs/cave-mouth/bridge connector semantics
  world-visual-certification Build/validate W52 production visual closure and explicit quarantines
  cliff-height-grammar Build/validate W53D Level 1/2/3/4 cliff-height acceptance grammar
  estate-composition Regenerate/validate W53E populated Estate composition
  building-exterior Validate W54A exact-frontage/component-roof building exterior grammar
  building-exterior-evidence Build W54C machine-local exact exterior source review evidence (no runtime publication)
  building-exterior-selections Validate W54D1 exact exterior source selections (historical exact evidence)
  starter-cottage   Validate W54E-or-later two-room starter cottage program
  cottage-visual-repair Regenerate/validate current W54F/W54G cottage shell + visibility/cutaway repair
  visual-checkpoint Validate the integrated W54B-W54G visual checkpoint
  estate-regeneration Regenerate/validate W53-W54B canonical Home Estate stack
  estate-visual-test Launch isolated current-content Estate runtime, validating W54G and bypassing normal gameplay saves
  visual-acceptance   Launch isolated W56 integrated visual acceptance board (cliffs/cottage/cave/nature)
  visual-acceptance-editor Launch the same W56 board directly in the native editor for parity review
  lpc-sync            Legacy alias: validate/acquire both pinned LPC repositories and rebuild the matrix
  lpc-audit           Force complete ElizaWy + Universal LPC audits and catalog rebuilds
  lpc-foundation      Validate both pinned LPC repositories and rebuild shared project catalogs
  lpc-runtime         Rebuild/validate player, objects, summer map, and paint compatibility assets
  lpc-summer-map      Rebuild/validate the complete 16x26 summer terrain source map
  lpc-seasonal-topology
                      Rebuild the shared 8-neighbor role map for every seasonal terrain sheet
  lpc-summer-runtime Rebuild and validate active summer runtime fills/transitions
  lpc-seams          Rebuild and validate mask-authoritative LPC edge signatures
  rust                Explicit strict Rust checkpoint: fmt/check/Clippy/tests/debug workspace build
  check               Fast Rust formatting and cargo check only
  test                Run all workspace tests
  validate [profile]  Run build, source, framework, or full validation (all maps to source)
  certify            Run explicit full project certification, including Cargo gates
  framework-audit    Run validator-framework self-tests and quality checks only
  character-audit     Validate character creation, profiles, GUI, and sprite runtime
  catalog             Regenerate the project asset catalog
  asset-pack-prepare ARCHIVE [options]
                      Extract an asset ZIP outside the repo, catalog it, and register it with Pixel Studio
  asset-pack-catalog  Rebuild metadata for all registered external asset roots
  asset-pack-audit    Validate external-library isolation and editor integration
  asset-utilization-audit [ZIP...]
                      Rebuild the LPC/Havenwild asset inventory and utilization planning report
  source-rollup [--output PATH]
                      Create a code/metadata rollup without raw external asset packs
  source-only [--output PATH]
                      Create complete source/contracts with all binary assets excluded
  asset-bake          Bake approved asset-intake atlas content
  tiles               Regenerate only LPC-derived terrain and expandable terrain stamp atlases
  stamps              Regenerate only LPC-derived expandable terrain stamp manifests
  island-previews [seed]
                      Generate previews and persist a collision-safe layout for the seed
  island-reroll       Derive the next shareable seed, reposition islands, and regenerate PNGs
  web                 Report archived browser-editor location (native editor / World Builder are authoritative)
  terrain-cert        Regenerate and validate the client terrain slice and all acceptance fixtures
  worldgen            Run world-generation validation
  editor [args]       Run the native editor from source
  editor-safe         Run the native editor without loading atlas textures
  pixel-studio        Run the native editor directly in Pixel Studio
  pixel-audit         Validate Pixel Studio and the imported CC0 source library
  pixel-doc-audit     Validate layered documents, autosave/recovery, and layer controls
  pixel-animation-audit
                      Validate the Pixel Studio / Animation Studio frame round trip
  animation-studio    Run the native editor directly in Animation Studio
  animation-audit     Validate Animation Studio contracts and publishing workflow
  game [args]         Run the game client from source
  client              Build the development client (debug profile)
  apps                Build development client + native editor (debug profile)
  release-client      Explicit release-only client build/staging
  release-apps        Explicit release-only client/editor build/staging
  fmt                 Format the Rust workspace
  doctor              Print detected build tools and paths
  clean               Run cargo clean and remove packaged Build outputs
HELP
    ;;
  *) log "ERROR: unknown build command: $COMMAND"; exit 1 ;;
esac
