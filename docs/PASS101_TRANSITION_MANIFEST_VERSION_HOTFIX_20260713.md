# Havenwild Pass 101 - Transition Manifest Version Hotfix

Pass 101 is a narrow correction on top of Pass 100 / V115 lineage.

## Why

`Promote-LpcTerrainFamiliesV90.py` correctly writes the Pass 99+ transition
manifest as version `0.8.1`, and the later V111/V115 source guards also expect
`0.8.1`.

`Validate-LpcEdgeSignatureSeamsV108.py` still expected `0.8.0`, which caused
`tools/build/Build.cmd all` to stop immediately after the transition atlas was generated.

## Changed

- Updated V108 to require `terrain_autotile_47_32.json` version `0.8.1`.
- No runtime resolver behavior changed.
- No terrain atlas artwork changed.
- No editor palette behavior changed.

## Follow-up

After this hotfix, continue the LPC path/town work from the Pass 100 asset
utilization foundation, not from the accidental Pass 85 rollups.
