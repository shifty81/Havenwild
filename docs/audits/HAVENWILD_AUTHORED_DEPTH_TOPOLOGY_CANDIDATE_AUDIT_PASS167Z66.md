# Havenwild Authored Depth Topology Candidate Audit — Pass 167Z66

## Finding

The Z65 immutable-snapshot repair removed mutation cascades but did not deduplicate equivalent observations already present in that snapshot. One unsupported pair of shallow-water contacts could be reported by two or three adjacent deep cells.

## Certified rule

An unsupported authored-depth conflict is identified by its sorted shallow-contact coordinate set within one water domain. Exactly one canonical deep-cell repair is selected for each contact set. Direct cardinal evidence outranks diagonal-only evidence, followed by stable row-major ordering.

## Required invariants

- Opposite north/south or east/west depth contacts repair one cell.
- An outer edge plus unrelated inner corner repairs one cell.
- Multiple unsupported diagonal contacts repair one cell.
- Marine and freshwater identities remain separate.
- Independent contact sets repair independently.
- Rendering remains sourced from complete authored tilesheet cells only.
