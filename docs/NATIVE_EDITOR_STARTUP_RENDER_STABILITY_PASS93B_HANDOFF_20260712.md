# Native Editor Startup and Render Stability — Pass 93B

## Purpose

Stabilize the native editor before further LPC/world-editor expansion and produce a complete source-only handoff with no binary/raw asset payload.

## Root causes addressed

1. Pixel Studio and Animation Studio performed recursive library scans during `EditorApp` construction. An external LPC root can contain tens of thousands of sheets, so startup could block or terminate before the first useful frame.
2. The Overworld Layout rendered every tile of every expanded 96×64 scene card every frame. A visible assembly could issue over one hundred thousand rectangle calls, causing a Windows unresponsive/ghosted dark window.
3. Startup and frame panics still terminated the editor process despite panic logging.
4. High-DPI editor scaling was always enabled, making diagnosis and viewport behavior less predictable on Windows display scaling.

## Changes

- Pixel and animation libraries now start empty and scan only when the user presses **Rescan**.
- Recursive external-library scanning is disabled by default. Set `HAVENWILD_PIXEL_SCAN_EXTERNAL=1` only for an explicit raw external scan; the large LPC library should ultimately use the paged slice-catalog workflow instead.
- Runtime atlas textures load after the first visible editor frame.
- Raw intake source previews are loaded on demand rather than during startup.
- Added `--safe-mode`, `tools/build/Build.cmd editor-safe`, and `./tools/build/dev.sh editor-safe`.
- Startup, update, and draw panics are contained and displayed in-window where possible.
- Panic logs now include a forced backtrace, executable path, arguments, and working directory.
- Overworld scene cards are visibility-culled, downsampled, and horizontal-color-run merged.
- UI camera/material state is reset before final overlays.
- Editor high DPI is disabled by default; opt in with `HAVENWILD_EDITOR_HIGH_DPI=1`.
- Added source-only export command and validator V105.

## Verification available in this environment

- Python syntax checks passed.
- `tools/build/Build.sh` and `tools/build/dev.sh` Bash syntax checks passed.
- V105 static stability validation passed.
- Source-only archive integrity and asset-exclusion checks passed.

Rust/Cargo is unavailable in the packaging environment. Run `tools/build/Build.cmd all` on Windows for authoritative formatting, check, strict Clippy, tests, and release packaging.
