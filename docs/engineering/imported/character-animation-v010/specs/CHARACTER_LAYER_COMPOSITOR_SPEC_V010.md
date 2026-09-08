# Character Layer Compositor Spec V010

## Layer order

Base recommended draw order:

```text
shadow
back accessory / cape back
back arm if direction requires
base body legs
pants / leg armor
boots
base body torso
shirt / chest armor
head
face
hair back
front arm if direction requires
gloves
held item behind/front depending frame flag
hair front
helmet / hat
front accessories
```

## Direction-sensitive depth

Some layers change order by direction.

Examples:

```text
north-facing held tool may draw partly behind body
south-facing held mug draws in front
east/west hands swap front/back emphasis
cape draws behind body except special motion
```

## Runtime composition modes

```text
prebaked composite cache
live layered draw
hybrid cache per outfit
debug socket overlay
```

Recommended:

```text
Use cached composites for normal runtime.
Use live layered draw in editor/character creator preview.
```

## Fallback behavior

If a layer fails validation:

```text
hide invalid layer
show debug warning
fall back to base body
do not crash runtime
```
