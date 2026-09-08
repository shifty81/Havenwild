# World Canvas / Scene Bank Pass 44

This pass starts the corrected standalone-editor world-map structure requested for Havenwild.

## Rules locked by this pass

- Exterior overworld scenes are drawn on a shared world canvas as placed rectangles.
- Each placed exterior rectangle renders from its actual `SceneMap`, not from a decorative generated island image.
- Interior, cave, dungeon, and special scenes do not become part of the overworld terrain surface.
- Off-world scenes appear in a scene bank and are connected by transitions.
- Clicking an overworld rectangle selects the scene rectangle.
- Clicking a scene-bank card selects it as the candidate scene for assignment.
- The inspector now exposes visible assignment controls instead of relying only on arrow keys and Enter/Backspace.

## Still required

The project still uses enum-backed `SceneId` values. Because of that, arbitrary scene creation/deletion cannot be honestly implemented as a simple button yet. The next architecture step is a scene identity migration to project-owned serializable IDs, then the editor can create/delete scenes and regions as real data.
