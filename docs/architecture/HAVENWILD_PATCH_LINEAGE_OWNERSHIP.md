# Havenwild Patch Lineage Ownership

**Milestone:** `HW-UPDATE-INBOX-GOVERNANCE-01`

## Locked ownership

Forge/Vault owns patch discovery, classification, retention, and lineage.
Havenwild PCC owns project-native application, rollback, verification, quality
gating, and certification.

A package appearing in Downloads or another watched source is evidence to
classify. It is **not** a pending Havenwild update merely because it was found.

Historical packages are moved/catalogued into the Havenwild project Patch
Lineage maintained by Forge/Vault. The lineage record preserves the transport,
checksum/sidecar when present, manifest metadata, hashes, observed and package
timestamps, original source location, and relationship to current authority.

## Lineage classes

Forge should classify a discovered package as one of:

- ancestor
- direct parent
- current
- descendant candidate
- parallel branch
- superseded
- duplicate
- unknown lineage
- invalid or untrusted

Only a validated **descendant candidate** with a compatible declared base may be
promoted into a pending-update workflow.

## Havenwild apply path

The existing Havenwild root-drop quality-gate workflow remains authoritative:

`approved candidate -> repository-root transport -> Full Quality Gate ->
transactional apply -> archive consumed transport -> certify GREEN -> publish`

Forge may orchestrate that workflow, but does not bypass or reimplement it.

## Legacy `updates/inbox`

`updates/inbox` is retired as repository history and as historical patch
storage. It may exist locally only as transient compatibility/intake space.

The 50 tracked `.zip.sha256` sidecars retired by this milestone were historical
transport bookkeeping, not current Havenwild source. Their corresponding
packages belong in Forge/Vault Havenwild Patch Lineage rather than being
restored to a pending-update folder.

No discovered historical package may be automatically re-applied from this
location.

## Repository hygiene result

After this one-time retirement is committed, Forge/Vault scans may classify any
number of historical Havenwild patches without making the Havenwild repository
dirty. Project source remains independent from patch-history storage.
