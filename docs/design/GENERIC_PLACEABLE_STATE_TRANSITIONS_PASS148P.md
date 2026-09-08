# Pass 148P — Generic Placeable State Transitions and Behavior Binding

Pass 148P makes pack-defined placeable state the runtime authority after stable asset resolution.

## State contract

Each placeable catalog entry may declare ordered states, visual frames for those states, behavior-node identity, and transitions with `from`, `trigger`, `to`, `authority`, and an optional message.

Runtime mutations require the host-authoritative context. Editor state preview is separate and may select any declared state for placement without pretending to execute multiplayer runtime behavior.

## Initial proof behaviors

- Chair toggles between `default` and `occupied`.
- Bed changes from `made` to `occupied`; reset is a separate trigger.
- Tree changes from `mature` to `stump` after harvest interaction.
- Door toggles between `closed` and `open`; unlocking is a separate trigger.
- Cave entrances may transition from `sealed` to `open` through an unlock trigger.

## Behavior binding

Every proof entry carries a pack-defined `node_id`. The current runtime logs the node identity with the dispatched interaction. Future behavior-node execution can replace the placeholder action dispatcher without changing save identity or catalog layout.

## Persistence and compatibility

`object_state` remains the saved state record. Old saves without state records use the entry's first declared state. `ObjectKind` remains a rendering/interaction fallback only when stable provider resolution fails.
