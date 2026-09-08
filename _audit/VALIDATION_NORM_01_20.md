# Havenwild VALIDATION-NORM-01..20

Date: 2026-09-08
Authority base: current GitHub `main`; v3 remains a preserved compatibility/historical registry and is not overwritten by this patch.

## Completed passes

1. **VALIDATION-NORM-01 — Registry v4 convergence:** added a thin v4 overlay that resolves the current v3 registry, quarantines its live-profile memberships, preserves `full`, and adds canonical current validators.
2. **VALIDATION-NORM-02 — Profile normalization:** added explicit v4 profile policy with exact `build=2`, `quick=2`, `source=10`, `framework=4` bounds.
3. **VALIDATION-NORM-03 — Framework contract normalization:** replaced live historical framework gates with canonical v4 framework/registry/runner contracts; historical checks remain full-only.
4. **VALIDATION-NORM-04 — Runtime-media/publication normalization:** added source validation for the existing required-runtime-media manifest, hashes, provenance, and GREEN publication authority. The accepted R3 title/hover/Harp publication fix is preserved.
5. **VALIDATION-NORM-05 — Evidence/receipt normalization:** declared generated evidence/debug/update receipts non-source-authoritative and moved build attestation authority to v4 contracts.
6. **VALIDATION-NORM-06 — Root-intake normalization:** source validation now certifies the transactional root-patch contract, safe-path/hash/rollback rules, and no patch-script execution.
7. **VALIDATION-NORM-07 — CI/check normalization:** added one stable `check_current.py` entrypoint for build/source/framework/full and a data contract usable by local scripts or CI.
8. **VALIDATION-NORM-08 — Alias/deprecation normalization:** centralized legacy suite/profile aliases and deprecated v3/v146 authority mappings without deleting their evidence.
9. **VALIDATION-NORM-09 — Docs/manifest normalization:** added one current validation-authority manifest and current documentation.
10. **VALIDATION-NORM-10 — Final convergence/legacy quarantine:** historical validators remain physically present but cannot enter build/quick/source/framework through the v4 overlay; NormalizationAudit resolves v4 instead of counting v3 memberships.

## Invariants

- Root patch intake remains the authoritative update path.
- `content/build/validator_registry_v3.json` is deliberately preserved and not overwritten.
- Runtime-media publication R3 is not reverted or replaced.
- Historical evidence is preserved.
- New pass validators do not accumulate in normal source validation.

## Continued cumulative hardening — VALIDATION-NORM-11..15

11. **VALIDATION-NORM-11 — Root test-path convergence:** `tools/build/Build.cmd` now intercepts generic `test` before the legacy Bash fallback.
12. **VALIDATION-NORM-12 — Current test wrapper:** `check_current.py --cargo-test` owns `cargo test --workspace` plus bounded source validation for the root quality gate.
13. **VALIDATION-NORM-13 — Generic historical-chain quarantine:** root-control `test` can no longer implicitly execute Wxx/Hxx/A14 pass-by-pass validators; those remain explicit compatibility/full-certification evidence.
14. **VALIDATION-NORM-14 — CI/build entrypoint contract:** CI/source validation certifies that the root build front door routes test/validate/certify/framework to v4.
15. **VALIDATION-NORM-15 — Legacy entrypoint declaration:** direct `Build.sh test` and `Build.ps1 test` are explicitly marked compatibility-only until their historical bodies are separately retired without overwriting newer build-command work.
16. **VALIDATION-NORM-16 — Legacy architecture-size gate quarantine:** removed the old line-count architecture validator from `source`; it remains available in `full`. The v4 registry-quality contract takes that source slot, so source remains exactly 10 and validates current authority rather than historical module-size thresholds already violated by legitimate current modules.
17. **VALIDATION-NORM-17 — Legacy manifest detachment:** the v4 runner is contractually forbidden from consuming `validation_manifest_v1.json` as live authority; it remains historical compatibility data only.
18. **VALIDATION-NORM-18 — Root quality-gate closure:** the CI/build contract now records the exact root-control build/test/source-validation/full-certification routes and forbids implicit historical certification.
19. **VALIDATION-NORM-19 — Current-source fail-fast cleanup:** current source validates live registry, publication, patch intake, evidence, CI and docs contracts rather than obsolete line-count policy; expensive historical checks stay explicit.
20. **VALIDATION-NORM-20 — Cumulative package convergence:** the replacement package carries every VALIDATION-NORM-01..20 payload together, so the new ZIP supersedes the earlier 01..10 transport rather than depending on patch application order.
