from __future__ import annotations
import datetime as dt, json, shutil
from pathlib import Path
from typing import Any

def write_combined_report(report: dict[str, Any], report_dir: Path) -> tuple[Path,Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp=dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path=report_dir/f"validation-{report['profile']}-{stamp}.json"
    md_path=report_dir/f"validation-{report['profile']}-{stamp}.md"
    json_path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    lines=["# Havenwild Unified Validation Report","",f"- Profile: `{report['profile']}`",f"- Status: **{report['status'].upper()}**",f"- Passed: `{report['summary']['passed']}`",f"- Failed: `{report['summary']['failed']}`",f"- Skipped: `{report['summary']['skipped']}`","","## Results","","| Order | Validator | Domain | Status | Seconds |","|---:|---|---|---|---:|"]
    for item in report["tasks"]:
        lines.append(f"| {item.get('order',0)} | `{item['id']}` | {item['domain']} | {item['status']} | {item['durationSeconds']:.3f} |")
    failures=[item for item in report["tasks"] if item["status"]=="failed"]
    if failures:
        lines += ["","## Failures",""]
        for item in failures:
            issues=item.get("issues") or []
            detail="; ".join(f"{issue['code']}: {issue['message']}" for issue in issues) or f"exit code {item.get('exitCode')}"
            lines.append(f"- `{item['id']}` — {detail}")
    md_path.write_text("\n".join(lines)+"\n",encoding="utf-8")
    shutil.copy2(json_path,report_dir/"latest.json"); shutil.copy2(md_path,report_dir/"latest.md")
    return json_path,md_path
