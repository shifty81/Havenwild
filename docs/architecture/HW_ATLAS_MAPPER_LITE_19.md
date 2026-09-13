# HW-ATLAS-MAPPER-LITE-19 / 19R2

## Purpose

Atlas Mapper Lite is a separate lightweight GUI for turning source atlas tiles into engine-readable assembly handoffs.

The tool is for the manual puzzle-piece workflow:

```text
Load PNG atlas
→ select individual 32x32 cells from the source sheet
→ drag cells onto an assembly canvas
→ rotate / flip / layer pieces
→ choose an asset category
→ export JSON describing the assembly
```

The source atlas is read-only and must never be modified by this tool.

## Run

From the repository root:

```powershell
.\tools\launch\HavenwildAtlasMapperLite.cmd
```

With a source atlas argument:

```powershell
.\tools\launch\HavenwildAtlasMapperLite.cmd "assets\source\licensed\lpc_revised\some_sheet.png"
```

The launcher is deliberately stored under `tools/launch`, not the repo root. It resolves the repository root by walking upward from its own location until it finds `Cargo.toml`, then runs Cargo from that root. This prevents the old failure where Cargo searched from `C:\Users\Shifty\Desktop` instead of the Havenwild repository.

## Output

The exported JSON uses:

```text
havenwild.atlas_assembly_handoff.v0_1
```

It records source atlas path, 32x32 tile size, asset category, source tile rectangles, assembly canvas positions, rotation, flips, and layer order.

## Status

This output is assembly evidence. It is not final runtime certification. The next importer pass must convert the handoff into Asset Authority candidates / PublishedWorldAssetMetadata drafts with sockets, footprints, collision, traversal, provenance, and validation before runtime publication.
