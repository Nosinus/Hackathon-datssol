from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.cli import _build_datssol_client

from datsteam_core.config.settings import FullSettings, load_from_env, load_from_yaml
from datsteam_core.types.core import ActionEnvelope, TickBudget
from games.datssol.api.client import DatsSolClient
from games.datssol.canonical.state import to_canonical
from games.datssol.models.raw import ArenaResponse, CommandRequest
from games.datssol.strategy.baseline import DatsSolBaselineStrategy
from games.datssol.validator import DatsSolSemanticValidator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DatsSol v1 loop")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--poll-only", action="store_true")
    parser.add_argument("--logs", action="store_true")
    parser.add_argument("--dry-run-submit", action="store_true")
    parser.add_argument("--ticks", type=int, default=1)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--record-sample", type=Path, default=None)
    parser.add_argument(
        "--fixture",
        type=Path,
        default=Path("tests/fixtures/datssol/arena_sample.json"),
    )
    return parser.parse_args()


def load_settings(config_path: Path | None) -> FullSettings:
    if config_path is None:
        return load_from_env()
    return load_from_yaml(config_path)


def build_client(settings: FullSettings) -> DatsSolClient:
    return _build_datssol_client(settings)


def _load_fixture(path: Path) -> ArenaResponse:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        payload = payload[0]
    return ArenaResponse.model_validate(payload)


def main() -> None:
    args = parse_args()
    settings = load_settings(args.config)
    client = build_client(settings)

    if args.logs:
        print(json.dumps(client.logs().model_dump(exclude_none=True), ensure_ascii=False, indent=2))
        if args.once:
            return

    for _ in range(max(1, args.ticks)):
        arena = _load_fixture(args.fixture) if args.dry_run_submit else client.arena()
        state = to_canonical(arena).state

        if args.poll_only:
            print(
                json.dumps(
                    {"tick": state.tick, "meta": state.metadata},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            if args.once:
                break
            continue

        action = DatsSolBaselineStrategy().choose_action(
            state,
            budget=TickBudget(tick=state.tick, deadline_ms=900),
        )
        validated = DatsSolSemanticValidator().validate(action, state)
        candidate = ActionEnvelope(tick=state.tick, payload=validated.payload, reason=action.reason)

        result: dict[str, object]
        if args.dry_run_submit:
            result = {
                "code": 0,
                "errors": [],
                "dry_run": True,
                "payload": candidate.payload,
                "semantic_success": validated.semantic_success,
            }
        else:
            request = CommandRequest.model_validate(candidate.payload)
            if not request.has_useful_action():
                result = {"code": 0, "errors": ["no useful action"], "semantic_success": False}
            else:
                outcome = client.submit_command(
                    request,
                    next_turn_in_seconds=client.last_next_turn_in_seconds,
                )
                result = outcome.response.model_dump(exclude_none=True)
                result["semantic_success"] = outcome.semantic_success

        output = {
            "tick": state.tick,
            "reason": candidate.reason,
            "action": candidate.payload,
            "validation_errors": list(validated.errors),
            "result": result,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))

        if args.record_sample is not None:
            args.record_sample.write_text(
                json.dumps(arena.model_dump(exclude_none=True), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        if args.once:
            break


if __name__ == "__main__":
    main()
