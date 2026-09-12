# HW-ASSET-UNDERSTANDING-03

Baseline: `c9ce64891cc608dc06154c3b4be45d7b85ec2884`

This pass creates the first deliberately small Published Asset Registry for
terrain, water, and cliffs.

The mechanical LPC slice inventory remains source-addressing infrastructure.
The published registry contains only components that Havenwild currently
understands well enough to name, validate, and consume by stable ID.

Initial published vocabulary includes reviewed V7 ground/water identities,
ElizaWy south cliff crest/body/foot and contour components, and the complete
authored 3x4 directional cliff ramps.

Assets Studio Library now merges these published records so normal authoring can
see semantic IDs rather than whole source sheets.

No world-generation algorithm is changed in this pass. The next pass should
provide an asset-constrained topology query:

`desired semantic connection -> certified published asset IDs`

Worldgen can then assemble only supported authored vocabulary instead of
generating arbitrary topology and repairing semantics afterward.
