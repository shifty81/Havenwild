# Havenwild Forge adapter

This directory is the additive integration boundary between Havenwild and the
universal Forge/Vault Project Control Center.

It does **not** replace Havenwild's internal PCC. Havenwild's existing
`HavenwildTools.cmd` and `tools/control/*` remain project authority and remain a
fully independent recovery/fallback path.

Forge should discover `.forge/project.toml`, then use
`tools/forge/HavenwildForgeAdapter.py` for detection, JSON status, capability
metadata, self-test, and stable command-key dispatch.

## Patch intake and lineage

Forge/Vault owns discovery, classification, retention, and patch lineage.
Havenwild PCC owns the actual project-native apply transaction and quality gate.

A package discovered in Downloads or any watched intake location must be
inspected and classified **before** it can be treated as a pending update.
Historical, ancestor, superseded, parallel, duplicate, or otherwise non-current
packages belong in that project's Forge/Vault Patch Lineage. Discovery alone
must never enqueue or apply them.

Only a validated descendant candidate with a compatible declared base may be
promoted to the pending-update workflow. The normal Havenwild execution path
remains root-drop -> Full Quality Gate -> transactional Havenwild PCC apply.

`updates/inbox` is legacy machine-local transient space only. It is not project
source, not historical storage, and not the Forge/Vault patch-lineage store.

Examples:

```text
python tools/forge/HavenwildForgeAdapter.py detect --json
python tools/forge/HavenwildForgeAdapter.py status --json
python tools/forge/HavenwildForgeAdapter.py self-test --json
python tools/forge/HavenwildForgeAdapter.py invoke project.quality.full
python tools/forge/HavenwildForgeAdapter.py fallback
```

The fallback action launches the existing Havenwild Project Control Center. If
`HavenwildTools.cmd` or its required control files are absent, Forge should show
the CLI fallback button disabled/greyed out.
