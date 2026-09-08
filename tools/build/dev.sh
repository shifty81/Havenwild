#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

LOG_ROOT="$ROOT/logs/dev"
RUN_ID="$(date +%Y%m%d-%H%M%S)"
LOG_FILE="$LOG_ROOT/dev-$RUN_ID.log"
mkdir -p "$LOG_ROOT"
exec > >(tee -a "$LOG_FILE") 2>&1
echo "Havenwild dev log: $LOG_FILE"
echo "Started: $(date -Iseconds)"
echo "Root: $ROOT"

PYTHON_BIN="${PYTHON:-}"
if [[ -z "$PYTHON_BIN" ]]; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  fi
fi

usage() {
  cat <<'EOF'
Havenwild dev helper

Usage:
  ./tools/build/dev.sh                 Open menu
  ./tools/build/dev.sh all             Run full tools/build/Build.sh all
  ./tools/build/dev.sh client          Build/package client
  ./tools/build/dev.sh apps            Build/package client + editor
  ./tools/build/dev.sh check           Format/check/clippy through tools/build/Build.sh
  ./tools/build/dev.sh test            Run workspace tests through tools/build/Build.sh
  ./tools/build/dev.sh tiles           Rebuild LPC terrain libraries through tools/build/Build.sh
  ./tools/build/dev.sh lpc-runtime     Rebuild/validate approved LPC runtime assets
  ./tools/build/dev.sh lpc-summer-map  Rebuild/validate the complete summer terrain map
  ./tools/build/dev.sh lpc-seasonal-topology
                            Rebuild shared summer-to-season topology roles
  ./tools/build/dev.sh lpc-summer-runtime
                            Rebuild active summer runtime terrain + conformance board
  ./tools/build/dev.sh lpc-seams        Rebuild and validate transition edge signatures
  ./tools/build/dev.sh validate [dom]  Run validation through tools/build/Build.sh
  ./tools/build/dev.sh game            Run game through tools/build/Build.sh
  ./tools/build/dev.sh editor          Run native editor through tools/build/Build.sh
  ./tools/build/dev.sh editor-safe     Run native editor without atlas textures
  ./tools/build/dev.sh export [name]   Create clean source zip with assets, no targets/builds
  ./tools/build/dev.sh source-only     Create full source/contracts zip without binary assets
  ./tools/build/dev.sh clean           Remove ignored build/runtime outputs only
  ./tools/build/dev.sh ignored         Show internal clean/export ignore policy
  ./tools/build/dev.sh help            Show this help
EOF
}

run_build() {
  if [[ ! -f "$ROOT/tools/build/Build.sh" ]]; then
    echo "tools/build/Build.sh was not found in $ROOT" >&2
    exit 1
  fi
  echo
  echo "==> tools/build/Build.sh $*"
  echo "    started: $(date -Iseconds)"
  bash "$ROOT/tools/build/Build.sh" "$@"
  echo "    finished: $(date -Iseconds)"
}

require_python() {
  if [[ -z "$PYTHON_BIN" ]]; then
    echo "python or python3 is required for this command." >&2
    exit 1
  fi
}

