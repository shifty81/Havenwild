# Universal Animation Library Reference Notes

Source archive inspected:

```text
C:/Users/Shifty/Downloads/Universal Animation Library[Standard] (3).zip
```

Local reference extraction:

```text
assets/raw/reference-packs/universal-animation-library-standard/extracted
```

License from archive:

```text
CC0 1.0 Universal (CC0 1.0)
Public Domain Dedication
Models by @Quaternius
```

## Contents

| File | Role |
|---|---|
| `UAL1_Standard.glb` | Godot/Unreal GLB with animation clips. |
| `UAL1_Standard.fbx` | Unity FBX with animation clips. |
| `Unity_Setup.png` | Unity setup reference. |
| `Unreal_Setup.png` | Unreal setup reference. |
| `Godot_Setup.png` | Godot setup reference. |

## Animation Clips Found

The GLB contains 45 animation clips:

```text
A_TPose
Crouch_Fwd_Loop
Crouch_Idle_Loop
Dance_Loop
Death01
Driving_Loop
Fixing_Kneeling
Hit_Chest
Hit_Head
Idle_Loop
Idle_Talking_Loop
Idle_Torch_Loop
Interact
Jog_Fwd_Loop
Jump_Land
Jump_Loop
Jump_Start
PickUp_Table
Pistol_Aim_Down
Pistol_Aim_Neutral
Pistol_Aim_Up
Pistol_Idle_Loop
Pistol_Reload
Pistol_Shoot
Punch_Cross
Punch_Jab
Push_Loop
Roll
Roll_RM
Sitting_Enter
Sitting_Exit
Sitting_Idle_Loop
Sitting_Talking_Loop
Spell_Simple_Enter
Spell_Simple_Exit
Spell_Simple_Idle_Loop
Spell_Simple_Shoot
Sprint_Loop
Swim_Fwd_Loop
Swim_Idle_Loop
Sword_Attack
Sword_Attack_RM
Sword_Idle
Walk_Formal_Loop
Walk_Loop
```

## Havenwild Usage Guidance

- Use this as a CC0 reference/source for 3D character motion vocabulary.
- For the current 2D/2.5D pixel direction, this is most useful for planning required character states before generating or drawing sprite sheets.
- Priority animation set for tavern/farm gameplay:
  - idle
  - walk
  - jog/sprint
  - interact
  - pickup/carry
  - sitting enter/idle/exit
  - talking idle
  - push
  - fixing/kneeling
  - hit/death for hazards or future combat
  - swim only if island/coast traversal uses visible water movement
- Combat, pistol, and spell clips should remain lower priority unless the design pivots toward combat-heavy systems.

## Pipeline Gap

The project still needs a character animation schema that can map gameplay verbs to either:

- generated pixel sprite sheets,
- imported skeletal animation clips,
- or runtime animation state names.

Recommended schema fields:

```text
character_id
rig_type
animation_id
source_clip
gameplay_verb
looping
root_motion
facing_mode
frame_rate_or_clip_speed
foot_anchor_px
event_markers
```
