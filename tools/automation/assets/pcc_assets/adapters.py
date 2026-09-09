from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectAdapter:
    name: str
    default_cell_width: int = 32
    default_cell_height: int = 32
    alpha_threshold: int = 1
    min_seam_touch_pixels: int = 2
    min_assembly_cells: int = 2
    allow_automatic_runtime_certification: bool = False
    output_root: str = "artifacts/asset-intake"

    def resolve_output_root(self, repo_root: Path) -> Path:
        return repo_root / self.output_root


HAVENWILD = ProjectAdapter(
    name="havenwild",
    default_cell_width=32,
    default_cell_height=32,
    alpha_threshold=1,
    min_seam_touch_pixels=2,
    min_assembly_cells=2,
    allow_automatic_runtime_certification=False,
    output_root="artifacts/asset-intake",
)

GENERIC = ProjectAdapter(
    name="generic",
    default_cell_width=32,
    default_cell_height=32,
    alpha_threshold=1,
    min_seam_touch_pixels=2,
    min_assembly_cells=2,
    allow_automatic_runtime_certification=False,
    output_root="artifacts/asset-intake",
)


def get_adapter(name: str) -> ProjectAdapter:
    key = (name or "generic").strip().lower()
    if key == "havenwild":
        return HAVENWILD
    if key == "generic":
        return GENERIC
    raise ValueError(f"unknown project adapter: {name}")
