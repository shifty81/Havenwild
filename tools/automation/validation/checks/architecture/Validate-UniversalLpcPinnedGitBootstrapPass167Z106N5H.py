from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
ENSURE = ROOT / "tools/automation/characters/Ensure-UniversalLpcGenerator.py"
LOCK = ROOT / "content/assets/intake/universal_lpc_generator_source_lock_v0_1.json"


def fail(message: str) -> None:
    print(f"FAILED Pass167Z106N5H Universal LPC pinned-Git bootstrap: {message}")
    raise SystemExit(1)


for path in (ENSURE, LOCK):
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")

source = ENSURE.read_text(encoding="utf-8")
lock = json.loads(LOCK.read_text(encoding="utf-8"))
commit = lock.get("commit")
repository = lock.get("repository")

if not commit or len(commit) != 40:
    fail("Universal LPC lock must retain an exact 40-character commit SHA")
if not repository or "Universal-LPC-Spritesheet-Character-Generator" not in repository:
    fail("Universal LPC lock repository is missing or unexpected")

required_fragments = [
    "def fetch_pinned_repository(lock: dict, destination: Path) -> Path:",
    '"fetch",',
    '"--depth",',
    '"1",',
    '"core.longpaths",',
    '"checkout", "--detach", "FETCH_HEAD"',
    'head.lower() != commit.lower()',
    'validate_source(staging, lock)',
    'write_state(source, lock, "pinned_git_fetch", mount_mode)',
    'HAVENWILD_OFFLINE',
]
for fragment in required_fragments:
    if fragment not in source:
        fail(f"bootstrap contract fragment missing: {fragment}")

archive_pos = source.find("archive = discover_archive(lock)")
fetch_pos = source.find("source = fetch_pinned_repository(lock, destination)")
if archive_pos < 0 or fetch_pos < 0 or fetch_pos <= archive_pos:
    fail("pinned Git acquisition must remain the fallback after local archive discovery")

if 'fetch", "--depth", "1", "origin", lock.get("defaultBranch"' in source:
    fail("bootstrap must fetch the locked commit, not the mutable default branch")

print(
    "Pass167Z106N5H Universal LPC pinned-Git bootstrap validated "
    f"({repository}@{commit})"
)
