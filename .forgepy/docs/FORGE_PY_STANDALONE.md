# ForgePY Standalone Universal PCC Architecture — U5

U5 adds automatic onboarding and component-aware project planning while preserving the U4 provider/GUI boundary and U3 hardened execution core.

## Layers

1. GUI client — human PCC views and live console.
2. CLI/JSONL clients — automation and Cortex/Forge/Ember calls.
3. Snapshot API — one-call status/operations/patches/Git/build-plan view.
4. Runtime core — locking, execution, process trees, logs, patching, GREEN certification and Git safety.
5. Provider resolver — project-owned authority before generated behavior.
6. Repository scanner — component discovery + cached onboarding plan.
7. Project contract — explicit `forge.project.v1` overrides/adapters.
8. Native project toolchain.

## Auto-onboarding

`repository_scan()` gathers build markers from Git when available or a bounded filesystem walk otherwise. It classifies components, generates unique operations with safe working directories, derives semantic defaults, records unresolved toolchains, and caches the plan by marker path/size/mtime signature.

No command is executed merely because it was discovered. Installation scans and diagnoses only. Building/running remains an explicit human or Cortex action.

## Mixed-project semantics

Each component keeps its own operation key. `build.default`, `test.default`, and `gate.fast` are composite semantic dispatchers that run all matching discovered component operations. `run.default` selects one shallow/root run target because automatically launching every runtime would be unsafe.

Full Gate runs unique gate → build → test component operations and writes certification evidence exactly as before.

## Adapter pinning

Automatic discovery remains dynamic. `onboarding-apply` is an explicit action that writes the current discovered component operations to `.forgepy/adapters/project.control.json`. ForgePY refuses to overwrite an adapter it does not own. Root project contracts and Internal PCC providers remain higher authority.

## Performance

The GUI now requests `snapshot` once per refresh. Repository scan classification is cached. Refresh requests are de-duplicated, and the GUI live console trims old text after a large threshold to avoid unbounded Tk text-widget slowdown.

## Security/control plane

Generic project patches cannot alter ForgePY runtime/package/gui/policy files, project identity, root `project.control.json`, `.forgepy/adapters/`, `.pcc/`, or PCC launchers. This prevents an ordinary source patch from silently changing future command execution authority.
