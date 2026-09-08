# Havenwild Pass 96E — Generated Atlas Test Stability Hotfix

The full build reached and passed strict Clippy, then four `haven_assets` tests
identified two issues:

1. the deterministic Pass 95 metadata restore omitted `runtimeOuterMasks`;
2. three tests asserted obsolete absolute variant indices after the atlas grew
   to nine ordered families.

Pass 96E restores `runtimeOuterMasks: true` and makes the tests verify stable
atlas contracts instead:

- requested group and mask;
- 32×32 content rectangle;
- alignment to the two-pixel-padded, 34-pixel-stride atlas grid;
- presence or intentional absence of verified inner-corner roles.

Absolute variant indices are an implementation detail of family ordering and
are no longer treated as a runtime contract.

Extract this complete source rollup over the repository and run:

```bat
tools/build/Build.cmd all
```
