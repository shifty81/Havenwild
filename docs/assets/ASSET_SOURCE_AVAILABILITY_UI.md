# Asset Source Availability UI

Pass 24 wires the prototype asset dry-run bake report into the in-game **Assets** editor tab.

The donor/reference catalog remains the source of truth for what packs exist and what policy applies. The dry-run bake report remains the source of truth for whether a locally supplied/quarantined source archive is currently available for a prototype adapter.

## Visible status values

The Assets tab now shows a per-source availability value:

- `ready`: all required local source inputs for that adapter were found.
- `missing`: the source is allowed for prototype use, but one or more required archives/sheets are not present in the local import/quarantine roots.
- `blocked`: the source is blocked/refused by license or policy and cannot enter the runtime bake path.
- `error`: the bake plan or adapter reference is invalid.
- `n/a`: the donor source is cataloged for reference/pixel-editor study but does not have a prototype bake adapter yet.

## Safety boundary

This UI does not copy raw files, generate runtime atlases, or promote donor art. It only reads:

```text
WORKSPACE/generated/prototype_imports/prototype_asset_bake_dry_run_report_v0_1.json
```

The dry-run report is produced by:

```text
tools/automation/assets/DryRun-PrototypeAssetBakeV29.py
```

Blocked/non-commercial/unverified sources stay visible for learning/reference purposes, but the bake report keeps them refused for runtime ingestion.

## Editor usage

Open dev mode, switch to the **Assets** tab, and use the existing filters:

- `[` / `]`: grid size filter
- `F`: family filter
- `P`: policy filter
- `J` / `K`: select donor record
- `R`: refresh summary text

The selected details show the availability state, found input count, dry-run entry count, and the dry-run reason/note.
