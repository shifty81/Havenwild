"""Universal Python asset intake, analysis, certification and prefab tooling.

This package is project-agnostic. Project-specific policy is supplied by adapters.
"""

__version__ = "0.1.0"

from .models import (
    CertificationState,
    GridSpec,
    SourceRecord,
    SheetAnalysis,
    AssemblyCandidate,
    PrefabRecipe,
)
