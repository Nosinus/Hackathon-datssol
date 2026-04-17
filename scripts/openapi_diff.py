from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"OpenAPI document at {path} must be JSON object")
    return payload


def _extract_operations(openapi: dict[str, object]) -> set[str]:
    out: set[str] = set()
    paths = openapi.get("paths", {})
    if not isinstance(paths, dict):
        return out
    for route, ops in paths.items():
        if not isinstance(route, str) or not isinstance(ops, dict):
            continue
        for method, spec in ops.items():
            if isinstance(method, str) and isinstance(spec, dict):
                out.add(f"{method.upper()} {route}")
    return out


def _extract_schemas(openapi: dict[str, object]) -> set[str]:
    components = openapi.get("components", {})
    if not isinstance(components, dict):
        return set()
    schemas = components.get("schemas", {})
    if not isinstance(schemas, dict):
        return set()
    return {name for name in schemas.keys() if isinstance(name, str)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Diff two OpenAPI JSON snapshots")
    parser.add_argument("--base", type=Path, required=True, help="base OpenAPI JSON file")
    parser.add_argument("--candidate", type=Path, required=True, help="candidate OpenAPI JSON file")
    args = parser.parse_args()

    base_doc = _load_json(args.base)
    cand_doc = _load_json(args.candidate)

    base_ops = _extract_operations(base_doc)
    cand_ops = _extract_operations(cand_doc)
    base_schemas = _extract_schemas(base_doc)
    cand_schemas = _extract_schemas(cand_doc)

    added_ops = sorted(cand_ops - base_ops)
    removed_ops = sorted(base_ops - cand_ops)
    added_schemas = sorted(cand_schemas - base_schemas)
    removed_schemas = sorted(base_schemas - cand_schemas)

    print(f"Base: {args.base}")
    print(f"Candidate: {args.candidate}")
    print()
    print("Operations:")
    print(f"  base={len(base_ops)} candidate={len(cand_ops)}")
    print(f"  added={len(added_ops)} removed={len(removed_ops)}")
    for item in added_ops:
        print(f"  + {item}")
    for item in removed_ops:
        print(f"  - {item}")

    print()
    print("Schemas:")
    print(f"  base={len(base_schemas)} candidate={len(cand_schemas)}")
    print(f"  added={len(added_schemas)} removed={len(removed_schemas)}")
    for item in added_schemas:
        print(f"  + {item}")
    for item in removed_schemas:
        print(f"  - {item}")

    changed = any([added_ops, removed_ops, added_schemas, removed_schemas])
    return 1 if changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
