# ForgePY Standalone Universal PCC — U5 Auto-Onboarding

**Build:** `FORGEPY-STANDALONE-U5-AUTO-ONBOARD`  
**Version:** `1.4.0-hardened`  
**Basis:** U4 GUI/provider + U3 hardened execution core

ForgePY is the detached repository-local execution provider used by a human Project Control Center, Cortex, Forge, or Ember. U5 can be dropped into an unfamiliar repository, scan the project structure, synthesize a transparent build/test/run plan, and expose the result through the same CLI/JSONL/GUI contract.

## Install

1. Extract the standalone ZIP into the repository root.
2. Run `ForgePY-Install.cmd` once.
3. Launch `PROJECT_CONTROL_CENTER.cmd` for the GUI.
4. Use `PROJECT_CONTROL_CENTER.cmd --cli` for the console PCC.
5. Use `ForgePY.cmd <command>` or `serve-jsonl` for automation.

Install performs package verification, initializes project-local ForgePY state/identity, scans the repository, writes an onboarding plan, and runs Doctor. It **does not** automatically build, run, patch, commit, pull, or push the project.

## U5 automatic onboarding

The scanner searches tracked/unignored project markers while pruning generated/vendor trees. In Git repositories it prefers `git ls-files -co --exclude-standard`; non-Git folders use a bounded pruned walk. Results are cached under `.forgepy/cache/` and invalidated when relevant project markers change.

Recognized project families include:

- Cargo/Rust
- Node package scripts with npm/pnpm/yarn/bun selection
- CMake
- Python
- .NET/MSBuild/dotnet
- Make
- Gradle
- Maven
- Go
- Zig
- Meson
- conventional build/test/run scripts
- Godot run targets
- Unreal project detection (reported unresolved until deterministic Engine/UBT configuration is declared)

Mixed repositories are represented as components. Operations get unique keys such as `build.node.node-frontend` or `build.cmake.cmake-native`. Semantic `build`, `test`, and `quick` operations compose every discovered target in that category. `run` deliberately chooses one safe default rather than launching every runnable component.

`ForgePY.cmd rescan` forces a new scan. `ForgePY.cmd --json scan` returns the full plan. `ForgePY.cmd onboarding-apply` can explicitly pin the current discovered component operations into `.forgepy/adapters/project.control.json`; it refuses to overwrite a project-owned adapter.

## Provider precedence

1. project Internal PCC declared by root `project.control.json`;
2. root project contract;
3. project-local ForgePY adapter;
4. ForgePY automatic discovery.

Explicit operations always outrank generated operations with the same key.

## GUI

The stdlib-only GUI is a thin client over the same runtime. U5 includes:

- Dashboard — source, certification, component count, patch inbox, provider and scan health;
- Build Plan — detected components, markers, semantic defaults, warnings, unresolved tooling, force-rescan and optional adapter pinning;
- Operations — searchable/filterable component-aware commands and provider ownership;
- Patches — explicit validate/apply workflow;
- Git — GREEN commit, FF-only pull, upstream-only push and history;
- Recovery — gate/certification evidence and debug bundles;
- Logs — live backend output with bounded in-memory history;
- Settings — project identity, provider precedence, capabilities and scan metadata.

GUI refresh uses a single `forgepy.snapshot.v1` backend request rather than launching separate status/operations/patch/Git queries.

## Main commands

```text
ForgePY.cmd status --json
ForgePY.cmd snapshot
ForgePY.cmd scan
ForgePY.cmd --json scan
ForgePY.cmd rescan
ForgePY.cmd onboarding-plan
ForgePY.cmd onboarding-apply
ForgePY.cmd discover
ForgePY.cmd capabilities
ForgePY.cmd identity
ForgePY.cmd operations --json
ForgePY.cmd history 100
ForgePY.cmd doctor
ForgePY.cmd runtime-self-test
ForgePY.cmd package-verify
ForgePY.cmd quick
ForgePY.cmd full
ForgePY.cmd build
ForgePY.cmd build-release
ForgePY.cmd test
ForgePY.cmd run
ForgePY.cmd patch-status
ForgePY.cmd patch-check update.patch
ForgePY.cmd patch-apply update.patch
ForgePY.cmd git-status
ForgePY.cmd git-history
ForgePY.cmd git-pull
ForgePY.cmd push
ForgePY.cmd commit-green
ForgePY.cmd debug-bundle
ForgePY.cmd serve-jsonl
```

## Safety boundary

U5 retains the hardened single-writer lock, timeouts/process-tree cancellation, GREEN receipts, source fingerprints, safe cwd validation, patch TOCTOU checks, protected runtime paths, symlink rejection, FF-only pulls and upstream-only pushes. Generic root-drop patches also cannot modify project execution-control metadata such as `project.control.json` or `.forgepy/adapters/`.

Repository-local ForgePY remains detached from machine-wide Vault governance, full-drive cataloging, Ember application hosting and Cortex reasoning. Those systems consume ForgePY as a versioned local project execution provider.
