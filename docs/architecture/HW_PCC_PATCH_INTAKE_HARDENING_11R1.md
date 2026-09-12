# HW-PCC-PATCH-INTAKE-HARDENING-11R1

## Purpose

This pass hardens the internal Havenwild PCC root patch intake after the first real `.patch` startup test failed before editor source changed. It preserves the proven manifest ZIP intake path from `HW-DEEP-NORMALIZATION-AUDIT-10` and improves text-patch behavior instead of replacing the PCC.

## Changes

- Keeps manifest ZIP transport as the primary reliable intake path.
- Keeps root `.patch` discovery added in patch 10.
- Adds a `git apply --3way` check/apply fallback for Git unified-diff transports.
- Improves failure details by logging plain, three-way, and reverse apply check output.
- Archives failed startup text patches out of the repository root instead of leaving the internal PCC poisoned on every boot.
- Keeps Full Gate strict: a bad patch reintroduced during a normal non-prompt gate still fails the gate.

## Why this comes before more editor work

The editor Assets input fix should not be repeatedly tested through a fragile intake branch. First the PCC must clearly report and safely quarantine bad text patches. After this hardening passes, the Assets recovery can be reissued either as a cleaned `.patch` or as a manifest ZIP overwrite if full source payloads are available.

## Manual cleanup expected

If the previous failed patch is still in root, this patch removes it from root through the manifest remove list:

- `Havenwild__20260912__HW-ASSETS-INPUT-RECOVERY-11.patch`
- `Havenwild__20260912__HW-ASSETS-INPUT-RECOVERY-11.patch.sha256`

## Acceptance

- Dropping this ZIP into root and running option 1 applies cleanly through the known manifest ZIP path.
- Launching the PCC with a bad `.patch` no longer traps startup forever.
- Failure logs include enough information to distinguish context drift, already-applied patches, and genuine patch corruption.
- Existing ZIP manifest patch workflow remains unchanged.
