from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal

Status = Literal["ready", "passed", "failed", "skipped"]

@dataclass
class ValidationIssue:
    code: str
    message: str
    path: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationResult:
    validator_id: str
    name: str
    status: Status
    domain: str
    phase: str
    duration_seconds: float = 0.0
    exit_code: int | None = None
    issues: list[ValidationIssue] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    skipped_because: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.validator_id, "name": self.name, "status": self.status,
            "domain": self.domain, "phase": self.phase,
            "durationSeconds": round(self.duration_seconds, 3),
            "exitCode": self.exit_code,
            "issues": [issue.__dict__ for issue in self.issues],
            "evidence": self.evidence, "skippedBecause": self.skipped_because,
        }
