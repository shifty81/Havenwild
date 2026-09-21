# B48R28C16R7 — Windows symlink privilege gate repair

## Evidence and exact failure

User-supplied Havenwild_DebugBundle_20260920-104119_FAIL.zip records R6 successfully applied at 2026-09-20 10:39 local, an experimental Git checkout, root hygiene PASS, Rust workspace check/build PASS and main Rust tests/validation PASS. The experimental candidate suite then passed its 89 Bevy candidate tests, ElizaWy publication and architecture convergence tests. The parallel-migration suite failed in `tests/architecture/test_parallel_migration.py:117`: creating a symlink during test setup raised `OSError: [WinError 1314] A required privilege is not held by the client` on this non-elevated Windows account. It is a test fixture setup privilege, not evidence of a successful symlink traversal or a regression in `existing_file`.

## Change

Only `tests/architecture/test_parallel_migration.py` changed from R6. Existing `test_rejects_symlink_escape` still creates an actual filesystem symlink and verifies the existing `EvidenceError: File escapes root` guard when creation is permitted. If and only if creation raises Windows WinError 1314, this particular OS-dependent test reports an explicit skip; unexpected OSErrors continue to fail rather than silently bypass coverage. A new, unconditional `test_rejects_resolved_escape_without_symlink_privilege` simulates a candidate path resolving outside its root using a scoped `Path.resolve` replacement and requires the original production `existing_file`/`compare_fixture` to reject that escape. This tests the guard even on unprivileged Windows without changing the actual validation policy or requiring elevation/Developer Mode. No production source or runtime changes.

## Package use and verification

This is a **single cumulative root-intake ZIP** from B48R26 through R7, replacing R6; do not stack earlier ZIPs or copy source by hand. Put only R7 in the experimental test checkout root; use HavenwildTools.cmd root patch intake, restart the GUI if open, and run the governed Full Quality Gate. Do not commit/push until that gate certifies this source. The new ZIP was checked for ZIP integrity, unique safe paths, SHA256/bytes of all manifest files and predecessor preservation. Linux Python: candidate 89 passed, mapper 7 passed, architecture 20 passed (1 full-checkout-dependent skip in patch-only staging). Original reference fixtures from B48R26 were test-only, not added to this incremental payload. Windows build, symlink privilege behavior and full PCC gate remain to be validated by user's next run.

## Additional audit finding; separate issue

The user's Rust test output still contains historical +1-elevation normalization tests (`ordinary_authoring_skips_reserved_level_one`, `thin_one_high_shelf_collapses_to_relief` and `generated_surface_has_no_standalone_level_one_cliff_cells`) that contradict the newer ElizaWy sea=0, +1..+30 rule. Their passing does not certify the new elevation contract. Do not change geography validators as part of this narrowly bounded symlink privilege repair; audit/migrate them in a dedicated terrain-authority pass with appropriate worldgen/editor/client evidence.
