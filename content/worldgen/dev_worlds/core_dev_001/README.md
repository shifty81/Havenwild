# Havenwild Core Development World

This directory is the source-controlled authored mirror for Havenwild's canonical development world.

- `world.tworld` is created/updated by the native editor on **Save All / Save & Push**.
- `WORKSPACE/saves/world.tworld` remains the machine-local working copy and is preferred when reopening the editor.
- If the local working copy is absent, the editor falls back to this source-controlled Core Dev copy.
- The running development client reloads this source-controlled copy when the editor pushes saved world changes.
- Do not place ordinary player save data here.
- Do not hand-edit the serialized world file while the editor is open.

This makes intentional editor-authored terrain/world corrections packageable in cumulative source patches and Development Handoff ZIPs while leaving runtime save state outside source authority.
