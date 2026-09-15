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
