# Havenwild W60B — Editor UI Authority Hotfix

W60B supersedes the proposed W60A fallback-font workaround. Segoe UI remains the normal Windows-native editor typeface.

## Font lifecycle

The native editor now gives Macroquad one completed graphics frame before allocating the Segoe UI font atlas. The first frame is a quiet dark surface with no fallback-font text. Segoe is then loaded and pre-warmed off-screen before the persistent staged loading surface is shown. The atlas is retained for the life of the editor and is not recreated when switching workspaces or returning from Play.

The default editor text scale is 1.15. `HAVENWILD_EDITOR_TEXT_SCALE` can override it from 1.0 through 1.5 without changing project content.

## Canvas chrome

The universal Tool Rack and Layer Rail are docks, not floating overlays. Scene, World, Scene Bank, Pixel, Animation, Character, and World Routes work areas reserve the left authoring gutter so the rail cannot cover rulers, toolbars, or editable content.

The tool rack uses a 36-pixel-wide hit target. Layer rows are 30 pixels high with explicit 30-pixel visibility and lock targets. Layer selection remains non-destructive and never implicitly arms Paint or Place.
