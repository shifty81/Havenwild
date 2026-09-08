# Pass 145 — Editor Command and Undo Normalization

All committed world edits must flow through the shared `haven_authoring::EditorCommandBus`.
The command envelope now owns affected bounds, dirty chunks, validation requests,
permission scope, persistence intent, and authoritative-host requirements.

Typed transactions remain the production undo/redo path. Snapshot history is retained
only as a compatibility bridge for the in-game overlay and should be migrated incrementally.
Future native editor, developer-mode, and player World Builder tools must not mutate the
world directly outside registered command handlers.
