# Pass 148H — Runtime Startup Discovery and Stable Asset Cache

Havenwild now mounts production-approved asset packs once at runtime startup and builds a session-local cache keyed by `StableAssetRef`.

The cache resolves pack-local source paths against the discovered project root and keeps pack/source/asset identity intact. Runtime texture loading first requests semantic providers through the shared resolver. Existing direct paths remain temporary explicit fallbacks and emit diagnostics when selected.

Initial migrated texture consumers are base terrain, mapped terrain, road/live autotile, runtime objects, and the player character sheet. The same session is retained by the game for later PCG, F3, animation, audio, UI, item, and object migrations.
