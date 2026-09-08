# Pass 148Y — LPC Revised Mapping Queues

Pass 148Y converts the full recursive LPC Revised inventory into actionable, category-neutral review queues. Every inventory entry enters exactly one queue; no file is promoted or discarded implicitly.

## Queues

- license review
- characters
- terrain
- structures
- placeables
- animals
- animations/effects
- UI
- items
- audio/music
- editor templates
- uncategorized review

Queue membership is not production approval. LPC Revised remains reference-only until each source family has compatible commercial and redistribution evidence.

## Content Library

When `WORKSPACE/generated/lpc_revised_mapping_queues_v1.json` exists, the Content Library appends each queued source as a reference-only entry. Searchable tags expose queue, promotion state, and recommended action. The original relative source path and proposed semantic identity remain intact.

## Workflow

```bash
python tools/automation/project/Build-LpcRevisedInventoryV148X.py --strict-source
python tools/automation/project/Build-LpcMappingQueuesV148Y.py
./tools/build/Build.sh all
```

The generated queue file stays local under `WORKSPACE/generated` and is regenerated from the mounted dependency.
