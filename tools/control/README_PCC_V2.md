# Havenwild PCC v2

The v2 shell is intentionally thin. It owns interactive orchestration and delegates mature project commands to `HavenwildTools.ps1` by stable registry key.

Authorities:
- shell: `HavenwildPccHost.ps1`
- quick status: `PccQuickState.py`
- patch preflight: `PccPatchPreflight.ps1`
- patch ledger: `PccPatchLedger.ps1`
- one-shot restart: `PccRestartTicket.ps1`
- structured jobs: `PccJobHost.ps1`
- command adapter: `PccCommandHost.ps1`
- legacy command execution: `HavenwildTools.ps1`
- certification: existing Full Quality Gate / `HavenwildGateAuthority.py`

The new host does not weaken the Full Gate. It only removes expensive certification work and fragile nested menu ownership from ordinary front-door operation.

## HW-46 through HW-55 integration

PCC v2 now performs two additional lightweight pre-gate contract checks before entering the canonical Full Gate:

- `pcc.validate-lifecycle` verifies the one-shot restart/update lifecycle and patch evidence policy.
- `pcc.validate-editor-v2` verifies the normalized Havenwild Editor Core contracts and shared command authority.

`tools/forge/HavenwildPccProvider.py` reads the live project command registry rather than maintaining a parallel ForgePY command list. ForgePY, standalone PCC and future Cortex adapters therefore consume the same project-native command keys.
