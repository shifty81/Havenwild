from __future__ import annotations

import time
from collections.abc import Callable

from validation.result import ValidationIssue, ValidationResult


def run_current_contract(entry: dict, checks: list[tuple[str, Callable[[], None]]]) -> ValidationResult:
    started = time.time()
    issues: list[ValidationIssue] = []
    evidence: list[str] = []
    for label, check in checks:
        try:
            check()
            evidence.append(label)
        except Exception as exc:  # validators must report rather than crash the runner
            issues.append(ValidationIssue("HWV-CONTRACT-001", f"{label}: {exc}"))
    return ValidationResult(
        validator_id=entry["id"],
        name=entry["name"],
        status="failed" if issues else "passed",
        domain=entry["domain"],
        phase=entry["phase"],
        duration_seconds=time.time() - started,
        exit_code=1 if issues else 0,
        issues=issues,
        evidence=evidence,
    )
