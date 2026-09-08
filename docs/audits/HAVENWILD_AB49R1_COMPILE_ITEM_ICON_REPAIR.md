# H21A14AB49R1 — Compile + Universal LPC Item Icon Binding Repair

Repairs the first Windows Full Quality Gate after AB40–AB49.

- Imports `GameplayTool` explicitly in the inventory interaction module.
- Stops calling `Path::display()` on the runtime item-icon manifest path because Havenwild runtime path helpers return `String`.
- Reconciles canonical gameplay equipment source IDs (`ulpc.*`) with the normalized Universal LPC catalog IDs (which intentionally omit the `ulpc.` prefix).
- Adds fail-closed validation if Universal LPC item-icon definition reconciliation ever regresses to zero resolved definitions.
- Extends the existing AB49 validator to guard all three repairs.

The source-ID reconciliation has been checked against the embedded pinned catalog metadata: 105/105 equipment seed definitions resolve after canonicalization. Actual PNG crop availability remains verified by the Windows build against the mounted pinned Universal LPC repository.
