# PCC-FRONTDOOR-01R2 — Publication Reconciliation

## Acceptance defect

A successful protected CommitPushGreen could leave the front door showing
LOCAL_AHEAD_GREEN_UNPUBLISHED even though Git was clean and the push passed.

## Repair

- a GREEN commit is recorded as `committedCommit`; it is not called published
  until remote verification succeeds;
- no-op protected commits reconcile an already-certified HEAD instead of
  returning before state is updated;
- protected push now fetches origin/main after push and proves
  `origin/main == HEAD`;
- only after that proof is `publishedCommit` updated;
- the publication record and canonical GREEN marker are updated together;
- a successful protected push prints an explicit publication-reconciled line;
- a clean working tree with a stale governed fingerprint reports
  `FINGERPRINT_MISMATCH_GATE_STALE` rather than `LOCAL_MODIFIED_GATE_STALE`;
- front-door MATCH also checks the local origin/main tracking ref when present.

## Required final state

After startup patch intake, Full Quality Gate, and Commit + Push Current GREEN:

    Git        : Clean
    Local      : PCC-FRONTDOOR-01R2
    Repository : PCC-FRONTDOOR-01R2
    Sync       : MATCH
    Gate       : GREEN PCC-FRONTDOOR-01R2
    Updates    : 0 pending
