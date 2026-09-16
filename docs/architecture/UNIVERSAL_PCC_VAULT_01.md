# UNIVERSAL-PCC-VAULT-01

`UNIVERSAL-PCC-VAULT-01` is the shared contract every project-owned internal Project Control Center should implement for reusable assets and external dependencies.

## Authority split

- **Project Internal PCC** owns build/test/run/certification and project-specific dependency locks.
- **D:\Vault** is the machine-wide shared storage/catalog authority.
- **ForgePY/Cortex/Ember** may inspect or invoke the same contract, but a project must remain independently buildable without them.

## Required resolution order

1. verified project-local mount
2. verified shared Vault source
3. verified project-local cache
4. verified shared Vault archive
5. explicit project/environment override
6. network acquisition as the last resort
7. fail with recovery evidence

A build must never prefer a live web download over an already-verified local or Vault copy.

## Promotion policy

Automatic promotion is allowed only when:

- the dependency lock provides exact required-file SHA-256 hashes and sizes;
- the source matches every required fingerprint;
- license labels are known;
- the lock explicitly enables `vault.autoPromote`;
- a canonical `vault.rootRelativePath` is declared.

Anything incomplete, ambiguous, conflicting, or unlicensed is review/quarantine material and is not silently promoted.

## Transactional layout

Each promoted entry uses:

```text
<entry>/
├── source/
├── archive/                 # optional
├── licenses/                # attribution/license copies when known
├── metadata/
│   ├── source-lock.json
│   └── provenance.json
└── asset.json
```

Invalid pre-existing Vault entries are moved to `D:\Vault\Quarantine` before replacement; they are never silently deleted.

## Stable PCC commands

```text
pcc.vault-status
pcc.vault-sync
```

`pcc.vault-status` reports project/Vault readiness without network mutation.

`pcc.vault-sync` performs only verified promotion/hydration. It does not download from the network; acquisition remains project-specific and subsequent successful acquisition may promote into Vault.

## Havenwild reference implementation

Havenwild is the first certification project. Its LPC Terrains V7 lock is mapped to:

```text
D:\Vault\Assets\LPC\Terrains\lpc-terrains-v7
```

On a machine where `D:\Vault\Assets` is empty but Havenwild already has the exact locked source, the next dependency resolution promotes the verified source into Vault. Future clean Havenwild checkouts hydrate from Vault before attempting OpenGameArt.

## Propagation requirement

When this contract is proven GREEN in Havenwild, every other internal PCC should adopt the same contract and command keys. Projects provide only their project-specific dependency manifest and lock metadata; they should not fork the Vault algorithm.
