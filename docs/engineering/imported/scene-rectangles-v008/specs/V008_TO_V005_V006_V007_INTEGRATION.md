# V008 Integration with V005, V006, and V007

## Inputs from V007

```text
landmass ID
height map
slope map
moisture map
biome map
river mask
shore profile map
harbor candidate map
city suitability map
```

## V008 creates

```text
scene rectangles
scene roles
scene adjacency graph
transition nodes
edge seam signatures
border/no-void contracts
streaming groups
editor validation targets
```

## Outputs to V005

```text
scene-local semantic terrain arrays
scene-local height/moisture/slope/biome arrays
scene-local shore profile arrays
neighbor seam data
border treatment hints
```

## Outputs to V006

```text
collision regions
object placement constraints
transition triggers
occlusion/fade reservations
fringe/overhead layer reservations
camera bounds
streaming/loading behavior
```
