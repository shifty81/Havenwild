# Havenwild Validation Architecture

Validation has three practical levels:

- `build` / `quick`: two lightweight pre-Cargo gates used by normal build tooling.
- `source`: ten current-authority checks for repository/layout, architecture, content, character visual policy, workspace contract and the current normalization checkpoint.
- `full`: explicit historical/subsystem certification plus Cargo checks/tests; never implicit in the fast development build.

The executable registry is `content/build/validator_registry_v3.json`. `content/validation/validation_manifest_v1.json` defines profile policy/counts and no longer claims historical pass chains are current source authority.

Historical pass validators remain available in `full`; they are evidence/certification, not normal continuation gates.

## Compact Control Center quality gate log lifecycle

The compact Control Center's **Build & Verify -> Full quality gate** is the normal local certification workflow.

A full quality gate now has an intentionally fresh diagnostic lifecycle:

1. delete the previous contents of `logs/` while preserving/truncating the live controller session file;
2. run root cleanliness audit;
3. run the full build;
4. run the workspace test suite;
5. on either PASS or FAIL, package the complete fresh `logs/` tree to `artifacts/debug-bundles/Havenwild_DebugBundle_<timestamp>_<PASS|FAIL>.zip`;
6. write a SHA-256 sidecar beside the debug ZIP and print both paths in the Control Center.

Standalone **Build all**, **Run tests**, and other diagnostic commands do not clear logs automatically. This preserves evidence when a developer is iterating on one failing command. The destructive log reset is limited to the explicit Full quality gate, where a self-contained diagnostic capture is desired.

Debug bundles live under `artifacts/`, which is excluded from source rollups and package baselines. This keeps diagnostics out of source authority and keeps the repository root clean.
