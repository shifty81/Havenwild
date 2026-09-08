# Havenwild Native Animation Studio Workflow — Pass 63

## Purpose

Animation Studio turns the project-owned and declared-CC0 source sheets already available to Pixel Studio into validated, publishable frame animations. It does not alter the original source PNG. Clip layout, timing, pivots, shadow anchors, sockets, and events are stored in animation metadata.

This pass is deliberately focused on frame animation. Bone hierarchies, IK dragging, weighted pixel deformation, layered clothing composition, and runtime state-machine graphs remain later systems.

## Workspace layout

The native editor now contains a sixth top-level workspace: **Animation Studio**.

- **Animation Sources**: searchable shared Pixel Studio source library filtered to character, animal, shadow, and animation sheets.
- **Source Sheet**: complete PNG with the logical frame grid and selected source cell.
- **Clip Preview**: nearest-neighbor playback with onion skin, pivot, shadow anchor, and socket markers.
- **Timeline**: ordered frame thumbnails with duration, event, socket, and selection indicators.
- **Inspector**: clip direction/loop settings, profile slicing, timing, pivot, shadow, sockets, events, save, validation, and runtime publishing.

## Opening a sheet

1. Launch the native editor and choose **Animation Studio**, or run `./tools/build/Build.sh animation-studio`.
2. Select a source sheet in the left library.
3. Choose **Open**. The image remains source-only.
4. Animation Studio restores an existing `.hhanim.json` document when one has already been saved for that sheet.

Working metadata is saved under:

```text
assets/source/original/animation_studio/<sheet>.hhanim.json
```

## Creating clips

### Recommended profile

**Apply Sheet Preset** creates directional clips for recognized CC0 sheet organizations:

- Chicken walk/eat: 32×32, four directions, four frames per row.
- Llama walk/eat: 128×128, four directions, four frames per row.
- Pig walk/eat: 128×128, four directions, four frames per row.
- Horse: 128×128, four walk rows plus four idle rows.
- Cat and base-character sheets remain manual because they contain mixed/non-uniform groups.

The preset is a starting point. Every generated clip and frame remains editable.

### Manual clip authoring

1. Add or select a clip.
2. Click a source-grid cell.
3. Choose **+ Frame** or press `A`.
4. Repeat for each frame.
5. Drag-order is represented by **Move <** and **Move >** in this foundation pass.
6. Use **Duplicate** or **Delete** where needed.
7. Set the direction and loop mode.

**Slice Selected Row** replaces the current clip with every valid frame cell on the selected grid row.

## Playback and timing

- `Space`: play or pause.
- Left/Right: previous or next frame.
- Shift+Left/Right: previous or next clip.
- Loop modes: Loop, Once, and Ping Pong.
- Each frame stores an independent duration in milliseconds.
- **- Duration** and **+ Duration** adjust timing in 25 ms increments.
- Onion skin shows the previous frame without modifying source pixels.

## Per-frame anchors

### Pivot

The pivot is a frame-local pixel coordinate used to keep feet/body placement stable between differently shaped frames.

- Press `P` or choose **Place Pivot**.
- Click the preview.
- **Pivot Bottom** restores the standard bottom-center foot anchor.

### Shadow anchor

The shadow anchor is stored as an offset from the frame pivot.

- Press `H` or choose **Place Shadow**.
- Click the desired ground contact point in the preview.
- **Reset Shadow** returns it to the pivot.

### Sockets

Each frame can place these sockets:

- Main Hand
- Off Hand
- Tool
- Head
- Back
- Mouth
- Ground
- Interaction

Choose the socket type, press `K` or choose **Place Socket**, then click the preview. Sockets are frame-local and can therefore follow hand, head, mouth, and tool motion correctly.

## Frame events

The selected frame can toggle:

- Footstep
- Sound
- Impact
- Eat
- Interaction
- Spawn Effect
- Custom

Pass 63 stores typed events and an optional payload field in the schema. A later property editor will expose payload text, sound browsing, and effect binding.

## Save and publish

**Save Animation** writes only the editable source metadata.

**Publish Runtime** first validates the document, then:

1. Saves the source metadata.
2. Copies the promoted image to `assets/generated/animations/`.
3. Writes runtime metadata under `content/animations/`.
4. Registers or updates the entry in `content/animations/animation_catalog_v0_1.json`.

A clip cannot publish when it has no frames, has duplicate/empty IDs, contains zero-duration frames, or references pixels outside the source image.

## Keyboard reference

```text
Space                 Play / pause
Left / Right          Previous / next frame
Shift+Left / Right    Previous / next clip
A                     Add selected source cell to clip
P                     Place pivot
H                     Place shadow anchor
K                     Place selected socket
Delete / Backspace    Delete selected frame
Escape                Stop playback and cancel point placement
```

## Bash workflow

```bash
./tools/build/Build.sh animation-audit
./tools/build/Build.sh animation-studio
./tools/build/Build.sh all
```

## Current boundary and next work

Pass 63 establishes non-destructive frame-animation authoring and publishing. The next animation phases should add:

1. Clip renaming and event-payload/property editing.
2. Timeline scrolling, box selection, drag reordering, and copy/paste between clips.
3. Separate shadow-sheet binding and runtime composite preview.
4. Equipment/clothing layer composition tied to shared pivots and sockets.
5. Runtime animation catalog loading and state-machine binding.
6. Skeleton hierarchy, IK handles, weighted regions, manual posing, keyframes, and pixel deformation after the frame-animation path is stable.
