from __future__ import annotations

import json
from pathlib import Path

from datsteam_core.evaluator.fixture_runner import run_offline_fixture
from datsteam_core.types.core import CanonicalState
from games.datsblack.canonical.state import to_canonical
from games.datsblack.models.raw import ScanResponse
from games.datsblack.strategy.baseline import SafeBaselineStrategy
from games.datsblack.strategy.legal import DatsBlackActionValidator


def _load_states(fixture_path: Path) -> list[CanonicalState]:
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        scans = [payload]
    elif isinstance(payload, list):
        scans = payload
    else:
        raise ValueError("Fixture must be JSON object or array")

    return [to_canonical(ScanResponse.model_validate(raw)).state for raw in scans]


def main() -> None:
    fixture_path = Path("tests/fixtures/datsblack_scan_multi_tick.json")
    states = _load_states(fixture_path)
    result = run_offline_fixture(
        SafeBaselineStrategy(),
        states,
        validator=DatsBlackActionValidator(),
    )
    print(result)


if __name__ == "__main__":
    main()
