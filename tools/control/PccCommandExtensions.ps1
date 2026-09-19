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
)
