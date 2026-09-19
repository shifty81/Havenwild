//! Native, source-pixel-only review export owned by Atlas Mapper.
//! Never treats successful rendering as semantic, visual or runtime certification.
use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

use image::imageops;
use image::{GenericImageView, Rgba, RgbaImage};
use serde::Serialize;

use super::{AssemblyPiece, SourceAssetDocument, TerrainHeightCell, TILE_SIZE};

const MAX_OUTPUT_SIDE: i32 = 8192;

#[derive(Serialize)]
struct ReviewLedger<'a> {
    schema: &'static str,
    approval: &'static str,
    source_assets: &'a [SourceAssetDocument],
    placements: &'a [AssemblyPiece],
    heightmap: &'a [TerrainHeightCell],
    output_pixel_size: [u32; 2],
    output_grid_origin: [i32; 2],
    evidence_notes: Vec<&'static str>,
}

pub(super) fn write_review(
    path: &Path,
    sources: &[SourceAssetDocument],
    pieces: &[AssemblyPiece],
    heightmap: &[TerrainHeightCell],
) -> Result<PathBuf, String> {
    if sources.is_empty() || pieces.is_empty() {
        return Err("At least one source and one placed tile are required".into());
    }
    let mut sheets = BTreeMap::new();
    let root = std::env::current_dir().map_err(|error| format!("Review root unavailable: {error}"))?;
    for source in sources {
        if source.id.is_empty() || sheets.contains_key(&source.id) {
            return Err(format!("Duplicate or empty source identity: {}", source.id));
        }
        let image = image::open(root.join(&source.path))
            .map_err(|error| format!("Source missing/unreadable {}: {error}", source.path))?
            .into_rgba8();
        sheets.insert(source.id.clone(), image);
    }
    let min_x = pieces.iter().map(|piece| piece.canvas_grid_x).min().unwrap();
    let min_y = pieces.iter().map(|piece| piece.canvas_grid_y).min().unwrap();
    let max_x = pieces.iter().map(|piece| piece.canvas_grid_x).max().unwrap();
    let max_y = pieces.iter().map(|piece| piece.canvas_grid_y).max().unwrap();
    let cols = i64::from(max_x) - i64::from(min_x) + 1;
    let rows = i64::from(max_y) - i64::from(min_y) + 1;
    if cols <= 0 || rows <= 0 || cols > i64::from(MAX_OUTPUT_SIDE / TILE_SIZE)
        || rows > i64::from(MAX_OUTPUT_SIDE / TILE_SIZE)
    {
        return Err("Review bounds exceed 8192px, or tile coordinates overflow".into());
    }
    let width = cols as u32 * TILE_SIZE as u32;
    let height = rows as u32 * TILE_SIZE as u32;
    let mut output = RgbaImage::from_pixel(width, height, Rgba([0, 0, 0, 0]));
    let mut order: Vec<_> = pieces.iter().collect();
    order.sort_by_key(|piece| (piece.layer, piece.id));
    for piece in order {
        let source_id = &piece.source_asset_id;
        let sheet = sheets.get(source_id)
            .ok_or_else(|| format!("Piece {} references missing source ID {}", piece.id, source_id))?;
        let [sx, sy, sw, sh] = piece.source_rect;
        if sx < 0 || sy < 0 || sw != TILE_SIZE || sh != TILE_SIZE
            || i64::from(sx) + i64::from(sw) > i64::from(sheet.width())
            || i64::from(sy) + i64::from(sh) > i64::from(sheet.height())
        {
            return Err(format!("Piece {} has an invalid source rectangle", piece.id));
        }
        let crop = sheet.view(sx as u32, sy as u32, sw as u32, sh as u32).to_image();
        let crop = if piece.flip_x { imageops::flip_horizontal(&crop) } else { crop };
        let crop = if piece.flip_y { imageops::flip_vertical(&crop) } else { crop };
        let crop = match piece.rotation_degrees.rem_euclid(360) {
            0 => crop, 90 => imageops::rotate90(&crop),
            180 => imageops::rotate180(&crop), 270 => imageops::rotate270(&crop),
            _ => return Err(format!("Piece {} has an unsupported rotation", piece.id)),
        };
        let dx = (i64::from(piece.canvas_grid_x) - i64::from(min_x)) * i64::from(TILE_SIZE);
        let dy = (i64::from(piece.canvas_grid_y) - i64::from(min_y)) * i64::from(TILE_SIZE);
        imageops::overlay(&mut output, &crop, dx, dy);
    }
    // Reject invalid heightmap values; no old one-level restriction is applied.
    if heightmap.iter().any(|cell| cell.elevation > 30 || cell.water_surface.is_some_and(|water| water > 30)) {
        return Err("Heightmap must use genuine elevation 0..=30, including +1".into());
    }
    let ledger = ReviewLedger {
        schema: "havenwild.atlas_mapper_review.v0_1",
        approval: "unreviewed_source_assembly_not_for_runtime",
        source_assets: sources,
        placements: pieces,
        heightmap,
        output_pixel_size: [width, height],
        output_grid_origin: [min_x, min_y],
        evidence_notes: vec![
            "PNG uses source pixel crops and recorded transforms only; it is not generated artwork.",
            "Review export does not certify seams, water connectivity, traversal, collision or editor/client parity.",
            "Source SHA-256 values are emitted by the separate verified intake pass, not guessed here.",
        ],
    };
    let ledger_path = path.with_extension("review.json");
    // Serialize first so an invalid document cannot leave behind a convincing PNG.
    let serialized = serde_json::to_vec_pretty(&ledger)
        .map_err(|error| format!("Review ledger serialization failed: {error}"))?;
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|error| format!("Cannot create review directory: {error}"))?;
    }
    output.save(path).map_err(|error| format!("Review PNG export failed: {error}"))?;
    fs::write(&ledger_path, serialized).map_err(|error| format!("Review ledger write failed: {error}"))?;
    Ok(ledger_path)
}