clean_source_export() {
  require_python
  local name="${1:-Havenwild_CleanSource_$(date +%Y%m%d-%H%M%S)}"
  local out_dir="$ROOT/WORKSPACE/exports"
  local stage_root="$ROOT/.local/clean-source-staging"
  local stage="$stage_root/$name"
  local zip_path="$out_dir/$name.zip"

  mkdir -p "$out_dir" "$stage_root"
  rm -rf "$stage"
  rm -f "$zip_path"

  echo
  echo "==> Export clean source"
  echo "    started: $(date -Iseconds)"
  echo "Exporting clean source snapshot..."
  echo "  root: $ROOT"
  echo "  zip:  $zip_path"

  "$PYTHON_BIN" - "$ROOT" "$stage" "$zip_path" <<'PY'
from __future__ import annotations

import fnmatch
import os
import shutil
import sys
import zipfile
from pathlib import Path

root = Path(sys.argv[1]).resolve()
stage = Path(sys.argv[2]).resolve()
zip_path = Path(sys.argv[3]).resolve()

excluded_dirs = {
    ".git",
    ".agents",
    ".codex",
    ".local",
    "__pycache__",
    "target",
    "Build",
    "logs",
    "WORKSPACE",
}
excluded_files = [
    "*.pyc",
    "*.pyo",
    "*.zip",
    "*.7z",
    "*.rar",
    "*.log",
    "*.tmp",
    "*.temp",
    "*.exe",
    "*.pdb",
    "*.ilk",
    "*.obj",
    "*.dll",
    "Thumbs.db",
    ".DS_Store",
]

def is_within(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False

stage_root = root / ".local" / "clean-source-staging"
if not is_within(stage_root.resolve(), stage):
    raise SystemExit(f"Refusing staging path outside {stage_root}: {stage}")

if stage.exists():
    shutil.rmtree(stage)
stage.mkdir(parents=True, exist_ok=True)
zip_path.parent.mkdir(parents=True, exist_ok=True)

copied_files = 0
copied_bytes = 0

for current, dirs, files in os.walk(root):
    current_path = Path(current)
    rel = current_path.relative_to(root)
    parts = set(rel.parts)
    if parts & excluded_dirs:
        dirs[:] = []
        continue
    dirs[:] = [d for d in dirs if d not in excluded_dirs]

    target_dir = stage / rel
    target_dir.mkdir(parents=True, exist_ok=True)
    for file_name in files:
        if any(fnmatch.fnmatch(file_name, pattern) for pattern in excluded_files):
            continue
        source = current_path / file_name
        source_rel = source.relative_to(root)
        if set(source_rel.parts) & excluded_dirs:
            continue
        target = stage / source_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied_files += 1
        copied_bytes += source.stat().st_size

with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in stage.rglob("*"):
        if path.is_file():
            archive.write(path, path.relative_to(stage))

zip_bytes = zip_path.stat().st_size
shutil.rmtree(stage)

print(f"Clean source zip created: {zip_path}")
print(f"Exported files: {copied_files}")
print(f"Source bytes before zip: {copied_bytes}")
print(f"Zip bytes: {zip_bytes}")
print("Excluded directories: " + ", ".join(sorted(excluded_dirs)))
PY
  echo "    finished: $(date -Iseconds)"
}

show_ignore_policy() {
  cat <<'EOF'
Internal clean policy

Clean removes only:
  target
  Build
  .local/clean-source-staging

Clean never removes:
  assets
  content
  apps
  crates
  tools/automation
  docs
  web
  logs
  Cargo.toml / Cargo.lock
  README.md
  tools/build/Build.sh / tools/build/Build.ps1 / tools/build/Build.cmd / tools/build/dev.sh

Clean source export includes assets/content/source and excludes:
  .git
  .agents
  .codex
  .local
  target
  Build
  __pycache__
  logs
  WORKSPACE
  pyc/pyo/zip/7z/rar/log/tmp/exe/pdb/obj/dll outputs
EOF
}

clean_outputs() {
  local clean_paths=(
    "$ROOT/target"
    "$ROOT/Build"
    "$ROOT/.local/clean-source-staging"
  )
  local protected_names=(
    "$ROOT/assets"
    "$ROOT/content"
    "$ROOT/apps"
    "$ROOT/crates"
    "$ROOT/tools/automation"
    "$ROOT/DOCS"
    "$ROOT/web"
    "$ROOT/logs"
    "$ROOT/Cargo.toml"
    "$ROOT/Cargo.lock"
    "$ROOT/README.md"
    "$ROOT/tools/build/Build.sh"
    "$ROOT/tools/build/Build.ps1"
    "$ROOT/tools/build/Build.cmd"
    "$ROOT/tools/build/dev.sh"
  )

  show_ignore_policy
  echo
  echo "Planned removals:"
  for path in "${clean_paths[@]}"; do
    echo "  $path"
  done
  echo
  echo "This clean is intentionally closer to an internal .gitignore sweep than a reset."
  echo "It preserves all project assets and content."
  echo "It also preserves logs so build/client/editor usage remains auditable."
  echo
  read -r -p "Type CLEAN to continue: " answer
  if [[ "$answer" != "CLEAN" ]]; then
    echo "Cancelled."
    return 0
  fi

  for path in "${clean_paths[@]}"; do
    local normalized
    normalized="$(cd "$(dirname "$path")" 2>/dev/null && pwd -W 2>/dev/null || cd "$(dirname "$path")" 2>/dev/null && pwd)/$(basename "$path")"
    for protected in "${protected_names[@]}"; do
      if [[ "$path" == "$protected" || "$path" == "$protected"/* ]]; then
        echo "Refusing to clean protected project path: $path" >&2
        exit 1
      fi
      if [[ "$normalized" == "$protected" || "$normalized" == "$protected"/* ]]; then
        echo "Refusing to clean protected project path: $normalized" >&2
        exit 1
      fi
    done
  done

  for path in "${clean_paths[@]}"; do
    echo "Removing ignored output: $path"
    rm -rf "$path"
  done
  echo "Ignored build/runtime outputs removed. Assets, content, and logs were not touched."
}

compat_clean_local_outputs() {
  cat <<'EOF'
The command name clean-local is kept as an alias.
Use ./tools/build/dev.sh clean going forward.
EOF
  clean_outputs
}

menu() {
  while true; do
    cat <<'EOF'

Havenwild Dev Menu
  1) Full build/package
  2) Build/package client
  3) Build/package client + editor
  4) Format/check/clippy
  5) Run tests
  6) Rebuild LPC terrain tiles
  7) Run validation
  8) Run game
  9) Run native editor
 10) Export clean source zip
 11) Clean ignored build/runtime outputs
 12) Show internal ignore policy
 13) Rebuild/validate approved LPC runtime assets
 14) Rebuild/validate complete LPC summer terrain map
 15) Rebuild shared seasonal terrain topology
 16) Run native editor in safe mode
 17) Export complete source without assets
 18) Rebuild active summer runtime terrain
 19) Rebuild/validate LPC transition seams
  0) Quit
EOF
    read -r -p "Choose: " choice
    case "$choice" in
      1) run_build all ;;
      2) run_build client ;;
      3) run_build apps ;;
      4) run_build check ;;
      5) run_build test ;;
      6) run_build tiles ;;
      7)
        read -r -p "Validation domain [all]: " domain
        run_build validate "${domain:-all}"
        ;;
      8) run_build game ;;
      9) run_build editor ;;
      10)
        read -r -p "Export name [timestamped]: " name
        clean_source_export "$name"
        ;;
      11) clean_outputs ;;
      12) show_ignore_policy ;;
      13) run_build lpc-runtime ;;
      14) run_build lpc-summer-map ;;
      15) run_build lpc-seasonal-topology ;;
      16) run_build editor-safe ;;
      17) run_build source-only ;;
      18) run_build lpc-summer-runtime ;;
      19) run_build lpc-seams ;;
      0) exit 0 ;;
      *) echo "Unknown choice: $choice" ;;
    esac
  done
}

cmd="${1:-menu}"
if [[ $# -gt 0 ]]; then
  shift || true
fi

case "$cmd" in
  menu) menu ;;
  all|client|apps|check|test|tiles|lpc-runtime|lpc-summer-map|lpc-seasonal-topology|lpc-summer-runtime|lpc-seams|game|editor|editor-safe) run_build "$cmd" "$@" ;;
  validate) run_build validate "${1:-all}" ;;
  export) clean_source_export "${1:-}" ;;
  source-only) run_build source-only "$@" ;;
  clean) clean_outputs ;;
  clean-local) compat_clean_local_outputs ;;
  ignored) show_ignore_policy ;;
  help|-h|--help) usage ;;
  *) echo "Unknown command: $cmd" >&2; usage; exit 1 ;;
esac
