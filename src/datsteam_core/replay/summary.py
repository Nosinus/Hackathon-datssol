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
    dropped_or_invalid_commands: int
    transport_error_count: int
    latency_avg_ms: float | None
    latency_p50_ms: int | None
    latency_p95_ms: int | None
    run_ids: list[str]
    policy_ids: list[str]

    def as_dict(self) -> dict[str, object]:
        return {
            "files": self.files,
            "tick_min": self.tick_min,
            "tick_max": self.tick_max,
            "action_count": self.action_count,
            "non_success_results": self.non_success_results,
            "fallback_count": self.fallback_count,
            "parser_unknown_field_count": self.parser_unknown_field_count,
            "dropped_or_invalid_commands": self.dropped_or_invalid_commands,
            "transport_error_count": self.transport_error_count,
            "latency_avg_ms": self.latency_avg_ms,
            "latency_p50_ms": self.latency_p50_ms,
            "latency_p95_ms": self.latency_p95_ms,
            "run_ids": self.run_ids,
            "policy_ids": self.policy_ids,
        }


def _to_envelope(payload: dict[str, Any]) -> ReplayTickEnvelope:
    if payload.get("schema_version") in {"replay.v2", "replay.v3"}:
        canonical_state = dict(payload.get("canonical_state", {}))
        action = dict(payload.get("chosen_action", {}))
        return ReplayTickEnvelope(
            schema_version="replay.v3",
            session_id=str(payload.get("session_id", "")),
            round_id=str(payload.get("round_id", "")),
            turn_id=int(payload.get("turn_id", 0)),
            server_tick=int(payload.get("server_tick", payload.get("turn_id", 0))),
            state_hash=str(payload.get("state_hash", "")),
            strategy_id=str(payload.get("strategy_id", "unknown_strategy")),
            action_reason=str(payload.get("action_reason", action.get("reason", ""))),
            request_payload=dict(payload.get("request_payload", {})),
            response_payload=dict(payload.get("response_payload", {})),
            canonical_state=canonical_state,
            chosen_action=action,
            validator_result=dict(payload.get("validator_result", {})),
            request_meta=dict(payload.get("request_meta", {})),
            response_meta=dict(payload.get("response_meta", {})),
            transport_error=payload.get("transport_error")
            if isinstance(payload.get("transport_error"), dict)
            else None,
            fallback_used=bool(payload.get("fallback_used", False)),
            candidate_count=int(payload.get("candidate_count", 0)),
            candidate_actions=list(payload.get("candidate_actions", [])),
            candidate_scores=list(payload.get("candidate_scores", [])),
            latency_ms=payload.get("latency_ms"),
            remaining_budget_ms=payload.get("remaining_budget_ms"),
            fallback_flags=dict(payload.get("fallback_flags", {})),
            validation_flags=dict(payload.get("validation_flags", {})),
            parser_extras=dict(payload.get("parser_extras", {})),
            run_metadata=dict(payload.get("run_metadata", {})),
        )
    return upgrade_legacy_record(payload)


def _percentile(values: list[int], p: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = int(round((len(ordered) - 1) * p))
    return ordered[idx]


def summarize_replay_dir(replay_dir: Path) -> ReplaySummary:
    ticks: list[int] = []
    actions = 0
    non_success = 0
    fallback_count = 0
    unknown_count = 0
    dropped_or_invalid = 0
    transport_error_count = 0
    latencies: list[int] = []
    run_ids: set[str] = set()
    policy_ids: set[str] = set()

    files = sorted(replay_dir.glob("tick_*.json"))
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        envelope = _to_envelope(payload)

        ticks.append(envelope.server_tick)

        action = envelope.chosen_action.get("payload")
        if isinstance(action, dict):
            actions += 1

        if _infer_result_success(envelope.response_payload) is not True:
            non_success += 1

        if envelope.fallback_used or any(envelope.fallback_flags.values()):
            fallback_count += 1

        unknowns = envelope.parser_extras.get("unknown_fields")
        if isinstance(unknowns, list):
            unknown_count += len(unknowns)

        if envelope.validator_result.get("dropped_invalid", False) or envelope.validation_flags.get(
            "sanitized", False
        ):
            dropped_or_invalid += 1

        if envelope.transport_error is not None:
            transport_error_count += 1

        if isinstance(envelope.latency_ms, int):
            latencies.append(envelope.latency_ms)
        run_id = envelope.run_metadata.get("run_id")
        if isinstance(run_id, str) and run_id:
            run_ids.add(run_id)
        policy_id = envelope.run_metadata.get("policy_id")
        if isinstance(policy_id, str) and policy_id:
            policy_ids.add(policy_id)

    avg = (sum(latencies) / len(latencies)) if latencies else None

    return ReplaySummary(
        files=len(files),
        tick_min=min(ticks) if ticks else None,
        tick_max=max(ticks) if ticks else None,
        action_count=actions,
        non_success_results=non_success,
        fallback_count=fallback_count,
        parser_unknown_field_count=unknown_count,
        dropped_or_invalid_commands=dropped_or_invalid,
        transport_error_count=transport_error_count,
        latency_avg_ms=avg,
        latency_p50_ms=_percentile(latencies, 0.5),
        latency_p95_ms=_percentile(latencies, 0.95),
        run_ids=sorted(run_ids),
        policy_ids=sorted(policy_ids),
    )


def _infer_result_success(payload: dict[str, object]) -> bool | None:
    success = payload.get("success")
    if isinstance(success, bool):
        return success
    code = payload.get("code")
    errors = payload.get("errors")
    if isinstance(code, int):
        if isinstance(errors, list):
            return code == 0 and len(errors) == 0
        return code == 0
    return None
