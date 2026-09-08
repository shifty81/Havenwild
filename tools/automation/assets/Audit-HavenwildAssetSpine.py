#!/usr/bin/env python3
"""Canonical Havenwild asset/terrain/validator normalization audit.

This tool is intentionally read-only. It does not promote assets, rewrite manifests,
change validators, or fetch external content. Its job is to make the current source
truth visible through one report so runtime/editor/validator cleanup can converge on
one asset spine instead of creating more pass-specific catalogs.

Outputs are written under artifacts/audits/asset-spine/<timestamp>/ plus a LATEST
pointer file. The tool uses only the Python standard library so it can run from the
Project Control Center without additional dependencies.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import json
import os
import re
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

IMAGE_EXTENSIONS = {".png", ".gif", ".webp", ".bmp", ".jpg", ".jpeg"}
AUDIO_EXTENSIONS = {".wav", ".ogg", ".mp3", ".flac", ".mid", ".midi"}
PASSISH = re.compile(r"(?:pass\d|v\d{2,}|w\d|z\d|r\d{2,}|h\d{2,})", re.I)

CAPABILITIES = (
    "repository.contract",
    "assets.sources.contract",
    "assets.recipes.contract",
    "runtime.bindings.contract",
    "terrain.structural.contract",
    "world.generation.contract",
    "editor.parity.contract",
    "acceptance.contract",
)


OGA_LPC_COLLECTION_URL = "https://opengameart.org/content/nearly-all-the-lpc-assets-in-one-place"
OGA_RELEVANCE = {
    "terrain": ("terrain", "mountain", "cliff", "beach", "desert", "forest", "snow", "ice", "water", "lava", "street", "road"),
    "nature": ("tree", "conifer", "flower", "plant", "fungi", "wood", "rock", "jungle", "bamboo", "baobab"),
    "farming": ("farm", "crop", "fruit", "orchard", "trough", "chicken", "cow", "pig", "goat", "sheep", "horse"),
    "structures": ("building", "wall", "floor", "roof", "door", "window", "bridge", "cave", "mine", "castle", "interior", "furniture", "tavern", "sawmill", "blacksmith", "woodshop", "tailor", "alchemy", "container", "shelf", "table"),
    "characters_equipment": ("character", "clothes", "clothing", "armor", "helmet", "hat", "hair", "tool", "axe", "pickaxe", "shovel", "hoe", "weapon", "shield", "backpack", "animation", "expression"),
    "animals_fishing": ("animal", "fish", "bird", "rabbit", "deer", "bear", "wolf", "boar", "rat", "cat", "dog", "snake"),
    "ui_fx_audio": ("ui", "interface", "effect", "explosion", "flame", "rain", "weather", "icon"),
}

class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(); self.links: list[tuple[str, str]] = []; self._href: str | None = None; self._text: list[str] = []
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a": return
        self._href = dict(attrs).get("href"); self._text = []
    def handle_data(self, data: str) -> None:
        if self._href is not None: self._text.append(data)
    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            title = " ".join("".join(self._text).split())
            if title: self.links.append((self._href, title))
            self._href = None; self._text = []

def oga_domains(title: str) -> list[str]:
    lower = title.lower()
    return [domain for domain, words in OGA_RELEVANCE.items() if any(word in lower for word in words)]

def discover_oga_lpc(root: Path, out_dir: Path) -> dict[str, Any]:
    request = urllib.request.Request(OGA_LPC_COLLECTION_URL, headers={"User-Agent": "Havenwild-Asset-Spine-Audit/1"})
    with urllib.request.urlopen(request, timeout=45) as response:
        html = response.read().decode("utf-8", errors="replace")
    parser = _LinkParser(); parser.feed(html)
    existing_pages: set[str] = set()
    registry = root / "content/assets/oga_lpc/manifests/oga_lpc_prototype_source_registry_v0_1.json"
    if registry.exists():
        try:
            data = load_json(registry); existing_pages = {str(x.get("sourcePage", "")).rstrip("/") for x in data.get("sources", [])}
        except Exception: pass
    seen: set[str] = set(); rows: list[dict[str, Any]] = []
    for href, title in parser.links:
        url = urljoin(OGA_LPC_COLLECTION_URL, href)
        parsed = urlparse(url)
        if parsed.netloc not in {"opengameart.org", "www.opengameart.org"}: continue
        if not parsed.path.startswith("/content/"): continue
        normalized = f"https://opengameart.org{parsed.path}".rstrip("/")
        if normalized == OGA_LPC_COLLECTION_URL.rstrip("/") or normalized in seen: continue
        seen.add(normalized)
        domains = oga_domains(title)
        rows.append({"title": title, "source_page": normalized, "havenwild_domains": ";".join(domains), "relevant": bool(domains), "already_tracked": normalized in existing_pages})
    rows.sort(key=lambda x: (not x["relevant"], x["title"].lower()))
    csv_write(out_dir / "oga_lpc_collection_discovery.csv", rows, ["title", "source_page", "havenwild_domains", "relevant", "already_tracked"])
    return {"collection": OGA_LPC_COLLECTION_URL, "totalLinks": len(rows), "relevantLinks": sum(bool(x["relevant"]) for x in rows), "alreadyTracked": sum(bool(x["already_tracked"]) for x in rows)}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_json_or_gzip(path: Path) -> Any:
    if path.suffix.lower() == ".gz":
        with gzip.open(path, "rt", encoding="utf-8-sig") as stream:
            return json.load(stream)
    return load_json(path)


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def csv_write(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def classify_schema_target(path: str, schema: str) -> tuple[str, str]:
    text = f"{path} {schema}".lower()
    historical = bool(PASSISH.search(text)) or any(k in text for k in ("closeout", "acceptance", "authority_boundary", "hotfix", "certification"))
    if historical:
        return "historical_evidence", "ABSORB_ASSERTIONS_THEN_ARCHIVE"
    if any(k in text for k in ("license", "credit", "provenance", "source_registry", "source_record", "source_lock")):
        return "asset_source_record", "MERGE"
    if any(k in text for k in ("cliff", "ramp", "ladder", "waterfall", "structural", "elevation", "cave_mouth")):
        return "structural_recipe", "MERGE"
    if any(k in text for k in ("terrain", "autotile", "transition", "shore", "water", "hydrology", "material")):
        return "terrain_recipe", "MERGE"
    if any(k in text for k in ("character", "clothing", "armor", "weapon", "tool", "npc", "animal", "animation")):
        return "typed_asset_category_metadata", "MERGE"
    if any(k in text for k in ("building", "wall", "floor", "door", "furniture", "structure", "interior", "scene", "dungeon")):
        return "typed_asset_category_metadata", "MERGE"
    if any(k in text for k in ("asset", "sprite", "atlas", "object", "crop", "tree", "foliage", "item", "recipe", "audio", "music", "ui")):
        return "asset_pack_or_category_metadata", "MERGE"
    if any(k in text for k in ("validator", "validation", "quality", "build")):
        return "validation_capability", "MERGE"
    return "domain_content", "KEEP_REVIEW"


def validator_capability(entry: dict[str, Any]) -> str:
    text = " ".join(str(entry.get(k, "")) for k in ("id", "name", "domain", "phase", "description")).lower()
    if any(k in text for k in ("acceptance", "visual", "performance", "certif")):
        return "acceptance.contract"
    if any(k in text for k in ("editor", "authoring", "pixel", "studio", "workbench")):
        return "editor.parity.contract"
    if any(k in text for k in ("worldgen", "world generation", "chunk", "persistence", "archipelago", "estate", "biome", "ecology")):
        return "world.generation.contract"
    if any(k in text for k in ("terrain", "cliff", "water", "shore", "ramp", "ladder", "cave", "hydrology", "autotile")):
        return "terrain.structural.contract"
    if any(k in text for k in ("runtime", "gameplay", "binding", "character", "equipment", "inventory", "tool", "audio")):
        return "runtime.bindings.contract"
    if any(k in text for k in ("asset", "source", "license", "credit", "lpc", "elizawy", "oga")):
        return "assets.sources.contract" if any(k in text for k in ("source", "license", "credit", "elizawy", "oga")) else "assets.recipes.contract"
    if any(k in text for k in ("architecture", "layout", "repository", "content", "framework", "validation")):
        return "repository.contract"
    return "assets.recipes.contract"


def terrain_target(path: str, schema: str) -> tuple[str, str]:
    text = f"{path} {schema}".lower()
    if bool(PASSISH.search(text)) or any(k in text for k in ("acceptance", "closeout", "certification", "authority_boundary", "hotfix")):
        return "acceptance_evidence", "ARCHIVE_AFTER_ASSERTION_ABSORPTION"
    if any(k in text for k in ("provenance", "source", "license", "reference_integrity")):
        return "source_provenance", "MERGE_TO_ASSET_SOURCE_RECORD"
    if any(k in text for k in ("cliff", "ramp", "ladder", "vine", "cave", "elevation", "structural")):
        return "structural_recipe_catalog", "MERGE"
    if any(k in text for k in ("water", "shore", "hydrology", "waterfall")):
        return "hydrology_recipe", "MERGE"
    if any(k in text for k in ("transition", "tuple", "junction", "autotile", "pattern", "topology")):
        return "terrain_transition_recipe", "MERGE"
    if any(k in text for k in ("material", "terrain_set", "terrain_standard", "palette", "priority", "gameplay", "compatibility")):
        return "terrain_material_definition", "MERGE"
    return "terrain_support_data", "REVIEW"


def code_target(path: str) -> tuple[str, str]:
    p = path.lower()
    name = Path(path).name.lower()
    if name == "elevation_cliff_v2.rs":
        return "structural_edge_resolver", "KEEP_AUTHORITY"
    if name in {"transition_resolver.rs", "terrain_tuple_resolver.rs"}:
        return "terrain_resolver", "KEEP_AND_CONVERGE_API"
    if name == "runtime_structural_cliff_draw.rs":
        return "terrain_render_plan_renderer", "REWRITE_THIN"
    if "elizawy_cliff_provider" in name or "lpc_cliff_ramp_provider" in name:
        return "structural_recipe_catalog", "MERGE_PROVIDER"
    if name in {"runtime_terrain_plan.rs", "terrain_render.rs"}:
        return "terrain_render_plan", "KEEP_REMOVE_REINTERPRETATION"
    if name == "structural_landform_ramps.rs":
        return "structural_connector_resolver", "KEEP_ROUTE_SELECTION_REMOVE_VISUAL_COUPLING"
    if any(k in p for k in ("structural_cliff", "waterfall", "terrain_cliff_bridge")):
        return "structural_edge_or_connector_adapter", "THIN_OR_MERGE"
    if "shoreline_resolver" in p or "hydrology" in p:
        return "terrain_resolver_hydrology", "CONVERGE"
    if "autotile" in p or "transition" in p or "terrain" in p:
        return "terrain_resolver_or_adapter", "CONVERGE_OR_THIN"
    return "review", "REVIEW"


def scan_json_schemas(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for base in (root / "content", root / "manifests"):
        if not base.exists():
            continue
        for path in base.rglob("*.json"):
            try:
                payload = load_json(path)
            except Exception as exc:
                rows.append({"path": rel(root, path), "schema": "[unreadable]", "bytes": path.stat().st_size, "target": "readability", "action": "FIX", "note": str(exc)})
                continue
            schema = payload.get("schema") if isinstance(payload, dict) else None
            if not schema:
                schema = payload.get("$id") if isinstance(payload, dict) else None
            schema = str(schema or "[none]")
            target, action = classify_schema_target(rel(root, path), schema)
            rows.append({"path": rel(root, path), "schema": schema, "bytes": path.stat().st_size, "target": target, "action": action, "note": ""})
    return rows


def scan_asset_packs(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pack_root = root / "content/asset_packs"
    if not pack_root.exists():
        return rows
    for path in sorted(pack_root.rglob("pack.json")):
        try:
            data = load_json(path)
        except Exception as exc:
            rows.append({"path": rel(root, path), "id": "[unreadable]", "production_enabled": False, "source_count": 0, "asset_count": 0, "categories": "", "missing_sources": 0, "missing_source_paths": "", "note": str(exc)})
            continue
        missing: list[str] = []
        for source in data.get("sources", []):
            raw = str(source.get("path", ""))
            if raw.startswith("provider://"):
                continue
            if raw and not (root / raw).exists():
                missing.append(raw)
        cats = Counter(str(a.get("category", "other")) for a in data.get("assets", []))
        rows.append({
            "path": rel(root, path), "id": data.get("id", ""), "production_enabled": bool(data.get("production_enabled", False)),
            "source_count": len(data.get("sources", [])), "asset_count": len(data.get("assets", [])),
            "categories": ";".join(f"{k}:{v}" for k, v in sorted(cats.items())), "missing_sources": len(missing),
            "missing_source_paths": " | ".join(missing), "note": "provider URI migration recommended" if missing else "",
        })
    return rows


def scan_validators(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    registry = root / "content/build/validator_registry_v3.json"
    if not registry.exists():
        return [], {"registry": "missing"}
    data = load_json(registry)
    entries = data.get("validators", [])
    ids = {str(v.get("id")) for v in entries}
    rows = []
    dangling = []
    for v in entries:
        deps = [str(x) for x in v.get("depends_on", [])]
        bad = [x for x in deps if x not in ids]
        dangling.extend((str(v.get("id")), x) for x in bad)
        historical = bool(PASSISH.search(" ".join([str(v.get("id", "")), str(v.get("name", "")), str(v.get("command", ""))])))
        capability = validator_capability(v)
        if v.get("runner") == "native" and not historical:
            action = "KEEP_OR_MERGE_NATIVE"
        else:
            action = "ABSORB_ASSERTIONS_THEN_ARCHIVE" if historical else "MERGE_INTO_CAPABILITY"
        rows.append({
            "id": v.get("id", ""), "name": v.get("name", ""), "domain": v.get("domain", ""), "phase": v.get("phase", ""),
            "runner": v.get("runner", ""), "profiles": ";".join(v.get("profiles", [])), "historical_signature": historical,
            "target_capability": capability, "action": action, "dangling_dependencies": ";".join(bad),
        })
    profile_counts = {p: sum(p in v.get("profiles", []) for v in entries) for p in ("build", "quick", "source", "framework", "full")}
    summary = {"schema": data.get("schema"), "version": data.get("version"), "validator_count": len(entries), "runner_counts": dict(Counter(str(v.get("runner")) for v in entries)), "profile_counts": profile_counts, "dangling_dependencies": dangling}
    return rows, summary


def scan_terrain_authorities(root: Path, schema_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    terrain_words = ("terrain", "cliff", "ramp", "ladder", "water", "shore", "hydrology", "autotile", "elevation", "cave")
    for item in schema_rows:
        text = f"{item['path']} {item['schema']}".lower()
        if not any(word in text for word in terrain_words):
            continue
        target, action = terrain_target(item["path"], item["schema"])
        rows.append({**item, "target_authority": target, "terrain_action": action})
    return rows


def scan_terrain_code(root: Path) -> list[dict[str, Any]]:
    rows = []
    roots = [root / "crates", root / "apps"]
    words = ("terrain", "cliff", "ramp", "water", "shore", "hydrology", "autotile", "elevation")
    for base in roots:
        if not base.exists(): continue
        for path in base.rglob("*.rs"):
            r = rel(root, path)
            if not any(w in r.lower() for w in words):
                continue
            try: text = path.read_text(encoding="utf-8")
            except Exception: continue
            target, action = code_target(r)
            rows.append({
                "path": r, "lines": text.count("\n") + 1,
                "TileKind_Cliff_refs": text.count("TileKind::Cliff"), "MountainPath_refs": text.count("MountainPath"),
                "StructuralCellV2_refs": text.count("StructuralCellV2"), "target_component": target, "action": action,
            })
    return sorted(rows, key=lambda x: x["path"])


def scan_media(root: Path) -> dict[str, Any]:
    counts = Counter(); total = 0; total_bytes = 0
    for base_name in ("assets", "content"):
        base = root / base_name
        if not base.exists(): continue
        for path in base.rglob("*"):
            if not path.is_file(): continue
            ext = path.suffix.lower()
            if ext not in IMAGE_EXTENSIONS | AUDIO_EXTENSIONS: continue
            total += 1; total_bytes += path.stat().st_size
            r = rel(root, path).lower()
            if "/generated/" in f"/{r}" or "/cache/" in f"/{r}" or "workspace/generated" in r:
                counts["generated_or_cache"] += 1
            elif r.startswith("assets/source/"):
                counts["authored_or_external_source"] += 1
            else:
                counts["packaged_content_or_other"] += 1
            counts["images" if ext in IMAGE_EXTENSIONS else "audio"] += 1
    return {"total_media": total, "total_bytes": total_bytes, **dict(counts)}


def scan_external_catalogs(root: Path) -> list[dict[str, Any]]:
    candidates = []
    for pattern in (
        "content/assets/**/*catalog*.json", "content/assets/**/*catalog*.json.gz",
        "content/characters/**/*catalog*.json", "content/characters/**/*catalog*.json.gz",
    ):
        candidates.extend(root.glob(pattern))
    rows = []
    seen = set()
    for path in sorted(candidates):
        if path in seen: continue
        seen.add(path)
        try: data = load_json_or_gzip(path)
        except Exception: continue
        count = None
        if isinstance(data, list): count = len(data)
        elif isinstance(data, dict):
            for key in ("records", "entries", "assets", "components", "items", "sources"):
                if isinstance(data.get(key), list): count = len(data[key]); break
            if count is None:
                summary = data.get("summary")
                if isinstance(summary, dict):
                    for key in ("total", "recordCount", "records", "entries"):
                        if isinstance(summary.get(key), int): count = summary[key]; break
        if count is not None and count >= 10:
            rows.append({"path": rel(root, path), "records": count, "schema": data.get("schema", "") if isinstance(data, dict) else "[list]"})
    return sorted(rows, key=lambda x: (-x["records"], x["path"]))


def build_summary(root: Path, out_dir: Path) -> dict[str, Any]:
    schemas = scan_json_schemas(root)
    packs = scan_asset_packs(root)
    validators, validator_summary = scan_validators(root)
    terrain = scan_terrain_authorities(root, schemas)
    terrain_code = scan_terrain_code(root)
    media = scan_media(root)
    external = scan_external_catalogs(root)

    csv_write(out_dir / "content_schema_migration.csv", schemas, ["path", "schema", "bytes", "target", "action", "note"])
    csv_write(out_dir / "asset_pack_utilization.csv", packs, ["path", "id", "production_enabled", "source_count", "asset_count", "categories", "missing_sources", "missing_source_paths", "note"])
    csv_write(out_dir / "validator_migration.csv", validators, ["id", "name", "domain", "phase", "runner", "profiles", "historical_signature", "target_capability", "action", "dangling_dependencies"])
    csv_write(out_dir / "terrain_authority_migration.csv", terrain, ["path", "schema", "bytes", "target_authority", "terrain_action", "action", "note"])
    csv_write(out_dir / "terrain_code_migration.csv", terrain_code, ["path", "lines", "TileKind_Cliff_refs", "MountainPath_refs", "StructuralCellV2_refs", "target_component", "action"])
    csv_write(out_dir / "external_catalogs.csv", external, ["path", "records", "schema"])

    schema_ids = Counter(r["schema"] for r in schemas)
    target_counts = Counter(r["target"] for r in schemas)
    terrain_targets = Counter(r["target_authority"] for r in terrain)
    validator_targets = Counter(r["target_capability"] for r in validators)
    total_assets = sum(int(r["asset_count"]) for r in packs)
    production_assets = sum(int(r["asset_count"]) for r in packs if r["production_enabled"])
    summary = {
        "schema": "havenwild.asset_spine_normalization_audit.v1",
        "generatedUtc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "root": str(root),
        "jsonFiles": len(schemas),
        "distinctSchemaIds": len(schema_ids),
        "schemaTargetCounts": dict(target_counts),
        "assetPacks": len(packs),
        "assetDefinitions": total_assets,
        "productionAssetDefinitions": production_assets,
        "missingPackSourcePaths": sum(int(r["missing_sources"]) for r in packs),
        "validator": validator_summary,
        "validatorTargetCounts": dict(validator_targets),
        "terrainAuthorityFiles": len(terrain),
        "terrainTargetCounts": dict(terrain_targets),
        "terrainCodeFiles": len(terrain_code),
        "semanticLeakage": {
            "TileKind::Cliff": sum(int(r["TileKind_Cliff_refs"]) for r in terrain_code),
            "MountainPath": sum(int(r["MountainPath_refs"]) for r in terrain_code),
            "StructuralCellV2": sum(int(r["StructuralCellV2_refs"]) for r in terrain_code),
        },
        "media": media,
        "largestExternalCatalogs": external[:25],
        "targetValidatorCapabilities": list(CAPABILITIES),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def write_markdown(summary: dict[str, Any], out_dir: Path) -> None:
    val = summary.get("validator", {})
    lines = [
        "# Havenwild Asset Spine Normalization Audit",
        "",
        f"Generated: `{summary['generatedUtc']}`",
        "",
        "## Current-state compression target",
        "",
        "`source/provider -> AssetPack + typed CategoryMetadata/recipes -> SemanticAssetResolver -> shared render/runtime plan -> editor + game`",
        "",
        "Validators verify that spine; they are not a second source of truth.",
        "",
        "## Census",
        "",
        f"- Parsed content/manifests JSON files: **{summary['jsonFiles']}**",
        f"- Distinct schema IDs: **{summary['distinctSchemaIds']}**",
        f"- Asset packs: **{summary['assetPacks']}**",
        f"- Canonical asset definitions: **{summary['assetDefinitions']}**",
        f"- Production-enabled asset definitions: **{summary['productionAssetDefinitions']}**",
        f"- Missing physical pack source paths: **{summary['missingPackSourcePaths']}**",
        f"- Terrain/cliff/water authority files: **{summary['terrainAuthorityFiles']}**",
        f"- Terrain-related Rust files: **{summary['terrainCodeFiles']}**",
        f"- Registered validators: **{val.get('validator_count', 0)}**",
        f"- Validator runners: `{val.get('runner_counts', {})}`",
        f"- Validator profiles: `{val.get('profile_counts', {})}`",
        "",
        "## Structural semantic leakage",
        "",
    ]
    for k, v in summary["semanticLeakage"].items(): lines.append(f"- `{k}` references in terrain-related code: **{v}**")
    lines += ["", "## Validator target", ""]
    for cap in summary["targetValidatorCapabilities"]: lines.append(f"- `{cap}`")
    dangling = val.get("dangling_dependencies", [])
    if dangling:
        lines += ["", "## Hard validator defects", ""]
        for owner, dep in dangling: lines.append(f"- `{owner}` depends on missing `{dep}`")
    lines += [
        "", "## Generated migration tables", "",
        "- `content_schema_migration.csv`: maps current schemas toward the small canonical spine.",
        "- `asset_pack_utilization.csv`: canonical pack exposure and unresolved physical source paths.",
        "- `validator_migration.csv`: every validator mapped to one of eight current capabilities.",
        "- `terrain_authority_migration.csv`: terrain/cliff/water JSON authorities mapped to material/transition/structural/hydrology/source/evidence targets.",
        "- `terrain_code_migration.csv`: terrain Rust modules mapped to resolver/render-plan/adapter targets.",
        "- `external_catalogs.csv`: large catalogs whose records need promotion/readiness coverage.",
        "",
        "## Locked rule",
        "",
        "Generated atlases and reports are caches/evidence. Source art plus semantic/structural data are authority. One recipe/resolver spine feeds both runtime and editor. The live validator registry contains capability validators only; pass-numbered validators are archived after their unique assertions are absorbed.",
    ]
    (out_dir / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Havenwild asset-spine normalization audit")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--refresh-oga", action="store_true", help="Refresh the OpenGameArt master LPC discovery feed into the audit output; does not download assets.")
    args = parser.parse_args()
    root = args.root.resolve()
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = (args.output.resolve() if args.output else root / "artifacts/audits/asset-spine" / stamp)
    out.mkdir(parents=True, exist_ok=True)
    summary = build_summary(root, out)
    if args.refresh_oga:
        try:
            summary["ogaLpcDiscovery"] = discover_oga_lpc(root, out)
            (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        except Exception as exc:
            summary["ogaLpcDiscoveryError"] = str(exc)
            (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_markdown(summary, out)
    latest = root / "artifacts/audits/asset-spine/LATEST.txt"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(str(out) + "\n", encoding="utf-8")
    print(f"Asset-spine audit complete: {out}")
    print(f"JSON files={summary['jsonFiles']} distinct schemas={summary['distinctSchemaIds']}")
    print(f"asset definitions={summary['assetDefinitions']} production={summary['productionAssetDefinitions']}")
    print(f"validators={summary['validator'].get('validator_count', 0)} terrain authorities={summary['terrainAuthorityFiles']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
