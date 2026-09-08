# Frame Rig and Socket Metadata Spec

## FrameRig

Every animation frame must define sockets.

```text
root_anchor
head_anchor
torso_anchor
shoulder_left
shoulder_right
hand_left
hand_right
hip_left
hip_right
knee_left
knee_right
foot_left
foot_right
held_item_anchor
shadow_anchor
```

## Root anchor

The root anchor is the most important point.

```text
root_anchor = bottom-center foot anchor
```

Every visual layer must preserve this root.

## Socket tolerance

Default editor tolerances:

```text
root anchor drift: 0px allowed for approved production layers
hand/foot socket drift: 1px warning, 2px error
head/torso drift: 1px warning, 2px error
tool anchor drift: 1px warning, 3px error
```

## Depth flags

Each frame may specify depth behavior:

```text
left_arm_front
right_arm_front
held_item_front
hair_front
cape_back
tool_behind_body
```

These flags allow arms/tools to appear in front of or behind the body depending on direction/action.
