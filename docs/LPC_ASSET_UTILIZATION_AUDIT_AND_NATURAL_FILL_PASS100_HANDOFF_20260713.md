# LPC Asset Utilization Audit and Natural Fill Hotfix — Pass 100

## Outcome

Pass 100 fixes the Pass 99 promotion failure:

```text
ValueError: riverbank_mud has no verified repeatable neighbor fill for natural
```

`natural` is an authoring-level terrain class, not a concrete repeatable LPC
base tile. The transition promoter now resolves abstract repeatable-fill
neighbors before compound-mask baking:

- `natural` -> `grass`
- `farm` -> `dirt`
- `water` -> `shallow_water`

The semantic family contract remains unchanged; only the internal fill tile
lookup is normalized.

## Asset utilization audit

Added `tools/automation/assets/Build-HavenwildAssetUtilizationAuditV115.py` and the build
command:

```bash
./tools/build/Build.sh asset-utilization-audit [optional zip paths...]
```

The generated report is:

```text
docs/assets/HAVENWILD_ASSET_UTILIZATION_AUDIT_PASS100.md
```

The report classifies available asset packs into usable planning lanes:

- canonical LPC source
- secondary LPC atlas/reference
- animal animation source
- foliage/object source
- reference/hold
- uncataloged archive

It also flags unreadable archives and unknown-license packs so old assets do
not accidentally return to production/editor palettes.

## Validation

Added `tools/automation/validation/checks/assets/Validate-HavenwildAssetUtilizationAuditV115.py` and registered it
in:

- `tools/build/Build.sh` pre-Cargo validation
- `tools/automation/validation/validate.py`

Validated locally in the no-assets source workspace:

```text
python3 tools/automation/validation/checks/misc/Validate-LpcAuthoredReplacementRolesV111.py
python3 tools/automation/validation/checks/misc/Validate-LpcPaintTopologyStabilityV114.py
python3 tools/automation/validation/checks/assets/Validate-HavenwildAssetUtilizationAuditV115.py
python3 -m py_compile tools/automation/terrain/Promote-LpcTerrainFamiliesV90.py tools/automation/assets/Build-HavenwildAssetUtilizationAuditV115.py tools/automation/validation/checks/assets/Validate-HavenwildAssetUtilizationAuditV115.py
bash -n tools/build/Build.sh
./tools/build/Build.sh asset-utilization-audit <uploaded asset/source zips>
```

Full `tools/build/Build.cmd all` must be run in the real local repository because this
ChatGPT source workspace intentionally excludes raw/generated asset payloads.
