# Havenwild W60E2 — Collision Truth

W60E2 turns the selected-region collision layer from an empty placeholder into a real round trip.

Pixel Studio now receives a locked **Physical Collision Reference** generated from current terrain/object/stamp/building collision, plus separate editable **Collision Add** and **Collision Subtract** masks. The normal authoring snap remains 8 px while the mask itself supports 1 px precision.

Committed masks are registered in `content/world/collision_overrides_v1.json`. Runtime movement loads the same registry: subtract pixels can carve an authored opening from normal tile/building collision and add pixels can block otherwise open space. Structural cliff-edge traversal remains governed by the structural system so a pixel mask cannot silently erase elevation rules.
