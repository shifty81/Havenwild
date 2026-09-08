# Havenwild — V010 Character Modular Animation Contract

## Purpose

V010 defines how character animation stays uniform across:

```text
base body
arms
legs
head
hair
face
clothing
armor
boots/gloves
held tools
NPC variants
staff work animations
```

## Core rule

```text
Base motion is the source of truth.
All modular layers conform to the same frame rig.
```

Do not allow each layer to invent its own body motion.

## Locked first character sheet

```text
cell size: 64x96
directions: 8
walk frames per direction: 8
sheet size: 512x768
root anchor: bottom-center foot anchor
collision: small foot collision mask
```

## Direction order

Recommended locked row order:

```text
row 0 = S
row 1 = SE
row 2 = E
row 3 = NE
row 4 = N
row 5 = NW
row 6 = W
row 7 = SW
```

## Frame order for walk cycle

```text
0 contact A
1 down A
2 passing A
3 up A
4 contact B
5 down B
6 passing B
7 up B
```

## Master motion template

Each frame stores:

```text
root anchor
head anchor
torso anchor
shoulder L/R
hand L/R
hip L/R
knee L/R
foot L/R
held item anchor
shadow anchor
depth flags
```

## Modular layer rule

A layer is valid only if it matches the frame rig.

```text
hair follows head anchor
shirt follows torso/shoulder anchors
pants follow hip/knee/foot anchors
boots follow foot anchors
gloves follow hand anchors
armor follows torso/shoulder/limb anchors
tools follow held-item anchors
```

## Runtime rule

The runtime compositor chooses:

```text
base body frame
+ face layer
+ hair layer
+ clothing layers
+ armor layers
+ held item
+ shadow
```

Then it draws the result according to direction, frame, depth flags, and Y-sort root anchor.
