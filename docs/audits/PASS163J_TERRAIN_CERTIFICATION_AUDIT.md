# Pass 163J Terrain Certification Audit

## Closed

- Ordinary building placement remains ground-only.
- Foundation and bridge workflows have an explicit semantic permission query.
- Water visuals cannot make land buildable or water walkable.
- Solid terrain cannot be bypassed by selecting a different support type.
- Static certification checks the atlas, tuple catalog, gameplay registry,
  editor inspector, and wrapped-seam scenario.

## Pending live certification

1. Run `tools/build/Build.cmd all` on Windows.
2. Launch the native World Builder.
3. Paint all acceptance scenarios.
4. Compare editor and runtime output.
5. Capture any unresolved tuple, seam, collision, or placement defect.
