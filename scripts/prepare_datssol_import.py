from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


def _expected_names(tag: str) -> dict[str, str]:
    return {
        "rules": f"rules/{tag}_official_rules.md",
        "openapi": f"openapi/{tag}_openapi.json",
        "examples": f"examples/{tag}_examples.json",
        "notes": f"notes/{tag}_release_notes.md",
        "screenshots": f"screenshots/{tag}_doc_capture.png",
        "truth_table": "docs/contract/current_truth_table.md",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare DatsSol official import checklist")
    parser.add_argument("--tag", type=str, default=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"))
    parser.add_argument("--target-dir", type=Path, default=Path("docs/input/datssol_imports"))
    args = parser.parse_args()

    names = _expected_names(args.tag)
    payload = {
        "tag": args.tag,
        "target_dir": str(args.target_dir),
        "folders": ["rules", "openapi", "examples", "screenshots", "notes"],
        "required_files": names,
        "found_files": {},
        "checklist": [
            "1) Save official rules/docs snapshot in rules/",
            "2) Save OpenAPI/Swagger source in openapi/",
            "3) Save request/response examples in examples/",
            "4) Save screenshots/explanatory captures in screenshots/",
            "5) Update docs/contract/current_truth_table.md and .yaml",
            "6) Add fixtures under tests/fixtures/datssol",
            "7) Run smoke: pytest + ruff + mypy + fixture run",
        ],
    }
    args.target_dir.mkdir(parents=True, exist_ok=True)
    for folder in payload["folders"]:
        (args.target_dir / folder).mkdir(parents=True, exist_ok=True)
    for rel in payload["required_files"].values():
        path = args.target_dir / rel
        payload["found_files"][rel] = path.exists()
    manifest = args.target_dir / f"{args.tag}_import_checklist.json"
    manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
