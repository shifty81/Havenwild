# Scene Bank + Runtime Scene Framing — Pass 54B

## Workspace identities

The native editor now exposes four permanent workspaces:

- **World Routes** — harbor nodes, sea routes, and regional travel relationships.
- **Overworld Layout** — the infinite snapped exterior-scene canvas and island PCG actions.
- **Scene Bank** — interiors, caves, dungeons, and special scenes that are connected by transitions instead of occupying overworld terrain.
- **Scene Editor** — the active scene's tile, object, zone, transition, asset, and inspector authoring surface.

The Scene Bank is no longer a narrow dock attached to Overworld Layout. It owns a persistent pan/zoom canvas, scene preview cards, a scene list, selection state, an inspector, and an **Open in Scene Editor** action.

## Runtime camera

The client now uses a fixed 115% gameplay zoom. Mouse-wheel and Home-key runtime zoom controls were removed so accidental input cannot alter the intended framing.

The camera follows the player only while enough scene space remains. Near a scene border the camera clamps to the scene bounds and the player moves away from screen center. This keeps scene edges anchored to the display instead of exposing space outside the active scene.

The native editor camera code is separate and unchanged.

## Night presentation

Night reaches a substantially darker blue-black level. Dusk and dawn use a smooth transition curve. The darkness overlay is rendered before UI so player-facing and developer interfaces remain readable at night.
