from __future__ import annotations

import json
from pathlib import Path

from datsteam_core.evaluator.fixture_runner import run_offline_fixture
from games.datsblack.canonical.state import to_canonical
from games.datsblack.models.raw import ScanResponse
from games.datsblack.strategy.baseline import SafeBaselineStrategy


def main() -> None:
    fixture_path = Path("tests/fixtures/datsblack_scan_sample.json")
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    raw = ScanResponse.model_validate(payload)
    canonical = to_canonical(raw).state
    result = run_offline_fixture(SafeBaselineStrategy(), [canonical])
    print(result)


if __name__ == "__main__":
    main()
