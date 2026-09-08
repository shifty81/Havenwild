# Havenwild Development Tools

`HavenwildTools.cmd` is the only supported human-facing launcher at repository root.

- `build/` — internal build, test, run, package, and advanced CLI entrypoints.
- `control/` — the Windows project control center and registered operations.
- `automation/` — domain-owned generators, validators, migrations, reports, and dependency tooling.
- `archive/` — compatibility-only scripts excluded from normal development lanes.

New scripts must be placed in the narrowest applicable domain. Loose scripts at `tools/automation/` root are not allowed.
