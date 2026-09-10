# Havenwild Forge PCC Adapter v1

## Purpose

Havenwild keeps its existing Project Control Center intact while becoming a
first-class Forge/Vault managed project. The adapter is a thin translation
layer, not a second PCC implementation.

## Ownership boundary

**Forge/Vault owns:** project discovery, project registration, Vault indexing,
central artifact indexing, source-control UI, run telemetry, project health
presentation, and the universal command surface.

**Havenwild PCC owns:** Havenwild-specific build semantics, Full/Fast Quality
Gate behavior, its transactional root-drop patch application, project-specific
validators/tools, and its standalone interactive recovery path.

Forge calls Havenwild by stable registered command key, never by menu position.
Examples include `build.all`, `test.workspace`, `run.editor`,
`validation.full-quality-gate`, and `diagnostics.create-debug-handoff`.

## Fallback contract

The Forge project header exposes a **Havenwild CLI** button only when these
project-native authorities exist:

- `HavenwildTools.cmd`
- `tools/control/HavenwildTools.ps1`
- `tools/control/ProjectCommandRegistry.ps1`

The button launches `HavenwildTools.cmd` unchanged. If any required authority is
missing, the button is disabled rather than substituting a generated shell.

This is specifically a Forge-failure/recovery path: the project remains
operable even if the universal Forge GUI or service cannot build or start.

## Strict-root compatibility

Havenwild's root audit intentionally permits only a small set of root files.
Therefore its Forge descriptor lives at `.forge/project.toml`, not at root
`forge.project.toml`. Forge project discovery must support both forms, with
`.forge/project.toml` preferred when a project declares or exhibits a strict
root policy.

No internal Havenwild PCC file is changed by this adapter.

## Quality gate and build mapping

| Forge capability | Havenwild PCC key |
|---|---|
| Project build | `build.all` |
| Tests | `test.workspace` |
| Validate | `validate.source` |
| Full certify | `validation.full-quality-gate` |
| Fast gate | `validation.fast-quality-gate` |
| Run editor | `run.editor` |
| Run client | `run.game` |
| Run development world | `run.development-world` |
| Asset catalog | `assets.refresh-catalog` |
| Asset source sync | `assets.sync-lpc` |
| Diagnostics bundle | `diagnostics.create-debug-handoff` |
| Update status | `updates.status` |
| Apply pending update | `updates.apply-pending` |

Forge should treat command keys as the compatibility API. Numeric PCC menu
choices and command IDs are presentation/implementation details and must not be
stored in the adapter.

## Vault artifact contract

Forge indexes Havenwild's project-local outputs without relocating or deleting
them. The project-local layout remains authoritative for the native PCC, while
Vault maintains the central cross-project index.

Primary sources are:

- `.havenwild/artifact-index.json`
- `.havenwild/last-green-quality-gate.json`
- `.havenwild/quality-gates/`
- `.havenwild/fast-gates/`
- `artifacts/packages/`
- `artifacts/recovery/`
- `artifacts/debug-bundles/`
- `artifacts/troubleshooting-bundles/`
- `artifacts/updates/applied/`
- `artifacts/updates/failed/`
- `artifacts/updates/undone/`
- `logs/` domain/run logs

Vault may copy or content-address artifacts into central storage according to
Forge retention policy, but must preserve the original project path, SHA-256,
run/gate relationship, patch relationship, timestamps, and provenance in its
index.

## Patch intake handoff

For Havenwild v1, Forge/Vault may own patch discovery/download queuing, but
Havenwild's established transactional root-drop intake remains the apply
authority. Once Forge has classified and preflighted a Havenwild patch, it may
stage the recognized transport into the repository root and invoke the native
Full Quality Gate. Havenwild then validates manifest paths/hashes, creates its
rollback backup, applies the patch, archives the consumed transport, and
continues through root audit/build/tests/certification.

This preserves the proven Havenwild recovery semantics while Forge becomes the
cross-project intake and observability layer.

## Cortex intake rule

When Cortex/Forge ingests a project that has no existing PCC/CLI, intake may
generate a project-specific CLI adapter after scanning the build system,
commands, tests, artifacts, logs, and repository structure. That generic intake
behavior is outside Havenwild's adapter because Havenwild already has a mature
native PCC and must not be replaced.
