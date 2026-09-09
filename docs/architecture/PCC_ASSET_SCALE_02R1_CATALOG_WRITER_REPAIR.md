# PCC-ASSET-SCALE-02R1 — Catalog Writer Repair

Repairs the compact asset-catalog publication defect exposed by the
PCC-FRONTDOOR-01 Full Quality Gate without rerunning the 64k-source scan.

The previous writer appended the literal characters `\\n` after the JSON
document. The repair uses strict JSON round trips plus temporary-file and
atomic-replace publication. The PCC asset self-test now covers compact/full
writer round trips.

Generated `artifacts/` JSON is also excluded from the Havenwild-owned source
content validator. The asset loader can atomically repair only the exact known
legacy trailing-literal catalog defect when that catalog is next opened.

The existing SQLite detail store, caches, source inventory, and assembly work
are preserved.
