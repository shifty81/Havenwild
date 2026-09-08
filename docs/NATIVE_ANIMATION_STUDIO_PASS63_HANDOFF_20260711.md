# Havenwild Pass 63 Handoff — Native Animation Studio

## Baseline

Built from `Havenwild_UpdatedSource_NativePixelStudioWorkflowPass62_20260711.zip`.

## Delivered

- New presentation-neutral animation model under `crates/haven_pixel/src/animation/`.
- Native **Animation Studio** workspace with source sheet, preview, timeline, and inspector.
- Non-destructive clip/frame authoring from the Pixel Studio/CC0 source library.
- Directional clips and Loop/Once/Ping Pong playback.
- Per-frame duration, pivot, shadow offset, sockets, and typed events.
- Recommended slicing profiles for chicken, llama, pig, and horse sheets.
- Saveable `.hhanim.json` source metadata.
- Validated runtime publishing to `assets/generated/animations` and `content/animations`.
- Runtime animation catalog registration.
- `./tools/build/Build.sh animation-studio` and `./tools/build/Build.sh animation-audit`.
- Validation contract V80.

## Editor workflow

1. Open **Animation Studio**.
2. Pick a CC0 or project-owned animation sheet.
3. Apply a known sheet preset or select/slice source cells manually.
4. Arrange frames, set timing, direction, and loop behavior.
5. Place pivots, shadow anchors, and equipment/tool sockets.
6. Toggle frame events.
7. Save the editable document.
8. Publish after validation.

## Important boundary

The original CC0/source PNG is never edited by Animation Studio. Publishing is explicit and creates a generated runtime copy. This pass is frame-animation authoring; it does not claim to provide skeleton IK or weighted pixel deformation yet.

## Verification

Static checks completed in the packaging environment:

- Rust delimiter sweep
- Architecture validation
- Content validation
- Pixel Studio V79
- Animation Studio V80
- JSON parsing
- Python compilation
- Bash syntax

Cargo, Rustc, Rustfmt, and Clippy were unavailable. The Windows workstation must run:

```bash
cd /c/Users/Shifty/Desktop/havenw
./tools/build/Build.sh animation-audit
./tools/build/Build.sh all
./tools/build/Build.sh animation-studio
```
