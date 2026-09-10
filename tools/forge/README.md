# Havenwild Forge adapter

This directory is the additive integration boundary between Havenwild and the
universal Forge/Vault Project Control Center.

It does **not** replace Havenwild's internal PCC. Havenwild's existing
`HavenwildTools.cmd` and `tools/control/*` remain project authority and remain a
fully independent recovery/fallback path.

Forge should discover `.forge/project.toml`, then use
`tools/forge/HavenwildForgeAdapter.py` for detection, JSON status, capability
metadata, self-test, and stable command-key dispatch.

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