#[cfg(test)]
mod tests {
    use super::*;
    use super::super::AssemblyPiece;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn test_directory() -> PathBuf {
        let nanos = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos();
        std::env::temp_dir().join(format!("havenwild_mapper_native_review_{}_{}", std::process::id(), nanos))
    }
    fn piece(id: u32, source: &str, x: i32) -> AssemblyPiece {
        AssemblyPiece {
            id, source_tile_x: 0, source_tile_y: 0, source_rect: [0, 0, 32, 32],
            canvas_grid_x: x, canvas_grid_y: 0, rotation_degrees: 0,
            flip_x: false, flip_y: false, layer: 0,
            semantic_role: "unreviewed".into(), source_asset_id: source.into(),
        }
    }
    #[test]
    fn two_distinct_original_sheets_roundtrip_review_pixels() {
        let directory = test_directory(); fs::create_dir_all(&directory).unwrap();
        let paths = [directory.join("one.png"), directory.join("two.png")];
        for (i, path) in paths.iter().enumerate() {
            RgbaImage::from_pixel(32, 32, Rgba([i as u8 * 80 + 40, 2, 3, 255])).save(path).unwrap();
        }
        let sources: Vec<_> = paths.iter().enumerate().map(|(i, path)| SourceAssetDocument {
            id: format!("source-{i}"), path: path.to_string_lossy().into_owned(),
            file_name: path.file_name().unwrap().to_string_lossy().into_owned(),
            source_sha256: None,
        }).collect();
        let placements = vec![piece(1, "source-0", -1), piece(2, "source-1", 0)];
        let png = directory.join("review.png");
        let receipt = write_review(&png, &sources, &placements, &[
            TerrainHeightCell {x: -1, y: 0, elevation: 1, water_surface: Some(0)},
            TerrainHeightCell {x: 0, y: 0, elevation: 30, water_surface: None},
        ]).unwrap();
        let image = image::open(&png).unwrap().to_rgba8();
        assert_eq!(image.dimensions(), (64,32));
        assert_eq!(image.get_pixel(0,0).0, [40,2,3,255]);
        assert_eq!(image.get_pixel(33,0).0, [120,2,3,255]);
        assert!(fs::read_to_string(receipt).unwrap().contains("unreviewed_source_assembly"));
        fs::remove_dir_all(directory).unwrap();
    }
    #[test]
    fn missing_source_and_invalid_cliff_height_are_rejected() {
        let source = SourceAssetDocument {
            id: "a".into(), path: "does_not_exist.png".into(),
            file_name: "does_not_exist.png".into(), source_sha256: None,
        };
        assert!(write_review(&test_directory().join("a.png"), &[source], &[piece(1,"a",0)], &[]).is_err());
    }
}
