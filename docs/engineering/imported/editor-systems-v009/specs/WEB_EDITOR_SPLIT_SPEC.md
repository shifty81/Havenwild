# Web Editor Split Spec

## Purpose

Web editors should handle data-heavy and form-heavy tasks that do not need immediate in-scene painting.

## Best web editor domains

```text
items
recipes
ingredients
cuisine tables
NPCs
staff traits
dialogue
quests
shops
economy/pricing
crops
fish
forage resources
island identities
localization
content audit dashboards
```

## Do not put these primarily in web editors

```text
pixel painting
scene layout
terrain painting
collision painting
object placement
animation timing preview
Y-sort visual testing
water/shore preview
```

These need direct visual feedback in the Rust editor.

## Web editor data flow

```text
web database table
        ↓
validated JSON/data record
        ↓
project database
        ↓
main Rust editor content browser
        ↓
runtime build/export
```

## Web editor requirements

```text
schema-driven forms
bulk table editing
search/filter/sort
validation errors inline
diff/preview changes
import/export CSV/JSON
content audit status
local-only first
optional future sync
```
