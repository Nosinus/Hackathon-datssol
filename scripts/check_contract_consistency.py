from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    Path("README.md"),
    Path("docs/contract/current_truth_table.md"),
    Path("docs/contract/current_truth_table.yaml"),
    Path("docs/contract/assumptions.md"),
    Path("docs/contract/open_questions.md"),
    Path("docs/contract/source_priority.md"),
    Path("docs/contract/implemented_vs_unknown.md"),
    Path("docs/operations/datsol_release_hour_runbook.md"),
    Path("docs/input/datsblack_openapi.json"),
]


def _assert_paths_exist() -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_PATHS:
        if not (ROOT / rel).exists():
            errors.append(f"missing required file: {rel}")
    return errors


def _assert_docs_input_is_canonical() -> list[str]:
    errors: list[str] = []
    docs_input = ROOT / "Docs" / "Input"
    for path in docs_input.glob("*.md"):
        if path.name == "README.md":
            continue
        errors.append(f"legacy markdown found in Docs/Input (move to docs/input): {path.name}")
    return errors


def _assert_manifest_sources_exist() -> list[str]:
    errors: list[str] = []
    manifest_path = ROOT / "docs/contract/current_truth_table.yaml"
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return ["current_truth_table.yaml must be a mapping"]

    source_priority = data.get("source_priority", [])
    if not isinstance(source_priority, list):
        return ["current_truth_table.yaml: source_priority must be a list"]

    for source in source_priority:
        if not isinstance(source, dict):
            errors.append("source_priority items must be mappings")
            continue
        path = source.get("path")
        if isinstance(path, str) and path.endswith("/"):
            if not (ROOT / path).is_dir():
                errors.append(f"missing source directory from manifest: {path}")
        elif isinstance(path, str):
            if not (ROOT / path).exists():
                errors.append(f"missing source file from manifest: {path}")
        else:
            errors.append("source_priority item missing string path")

    return errors


def main() -> int:
    errors: list[str] = []
    errors.extend(_assert_paths_exist())
    errors.extend(_assert_docs_input_is_canonical())
    errors.extend(_assert_manifest_sources_exist())

    if errors:
        print("Contract consistency check FAILED")
        for err in errors:
            print(f" - {err}")
        return 1

    print("Contract consistency check OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
