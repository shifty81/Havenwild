from pathlib import Path
import ast
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
REGISTRY = ROOT / "content/build/generated_output_registry_v2.json"
HELPER = ROOT / "tools/automation/common/atomic_io.py"
ATOMIC_FUNCTIONS = {
    "atomic_save_image",
    "atomic_write_bytes",
    "atomic_write_json",
    "atomic_write_text",
}


def imported_atomic_functions(tree: ast.AST) -> set[str]:
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "generation.atomic_io":
            imported.update(alias.asname or alias.name for alias in node.names)
    return imported


def called_atomic_functions(tree: ast.AST) -> set[str]:
    called: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in ATOMIC_FUNCTIONS:
                called.add(node.func.id)
    return called


def validate_generator_imports() -> list[str]:
    errors: list[str] = []
    for script in sorted((ROOT / "tools/automation").glob("*.py")):
        source = script.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(script))
        called = called_atomic_functions(tree)
        if not called:
            continue
        imported = imported_atomic_functions(tree)
        locally_defined = {
            node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        missing = sorted(called - imported - locally_defined)
        if missing:
            errors.append(f"{script.name} calls atomic helpers without importing them: {missing}")
    return errors


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    helper = HELPER.read_text(encoding="utf-8")
    required = ["os.replace", "atomic_path", "atomic_write_json", "atomic_save_image"]
    missing = [token for token in required if token not in helper]
    if missing:
        print(f"Atomic generation helper missing {missing}", file=sys.stderr)
        return 1

    import_errors = validate_generator_imports()
    if import_errors:
        for error in import_errors:
            print(error, file=sys.stderr)
        return 1

    for entry in registry["outputs"]:
        if not entry.get("atomic_write_required"):
            print(f"Generated output lacks atomic-write requirement: {entry['output']}", file=sys.stderr)
            return 1
        if not entry.get("provenance"):
            print(f"Generated output lacks provenance sidecar: {entry['output']}", file=sys.stderr)
            return 1
    build_sh = (ROOT / "tools/build/Build.sh").read_text(encoding="utf-8")
    build_ps1 = (ROOT / "tools/build/Build.ps1").read_text(encoding="utf-8")
    stamp = "Stamp-GeneratedOutputProvenanceV146D.py"
    if stamp not in build_sh or stamp not in build_ps1:
        print("Build entrypoints do not stamp generated provenance", file=sys.stderr)
        return 1
    print("Pass 146D atomic generation contract validated, including atomic helper imports")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
