# HW-AUTHORITY-05 — Document Lifecycle Authority

This checkpoint adapts the existing editor rather than replacing working domain owners.

KEEP: existing Scene/Pixel/Animation/Character/Logic/Sound/UI owners, close dialog, and tab hosts.
ADAPT: existing per-domain dirty/save state behind a registry snapshot.
RETIRE: Character `dirty = false` and `Save & Close -> Save All`.
ADD: stable DocumentId versus presentation DocumentHostId.
REJECT: moving domain documents into a new god-object registry.

`document_authority.rs` is an adapter/index only. Character dirty state is derived from
the working recipe versus its last saved/loaded fingerprint. The close dialog now saves
only its requested target. Explicit Save All remains and now includes Character Studio.

The Full Quality Gate runs `Validate-DocumentAuthorityAuth05.py`. Manual acceptance is:
dirty Scene, Character, Animation, Pixel, Logic and Sound; save Character only; Save &
Close Animation only; cancel Pixel close; Save All; restart with no bogus recovery prompts.
