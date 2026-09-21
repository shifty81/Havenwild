# ForgePY Standalone Universal PCC — U5 Auto-Onboarding

**Build:** `FORGEPY-STANDALONE-U5-HW-C16R10-PCC-GIT-AUTHORITY`  
**Version:** `1.4.0-hardened+havenwild.c16r10`  
**Basis:** U4 GUI/provider + U3 hardened execution core

ForgePY is the detached repository-local execution provider used by a human Project Control Center, Cortex, Forge, or Ember. U5 can be dropped into an unfamiliar repository, scan the project structure, synthesize a transparent build/test/run plan, and expose the result through the same CLI/JSONL/GUI contract.

## Install

1. Extract the standalone ZIP into the repository root.
2. Run `ForgePY-Install.cmd` once.
3. Launch `ForgePY-GUI.cmd` for the ForgePY GUI.
4. Use `HavenwildTools.cmd` for the authoritative Havenwild PCC.
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

- Dashboard — source, certification, component count, patch inbox, provider and scan health, plus guarded Havenwild PCC Full Gate and Commit + Push GREEN controls;
- Build Plan — detected components, markers, semantic defaults, warnings, unresolved tooling, force-rescan and optional adapter pinning;
- Operations — searchable/filterable component-aware commands and provider ownership;
- Patches — explicit validate/apply workflow;
- Git — guarded Havenwild PCC Commit + Push GREEN, FF-only pull and history;
- Recovery — gate/certification evidence and debug bundles;
- Persistent lower project console — live, headless stdout/stderr and full per-operation transcripts; the Logs navigation focuses it;
- Settings — project identity, provider precedence, capabilities and scan metadata.

GUI refresh uses a single `forgepy.snapshot.v1` backend request rather than launching separate status/operations/patch/Git queries.

### Havenwild headless console integration (C16R3)

The persistent bottom console stays visible while switching Dashboard, Build Plan, Operations, Patches, Git, Recovery and Settings. Operations start from the GUI using an unbuffered Python backend and hidden Windows console-subsystem children. Both stdout and stderr are merged and forwarded in chunks (including partial lines); the full GUI transcript is saved under `.forgepy/state/logs/gui-*.log` or the configured in-project state directory. Child operation logs and exit receipts are also retained. Clear only clears the onscreen transcript; it does not delete logs.

GUI operations are non-interactive. `Read-Host`, `pause`, terminal-only TUI programs and commands that launch independent terminal windows must be adapted to use non-interactive flags and inherit stdout/stderr; such child windows cannot be captured after they detach. The GUI does not silently fall back to a console PCC on startup failure. Use `ForgePY.cmd menu` explicitly for interactive CLI operations. The normal Havenwild `HavenwildTools.cmd` PCC is retained unchanged as the project authority; this is a ForgePY GUI transport correction, not a new PCC.

Use `ForgePY-Verify.cmd` to run package integrity and the headless-console regression self-test. On Windows, visually confirm that Build/Test shows continuous output without extra console windows and Cancel stops the process tree. The source tests here do not certify native Windows window behavior or the game renderer.

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

### Havenwild governed dashboard publication (C16R4)

The dashboard PCC FULL GATE control invokes `tools/control/HavenwildPccHost.ps1 -Command validation.full-quality-gate` using a hidden, noninteractive PowerShell child. After a successful project-owned Full Quality Gate, refresh reads `tools/control/PccQuickState.py` (read-only). `Commit + Push Current GREEN` becomes enabled only for an authorized lane with current PCC certification and unpublished changes. It asks for confirmation, then invokes `HavenwildPccHost.ps1 -Command source-control.commit-push-green`; the PCC alone verifies fingerprints, stages, commits, pushes, reconciles and creates publication receipts. This is not ForgePY's generic `commit-green` followed by `push`. All subprocess output stays in the lower console and per-operation log.

A root-level pytest collection bug in `tools/control/test_reconcile_held_duplicate.py` was also corrected: the historical transport-dependent fixture is now a normal test function and skips when its exact archive is absent, rather than `SystemExit(0)` during module import. Both scenarios preserve previous source and evidence requirements.

The Python regression suite cannot certify native Windows PowerShell execution, remote GitHub publication, or the actual Havenwild Full Quality Gate. Run the gate before publishing; never override a blocked PCC action.

### Havenwild console and patch intake (C16R5)

The persistent console now supplies `Copy All` (all visible text) and `Copy Full Log` (complete operation transcript including output trimmed from the on-screen widget). Clipboard copy is limited to 16 MiB for UI responsiveness; larger files can be shared from `Open Log Folder`. Clear never deletes retained log files. Standardize these controls in other consoles through their own project-owned GUIs; this package changes only Havenwild's bundled ForgePY.

Havenwild PCC ZIPs are inspected as a read-only manifest preview, then `Apply via Havenwild PCC` calls `HavenwildPccHost.ps1 -Command updates.apply-pending`. No new ZIP writer, direct archive extraction, generic patch override, or invented green state is introduced. Only one recognized root transport may be pending when the GUI invokes this whole-inbox PCC entry point; other transports must be reconciled first. Restart GUI after a self-update and use PCC Full Gate before publishing. The standalone runtime is still a U5-derived core with Havenwild R5 adaptations, not a claimed U8/U9 source migration.

### Havenwild PCC dashboard and candidate launch receipts (C16R8)

The dashboard badge and certification card now read `PccQuickState.py` together with the existing publication button. Generic ForgePY's last-gate status remains a separate diagnostic and cannot overwrite the PCC's current GREEN or certify stale source. Candidate PowerShell output is streamed to host output so the existing PCC job caller receives only a numeric exit code. A candidate `cargo run` exit zero means the process exited normally, not renderer parity; Vulkan validation errors require a separate Windows GPU diagnosis. The Bevy GUI uses horizontal menus and reserves a smaller, resizable diagnostics dock. U5 remains the actual ForgePY donor generation; no U8/U9 migration.

### Havenwild protected publication (C16R10)

Both Dashboard and Git publish through `tools/control/HavenwildPccHost.ps1`
using the `source-control.commit-push-green` command. The generic ForgePY
`commit-green` and `push` commands now fail closed when this internal PCC
is present. A missing `.forgepy/state/last-green.json` reflects ForgePY's
**separate** generic gate and is not evidence that Havenwild's canonical
`.havenwild/last-green-quality-gate.json` is missing.

The project's protected authority hashes the complete governed tree before
staging, refuses unrelated staged changes, force-stages ONLY the certified
manifest, and retires tracked machine-local `.forgepy/state`, `.forgepy/cache`,
Bevy candidate evidence, and nested Cargo `target/` paths from the Git index
without deleting working files. This is performed only after the full-source
fingerprint matches a current PCC GREEN marker. Run a new Havenwild FULL QUALITY
GATE after applying C16R10; never reuse a previous GREEN marker by rewriting
a receipt. Do not manually `git add -A`/`push` around this workflow.
