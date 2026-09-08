from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os, platform

@dataclass(frozen=True)
class ValidationContext:
    root: Path
    platform: str
    python_executable: str

    @classmethod
    def discover(cls, start: Path | None = None) -> "ValidationContext":
        here = (start or Path(__file__)).resolve()
        root = here if here.is_dir() else here.parent
        while root.parent != root and not (root / "Cargo.toml").exists():
            root = root.parent
        return cls(root=root, platform=platform.system().lower(), python_executable=os.environ.get("PYTHON", "python"))

    def path(self, relative: str) -> Path:
        return self.root / relative

    @property
    def reports(self) -> Path:
        return self.root / "logs/validation"
