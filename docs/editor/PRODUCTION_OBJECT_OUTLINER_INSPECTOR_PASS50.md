# Havenwild Pass 50 — Production Object Outliner and Inspector

Pass 50 gives the permanent Scene Map workspace a stable-ID object outliner, a property inspector, and project-scene lifecycle controls. It builds directly on the project-owned scene registry, canonical selection model, and typed transaction history from Passes 48B–49.

## Scene lifecycle

The left dock now exposes **New**, **Duplicate**, **Rename**, and **Delete** for project scenes.

- New scenes use a project-owned `ProjectSceneId` derived from the entered display name.
- Duplicate copies the selected scene and creates a unique `_copy` identifier.
- Rename updates the registry identity, display name, active-scene reference, and transition references through the existing registry repair path.
- Delete requires a second confirmation click and continues to honor active-scene and inbound-transition guards.
- Create, duplicate, rename, and delete are typed undoable operations. Scene insertion order is restored during undo.

Scene names are entered inline. Enter confirms and Escape cancels. The scene list is paged so arbitrary project scenes are no longer constrained by the original seed-scene count.

## Object outliner

The selected scene exposes a searchable, paged object list.

- Search matches object kind labels and stable object IDs.
- Clicking a row selects `SelectionItem::Object(ObjectId)` rather than a vector position.
- Outliner selection activates the Objects layer, selects the Select tool, and opens the Inspector tab.
- List insertion, deletion, sorting, duplication, and undo do not silently rebind the inspector to a different object.
- Row count adapts to the available dock height so the pager remains inside the permanent editor shell.

## Object inspector

The right dock now has **Tools** and **Inspector** tabs. The inspector is bound to the selected stable `ObjectId` and displays:

- object kind and stable ID;
- anchor tile;
- current asset key;
- current provenance summary;
- visual, collision, and interaction footprint values;
- movement blocking, occlusion, and fade behavior.

The Visual, Collision, and Interaction footprint targets each support offset X/Y and width/height changes. Collision and interaction footprints may be reduced to zero size; visual footprints retain a minimum 1×1 display size.

Changes are validated against map bounds and other object footprints before being accepted. Every accepted property action records a reversible typed `UpdateObject` transaction.

Inspector actions include:

- Focus selection;
- Duplicate;
- Delete;
- Reset the active footprint target;
- Reset the complete object footprint to the object-kind default.

Custom arbitrary metadata fields are intentionally deferred until the project has one canonical metadata schema. Pass 50 displays the active asset key and provenance without inventing a second metadata format.

## Canvas overlays

While the Inspector tab is active, the selected object displays three snapped overlays in the permanent canvas:

- blue: visual footprint;
- green: collision footprint;
- gold: interaction footprint.

The overlays use the same world/grid transform as object rendering, selection, placement, and editing.

## Architecture

Headless authoring behavior:

- `crates/haven_editor/src/object_inspector.rs`
- `crates/haven_editor/src/scene_management.rs`
- `crates/haven_authoring/src/transactions.rs`

Native workspace behavior:

- `apps/haven_editor_native/src/app/object_inspector.rs`
- `apps/haven_editor_native/src/app/scene_outliner.rs`

This separation keeps scene/object authoring reusable by tests, automation, and the future in-game developer surface without introducing Macroquad into the headless editor crate.

## Verification workflow

1. Launch the native editor and open Scene Map.
2. Select an object in the Object Outliner; verify the Inspector opens and the canvas shows all three footprints.
3. Change visual width and press `Ctrl+Z`; verify the width and overlay return together.
4. Search for `table` or an object ID and verify selection still binds to the intended object.
5. Create a scene, rename it, undo, redo, duplicate it, and delete the duplicate with the two-click confirmation.
6. Verify a scene referenced by an inbound transition cannot be deleted.

Validate the static contract with:

```powershell
.\tools\automation\validation\checks\editor\Validate-ProductionObjectOutlinerInspectorV63.ps1
```
