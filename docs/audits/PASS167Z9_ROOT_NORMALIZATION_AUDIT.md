# Pass 167Z9 — Root and Documentation Normalization

- Reduced loose root files from 282 to 9.
- Enforced the existing nine-file root contract.
- Merged uppercase `DOCS/` into canonical lowercase `docs/`.
- Preserved validated lowercase terrain evidence when duplicate generated outputs differed.
- Archived historical manifests, inventories, handoffs, scripts, and provenance by category.
- Rewrote 279 hard-coded uppercase documentation paths.
- Added a machine-readable normalization manifest and removal list.

This pass is structural. Runtime, content, and gameplay behavior are intentionally unchanged.

## Validation

- Content-integrity suite: 17/17 passed.
- Universal LPC character catalog: passed.
- Production LPC runtime binding: passed.
- Terrain topology certification: passed.
- Root contract: 9/9 allowed files, no uppercase `DOCS/`.
- Inherited gap: legacy Pass 146 completeness still expects missing `assets/source/original/cave_entrance_96.png`.
