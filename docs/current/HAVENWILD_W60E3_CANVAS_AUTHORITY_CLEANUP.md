# Havenwild W60E3 — Canvas Authority Cleanup

W60E3 makes the centralized CanvasWorkspace authoritative rather than decorative.

- Tool Rail + Layer Dock start at the canvas host origin and reserve permanent left-side canvas geometry.
- A synthetic layer such as Buildings, Authored Pixel Override, Collision, or Terrain Transitions now has a real active canvas context rather than leaving the prior Terrain/Object context active underneath it.
- Changing Scene/World layers always returns to Select; it never silently arms Paint or Place.
- Locked Pixel Studio reference layers disable mutating tools.
- Tools that do not yet have a real adapter remain visible in their group but greyed/unselectable.
- Pixel Studio no longer exposes a second Layer Stack in the right Inspector. The canvas Layer Dock is the layer authority; the right side is Properties / Animation / Color.
- Scene/World toolbar chrome begins after the permanent left authoring inset so permanent Tool/Layer chrome cannot obscure it.

This is deliberately conservative: unfinished Move/Link/Socket/Event adapters are disabled instead of pretending to work by falling back to Select.
