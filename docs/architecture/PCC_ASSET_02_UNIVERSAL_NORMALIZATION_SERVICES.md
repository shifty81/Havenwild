# PCC-ASSET-02 — Universal Asset Normalization Services

PCC-ASSET-02 begins the actual consolidation of Havenwild's legacy asset
automation around the PCC Python spine.

The generated legacy inventory found hundreds of scripts because previous passes
implemented the same broad operations repeatedly. PCC-ASSET-02 does **not**
rewrite or delete those tools. It introduces stable service boundaries so they
can be migrated in batches.

## Canonical services

- source intake manifests;
- canonical catalog scan;
- sprite-sheet analysis;
- Tiled metadata evidence;
- provenance;
- prefab extraction/generation;
- certification queues;
- derived-output planning;
- runtime promotion planning;
- catalog validation;
- legacy normalization planning.

## Safety

Existing tools remain authoritative until parity is demonstrated.

The migration sequence remains:

`extract -> parity -> wrapper -> PCC command -> archive`

No script is automatically deleted. Runtime promotion requires
`runtime_certified`. Generated house recipes with missing roles remain candidate
recipes and never synthesize substitute art.

## Why validators are not migrated first

The inventory contains far more validators than any other category. Rewriting
them one-by-one would preserve duplication. Validators should instead converge
on the canonical services and schemas established here, then shrink by
capability/domain in later passes.

## Next

PCC-ASSET-03 should use the generated normalization plan to migrate the first
P0 donor batch: source intake, catalog, provenance and LPC/ElizaWy analysis,
with explicit output-parity records against the existing scripts.
