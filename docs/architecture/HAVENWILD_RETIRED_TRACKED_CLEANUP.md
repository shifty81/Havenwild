# Havenwild Retired Tracked Cleanup

Milestone: `HW-PCC-RETIRED-TRACKED-CLEANUP-01`

`updates/inbox` is machine-local/transient and is excluded from governed source.
Older commits still tracked checksum sidecars beneath that prefix.

The protected Havenwild PCC publication bridge now stages only tracked deletions
already observed beneath `updates/inbox/` when publishing a certified GREEN
commit. It does not stage new ignored files, arbitrary modifications elsewhere,
or broaden the governed-source snapshot.

This closes the one-time repository retirement while keeping the normal flow:

`root-drop patch -> Full Quality Gate -> GREEN -> Commit + Push CURRENT GREEN`

Acceptance is a clean Git work tree after publication with local/repository pass
and GREEN certification still synchronized.
