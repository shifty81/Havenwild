# Pass 139 — Character Creator GUI

## Purpose
Promote the Pass 136–138 character contracts into a visible Macroquad creator surface without exposing progression equipment during initial creation.

## Added
- Catalog-driven category tabs for body, head, eyes, eyebrows, facial hair, hair, starter top, starter bottom, starter shoes, and colors.
- Name entry capped at 24 characters.
- Option-card selection driven by semantic character option IDs.
- Five creator color channels.
- Four-direction neutral idle preview controls.
- Layered preview recipe display wired to `build_character_preview_layers`.
- Validation-gated Create Character action.

## Integration boundary
`CharacterCreatorUi` is deliberately self-contained. The frontend flow should own whether the user is selecting an existing profile or creating a new one. The UI returns a commit signal only after the Pass 137 policy and catalog validation succeed.

## Remaining production work
- Replace the preview recipe text with actual atlas-layer drawing after the promoted LPC character sheets are normalized into runtime texture roles.
- Add the five-card character profile selector immediately before this creator.
- Save the committed selection through `PersistentCharacterProfile` and `save_character_profile`.
- Add gamepad focus/navigation and scroll clipping for large future catalogs.
