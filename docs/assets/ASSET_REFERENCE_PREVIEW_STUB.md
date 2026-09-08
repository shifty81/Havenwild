# Asset Reference Preview Stub

Pass 26 adds metadata-only preview support for donor/reference asset packs.

The preview catalog lives at:

```text
content/assets/reference_previews/asset_reference_preview_catalog_v0_1.json
```

It points to optional local/generated contact sheets under:

```text
WORKSPACE/generated/asset_reference_previews/
```

These preview paths are intentionally local/generated. The manifest does not copy raw third-party sheets into the source tree and does not authorize runtime use. Restricted or non-commercial sources may be visible as local editor references only; they remain blocked from runtime promotion unless their license state changes.

In the in-game **Assets** tab, use the new **Preview** button or **V** hotkey to show the selected source preview status/path.

Future pass: generate thumbnails/contact sheets locally from user-supplied donor packs after dry-run availability succeeds, while respecting each source policy.
