from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from datsteam_core.replay.schema import ReplayTickEnvelope, upgrade_legacy_record


@dataclass(frozen=True)
class ReplaySummary:
    files: int
    tick_min: int | None
    tick_max: int | None
    action_count: int
    non_success_results: int
    fallback_count: int
    parser_unknown_field_count: int

    def as_dict(self) -> dict[str, object]:
        return {
            "files": self.files,
            "tick_min": self.tick_min,
            "tick_max": self.tick_max,
            "action_count": self.action_count,
            "non_success_results": self.non_success_results,
            "fallback_count": self.fallback_count,
            "parser_unknown_field_count": self.parser_unknown_field_count,
        }


def _to_envelope(payload: dict[str, Any]) -> ReplayTickEnvelope:
    if payload.get("schema_version") == "replay.v2":
        return ReplayTickEnvelope(
            schema_version="replay.v2",
            session_id=str(payload.get("session_id", "")),
            round_id=str(payload.get("round_id", "")),
            turn_id=int(payload.get("turn_id", 0)),
            server_tick=int(payload.get("server_tick", payload.get("turn_id", 0))),
            request_payload=dict(payload.get("request_payload", {})),
            response_payload=dict(payload.get("response_payload", {})),
            canonical_state=dict(payload.get("canonical_state", {})),
            chosen_action=dict(payload.get("chosen_action", {})),
            candidate_actions=list(payload.get("candidate_actions", [])),
            candidate_scores=list(payload.get("candidate_scores", [])),
            latency_ms=payload.get("latency_ms"),
            remaining_budget_ms=payload.get("remaining_budget_ms"),
            fallback_flags=dict(payload.get("fallback_flags", {})),
            validation_flags=dict(payload.get("validation_flags", {})),
            parser_extras=dict(payload.get("parser_extras", {})),
        )
    return upgrade_legacy_record(payload)


def summarize_replay_dir(replay_dir: Path) -> ReplaySummary:
    ticks: list[int] = []
    actions = 0
    non_success = 0
    fallback_count = 0
    unknown_count = 0

    files = sorted(replay_dir.glob("tick_*.json"))
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        envelope = _to_envelope(payload)

        ticks.append(envelope.server_tick)

        action = envelope.chosen_action.get("payload")
        if isinstance(action, dict):
            actions += 1

        if envelope.response_payload.get("success") is not True:
            non_success += 1

        if any(envelope.fallback_flags.values()):
            fallback_count += 1

        unknowns = envelope.parser_extras.get("unknown_fields")
        if isinstance(unknowns, list):
            unknown_count += len(unknowns)

    return ReplaySummary(
        files=len(files),
        tick_min=min(ticks) if ticks else None,
        tick_max=max(ticks) if ticks else None,
        action_count=actions,
        non_success_results=non_success,
        fallback_count=fallback_count,
        parser_unknown_field_count=unknown_count,
    )
