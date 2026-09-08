from __future__ import annotations
import json
import time
from pathlib import Path
from validation.registry import load_registry
from validation.result import ValidationIssue, ValidationResult

REGISTRY = Path("content/build/validator_registry_v4.json")
PROFILES = Path("content/build/validation_profiles_v4.json")
EXPECTED_SOURCE = {
    "architecture.foundation.validate_development_layout",
    "architecture.foundation.validate_architecture",
    "content.foundation.validate_content",
    "content.integrity.current-contract",
    "architecture.validation.framework-contract",
    "runtime.publication.contract",
    "architecture.validation.evidence-contract",
    "architecture.validation.root-intake-contract",
    "architecture.validation.ci-contract",
    "architecture.validation.docs-contract",
}
EXPECTED_FRAMEWORK = {
    "architecture.foundation.validate_development_layout",
    "architecture.validation.framework-contract",
    "architecture.validation.registry-contract",
    "architecture.validation.runner-contract",
}
EXPECTED_BUILD = {
    "architecture.foundation.validate_development_layout",
    "content.foundation.validate_content",
}


def _result(entry, started, issues, evidence):
    return ValidationResult(entry["id"], entry["name"], "failed" if issues else "passed", entry["domain"], entry["phase"], time.time()-started, 1 if issues else 0, issues, evidence)


def _load(root: Path):
    return load_registry(root / REGISTRY), json.loads((root / PROFILES).read_text(encoding="utf-8"))


def validate(entry, root: Path):
    started=time.time(); issues=[]; evidence=[]
    try:
        reg, profiles = _load(root)
    except Exception as exc:
        return _result(entry, started, [ValidationIssue("HWV-MANIFEST-001", str(exc), path=str(REGISTRY))], [])
    vals=reg.get("validators", [])
    if reg.get("schema") != "havenwild.validator.registry.v4":
        issues.append(ValidationIssue("HWV-MANIFEST-001", "resolved registry v4 schema required"))
    counts={name:sum(name in v.get("profiles",[]) for v in vals) for name in ("build","quick","source","framework","full")}
    expected={"build":2,"quick":2,"source":10,"framework":4}
    for name,count in expected.items():
        if counts[name] != count:
            issues.append(ValidationIssue("HWV-QUALITY-001", f"{name} profile must contain exactly {count} validators", details=counts))
    assignments={name:{v["id"] for v in vals if name in v.get("profiles",[])} for name in ("build","source","framework")}
    if assignments["build"] != EXPECTED_BUILD: issues.append(ValidationIssue("HWV-QUALITY-001", "build profile authority drift", details={"actual":sorted(assignments["build"])}))
    if assignments["source"] != EXPECTED_SOURCE: issues.append(ValidationIssue("HWV-QUALITY-001", "source profile authority drift", details={"actual":sorted(assignments["source"])}))
    if assignments["framework"] != EXPECTED_FRAMEWORK: issues.append(ValidationIssue("HWV-QUALITY-001", "framework profile authority drift", details={"actual":sorted(assignments["framework"])}))
    if any(v.get("read_only", True) is not True for v in vals if set(v.get("profiles",[])) & {"build","quick","source","framework"}):
        issues.append(ValidationIssue("HWV-QUALITY-001", "live validators must be read-only"))
    overlay=json.loads((root/REGISTRY).read_text(encoding="utf-8"))
    if overlay.get("baseRegistry") != "content/build/validator_registry_v3.json": issues.append(ValidationIssue("HWV-MANIFEST-001", "v4 must preserve v3 as historical/full compatibility base"))
    if set(overlay.get("stripProfilesFromBase",[])) != {"build","quick","source","framework"}: issues.append(ValidationIssue("HWV-QUALITY-001", "v4 must quarantine base validators from live profiles"))
    policy=profiles.get("policy",{})
    if policy.get("sourceValidationValidatorCount") != 10 or policy.get("normalBuildValidatorCount") != 2 or policy.get("frameworkAuditValidatorCount") != 4:
        issues.append(ValidationIssue("HWV-MANIFEST-001", "profile policy counts disagree with v4 authority"))
    evidence=[f"build={counts['build']}",f"source={counts['source']}",f"framework={counts['framework']}",f"full={counts['full']}",f"total={len(vals)}"]
    return _result(entry, started, issues, evidence)


def validate_registry_quality(entry, root: Path):
    started=time.time(); issues=[]; evidence=[]
    try: reg,_=_load(root)
    except Exception as exc: return _result(entry, started, [ValidationIssue("HWV-MANIFEST-001",str(exc),path=str(REGISTRY))], [])
    vals=reg.get("validators",[]); ids=[v.get("id") for v in vals]
    if len(ids)!=len(set(ids)): issues.append(ValidationIssue("HWV-MANIFEST-001","duplicate validator IDs"))
    valid_runners={"native","process"}
    for v in vals:
        if v.get("runner") not in valid_runners: issues.append(ValidationIssue("HWV-MANIFEST-001",f"unsupported runner for {v.get('id')}"))
        if v.get("runner")=="native" and not v.get("module"): issues.append(ValidationIssue("HWV-MANIFEST-001",f"native validator missing module: {v.get('id')}"))
        if v.get("runner")=="process" and not v.get("command"): issues.append(ValidationIssue("HWV-MANIFEST-001",f"process validator missing command: {v.get('id')}"))
    evidence=[f"validatedIds={len(ids)}",f"native={sum(v.get('runner')=='native' for v in vals)}",f"process={sum(v.get('runner')=='process' for v in vals)}"]
    return _result(entry, started, issues, evidence)


def validate_runner_contract(entry, root: Path):
    started=time.time(); issues=[]; evidence=[]
    runner_path=root/"tools/automation/validation/validation_runner.py"
    text=runner_path.read_text(encoding="utf-8")
    required=("validator_registry_v4.json","validation_profiles_v4.json","resolve_profile","invoke_native","readonly_snapshot","havenwild.validation.report.v3")
    for token in required:
        if token not in text: issues.append(ValidationIssue("HWV-QUALITY-001",f"runner missing {token}",path=str(runner_path.relative_to(root))))
    old_authority='REGISTRY = ROOT / "content/build/validator_registry_v3.json"'
    if old_authority in text: issues.append(ValidationIssue("HWV-QUALITY-001","runner still declares v3 as current registry"))
    evidence=[f"runner={runner_path.relative_to(root)}",f"tokens={len(required)}"]
    return _result(entry, started, issues, evidence)
