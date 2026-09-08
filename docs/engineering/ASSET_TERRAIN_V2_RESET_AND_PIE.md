# Asset + Terrain V2 Reset / PIE Foundation

This reset preserves useful Havenwild assets and evidence while replacing fragmented runtime
authority with one production path.

Run the inventory before cutover:

`python tools/automation/audit/Audit-AssetTerrainV2Authorities.py`

The report is evidence only. It does not declare every matching file obsolete. Removal happens only
after V2 parity/certification proves that a V1 authority has been displaced.

PIE is part of the replacement definition of done. The native editor may add authoring overlays, but
the underlying world/resource/terrain/structure resolution and renderer must be the production path
used by the standalone client.
