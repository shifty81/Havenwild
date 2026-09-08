# Havenwild H21A14AB40-AB49 — Player Interaction + GUI Closeout

## Scope

This batch preserves the existing main menu while replacing post-menu prototype presentation with one player-facing runtime authority.

## HUD

- No full-width bottom HUD band.
- Actual character portrait/vitals live at top-left.
- Circular player-centered minimap lives at top-right.
- Chat is a bounded bottom-left overlay with keyboard focus rather than a permanent global footer.
- The hotbar is an independent compact control and uses item-identity-backed icon crops generated from pinned Universal LPC equipment source art.

## Equipment

The inventory screen uses the actual runtime character compositor as the equipment paper doll. The eight canonical runtime slots are arranged around that character. Backpack stacks can be dragged onto compatible equipment slots and equipped items can be dragged back to backpack slots. Right-click remains a quick mouse unequip/split affordance.

## Ranged foundation

Shoot/spellcast equipment uses the mouse world position as an aim target. Primary input starts an aim state, holding input advances bounded charge and holds the LPC action pose, and release commits the actual LPC action. The projectile is spawned at the declared animation contact/release phase rather than on initial button press. Projectile impacts are world-space and are ready for AB50+ ECS wildlife/combat targets.

## Door diagnosis and repair

The generated `havenwild_structure_components_w45b.png` door strip was inspected directly. Its seven 32×64 source frames already keep the swing silhouette centered around the same in-cell hinge axis as the door narrows edge-on. Published W57K metadata additionally applied horizontal offsets from +12 to -12 pixels. Those offsets therefore translated a strip that was already normalized, producing the reported visible slide/detach.

AB48 keeps the certified source rectangles and timing, but zeros the redundant horizontal offsets for both static states and animation frames. Scene doors and BuildingInstance doors continue to consume the same published visual authority.

## Intentionally deferred

This is the presentation/input/projectile foundation, not a claim that the AB50+ wildlife/combat simulation is complete. Animal health, carcass processing, ammunition, weapon stat scaling, learn-by-doing combat XP, and network chat transport remain subsequent gameplay passes.
