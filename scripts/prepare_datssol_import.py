from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _expected_names(tag: str) -> dict[str, str]:
    return {
        "event_notes": f"{tag}_event_notes.md",
        "openapi": f"{tag}_openapi.json",
        "examples": f"{tag}_examples.json",
        "extra_notes": f"{tag}_extra_notes.md",
        "truth_table": "docs/contract/current_truth_table.md",
    }


def _resolve_required_path(path_hint: str, *, target_dir: Path) -> Path:
    candidate = Path(path_hint)
    if candidate.is_absolute():
        return candidate
    if candidate.parts and candidate.parts[0] in {"docs", "src", "tests", "scripts"}:
        return REPO_ROOT / candidate
    return target_dir / candidate


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare DatsSol official import checklist")
    parser.add_argument("--tag", type=str, default=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"))
    parser.add_argument("--target-dir", type=Path, default=Path("docs/input/datssol_imports"))
    args = parser.parse_args()

    names = _expected_names(args.tag)
    payload = {
        "tag": args.tag,
        "target_dir": str(args.target_dir),
        "required_files": names,
        "found_files": {},
        "checklist": [
            "1) Save official docs snapshot in target dir",
            "2) Save OpenAPI JSON using naming convention",
            "3) Save request/response examples snapshot",
            "4) Save screenshots/notes into extra_notes artifact",
            "5) Update docs/contract/current_truth_table.md and .yaml",
            "6) Add fixtures under tests/fixtures/datssol",
            "7) Run smoke: pytest + ruff + mypy + fixture run",
        ],
    }
    args.target_dir.mkdir(parents=True, exist_ok=True)
    for key, rel in names.items():
        path = _resolve_required_path(rel, target_dir=args.target_dir)
        payload["found_files"][key] = path.exists()
    manifest = args.target_dir / f"{args.tag}_import_checklist.json"
    manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
