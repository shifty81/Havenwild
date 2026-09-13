# HW-EMBERWRIGHT-WIDGETKIT-SEAM-17

## Purpose

This pass resumes editor normalization after the PCC identity recovery by adding a small, compile-safe professional widget/overlay contract seam.

It does not rewrite the GUI and it does not touch runtime play behavior. The goal is to make the next visible GUI passes safer by giving the editor a single vocabulary for professional widgets, dock/floating surfaces, and opaque canvas overlays.

## Locked rules

- Canvas / Room Canvas / Game Canvas stays the permanent center.
- Tool Rail and Layer Rail are opaque canvas overlays.
- Normal editor widgets must use theme tokens and support disabled/hover/active/focus behavior.
- PIE hides ordinary canvas overlays and keeps only the PIE control strip visible.
- Docked panels and floating panels must be normalized through stable panel/widget identities.

## Why this is small

The previous large cumulative GUI packages failed because too much source was overwritten at once. This patch intentionally adds one isolated Rust module and one module registration only.

## Next pass

HW-EMBERWRIGHT-TOOLPANEL-REGISTRY-18 should add the matching panel registry seam for:

- Asset Browser
- Source Library
- Asset Authority
- Catalog Health
- Atlas Assembly
- Inspector
- Properties
- Output / Problems / Build / Activity / Chat

Then later passes can wire existing UI into those seams one panel at a time.
