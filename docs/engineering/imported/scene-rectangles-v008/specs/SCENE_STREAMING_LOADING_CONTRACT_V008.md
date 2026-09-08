# Scene Streaming and Loading Contract V008

## Runtime loading rule

```text
Load active scene.
Load north/east/south/west neighboring scenes.
Preload diagonals when player approaches scene corners.
Unload distant scenes after safe transition threshold.
```

## Harbor and island travel

Initial system:

```text
player reaches harbor/travel node
select destination island/city/harbor
show boat travel loading screen
load destination harbor scene
```

Future system:

```text
player-owned boat
active sailing scene
hazard/weather route simulation
employee couriers/boat captains
```

## Scene transition types

```text
walk_edge_transition
door_transition
cave_transition
harbor_travel_transition
city_district_transition
owned_land_transition
dungeon_depth_transition
```
