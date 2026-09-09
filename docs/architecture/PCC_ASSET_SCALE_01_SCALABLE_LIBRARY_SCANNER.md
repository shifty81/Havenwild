# PCC-ASSET-SCALE-01 — Scalable Library Scanner

The first real LPC scan discovered more than sixty thousand PNG files. The
PCC-ASSET-01 scanner treated every PNG as an expensive generic sheet-analysis
job. That behavior was correct for small fixtures but inappropriate for a real
source ecosystem.

PCC-ASSET-SCALE-01 changes scanning from brute force to a staged pipeline.

## Pipeline

1. fast inventory and PNG header dimensions;
2. domain/analyzer classification;
3. persistent parallel content hashing;
4. exact duplicate grouping;
5. structural variant-family grouping;
6. Tiled metadata intake;
7. profile-selected deep analysis;
8. persistent analysis cache;
9. canonical catalog.

## Default SMART profile

SMART deep-analyzes unique grid-compatible terrain, structure and prop sources.
Character trees are indexed/classified instead of blindly running terrain-style
seam analysis over every color/action PNG. Specialized character analysis can
use the same catalog/family records in later passes.

SMART also has a bounded default deep-analysis budget. Any overflow is explicitly
reported as deferred; it is not silently lost.

## Scan profiles

- smart
- index
- terrain
- structures
- characters
- props
- animations
- full

FULL is now explicit.

## Cache and interruption

`artifacts/asset-intake/cache/pcc_asset_cache.sqlite`

stores file hashes and deep-analysis JSON keyed by content hash and analyzer
contract. A stopped scan preserves completed work. Re-running the same source
reuses that work automatically.

## Source identity

The catalog records both:

- the logical mount requested by the project; and
- the resolved physical dependency root.

This prevents machine-local dependency paths from replacing project-facing
source identity.

## Runtime safety

No runtime asset is promoted or certified by scanning. Pixel classification and
multi-tile detection remain evidence/candidates only.
