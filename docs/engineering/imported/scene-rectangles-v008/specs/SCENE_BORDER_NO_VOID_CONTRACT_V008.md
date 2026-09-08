# Scene Border and No-Void Composition V008

## Rule

The player should never see a raw void at the edge of a scene.

Every exposed scene edge must have either:

```text
a neighboring scene
a transition link
a natural border
a constructed border
an occluding edge treatment
```

## Border types

```text
forest_border
mountain_border
ocean_border
river_continuation
city_wall_border
cliff_drop_border
cave_darkness_border
fence_property_border
fog_soft_boundary
```

## Border depth

Borders need multiple bands:

```text
walkable gameplay interior
soft transition band
blocking/framing band
background continuation band
```
