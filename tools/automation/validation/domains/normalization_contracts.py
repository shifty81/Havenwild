from __future__ import annotations
import hashlib
import json
import re
import time
from pathlib import Path
from validation.result import ValidationIssue, ValidationResult

SHA256_RE=re.compile(r"^[0-9a-fA-F]{64}$")


def _result(entry, started, issues, evidence):
    return ValidationResult(entry["id"],entry["name"],"failed" if issues else "passed",entry["domain"],entry["phase"],time.time()-started,1 if issues else 0,issues,evidence)


def _json(root:Path, rel:str):
    return json.loads((root/rel).read_text(encoding="utf-8"))


def _sha(path:Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()


def validate_runtime_publication(entry, root:Path):
    started=time.time(); issues=[]; evidence=[]
    rel="content/runtime_media_manifest_v1.json"
    try: data=_json(root,rel)
    except Exception as exc: return _result(entry,started,[ValidationIssue("HWV-MANIFEST-001",str(exc),path=rel)],[])
    if data.get("schema")!="havenwild.runtime_media_manifest.v1": issues.append(ValidationIssue("HWV-MANIFEST-001","runtime media manifest schema mismatch",path=rel))
    ids=set(); paths=set(); required=0
    for asset in data.get("assets",[]):
        aid=str(asset.get("id", "")); path=str(asset.get("path", "")); expected=str(asset.get("sha256", ""))
        if not aid or aid in ids: issues.append(ValidationIssue("HWV-MANIFEST-001",f"invalid/duplicate runtime media id: {aid!r}",path=rel))
        if not path or path in paths or path.startswith(("/","\\")) or ".." in Path(path).parts: issues.append(ValidationIssue("HWV-MANIFEST-001",f"invalid/duplicate runtime media path: {path!r}",path=rel))
        ids.add(aid); paths.add(path)
        if asset.get("requiredForCleanCheckout") is True:
            required+=1; file=root/path
            if not file.is_file(): issues.append(ValidationIssue("HWV-PREREQ-001","required runtime media missing",path=path)); continue
            if not SHA256_RE.fullmatch(expected): issues.append(ValidationIssue("HWV-MANIFEST-001","runtime media SHA-256 malformed",path=path))
            elif _sha(file).lower()!=expected.lower(): issues.append(ValidationIssue("HWV-QUALITY-001","runtime media SHA-256 mismatch",path=path))
            provenance=str(asset.get("provenance", ""))
            if not provenance or not (root/provenance).is_file(): issues.append(ValidationIssue("HWV-PREREQ-001","runtime media provenance missing",path=provenance or path))
    if required < 3: issues.append(ValidationIssue("HWV-QUALITY-001","expected at least three clean-checkout runtime media assets",details={"required":required}))
    gate=root/"tools/control/HavenwildGateAuthority.py"
    if not gate.is_file(): issues.append(ValidationIssue("HWV-PREREQ-001","protected GREEN publication authority missing",path=str(gate.relative_to(root))))
    else:
        text=gate.read_text(encoding="utf-8",errors="replace")
        for token in ("runtime_media_manifest_v1.json","requiredForCleanCheckout"):
            if token not in text: issues.append(ValidationIssue("HWV-QUALITY-001",f"GREEN publication authority missing runtime-media token {token}",path=str(gate.relative_to(root))))
    evidence=[f"assets={len(data.get('assets',[]))}",f"required={required}"]
    return _result(entry,started,issues,evidence)


def validate_evidence_contract(entry, root:Path):
    started=time.time(); issues=[]; evidence=[]; rel="content/validation/evidence_receipt_contract_v1.json"
    try:data=_json(root,rel)
    except Exception as exc:return _result(entry,started,[ValidationIssue("HWV-MANIFEST-001",str(exc),path=rel)],[])
    if data.get("schema")!="havenwild.validation.evidence_receipt_contract.v1": issues.append(ValidationIssue("HWV-MANIFEST-001","evidence receipt contract schema mismatch",path=rel))
    policy=data.get("policy",{})
    if policy.get("generatedEvidenceIsSourceAuthority") is not False: issues.append(ValidationIssue("HWV-QUALITY-001","generated evidence must not be source authority",path=rel))
    roots=data.get("generatedRoots",[])
    if not roots or any(Path(str(p)).is_absolute() or ".." in Path(str(p)).parts for p in roots): issues.append(ValidationIssue("HWV-MANIFEST-001","generated evidence roots must be safe repository-relative paths",path=rel))
    receipts=data.get("receipts",[])
    if len({r.get('id') for r in receipts})!=len(receipts): issues.append(ValidationIssue("HWV-MANIFEST-001","duplicate evidence receipt ids",path=rel))
    evidence=[f"generatedRoots={len(roots)}",f"receipts={len(receipts)}"]
    return _result(entry,started,issues,evidence)


def validate_root_intake_contract(entry, root:Path):
    started=time.time(); issues=[]; evidence=[]; rel="content/architecture/root_patch_intake_contract_v1.json"
    try:data=_json(root,rel)
    except Exception as exc:return _result(entry,started,[ValidationIssue("HWV-MANIFEST-001",str(exc),path=rel)],[])
    if data.get("schema")!="havenwild.root_patch_intake_contract.v1": issues.append(ValidationIssue("HWV-MANIFEST-001","root patch intake contract schema mismatch",path=rel))
    authority=str(data.get("authority", "")); script=root/authority
    if not authority or not script.is_file(): issues.append(ValidationIssue("HWV-PREREQ-001","root patch intake authority missing",path=authority or rel))
    else:
        text=script.read_text(encoding="utf-8",errors="replace")
        required=("havenwild.root_patch.v1","PATCH_MANIFEST.json","Test-SafeRelativePath","Get-FileHash","ROLLBACK","artifacts\\updates\\applied","artifacts\\updates\\failed")
        for token in required:
            if token not in text: issues.append(ValidationIssue("HWV-QUALITY-001",f"root intake authority missing {token}",path=authority))
        if "Invoke-Expression" in text: issues.append(ValidationIssue("HWV-QUALITY-001","root patch intake must not execute patch-supplied code",path=authority))
    safety=data.get("safety",{})
    if safety.get("rollbackOnFailure") is not True or safety.get("executesPatchScripts") is not False: issues.append(ValidationIssue("HWV-QUALITY-001","root intake safety policy drift",path=rel))
    evidence=[f"authority={authority}",f"rollback={safety.get('rollbackOnFailure')}",f"executesPatchScripts={safety.get('executesPatchScripts')}"]
    return _result(entry,started,issues,evidence)


def validate_ci_contract(entry, root:Path):
    started=time.time(); issues=[]; evidence=[]; rel="content/validation/ci_validation_contract_v1.json"
    try:data=_json(root,rel)
    except Exception as exc:return _result(entry,started,[ValidationIssue("HWV-MANIFEST-001",str(exc),path=rel)],[])
    if data.get("schema")!="havenwild.ci_validation_contract.v1": issues.append(ValidationIssue("HWV-MANIFEST-001","CI validation contract schema mismatch",path=rel))
    entrypoint=str(data.get("entrypoint", ""))
    if not entrypoint or not (root/entrypoint).is_file(): issues.append(ValidationIssue("HWV-PREREQ-001","CI validation entrypoint missing",path=entrypoint or rel))
    commands=data.get("commands",{})
    for profile in ("build","source","framework","full"):
        cmd=commands.get(profile)
        if not isinstance(cmd,list) or entrypoint not in cmd:
            issues.append(ValidationIssue("HWV-MANIFEST-001",f"CI command missing normalized entrypoint for {profile}",path=rel))
    quality_test=commands.get("quality-test")
    if not isinstance(quality_test,list) or entrypoint not in quality_test or "--cargo-test" not in quality_test:
        issues.append(ValidationIssue("HWV-MANIFEST-001","quality-test must use current validation plus cargo tests",path=rel))
    root_entry=str(data.get("rootBuildEntrypoint", ""))
    root_script=root/root_entry if root_entry else None
    if not root_entry or root_script is None or not root_script.is_file():
        issues.append(ValidationIssue("HWV-PREREQ-001","root build entrypoint missing",path=root_entry or rel))
    else:
        text=root_script.read_text(encoding="utf-8",errors="replace")
        for token in ("check_current.py", "--cargo-test", ":current_test", ":current_validate", ":current_certify", ":current_framework", "framework-audit"):
            if token not in text:
                issues.append(ValidationIssue("HWV-QUALITY-001",f"root build entrypoint missing normalized route {token}",path=root_entry))
        # The authoritative front door may dispatch specialized commands to Build.sh,
        # but generic test/validate/certify/framework-audit must be intercepted before that fallback.
        bash_index=text.find(':bash_dispatch')
        for command in ("test","validate","certify","framework-audit"):
            intercept=text.find(f'if /I "%~1"=="{command}"')
            if intercept < 0 or bash_index < 0 or intercept > bash_index:
                issues.append(ValidationIssue("HWV-QUALITY-001",f"generic {command} interception must precede Bash fallback",path=root_entry))
    policy=data.get("policy",{})
    if policy.get("rootControlTestUsesCurrentAuthority") is not True:
        issues.append(ValidationIssue("HWV-QUALITY-001","root-control tests must use current validation authority",path=rel))
    if policy.get("genericTestMayRunHistoricalPassValidators") is not False:
        issues.append(ValidationIssue("HWV-QUALITY-001","generic tests must not run historical pass validators",path=rel))
    gate=data.get("qualityGate",{})
    if gate.get("buildFrontDoor") != root_entry or gate.get("historicalImplicit") is not False:
        issues.append(ValidationIssue("HWV-QUALITY-001","root quality-gate routing contract drift",path=rel))
    validation_route=gate.get("validationRoute",[])
    if entrypoint not in validation_route or "source" not in validation_route:
        issues.append(ValidationIssue("HWV-MANIFEST-001","root quality gate must include bounded source validation",path=rel))
    historical_route=gate.get("historicalCertificationRoute",[])
    if entrypoint not in historical_route or "full" not in historical_route:
        issues.append(ValidationIssue("HWV-MANIFEST-001","explicit historical certification route missing",path=rel))
    evidence=[f"entrypoint={entrypoint}",f"rootBuildEntrypoint={root_entry}",f"commands={len(commands)}", "historicalImplicit=false"]
    return _result(entry,started,issues,evidence)


def validate_docs_contract(entry, root:Path):
    started=time.time(); issues=[]; evidence=[]; rel="content/validation/validation_authority_v4.json"
    try:data=_json(root,rel)
    except Exception as exc:return _result(entry,started,[ValidationIssue("HWV-MANIFEST-001",str(exc),path=rel)],[])
    if data.get("schema")!="havenwild.validation.authority.v4": issues.append(ValidationIssue("HWV-MANIFEST-001","validation authority schema mismatch",path=rel))
    references=[data.get("registry"),data.get("profiles"),data.get("aliases"),data.get("runner"),data.get("historicalBaseRegistry")]
    references += list(data.get("contracts",{}).values())
    missing=[str(p) for p in references if p and not (root/str(p)).exists()]
    if missing: issues.append(ValidationIssue("HWV-PREREQ-001","validation authority references missing files",path=rel,details={"missing":missing}))
    quarantine=_json(root,"content/validation/legacy_quarantine_policy_v1.json")
    if quarantine.get("allowedImplicitProfiles") != ["full"]: issues.append(ValidationIssue("HWV-QUALITY-001","legacy validators must be explicit full-only",path="content/validation/legacy_quarantine_policy_v1.json"))
    readme=(root/"tools/automation/validation/README.md").read_text(encoding="utf-8")
    docs=(root/"docs/current/VALIDATION.md").read_text(encoding="utf-8")
    for token in ("validator_registry_v4.json","10 current-authority","historical"):
        if token not in readme and token not in docs: issues.append(ValidationIssue("HWV-QUALITY-001",f"validation documentation missing {token}"))
    evidence=[f"references={len(references)}",f"legacyRoot={quarantine.get('historicalValidatorRoot')}"]
    return _result(entry,started,issues,evidence)
