@(
  @{ Id='pcc-v2-status'; Key='pcc.status'; Label='PCC v2 quick status'; Kind='PccBuiltin'; Menu=@('project'); MenuOrder=5 }
  @{ Id='pcc-v2-patches'; Key='pcc.patch-ledger'; Label='PCC patch ledger'; Kind='PccBuiltin'; Menu=@('project','logs'); MenuOrder=6 }
  @{ Id='pcc-v2-capabilities'; Key='pcc.capabilities'; Label='PCC capability report'; Kind='PccBuiltin'; Menu=@('project'); MenuOrder=7 }
  @{ Id='pcc-v2-validate'; Key='pcc.validate-v2'; Label='Validate PCC v2 contracts'; Kind='PccBuiltin'; Menu=@('project'); MenuOrder=8 }
  @{ Id='pcc-v3-lifecycle'; Key='pcc.validate-lifecycle'; Label='Validate PCC lifecycle / restart contract'; Kind='PccBuiltin'; Menu=@('project'); MenuOrder=9 }
  @{ Id='editor-v2-architecture'; Key='pcc.validate-editor-v2'; Label='Validate Experimental Editor architecture v2'; Kind='PccBuiltin'; Menu=@('project'); MenuOrder=10 }
  @{ Id='pcc-vault-status'; Key='pcc.vault-status'; Label='Vault dependency status'; Kind='PccBuiltin'; Menu=@('project','logs'); MenuOrder=11 }
  @{ Id='pcc-vault-sync'; Key='pcc.vault-sync'; Label='Sync verified dependencies with Vault'; Kind='PccBuiltin'; Menu=@('project'); MenuOrder=12 }
  # Experimental Bevy work is hosted by the existing PCC, never a second PCC.
  @{ Id='bevy-exp-status'; Key='experimental.bevy.status'; Label='Bevy candidate: project/status'; Kind='Script'; Script='HavenwildBevyCandidate.ps1'; Category='validation'; Menu=@('build'); MenuOrder=180; Args=@('-Action','Status') }
  @{ Id='bevy-exp-verify'; Key='experimental.bevy.verify'; Label='Bevy candidate: source + fixture verify'; Kind='Script'; Script='HavenwildBevyCandidate.ps1'; Category='validation'; Menu=@('build'); MenuOrder=190; Args=@('-Action','Verify') }
  @{ Id='bevy-exp-scene-plan'; Key='experimental.bevy.scene-plan'; Label='Bevy candidate: semantic scene plan (unmapped evidence)'; Kind='Script'; Script='HavenwildBevyCandidate.ps1'; Category='validation'; Menu=@('build','world'); MenuOrder=195; Args=@('-Action','ScenePlan') }
  @{ Id='bevy-exp-draft-plan'; Key='experimental.bevy.draft-plan'; Label='Bevy candidate: original-pixel UNAPPROVED GPU draw plan'; Kind='Script'; Script='HavenwildBevyCandidate.ps1'; Category='validation'; Menu=@('build','world'); MenuOrder=196; Args=@('-Action','DraftPlan') }
  @{ Id='bevy-exp-build'; Key='experimental.bevy.build'; Label='Bevy candidate: cargo check'; Kind='Script'; Script='HavenwildBevyCandidate.ps1'; Category='builds'; Menu=@('build'); MenuOrder=200; Args=@('-Action','Build') }
  @{ Id='bevy-exp-run'; Key='experimental.bevy.run'; Label='Bevy candidate: run isolated preview'; Kind='Script'; Script='HavenwildBevyCandidate.ps1'; Category='builds'; Menu=@('run'); MenuOrder=80; Args=@('-Action','Run') }
  # R9 GPU backend differential: never alter the normal Run backend or the production client.
  @{ Id='bevy-exp-run-dx12'; Key='experimental.bevy.run-dx12'; Label='Bevy diagnostic: DX12 full candidate (compare Vulkan)'; Kind='Script'; Script='HavenwildBevyCandidate.ps1'; Category='builds'; Menu=@('run'); MenuOrder=81; Args=@('-Action','RunDx12') }
  @{ Id='bevy-exp-run-primary-probe'; Key='experimental.bevy.run-primary-probe'; Label='Bevy diagnostic: primary window only / auto backend'; Kind='Script'; Script='HavenwildBevyCandidate.ps1'; Category='builds'; Menu=@('run'); MenuOrder=82; Args=@('-Action','RunPrimaryProbe') }
  @{ Id='bevy-exp-run-dx12-primary-probe'; Key='experimental.bevy.run-dx12-primary-probe'; Label='Bevy diagnostic: primary window only / DX12'; Kind='Script'; Script='HavenwildBevyCandidate.ps1'; Category='builds'; Menu=@('run'); MenuOrder=83; Args=@('-Action','RunDx12PrimaryProbe') }
  # B48R28C7-C16: One integrated infrastructure lane, candidate-only receipts.
  @{ Id='bevy-infra-audit'; Key='experimental.bevy.infra-audit'; Label='Bevy infrastructure: honest readiness report'; Kind='Script'; Script='HavenwildBevyCandidate.ps1'; Category='validation'; Menu=@('build'); MenuOrder=205; Args=@('-Action','InfraAudit') }
  @{ Id='bevy-infra-source'; Key='experimental.bevy.infra-source'; Label='Bevy infrastructure: verified source stack'; Kind='Script'; Script='HavenwildBevyCandidate.ps1'; Category='assets'; Menu=@('assets'); MenuOrder=207; Args=@('-Action','InfraSource') }
  @{ Id='bevy-infra-open'; Key='experimental.bevy.infra-open'; Label='Bevy infrastructure: open isolated river document'; Kind='Script'; Script='HavenwildBevyCandidate.ps1'; Category='assets'; Menu=@('world'); MenuOrder=210; Args=@('-Action','InfraOpen') }
  @{ Id='bevy-infra-mapper'; Key='experimental.bevy.infra-mapper'; Label='Bevy infrastructure: mapper topology review queue'; Kind='Script'; Script='HavenwildBevyCandidate.ps1'; Category='assets'; Menu=@('world'); MenuOrder=211; Args=@('-Action','InfraMapper') }
  @{ Id='bevy-infra-packets'; Key='experimental.bevy.infra-packets'; Label='Bevy infrastructure: renderer-neutral UNAPPROVED packets'; Kind='Script'; Script='HavenwildBevyCandidate.ps1'; Category='assets'; Menu=@('world'); MenuOrder=212; Args=@('-Action','InfraPackets') }
  @{ Id='bevy-infra-save'; Key='experimental.bevy.infra-save'; Label='Bevy infrastructure: candidate-only snapshot save'; Kind='Script'; Script='HavenwildBevyCandidate.ps1'; Category='validation'; Menu=@('build'); MenuOrder=213; Args=@('-Action','InfraSave') }
  @{ Id='bevy-infra-reopen'; Key='experimental.bevy.infra-reopen'; Label='Bevy infrastructure: verify candidate save/reopen'; Kind='Script'; Script='HavenwildBevyCandidate.ps1'; Category='validation'; Menu=@('build'); MenuOrder=214; Args=@('-Action','InfraReopen') }
  @{ Id='bevy-infra-pie'; Key='experimental.bevy.infra-pie'; Label='Bevy infrastructure: PIE handoff ticket (NO GAME LAUNCH)'; Kind='Script'; Script='HavenwildBevyCandidate.ps1'; Category='validation'; Menu=@('build'); MenuOrder=215; Args=@('-Action','InfraPie') }
  @{ Id='bevy-infra-parity'; Key='experimental.bevy.infra-parity'; Label='Bevy infrastructure: semantic diff (NOT runtime parity)'; Kind='Script'; Script='HavenwildBevyCandidate.ps1'; Category='validation'; Menu=@('build'); MenuOrder=216; Args=@('-Action','InfraParity') }
)
