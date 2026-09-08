# Pass 148L — Semantic Stamp Discovery and Editor Placement

Stamp catalogs are discovered from mounted production asset packs. Any `editor_template` asset whose semantic ID begins with `stamp.catalog.` is treated as a catalog provider. Its `metadata.sheet_semantic_id` resolves the visual sheet through the same pack, preserving both stable references.

The registry no longer depends on a global manifest list. Runtime F3 placement, native editor placement, the asset palette, and runtime drawing all consume the same discovered `StampRegistry`. Pack-qualified stamp IDs prevent collisions, while legacy unqualified IDs remain readable for existing saves.

Save-owned previews and diagnostic images remain outside the stamp provider system.
