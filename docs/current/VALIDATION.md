# Havenwild Validation Authority v4

The current validation authority is `content/build/validator_registry_v4.json`. It resolves the preserved v3 registry as a historical/full-certification base, removes historical validator membership from live profiles, and then assigns bounded current profiles explicitly.

## Live profiles

| Profile | Exact size | Purpose |
|---|---:|---|
| `build` | 2 | lightweight pre-Cargo development gates |
| `quick` | 2 | alias-equivalent lightweight gates |
| `source` | 10 | current source authority from a clean checkout |
| `framework` | 4 | validation framework integrity |
| `full` | variable | explicit historical/subsystem certification + Rust gates |

`source` must remain at **10 current-authority** validators. A new pass-specific validator does not get appended to source; it either replaces a current authority or stays in `full` certification.

## Normalized contracts

Runtime media publication is governed by `content/runtime_media_manifest_v1.json`; generated evidence/receipts by `content/validation/evidence_receipt_contract_v1.json`; transactional patch intake by `content/architecture/root_patch_intake_contract_v1.json`; local/CI checks by `content/validation/ci_validation_contract_v1.json`; command aliases/deprecations by `content/validation/validator_aliases_v1.json`; and historical quarantine by `content/validation/legacy_quarantine_policy_v1.json`.

Historical validators and evidence are preserved. They are not deleted and they do not become current authority merely because they remain in the repository.

## Root quality-gate routing

`HavenwildTools.cmd` remains the project-control front door. Its registered build actions route through `tools/build/Build.cmd`. The generic `test`, `validate`, `certify`, and `framework-audit` commands are intercepted there and routed to the v4 Python authority before any legacy Bash compatibility path can run.

`Build.cmd test` now performs `cargo test --workspace` and then the bounded `source` profile. It does **not** execute the historical Wxx/Hxx/A14 pass-by-pass validator chain. `Build.cmd certify` is the explicit route to `full` historical/subsystem certification.

Direct `Build.sh test` and `Build.ps1 test` invocations are compatibility-only legacy entry points. They are not the root Project Control Center authority and should not be used as the normal validation path while their old pass-specific blocks remain preserved for source archaeology.

The historical module line-count architecture check is **full-certification only**. It is intentionally not part of the current `source` profile because present authoritative modules already exceed those legacy thresholds. Current source instead certifies registry integrity and actual architecture/ownership contracts; refactoring oversized modules remains engineering debt, not a false source-invalid state.
