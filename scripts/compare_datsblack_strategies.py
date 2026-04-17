from __future__ import annotations

import argparse
import json
from pathlib import Path

from datsteam_core.evaluator.fixture_runner import EvalResult, run_offline_fixture
from datsteam_core.types.core import CanonicalState
from games.datsblack.canonical.state import to_canonical
from games.datsblack.models.raw import ScanResponse
from games.datsblack.strategy.baseline import SafeBaselineStrategy
from games.datsblack.strategy.legal import DatsBlackActionValidator


def load_states(path: Path) -> list[CanonicalState]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        items = [payload]
    else:
        raise ValueError("Fixture must be object or list")

    states: list[CanonicalState] = []
    for item in items:
        states.append(to_canonical(ScanResponse.model_validate(item)).state)
    return states


def render_result(name: str, result: EvalResult) -> dict[str, object]:
    return {
        "strategy": name,
        "ticks": result.ticks,
        "actions": result.actions,
        "invalid_actions": result.invalid_actions,
        "empty_actions": result.empty_actions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare strategies on DatsBlack fixtures")
    parser.add_argument(
        "--fixture",
        type=Path,
        default=Path("tests/fixtures/datsblack_scan_multi_tick.json"),
        help="fixture path (single scan object or list of scan objects)",
    )
    args = parser.parse_args()

    states = load_states(args.fixture)
    validator = DatsBlackActionValidator()

    # Scaffold: duplicate strategy now; replace second one when new strategy appears.
    baseline = SafeBaselineStrategy()
    conservative = SafeBaselineStrategy()

    results = [
        render_result("safe_baseline", run_offline_fixture(baseline, states, validator=validator)),
        render_result(
            "safe_baseline_clone", run_offline_fixture(conservative, states, validator=validator)
        ),
    ]
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
